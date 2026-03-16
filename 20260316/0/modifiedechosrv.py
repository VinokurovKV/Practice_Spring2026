import asyncio

async def echo(reader, writer):
    while data := await reader.readline():
        match data.decode().split():
            case ['print', *args]:
                writer.write((' '.join(args) + '\n').encode())
            case ['info', 'host']:
                writer.write((writer.get_extra_info('peername')[0] + '\n').encode())
            case ['info', 'port']:
                writer.write((str(writer.get_extra_info('peername')[1]) + '\n').encode())
            case _:
                writer.write('UNKNOWN COMMAND\n'.encode())
    writer.close()
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(echo, '0.0.0.0', 1337)
    async with server:
        await server.serve_forever()

asyncio.run(main())
