import base64
import os
import uuid


class KeyGenerator:
    @staticmethod
    def generate_key(size: int) -> dict:
        return {
            'key_ID': str(uuid.uuid4()),
            'key': base64.b64encode(os.urandom(size)).decode('ascii')
        }
