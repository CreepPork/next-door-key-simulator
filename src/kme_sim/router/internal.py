import os

import flask

from network.scanner import Scanner
from keys.key_store import KeyStore

import logger.logger as logger

# noinspection PyMethodMayBeStatic
class Internal:
    def __init__(self, scanner: Scanner, key_store: KeyStore):
        self.scanner = scanner
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

    def get_network(self):
        return self.scanner.kme_list

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

    def do_announce(self, request: flask.Request):
        logger.debug('Someone is announcing')

        # Prevent double requests
        self.scanner.do_not_announce.set()

        self.scanner.stop.set()
        self.scanner.stop.clear()

        logger.debug('Announcement finished')

        return {'message': 'Scanner is being re-run.'}
