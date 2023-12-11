# Chat Room Example

## Requirements

- 1x Server
- 2x Clients

## Description

The server acts independently of any KMEs.
The only function of the server is to broadcast messages between clients and to announce when a second client joins.

The clients are the SAE's and communicate with their attached KME.

The clients handle encryption of their messages and retrieve the encryption key from the other KME using the Key ID.

## In-depth Overview

1. The server hosts the chat room.
2. Once a client connects, the client asks if there are any other clients joined.
    - If no other clients, then it waits for a new client, before proceeding.
3. Once a new client is found, the first one that joined becomes the master SAE and requests the other client to send
   its SAE ID.
4. Master SAE generates 1 encryption key for communication using the slave SAE ID
5. Once master SAE receives its encryption key from the KME, it announces the master SAE ID and the key ID.
6. The second client or the slave SAE, asks its KME for the encryption key.
7. Once the key is retrieved, both parties encrypt their messages using the generated key.

## Running

1. `git clone https://github.com/CreepPork/qkd-kme-simulator`
2. `cd qkd-kme-simulator`
3. `bash ./certs/generate.sh`
4. `docker compose up -d`
5. `cd examples/chat`
6. Open 3 different terminals:
    1. `python3 server.py`
    2. `python3 client.py` & select 0
    3. `python3 client.py` & select 1
7. Chat away!