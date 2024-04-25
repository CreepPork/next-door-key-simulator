import os
import random
import threading

import requests


class Scanner:
    def __init__(self, kme_list: list, kme_lock: threading.Lock):
        self.kme_list = kme_list
        self.kme_lock = kme_lock
        self.stop = threading.Event()

    def start(self) -> None:
        while not self.stop.is_set():
            logger.debug('DEBG: Acquiring kme_lock')

            if not self.kme_lock.acquire(blocking=True, timeout=30):
                print('WARN: Failed to acquire kme_lock in scanner thread')
                continue

            print('DEBG: Acquired kme_lock')

            old_kme_list = list(map(lambda x: x['KME_ID'], self.kme_list))

            self.kme_list.clear()

            for kme in os.getenv('OTHER_KMES').split(','):
                try:
                    print(f'DEBG: Getting KME status from {kme}...')
                    data = requests.get(
                        url=f'{kme}/api/v1/kme/status',
                        verify=False,
                        cert=(os.getenv('KME_CERT'), os.getenv('KME_KEY')),
                        timeout=15
                    ).json()

                    self.kme_list.append({
                        'KME_ID': data['KME_ID'],
                        'SAE_ID': data['SAE_ID'],
                        'KME_URL': kme,
                    })
                except requests.exceptions.RequestException as exception:
                    print(f'ERR: Unable to fetch KME status for {kme}.')
                    print(exception)
                except requests.exceptions.JSONDecodeError:
                    print(f'ERR: KME {kme} did not return a valid JSON response.')

            new_kme_list = set(list(map(lambda x: x['KME_ID'], self.kme_list)) + old_kme_list)

            if len(self.kme_list) == 0 and len(old_kme_list) > 0:
                print('WARN: Lost all KMEs from the domain!')
            elif len(self.kme_list) != 0 and len(new_kme_list) != len(old_kme_list):
                print('INFO: Refreshed KME statuses, established new domain of KMEs:')
                print(self.kme_list)

                self.announce_presence()

            self.kme_lock.release()
            print('DEBG: KME scanner paused')
            self.stop.wait(random.randint(10, 20))
            print('DEBG: KME scanner running')

        print('WARN: KME scanner has exited')

    def find_kme(self, sae_id: str) -> tuple[str, str] | None:
        if os.getenv('ATTACHED_SAE_ID') == sae_id:
            return os.getenv('KME_ID'), os.getenv('ATTACHED_SAE_ID')

        for value in self.kme_list:
            if value['SAE_ID'] == sae_id:
                return value['KME_ID'], value['SAE_ID']

        return None

    def announce_presence(self):
        for kme in self.kme_list:
            print('DEBG: Announcing to everyone')
            requests.post(
                url=f'{kme["KME_URL"]}/api/v1/kme/announce',
                verify=False,
                cert=(os.getenv('KME_CERT'), os.getenv('KME_KEY')),
            )

