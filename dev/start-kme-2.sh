#!/bin/bash
set -e

# Change working directory
__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$__dir"

source ../venv/bin/activate

ls ../*.py | PORT=8020 \
KME_ID=ffb23f4d-5d5b-47e5-a8c5-fe9e47d646cd \
ATTACHED_SAE_ID=c565d5aa-8670-4446-8471-b0e53e315d2a \
DEFAULT_KEY_SIZE=32 \
MAX_KEY_COUNT=100000 \
MAX_KEYS_PER_REQUEST=128 \
MAX_KEY_SIZE=1024 \
MIN_KEY_SIZE=32 \
KEY_GEN_SEC_TO_GEN=30 \
OTHER_KMES=https://127.0.0.1:8010,https://127.0.0.1:8030 \
CA_FILE=../certs/ca.crt.pem \
KME_CERT=../certs/kme-2.crt.pem \
KME_KEY=../certs/kme-2.key.pem \
SAE_CERT=../certs/sae-2.crt.pem \
entr -r python3 ../app.py