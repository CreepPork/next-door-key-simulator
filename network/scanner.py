import os
import threading

import requests


class Scanner:
    def __init__(self, kme_list: list, kme_lock: threading.Lock):
        self.kme_list = kme_list
        self.kme_lock = kme_lock
        self.stop = threading.Event()

    def start(self) -> None:
        while not self.stop.is_set():
            self.kme_lock.acquire(blocking=True)

            old_kme_list = list(map(lambda x: x['KME_ID'], self.kme_list))

            self.kme_list.clear()

            for kme in os.getenv('OTHER_KMES').split(','):
                try:
                    data = requests.get(
                        url=f'{kme}/api/v1/kme/status',
                        verify=False,
                        cert=(os.getenv('KME_CERT'), os.getenv('KME_KEY'))
                    ).json()

                    self.kme_list.append(data)
                except requests.exceptions.RequestException:
                    print(f'Unable to fetch KME status for {kme}.')
                except requests.exceptions.JSONDecodeError:
                    print(f'KME {kme} did not return a valid JSON response.')

            new_kme_list = set(list(map(lambda x: x['KME_ID'], self.kme_list)) + old_kme_list)

            if len(self.kme_list) == 0 and len(old_kme_list) > 0:
                print('Lost all KMEs from the domain!')
            elif len(self.kme_list) != 0 and len(new_kme_list) != len(old_kme_list):
                print('Refreshed KME statuses, established new domain of KMEs:')
                print(self.kme_list)

            self.kme_lock.release()
            self.stop.wait(15)

    def find_kme(self, sae_id: str) -> tuple[str, str] | None:
        if os.getenv('ATTACHED_SAE_ID') == sae_id:
            return os.getenv('KME_ID'), os.getenv('ATTACHED_SAE_ID')

        for value in self.kme_list:
            if value['SAE_ID'] == sae_id:
                return value['KME_ID'], value['SAE_ID']

        return None
