import asyncio


class ChatServer:
    def __init__(self):
        self.clients = []

    async def handle_client(self, reader, writer):
        self.clients.append(writer)
        address = writer.get_extra_info('peername')
        print(f'New connection from {address}')

        try:
            while True:
                data = await reader.read(100)
                if not data:
                    break

                message = data.decode()
                print(f'Received message from {address}: {message}')

                await self.broadcast(message, writer)

        except asyncio.CancelledError:
            pass

        finally:
            print(f'Connection closed from {address}')
            self.clients.remove(writer)
            writer.close()
            await writer.wait_closed()

    async def broadcast(self, message, sender):
        for client in self.clients:
            if client != sender:
                try:
                    client.write(message.encode())
                    await client.drain()
                except:
                    continue

    async def run_server(self, host, port):
        server = await asyncio.start_server(
            self.handle_client, host, port
        )

        async with server:
            await server.serve_forever()


if __name__ == "__main__":
    chat_server = ChatServer()
    asyncio.run(chat_server.run_server('127.0.0.1', 8888))
