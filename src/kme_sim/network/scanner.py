import os
import random
import threading

import requests

import logger.logger as logger

class Scanner:
    def __init__(self, kme_list: list, kme_lock: threading.Lock):
        self.kme_list = kme_list
        self.kme_lock = kme_lock

        self.do_not_announce = threading.Event()
        self.stop = threading.Event()

    def start(self) -> None:
        while not self.stop.is_set():
            logger.debug('Acquiring kme_lock')

            if not self.kme_lock.acquire(blocking=True, timeout=30):
                logger.warn('Failed to acquire kme_lock in scanner thread')
                continue

            logger.debug('Acquired kme_lock')

            old_kme_list = list(map(lambda x: x['KME_ID'], self.kme_list))

            self.kme_list.clear()

            for kme in os.getenv('OTHER_KMES').split(','):
                try:
                    logger.debug(f'Getting KME status from {kme}...')

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
                    logger.error(f'Unable to fetch KME status for {kme}.')
                    logger.error(exception)
                except requests.exceptions.JSONDecodeError:
                    logger.error(f'KME {kme} did not return a valid JSON response.')

            new_kme_list = set(list(map(lambda x: x['KME_ID'], self.kme_list)) + old_kme_list)

            if len(self.kme_list) == 0 and len(old_kme_list) > 0:
                logger.warn('Lost all KMEs from the domain!')
            elif len(self.kme_list) != 0 and len(new_kme_list) != len(old_kme_list):
                logger.info('Refreshed KME statuses, established new domain of KMEs:')
                logger.info(self.kme_list)

                self.announce_presence()

            self.kme_lock.release()

            logger.debug('KME scanner paused')
            self.stop.wait(random.randint(10, 20))
            logger.debug('KME scanner running')

        logger.warn('KME scanner has exited')

    def find_kme(self, sae_id: str) -> tuple[str, str] | None:
        if os.getenv('ATTACHED_SAE_ID') == sae_id:
            return os.getenv('KME_ID'), os.getenv('ATTACHED_SAE_ID')

        for value in self.kme_list:
            if value['SAE_ID'] == sae_id:
                return value['KME_ID'], value['SAE_ID']

        return None

    def announce_presence(self):
        if self.do_not_announce.is_set():
            return

        for kme in self.kme_list:
            logger.debug('Announcing to everyone')

            requests.post(
                url=f'{kme["KME_URL"]}/api/v1/kme/announce',
                verify=False,
                cert=(os.getenv('KME_CERT'), os.getenv('KME_KEY')),
                timeout=15
            )

