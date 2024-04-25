#!/bin/bash
set -e

# Change working directory
__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$__dir"

echo "This will generate the keys based on the README instructions."
echo "And it will take into account the default structure and configuration of the docker-compose.yml file."
echo "This will only generate the keys for 3rd KME, to generate for KME 1 and KME 2, use the generate.sh script."

read -r -p "Do you want to continue? <Y/n> " prompt

if [[ $prompt == "n" || $prompt == "N" || $prompt == "no" || $prompt == "No" ]]
then
  exit 0
fi

ca_cert=$(grep "CA_FILE=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n 1p)

# Get KME 3
kme_3_cert=$(grep "KME_CERT=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n 3p)
kme_3_key=$(grep "KME_KEY=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n 3p)
kme_3_id=$(grep "KME_ID=" ../docker-compose.yml | sed 's/^.*=//' | sed -n 3p)

# Get SAE 3
sae_3_cert=$(grep "SAE_CERT=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n 3p)
sae_3_id=$(grep "ATTACHED_SAE_ID=" ../docker-compose.yml | sed 's/^.*=//' | sed -n 3p)

# List info
echo "CA: $ca_cert"

echo "KME 3: cert $kme_3_cert, key $kme_3_key, id $kme_3_id"
echo "SAE 3: cert $sae_3_cert, id $sae_3_id"

echo ""

# Generate KME 3
echo "Generating KME 3..."
openssl req -new -nodes -out kme-3.csr -newkey rsa:4096 -keyout "$kme_3_key" -subj "/CN=$kme_3_id/O=KME 3/C=LV"
openssl x509 -req -in kme-3.csr -CA "$ca_cert" -CAkey ca.key.pem -CAcreateserial -out "$kme_3_cert" -days 365 -sha256

# Generate SAE 3
echo "Generating SAE 3..."
openssl req -new -nodes -out sae-3.csr -newkey rsa:4096 -keyout sae-3.key.pem -subj "/CN=$sae_3_id/O=SAE 3/C=LV"
openssl x509 -req -in sae-3.csr -CA "$ca_cert" -CAkey ca.key.pem -CAcreateserial -out "$sae_3_cert" -days 365 -sha256