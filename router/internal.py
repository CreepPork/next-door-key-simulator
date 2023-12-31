import os

import flask

from keys.key_store import KeyStore


# noinspection PyMethodMayBeStatic
class Internal:
    def __init__(self, key_store: KeyStore):
        self.key_store = key_store

    def get_kme_status(self):
        return {
            'KME_ID': os.getenv('KME_ID'),
            'SAE_ID': os.getenv('ATTACHED_SAE_ID'),
        }

    def get_key_pool(self):
        return {
            'keys': self.key_store.key_pool.keys
        }

    def do_kme_key_exchange(self, request: flask.Request):
        data = request.get_json()

        return self.key_store.append_keys(
            data['master_sae_id'],
            data['slave_sae_id'],
            data['keys'],
            do_broadcast=False)

    def do_remove_kme_key(self, request: flask.Request):
        data = request.get_json()

        self.key_store.remove_keys(
            data['master_sae_id'],
            data['slave_sae_id'],
            data['keys'],
            do_broadcast=False)

        return {'message': 'Keys have been removed from the local key store.'}
