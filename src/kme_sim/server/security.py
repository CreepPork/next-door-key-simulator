import os

import OpenSSL
import flask
from flask import Request

import logger.logger as logger


def ensure_valid_sae_id(request: Request):
    sae_id = request.environ['client_cert_common_name']

    if sae_id != os.getenv('ATTACHED_SAE_ID'):
        logger.error('Client cert common name does not match the attached_sae_id value!')
        flask.abort(401)

    sae_x509 = OpenSSL.crypto.load_certificate(
        OpenSSL.crypto.FILETYPE_PEM,
        open(os.getenv('SAE_CERT'), 'rb').read()
    )

    if sae_x509.get_serial_number() != request.environ['client_cert_serial_number']:
        logger.error('Client cert serial number does not match the loaded SAE certificate serial number!')
        flask.abort(401)
