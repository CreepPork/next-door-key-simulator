#!/bin/bash
set -e

# Change working directory
__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$__dir"

source ../venv/bin/activate

ls ../src/**/*.py | PORT=8030 \
KME_ID=b5c4f6a4-7236-4136-ac2b-4f0d888e80fb \
ATTACHED_SAE_ID=875845ac-dd9a-451b-b975-055fac89cefe \
DEFAULT_KEY_SIZE=32 \
MAX_KEY_COUNT=100000 \
MAX_KEYS_PER_REQUEST=128 \
MAX_KEY_SIZE=1024 \
MIN_KEY_SIZE=32 \
KEY_GEN_SEC_TO_GEN=30 \
OTHER_KMES=https://127.0.0.1:8010,https://127.0.0.1:8020 \
CA_FILE=../certs/ca.crt.pem \
KME_CERT=../certs/kme-3.crt.pem \
KME_KEY=../certs/kme-3.key.pem \
SAE_CERT=../certs/sae-3.crt.pem \
entr -r python3 ../src/kme-sim/app.py