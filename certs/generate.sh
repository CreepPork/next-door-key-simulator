#!/bin/bash
set -e

# Change working directory
__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$__dir"

echo "This will generate the keys based on the README instructions."
echo "And it will take into account the default structure and configuration of the docker-compose.yml file."

read -r -p "Do you want to continue? <Y/n> " prompt

if [[ $prompt == "n" || $prompt == "N" || $prompt == "no" || $prompt == "No" ]]
then
  exit 0
fi

ca_cert=$(grep "CA_FILE=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n 1p)

# Get KME 1
kme_1_cert=$(grep "KME_CERT=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n 1p)
kme_1_key=$(grep "KME_KEY=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n 1p)
kme_1_id=$(grep "KME_ID=" ../docker-compose.yml | sed 's/^.*=//' | sed -n 1p)

# Get KME 2
kme_2_cert=$(grep "KME_CERT=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n 2p)
kme_2_key=$(grep "KME_KEY=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n 2p)
kme_2_id=$(grep "KME_ID=" ../docker-compose.yml | sed 's/^.*=//' | sed -n 2p)

# Get SAE 1
sae_1_cert=$(grep "SAE_CERT=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n 1p)
sae_1_id=$(grep "ATTACHED_SAE_ID=" ../docker-compose.yml | sed 's/^.*=//' | sed -n 1p)

# Get SAE 2
sae_2_cert=$(grep "SAE_CERT=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n 2p)
sae_2_id=$(grep "ATTACHED_SAE_ID=" ../docker-compose.yml | sed 's/^.*=//' | sed -n 2p)

# List info
echo "CA: $ca_cert"

echo "KME 1: cert $kme_1_cert, key $kme_1_key, id $kme_1_id"
echo "SAE 1: cert $sae_1_cert, id $sae_1_id"

echo "KME 2: cert $kme_2_cert, key $kme_2_key, id $kme_2_id"
echo "SAE 2: cert $sae_2_cert, id $sae_2_id"

echo ""

# Generate CA
echo "Generating CA..."
openssl genrsa -out ca.key.pem 4096
openssl req -x509 -new -nodes -key ca.key.pem -sha256 -days 730 -out "$ca_cert" -subj '/CN=CA/O=CA/C=LV'

# Generate KME 1
echo "Generating KME 1..."
openssl req -new -nodes -out kme-1.csr -newkey rsa:4096 -keyout "$kme_1_key" -subj "/CN=$kme_1_id/O=KME 1/C=LV"
openssl x509 -req -in kme-1.csr -CA "$ca_cert" -CAkey ca.key.pem -CAcreateserial -out "$kme_1_cert" -days 365 -sha256

# Generate KME 2
echo "Generating KME 2..."
openssl req -new -nodes -out kme-2.csr -newkey rsa:4096 -keyout "$kme_2_key" -subj "/CN=$kme_2_id/O=KME 2/C=LV"
openssl x509 -req -in kme-2.csr -CA "$ca_cert" -CAkey ca.key.pem -CAcreateserial -out "$kme_2_cert" -days 365 -sha256

# Generate SAE 1
echo "Generating SAE 1..."
openssl req -new -nodes -out sae-1.csr -newkey rsa:4096 -keyout sae-1.key.pem -subj "/CN=$sae_1_id/O=SAE 1/C=LV"
openssl x509 -req -in sae-1.csr -CA "$ca_cert" -CAkey ca.key.pem -CAcreateserial -out "$sae_1_cert" -days 365 -sha256

# Generate SAE 2
echo "Generating SAE 2..."
openssl req -new -nodes -out sae-2.csr -newkey rsa:4096 -keyout sae-2.key.pem -subj "/CN=$sae_2_id/O=SAE 2/C=LV"
openssl x509 -req -in sae-2.csr -CA "$ca_cert" -CAkey ca.key.pem -CAcreateserial -out "$sae_2_cert" -days 365 -sha256