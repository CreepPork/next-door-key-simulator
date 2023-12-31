import os
import threading

from keys.key_generator import KeyGenerator


class KeyPool:
    def __init__(self, gen_lock: threading.Lock):
        self.keys: list[dict[str, str]] = []
        self.gen_lock = gen_lock
        self.stop = threading.Event()

        self.default_key_size = int(os.getenv('DEFAULT_KEY_SIZE'))
        self.max_key_count = int(os.getenv('MAX_KEY_COUNT'))

    def add_key(self) -> None:
        self.keys.append(KeyGenerator.generate_key(self.default_key_size))

    def get_key(self, key_size: int) -> dict[str, str] | None:
        if len(self.keys) == 0:
            return None

        # If non-default key size is requested, then we generate that directly.
        # Not sure how this would happen in the real device.
        if key_size and key_size != self.default_key_size:
            print('INFO: Generating key not from pool, for different size request')

            return KeyGenerator.generate_key(key_size)

        print(f'INFO: Removing key from pool ({len(self.keys) - 1}/{self.max_key_count})')

        return self.keys.pop()

    def start(self) -> None:
        while not self.stop.is_set():
            self.gen_lock.acquire(blocking=True)

            if len(self.keys) <= self.max_key_count:
                self.add_key()

                print(f'INFO: Key generated ({len(self.keys)}/{self.max_key_count})')
            else:
                print('INFO: Key pool is full')

            self.gen_lock.release()
            self.stop.wait(float(os.getenv('KEY_GEN_SEC_TO_GEN')))
