import asyncio
import base64
import sys
from asyncio import StreamReader, StreamWriter

import requests
import urllib3
from cryptography.fernet import Fernet

KME_LIST = [
    ('https://127.0.0.1:8010', ('../../certs/sae-1.crt.pem', '../../certs/sae-1.key.pem'),
     '25840139-0dd4-49ae-ba1e-b86731601803'),
    ('https://127.0.0.1:8020', ('../../certs/sae-2.crt.pem', '../../certs/sae-2.key.pem'),
     'c565d5aa-8670-4446-8471-b0e53e315d2a')
]


class KmeModule:
    def __init__(self, kme_data: tuple):
        self.kme_url = kme_data[0]
        self.kme_certs = kme_data[1]
        self.sae_id = kme_data[2]

    def __post(self, url: str, data: dict) -> dict:
        response = requests.post(f'{self.kme_url}{url}', verify=False, cert=self.kme_certs, json=data)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            print(f'ERR: {response.json()}')
            raise

        return response.json()

    def create_key(self, slave_sae_id: str) -> dict:
        return self.__post(f'/api/v1/keys/{slave_sae_id}/enc_keys', {
            'number': 1,
            'size': 32  # Fernet key length
        })['keys'][0]

    def get_key(self, master_sae_id: str, key_id: str) -> dict:
        return self.__post(f'/api/v1/keys/{master_sae_id}/dec_keys', {
            'key_IDs': [
                {
                    'key_ID': key_id
                }
            ]
        })

    def encrypt_message(self, key: str, message: str) -> bytes:
        return base64.b64encode(
            Fernet(key).encrypt(message.encode())
        )

    def decrypt_message(self, key: str, message: bytes) -> bytes:
        return Fernet(key).decrypt(base64.b64decode(message))


class ChatClient:
    def __init__(self, reader: StreamReader, writer: StreamWriter, selected_kme: tuple):
        self.reader = reader
        self.writer = writer
        self.kme = KmeModule(selected_kme)

        self.encryption_key = None

    async def handle_messages(self):
        while True:
            data = await self.reader.read(4096)

            if not data:
                break

            if data.decode().startswith('<system,'):
                await self.handle_system_message(data.decode())
            else:
                message = self.kme.decrypt_message(self.encryption_key, data).decode()

                print(f'\n[Other]: {message}\n[You]: ', end='')

    async def handle_system_message(self, message: str):
        print(f'\n[System]: {message}')

        # Received only when a different client connects
        if message == '<system,joined>':
            await self.__send_message('<system,send_sae_id>', encrypt=False)
        elif message.startswith('<system,send_sae_id>'):
            await self.__send_message(f'<system,sae_id,{self.kme.sae_id}>', encrypt=False)
        elif message.startswith('<system,sae_id,'):
            await self.generate_encryption_key(message.split('<system,sae_id,')[1][:-1])
        elif message.startswith('<system,new_key,'):
            data_blocks = message.split('<system,new_key,')[1][:-1]
            master_sae_id, key_id = data_blocks.split(',')

            await self.load_encryption_key(master_sae_id, key_id)

    async def generate_encryption_key(self, slave_sae_id: str):
        key_data = self.kme.create_key(slave_sae_id)
        self.encryption_key = key_data['key']

        await self.__send_message(f'<system,new_key,{self.kme.sae_id},{key_data["key_ID"]}>', encrypt=False)

    async def load_encryption_key(self, master_sae_id: str, key_id: str):
        # Minimize race condition that the key will not be exchanged as quickly as it is retrieved
        print('<loading encryption key...>')
        await asyncio.sleep(3)

        self.encryption_key = self.kme.get_key(master_sae_id, key_id)['keys'][0]['key']
        print('<encryption key loaded>')

    def get_input(self):
        return input('[You]: ')

    async def __send_message(self, message, encrypt=True):
        if self.encryption_key and encrypt:
            self.writer.write(self.kme.encrypt_message(self.encryption_key, message))
        else:
            self.writer.write(message.encode())

        await self.writer.drain()

    async def send_message(self):
        while True:
            message = await asyncio.to_thread(self.get_input)
            await self.__send_message(message)


def select_kme() -> tuple:
    for i, kme in enumerate(KME_LIST):
        print(f'[{i}]: {kme[0]}')

    selected = input('Select attached KME by entering number: ')

    try:
        return KME_LIST[int(selected)]
    except IndexError:
        print('Invalid KME selected!')

        sys.exit(1)


async def main():
    # Disable unsecure HTTPS warnings (e.g. invalid certificate)
    urllib3.disable_warnings()

    selected_kme = select_kme()

    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)

    chat_client = ChatClient(reader, writer, selected_kme)

    await asyncio.gather(
        chat_client.handle_messages(),
        chat_client.send_message()
    )


if __name__ == "__main__":
    asyncio.run(main())
