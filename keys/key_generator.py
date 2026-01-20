import base64
import os
import uuid

class KeyGenerator:
    @staticmethod
    def generate_key(size: int) -> dict:
        bits_bytes = int(size / 8)
        print(f"Requesting key of size {size} in bits / {bits_bytes} bytes")
        random_bytes = os.urandom(bits_bytes)
        print(f"Random bytes: {random_bytes}")
        generated_key = base64.b64encode(random_bytes).decode('ascii')
        print(f"Generated key: {generated_key}")
        return {
            'key_ID': str(uuid.uuid4()),
            'key': generated_key
        }