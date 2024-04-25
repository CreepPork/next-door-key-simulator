#!/bin/bash
set -e

# Change working directory
__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$__dir"

source ../venv/bin/activate

ls ../src/**/*.py | PORT=8010 \
KME_ID=9b7703f1-9b6d-403d-b850-18a1b6fd6d8f \
ATTACHED_SAE_ID=25840139-0dd4-49ae-ba1e-b86731601803 \
DEFAULT_KEY_SIZE=32 \
MAX_KEY_COUNT=100000 \
MAX_KEYS_PER_REQUEST=128 \
MAX_KEY_SIZE=1024 \
MIN_KEY_SIZE=32 \
KEY_GEN_SEC_TO_GEN=30 \
OTHER_KMES=https://127.0.0.1:8020,https://127.0.0.1:8030 \
CA_FILE=../certs/ca.crt.pem \
KME_CERT=../certs/kme-1.crt.pem \
KME_KEY=../certs/kme-1.key.pem \
SAE_CERT=../certs/sae-1.crt.pem \
entr -r python3 ../src/kme_sim/app.py