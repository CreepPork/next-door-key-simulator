import asyncio


async def handle_messages(reader):
    while True:
        data = await reader.read(100)

        if not data:
            break

        message = data.decode()
        print(f"\n[Other]: {message}\n[You]: ", end='')


def get_input():
    return input("[You]: ")


async def send_message(writer):
    while True:
        message = await asyncio.to_thread(get_input)
        writer.write(message.encode())
        await writer.drain()


async def main():
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)

    await asyncio.gather(
        handle_messages(reader),
        send_message(writer)
    )


if __name__ == "__main__":
    asyncio.run(main())
