import os
import ssl
from ssl import SSLContext


def create_ssl_context() -> SSLContext:
    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH, cafile=os.getenv('CA_FILE'))
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(os.getenv('KME_CERT'), os.getenv('KME_KEY'))
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False

    return context
