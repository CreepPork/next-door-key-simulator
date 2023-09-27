import base64
import json
import os
import ssl
import threading
import uuid

import OpenSSL
import flask
import requests
import urllib3
from dotenv import load_dotenv
from flask import Flask, request
from markupsafe import escape

from request_handler import PeerCertWSGIRequestHandler

load_dotenv('.env')
app = Flask(__name__)

KME_LIST = []
SCANNING_FOR_KMES = threading.Lock()

KEY_STORE = []


def __setup_app():
    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH, cafile=os.getenv('CA_FILE'))
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(os.getenv('KME_CERT'), os.getenv('KME_KEY'))
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False

    app.run(host=os.getenv('HOST'), port=os.getenv('PORT'), ssl_context=context, request_handler=PeerCertWSGIRequestHandler)


def __validate_sae_id():
    sae_id = request.environ['client_cert_common_name']

    if sae_id != os.getenv('ATTACHED_SAE_ID'):
        print('Client cert common name does not match the attached_sae_id value!')
        flask.abort(401)

    sae_x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, open(os.getenv('SAE_CERT'), 'rb').read())

    if sae_x509.get_serial_number() != request.environ['client_cert_serial_number']:
        print('Client cert serial number does not match the loaded SAE certificate serial number!')
        flask.abort(401)


def __start_kme_scan(stop: threading.Event):
    while not stop.is_set():
        SCANNING_FOR_KMES.acquire(blocking=True)

        old_kmes = list(map(lambda x: x['KME_ID'], KME_LIST))

        KME_LIST.clear()

        for kme in os.getenv('OTHER_KMES').split(','):
            try:
                data = requests.get(f'{kme}/api/v1/kme/status', verify=False, cert=(os.getenv('KME_CERT'), os.getenv('KME_KEY'))).json()

                KME_LIST.append(data)
            except requests.exceptions.RequestException:
                print(f'Unable to fetch KME status for {kme}.')
            except requests.exceptions.JSONDecodeError:
                print(f'KME {kme} did not return a valid JSON response.')

        new_kmes = set(list(map(lambda x: x['KME_ID'], KME_LIST)) + old_kmes)

        if len(KME_LIST) == 0 and len(old_kmes) > 0:
            print('Lost all KMEs from the domain!')
        elif len(KME_LIST) != 0 and len(new_kmes) != len(old_kmes):
            print('Refreshed KME statuses, established new domain of KMEs:')
            print(KME_LIST)

        SCANNING_FOR_KMES.release()
        stop.wait(15)


def find_kme_by_sae_id(sae_id: str) -> tuple[str, str] | None:
    if os.getenv('ATTACHED_SAE_ID') == sae_id:
        return os.getenv('KME_ID'), os.getenv('ATTACHED_SAE_ID')

    for value in KME_LIST:
        if value['SAE_ID'] == sae_id:
            return value['KME_ID'], value['SAE_ID']

    return None


def get_stored_keys(master_sae_id: str, slave_sae_id: str) -> list:
    container = list(filter(
        lambda x: x['master_sae_id'] == master_sae_id and x['slave_sae_id'] == slave_sae_id,
        KEY_STORE
    ))

    return [] if len(container) == 0 else container[0]['keys']


def append_keys_to_sae_id(master_sae_id: str, slave_sae_id: str, keys: list, do_exchange: bool = True) -> list:
    container = get_stored_keys(master_sae_id, slave_sae_id)

    if len(container) > 0:
        for key in keys:
            container.append(key)

        keys = container
    else:
        KEY_STORE.append({'master_sae_id': master_sae_id, 'slave_sae_id': slave_sae_id, 'keys': keys})

    if do_exchange:
        send_keys_to_other_kme(master_sae_id, slave_sae_id, keys)

    return keys


def send_keys_to_other_kme(master_sae_id: str, slave_sae_id: str, keys: list) -> None:
    for kme in os.getenv('OTHER_KMES').split(','):
        requests.post(
            f'{kme}/api/v1/kme/keys/exchange',
            verify=False,
            cert=(os.getenv('KME_CERT'), os.getenv('KME_KEY')),
            json=json.loads(json.dumps({
                'master_sae_id': master_sae_id,
                'slave_sae_id': slave_sae_id,
                'keys': keys
            }, default=str)))


def remove_keys_from_other_kmes(master_sae_id: str, slave_sae_id: str, keys: list) -> None:
    for kme in os.getenv('OTHER_KMES').split(','):
        requests.post(
            f'{kme}/api/v1/kme/keys/remove',
            verify=False,
            cert=(os.getenv('KME_CERT'), os.getenv('KME_KEY')),
            json=json.loads(json.dumps({
                'master_sae_id': master_sae_id,
                'slave_sae_id': slave_sae_id,
                'keys': keys
            }, default=str)))


def remove_keys_from_key_store(master_sae_id: str, slave_sae_id: str, keys: list, do_exchange: bool = True) -> None:
    for key in keys:
        for i, value in enumerate(KEY_STORE):
            if value['master_sae_id'] == master_sae_id and value['slave_sae_id'] == slave_sae_id:
                for j, k in enumerate(value['keys']):
                    if k['key_ID'] == key['key_ID']:
                        del KEY_STORE[i]['keys'][j]

                        break

    if do_exchange:
        remove_keys_from_other_kmes(master_sae_id, slave_sae_id, keys)


def main():
    stop = threading.Event()

    try:
        kme_scanner_thread = threading.Thread(target=__start_kme_scan, args=[stop])
        kme_scanner_thread.start()

        __setup_app()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()


@app.before_request
def before_request():
    SCANNING_FOR_KMES.acquire(blocking=True)


@app.after_request
def after_request(response):
    SCANNING_FOR_KMES.release()

    return response


@app.route('/api/v1/kme/status')
def get_kme_status():
    return {
        'KME_ID': os.getenv('KME_ID'),
        'SAE_ID': os.getenv('ATTACHED_SAE_ID'),
    }


@app.route('/api/v1/kme/keys/exchange', methods=['POST'])
def key_exchange():
    data = request.get_json()

    return append_keys_to_sae_id(data['master_sae_id'], data['slave_sae_id'], data['keys'], do_exchange=False)


@app.route('/api/v1/kme/keys/remove', methods=['POST'])
def key_remove_exchange():
    data = request.get_json()

    remove_keys_from_key_store(data['master_sae_id'], data['slave_sae_id'], data['keys'], do_exchange=False)

    return {'message': 'ok'}


@app.route('/api/v1/keys/<slave_sae_id>/status')
def get_status(slave_sae_id):
    __validate_sae_id()

    slave_sae_id = escape(slave_sae_id)
    kme = find_kme_by_sae_id(slave_sae_id)

    if kme is None:
        return {'message': 'The given slave SAE ID is unknown by this KME.'}, 400

    is_this_sae_slave = slave_sae_id == os.getenv('ATTACHED_SAE_ID')
    master_sae_id = kme[1] if is_this_sae_slave else os.getenv('ATTACHED_SAE_ID')

    return {
        'source_KME_ID': kme[0] if is_this_sae_slave else os.getenv('KME_ID'),
        'target_KME_ID': os.getenv('KME_ID') if is_this_sae_slave else kme[0],
        'master_SAE_ID': master_sae_id,
        'slave_SAE_ID': slave_sae_id,
        'key_size': int(os.getenv('DEFAULT_KEY_SIZE')),
        'stored_key_count': len(
            get_stored_keys(master_sae_id, slave_sae_id)
            + get_stored_keys(slave_sae_id, master_sae_id)),
        'max_key_count': int(os.getenv('MAX_KEY_COUNT')),
        'max_key_per_request': int(os.getenv('MAX_KEYS_PER_REQUEST')),
        'max_key_size': int(os.getenv('MAX_KEY_SIZE')),
        'min_key_size': int(os.getenv('MIN_KEY_SIZE')),
        'max_SAE_ID_count': 0
    }


@app.route('/api/v1/keys/<slave_sae_id>/enc_keys', methods=['POST'])
def get_key(slave_sae_id):
    __validate_sae_id()

    # Prepare data
    slave_sae_id = escape(slave_sae_id)
    data = request.get_json()

    # Get data
    number_of_keys = data.get('number', 1)
    key_size = data.get('size', os.getenv('DEFAULT_KEY_SIZE'))

    # Validate data
    if number_of_keys > int(os.getenv('MAX_KEYS_PER_REQUEST')):
        return {'message': 'Number of requested keys exceed allowed max keys per request.'}, 400

    if key_size > int(os.getenv('MAX_KEY_SIZE')):
        return {'message': 'The requested key size is too large.'}, 400

    if key_size < int(os.getenv('MIN_KEY_SIZE')):
        return {'message': 'The requested key size is too small.'}, 400

    kme = find_kme_by_sae_id(slave_sae_id)

    if kme is None:
        return {'message': 'The given slave SAE ID is unknown by this KME.'}, 400

    is_this_sae_slave = slave_sae_id == os.getenv('ATTACHED_SAE_ID')
    master_sae_id = kme[1] if is_this_sae_slave else os.getenv('ATTACHED_SAE_ID')

    if len(get_stored_keys(master_sae_id, slave_sae_id)) + number_of_keys > int(os.getenv('MAX_KEY_COUNT')):
        return {'message': 'The requested total of keys exceeds the maximum key count that can be stored.'}, 400

    # Generate keys
    keys = []

    for i in range(number_of_keys):
        keys.append(__generate_key(key_size))

    append_keys_to_sae_id(master_sae_id, slave_sae_id, keys)

    return {'keys': keys}


@app.route('/api/v1/keys/<master_sae_id>/dec_keys', methods=['POST'])
def get_key_with_ids(master_sae_id):
    __validate_sae_id()

    # Get data
    master_sae_id = escape(master_sae_id)
    slave_sae_id = request.environ['client_cert_common_name']

    data = request.get_json()

    # Validate data
    if len(get_stored_keys(master_sae_id, slave_sae_id)) == 0 or len(get_stored_keys(slave_sae_id, master_sae_id)) == 0:
        return {'message': 'The given master_sae_id is not involved in any key exchanges.'}, 401

    try:
        # Get the keys & prepare for removal those that just have been used
        requested_keys = list(map(lambda x: x['key_ID'], data['key_IDs']))

        selected_keys = list(filter(
            lambda x: x['key_ID'] in requested_keys,
            get_stored_keys(master_sae_id, request.environ['client_cert_common_name'])
        ))
    except IndexError:
        return {'message': 'The given data is in invalid format.'}, 400

    if len(requested_keys) != len(selected_keys):
        return {'message': 'Some of the requested keys do not exist in this KME.'}, 400

    # Remove from the key store and broadcast to other KMEs
    remove_keys_from_key_store(master_sae_id, request.environ['client_cert_common_name'], selected_keys)

    return {'keys': selected_keys}


def __generate_key(size: int) -> dict:
    return {'key_ID': str(uuid.uuid4()), 'key': base64.b64encode(os.urandom(size)).decode('ascii')}


if __name__ == '__main__':
    urllib3.disable_warnings()
    main()
