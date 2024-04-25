from keys.key_pool import KeyPool
from network.broadcaster import Broadcaster


# noinspection PyMethodMayBeStatic
class KeyStore:
    def __init__(self, key_pool: KeyPool, broadcaster: Broadcaster):
        self.container: list[dict[str, str, list]] = []
        self.key_pool = key_pool
        self.broadcaster = broadcaster

    def get_sae_key_container(self, master_sae_id: str, slave_sae_id) -> list:
        return list(filter(
            lambda x: x['master_sae_id'] == master_sae_id and x['slave_sae_id'] == slave_sae_id,
            self.container
        ))

    def get_new_key(self, key_size: int) -> dict[str, str] | None:
        return self.key_pool.get_key(key_size)

    def get_keys(self, master_sae_id: str, slave_sae_id: str) -> list:
        container = self.get_sae_key_container(master_sae_id, slave_sae_id)

        return [] if len(container) == 0 else container[0]['keys']

    def append_keys(self, master_sae_id: str, slave_sae_id: str, keys: list, do_broadcast: bool = True) -> list:
        container = self.get_sae_key_container(master_sae_id, slave_sae_id)

        if len(container) == 0:
            self.container.append({'master_sae_id': master_sae_id, 'slave_sae_id': slave_sae_id, 'keys': keys})
        else:
            # Remove the old keys
            self.container = list(filter(
                lambda x: x['master_sae_id'] != master_sae_id and x['slave_sae_id'] != slave_sae_id,
                self.container
            ))

            # Append new keys
            self.container.append({'master_sae_id': master_sae_id, 'slave_sae_id': slave_sae_id, 'keys': keys})

        if do_broadcast:
            self.broadcaster.send_keys(master_sae_id, slave_sae_id, keys)

        return keys

    def remove_keys(self, master_sae_id: str, slave_sae_id: str, keys: list, do_broadcast: bool = True):
        for key in keys:
            for i, value in enumerate(self.container):
                if value['master_sae_id'] == master_sae_id and value['slave_sae_id'] == slave_sae_id:
                    for j, k in enumerate(value['keys']):
                        if k['key_ID'] == key['key_ID']:
                            del self.container[i]['keys'][j]

                            break

        if do_broadcast:
            self.broadcaster.remove_keys(master_sae_id, slave_sae_id, keys)
