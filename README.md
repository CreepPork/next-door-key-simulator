# QKD KME Simulator

## Installation

### Generate self-signed certificates (or use your own certificates)

Required certificates to be mounted:
- CA certificates:
  - `ca.crt.pem`
- KME certificates:
  - `kme.crt.pem`
  - `kme.key.pem`
- SAE certificates:
  - `sae.crt.pem`

#### Generate CA certificate

```shell
openssl genrsa -out ca.key.pem 4096
openssl req -x509 -new -nodes -key ca.key.pem -sha256 -days 730 -out ca.crt.pem
```

#### Generate KME certificate

In the common name (CN) enter the KME ID that you will be using.

```shell
openssl req -new -nodes -out kme.csr -newkey rsa:4096 -keyout kme.key.pem
openssl x509 -req -in kme.csr -CA ca.crt.pem -CAkey ca.key.pem -CAcreateserial -out kme.crt.pem -days 365 -sha256
```

#### Generate SAE certificate

In the common name (CN) enter the SAE ID that you will be using.

```shell
openssl req -new -nodes -out sae.csr -newkey rsa:4096 -keyout sae.key.pem
openssl x509 -req -in sae.csr -CA ca.crt.pem -CAkey ca.key.pem -CAcreateserial -out sae.crt.pem -days 365 -sha256
```

openssl req -new -nodes -out sae-slave.csr -newkey rsa:4096 -keyout sae-slave.key.pem
openssl x509 -req -in sae-slave.csr -CA ca.crt.pem -CAkey ca.key.pem -CAcreateserial -out sae-slave.crt.pem -days 365 -sha256