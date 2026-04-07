"""MOOD server logic."""

import asyncio
import datetime
import random
import shlex
import sys

from ..common import DEFAULT_HOST, DEFAULT_PORT, GRID_HEIGHT, GRID_WIDTH
from ..common import make_monster_message


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

DIRECTIONS = {
    "right": (1, 0),
    "left": (-1, 0),
    "down": (0, 1),
    "up": (0, -1),
}


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


def encounter_messages(x, y):
    monster = monsters.get((x, y))
    if monster:
        return [make_monster_message(monster["name"], monster["hello"])]
    return []


def clients_at(x, y):
    return [client for client in clients.values() if client.x == x and client.y == y]


def move(client, dx, dy):
    client.x = (client.x + dx) % GRID_WIDTH
    client.y = (client.y + dy) % GRID_HEIGHT

    result = [f"Moved to ({client.x}, {client.y})"]
    result.extend(encounter_messages(client.x, client.y))
    return result


def addmon(client, name, hello, hp, mx, my):
    replaced = (mx, my) in monsters

    monsters[(mx, my)] = {
        "name": name,
        "hello": hello,
        "hp": hp,
    }

    msg = f"{client.name} added monster {name} to ({mx}, {my}) saying {hello} with {hp} hp"

    result = [msg]
    if replaced:
        result.append("Replaced the old monster")

    return result


def attack(client, monster_name, damage, weapon):
    monster = monsters.get((client.x, client.y))

    if monster is None:
        if monster_name == "*":
            return False, ["No monster here"]
        return False, [f"No {monster_name} here"]

    if monster_name != "*" and monster["name"] != monster_name:
        return False, [f"No {monster_name} here"]

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

    return True, result


def move_random_monster():
    if not monsters:
        return None

    if len(monsters) >= GRID_WIDTH * GRID_HEIGHT:
        return None

    while True:
        old_pos = random.choice(list(monsters.keys()))
        monster = monsters[old_pos]

        direction = random.choice(list(DIRECTIONS.keys()))
        dx, dy = DIRECTIONS[direction]

        new_x = (old_pos[0] + dx) % GRID_WIDTH
        new_y = (old_pos[1] + dy) % GRID_HEIGHT
        new_pos = (new_x, new_y)

        if new_pos in monsters:
            continue

        del monsters[old_pos]
        monsters[new_pos] = monster
        return monster["name"], direction, new_x, new_y


async def wandering_monsters_loop():
    while True:
        await asyncio.sleep(30)

        moved = move_random_monster()
        if moved is None:
            continue

        monster_name, direction, x, y = moved
        await broadcast(f"{monster_name} moved one cell {direction}")

        for client in clients_at(x, y):
            await send_to(client, encounter_messages(x, y))


def process_command(client, line):
    parts = shlex.split(line)
    if not parts:
        return "personal", []

    cmd = parts[0]

    try:
        if cmd == "move":
            dx = int(parts[1])
            dy = int(parts[2])
            return "personal", move(client, dx, dy)

        if cmd == "addmon":
            name = parts[1]
            hello = parts[2]
            hp = int(parts[3])
            mx = int(parts[4])
            my = int(parts[5])
            return "broadcast", addmon(client, name, hello, hp, mx, my)

        if cmd == "attack":
            monster_name = parts[1]
            damage = int(parts[2])
            weapon = parts[3]
            success, result = attack(client, monster_name, damage, weapon)
            if success:
                return "broadcast", result
            return "personal", result

        if cmd == "sayall":
            if len(parts) != 2:
                return "personal", ["Invalid arguments"]
            return "broadcast", [f"{client.name}: {parts[1]}"]

    except (IndexError, ValueError):
        return "personal", ["Invalid arguments"]

    return "personal", ["Unknown command"]


async def handle_client(reader, writer):
    try:
        data = await reader.readline()
        if not data:
            writer.close()
            await writer.wait_closed()
            return

        username = data.decode().strip()

        if not username or any(ch.isspace() for ch in username):
            writer.write(b"Invalid username\n\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

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

            mode, reply = process_command(client, line)

            if not reply:
                continue

            if mode == "broadcast":
                await broadcast(reply)
            else:
                await send_to(client, reply)

    except ConnectionResetError:
        if "username" in locals():
            log(f"{username} connection reset")

    finally:
        if "username" in locals() and username in clients:
            del clients[username]
            log(f"{username} disconnected")
            await broadcast(f"{username} left the MUD")

        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def run_server(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """Start the server."""
    server = await asyncio.start_server(handle_client, host, port)
    monster_task = asyncio.create_task(wandering_monsters_loop())

    log(f"Server started on {host}:{port}")

    async with server:
        try:
            await server.serve_forever()
        except KeyboardInterrupt:
            log("Shutting down server...")

            monster_task.cancel()
            try:
                await monster_task
            except asyncio.CancelledError:
                pass

            for client in list(clients.values()):
                try:
                    client.writer.close()
                    await client.writer.wait_closed()
                except Exception:
                    pass

            server.close()
            await server.wait_closed()

            log("Server stopped")


def main(argv=None):
    """Run the server."""
    if argv is None:
        argv = sys.argv[1:]

    host = DEFAULT_HOST
    port = DEFAULT_PORT

    if len(argv) >= 1:
        host = argv[0]
    if len(argv) >= 2:
        port = int(argv[1])

    asyncio.run(run_server(host, port))


if __name__ == "__main__":
    main()
