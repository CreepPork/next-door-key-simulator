import os

import flask

from keys.key_store import KeyStore
from network.scanner import Scanner
from server import security


# noinspection PyMethodMayBeStatic
class External:
    def __init__(self, scanner: Scanner, key_store: KeyStore):
        self.scanner = scanner
        self.key_store = key_store

    def get_status(self, request: flask.Request, slave_sae_id: str):
        security.ensure_valid_sae_id(request)

        kme = self.scanner.find_kme(slave_sae_id)

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
                self.key_store.get_keys(master_sae_id, slave_sae_id)
                + self.key_store.get_keys(slave_sae_id, master_sae_id)
            ),
            'max_key_count': int(os.getenv('MAX_KEY_COUNT')),
            'max_key_per_request': int(os.getenv('MAX_KEYS_PER_REQUEST')),
            'max_key_size': int(os.getenv('MAX_KEY_SIZE')),
            'min_key_size': int(os.getenv('MIN_KEY_SIZE')),
            'max_SAE_ID_count': 0
        }

    def get_key(self, request: flask.Request, slave_sae_id: str):
        security.ensure_valid_sae_id(request)

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

        kme = self.scanner.find_kme(slave_sae_id)

        if kme is None:
            return {'message': 'The given slave SAE ID is unknown by this KME.'}, 400

        is_this_sae_slave = slave_sae_id == os.getenv('ATTACHED_SAE_ID')
        master_sae_id = kme[1] if is_this_sae_slave else os.getenv('ATTACHED_SAE_ID')

        stored_keys = self.key_store.get_keys(master_sae_id, slave_sae_id)

        if len(stored_keys) + number_of_keys > int(os.getenv('MAX_KEY_COUNT')):
            return {'message': 'The requested total of keys exceeds the maximum key count that can be stored.'}, 400

        # Generate keys
        keys = []

        for i in range(number_of_keys):
            keys.append(self.key_store.generate_key(key_size))

        self.key_store.append_keys(master_sae_id, slave_sae_id, keys)

        return {'keys': keys}

    def get_key_with_ids(self, request: flask.Request, master_sae_id: str):
        security.ensure_valid_sae_id(request)

        # Get data
        slave_sae_id = request.environ['client_cert_common_name']
        data = request.get_json()

        # Validate data
        if len(self.key_store.get_keys(master_sae_id, slave_sae_id)) == 0 and len(
                self.key_store.get_keys(slave_sae_id, master_sae_id)) == 0:
            return {'message': 'The given master_sae_id is not involved in any key exchanges.'}, 401

        try:
            # Get the keys & prepare for removal those that just have been used
            requested_keys = list(map(lambda x: x['key_ID'], data['key_IDs']))

            selected_keys = list(filter(
                lambda x: x['key_ID'] in requested_keys,
                self.key_store.get_keys(master_sae_id, request.environ['client_cert_common_name'])
            ))
        except IndexError:
            return {'message': 'The given data is in invalid format.'}, 400

        if len(requested_keys) != len(selected_keys):
            return {'message': 'Some of the requested keys do not exist in this KME.'}, 400

        # Remove from the key store and broadcast to other KMEs
        self.key_store.remove_keys(master_sae_id, request.environ['client_cert_common_name'], selected_keys)

        return {'keys': selected_keys}
