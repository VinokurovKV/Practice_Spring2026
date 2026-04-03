import asyncio
import shlex
import datetime

W = 10
H = 10
HOST = "127.0.0.1"
PORT = 1337


def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


class Client:
    def __init__(self, name, reader, writer):
        self.name = name
        self.reader = reader
        self.writer = writer
        self.x = 0
        self.y = 0


clients = {}
monsters = {}


async def send_to(client, message):
    try:
        if isinstance(message, list):
            for line in message:
                client.writer.write((line + "\n").encode())
        else:
            client.writer.write((message + "\n").encode())

        client.writer.write(b"\n")
        await client.writer.drain()
    except Exception:
        pass


async def broadcast(message):
    for c in list(clients.values()):
        await send_to(c, message)


def move(client, dx, dy):
    client.x = (client.x + dx) % W
    client.y = (client.y + dy) % H

    result = [f"{client.name} moved to ({client.x}, {client.y})"]

    monster = monsters.get((client.x, client.y))
    if monster:
        # индивидуальное сообщение
        asyncio.create_task(
            send_to(
                client,
                f"encounter {monster['name']} {monster['hello']}",
            )
        )

    return result


def addmon(client, name, hello, hp, mx, my):
    replaced = (mx, my) in monsters

    monsters[(mx, my)] = {
        "name": name,
        "hello": hello,
        "hp": hp,
    }

    msg = f"{client.name} added monster {name} to ({mx}, {my}) saying {hello} with {hp} hp"

    if replaced:
        msg += " (replaced old monster)"

    return [msg]


def attack(client, monster_name, damage, weapon):
    monster = monsters.get((client.x, client.y))

    if monster is None:
        if monster_name == "*":
            return [f"{client.name}: No monster here"]
        return [f"{client.name}: No {monster_name} here"]

    if monster_name != "*" and monster["name"] != monster_name:
        return [f"{client.name}: No {monster_name} here"]

    actual_damage = min(damage, monster["hp"])
    monster["hp"] -= actual_damage

    name = monster["name"]
    hp_left = monster["hp"]

    result = [
        f"{client.name} attacked {name} with {weapon}, damage {actual_damage} hp"
    ]

    if hp_left == 0:
        del monsters[(client.x, client.y)]
        result.append(f"{name} died")
    else:
        result.append(f"{name} now has {hp_left}")

    return result


def process_command(client, line):
    parts = shlex.split(line)
    if not parts:
        return []

    cmd = parts[0]

    try:
        if cmd == "move":
            dx = int(parts[1])
            dy = int(parts[2])
            return move(client, dx, dy)

        if cmd == "addmon":
            name = parts[1]
            hello = parts[2]
            hp = int(parts[3])
            mx = int(parts[4])
            my = int(parts[5])
            return addmon(client, name, hello, hp, mx, my)

        if cmd == "attack":
            monster_name = parts[1]
            damage = int(parts[2])
            weapon = parts[3]
            return attack(client, monster_name, damage, weapon)

    except (IndexError, ValueError):
        return [f"{client.name}: Invalid arguments"]

    return [f"{client.name}: Unknown command"]


async def handle_client(reader, writer):
    global clients

    try:
        # получаем имя
        data = await reader.readline()
        if not data:
            writer.close()
            await writer.wait_closed()
            return

        username = data.decode().strip()

        if username in clients:
            writer.write(f"Username {username} is already taken\n\n".encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        client = Client(username, reader, writer)
        clients[username] = client

        log(f"{username} connected")

        await send_to(client, f"Successfully logged in as {username}")
        await broadcast(f"{username} entered the MUD")

        while True:
            line = await reader.readline()
            if not line:
                break

            line = line.decode().strip()
            if not line:
                continue

            log(f"{username} -> {line}")

            reply = process_command(client, line)

            if reply:
                await broadcast(reply)

    except ConnectionResetError:
        log(f"{username} connection reset")

    finally:
        if 'username' in locals() and username in clients:
            del clients[username]

            log(f"{username} disconnected")

            await broadcast(f"{username} left the MUD")

        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)

    log(f"Server started on {HOST}:{PORT}")

    async with server:
        try:
            await server.serve_forever()
        except KeyboardInterrupt:
            log("Shutting down server...")

            for client in list(clients.values()):
                try:
                    client.writer.close()
                    await client.writer.wait_closed()
                except Exception:
                    pass

            server.close()
            await server.wait_closed()

            log("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())