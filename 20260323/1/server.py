import asyncio
import io
import shlex
from dataclasses import dataclass, field

import cowsay

W = 10
H = 10
HOST = "127.0.0.1"
PORT = 1337

CUSTOM_MONSTERS = ["jgsbat"]
WEAPONS = {
    "sword": 10,
    "spear": 15,
    "axe": 20,
}

jgsbat = cowsay.read_dot_cow(io.StringIO(r"""
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\--//|.'-._  (
     )'   .'\/o\/o\/'.   `(
      ) .' . \====/ . '. (
       )  / <<    >> \  (
        '-._/``  ``\_.-'
  jgs     \\'--'//
         (((""  "")))
"""))


def make_monster_message(name, hello):
    if name == "jgsbat":
        return cowsay.cowsay(hello, cowfile=jgsbat)
    return cowsay.cowsay(hello, cow=name)


@dataclass
class ClientState:
    name: str
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    x: int = 0
    y: int = 0
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)


class Game:
    def __init__(self):
        self.monsters = {}

    def move(self, client):
        result = [f"Moved to ({client.x}, {client.y})"]

        monster = self.monsters.get((client.x, client.y))
        if monster is not None:
            result.append(make_monster_message(monster["name"], monster["hello"]))

        return result

    def addmon(self, name, hello, hp, mx, my):
        replaced = (mx, my) in self.monsters

        self.monsters[(mx, my)] = {
            "name": name,
            "hello": hello,
            "hp": hp,
        }

        result = [
            f"added monster {name} to ({mx}, {my}) saying {hello} with {hp} hp"
        ]
        if replaced:
            result.append("Replaced the old monster")
        return result

    def attack(self, client_name, x, y, monster_name, damage, weapon_name):
        monster = self.monsters.get((x, y))

        if monster is None:
            if monster_name == "*":
                return [False, ["No monster here"]]
            return [False, [f"No {monster_name} here"]]

        if monster_name != "*" and monster["name"] != monster_name:
            return [False, [f"No {monster_name} here"]]

        actual_damage = min(damage, monster["hp"])
        monster["hp"] -= actual_damage
        name = monster["name"]
        hp_left = monster["hp"]

        if hp_left == 0:
            del self.monsters[(x, y)]
            return [
                True,
                [
                    f"{client_name} attacked {name} with {weapon_name}, damage {actual_damage} hp",
                    f"{name} died",
                ],
            ]

        return [
            True,
            [
                f"{client_name} attacked {name} with {weapon_name}, damage {actual_damage} hp",
                f"{name} now has {hp_left} hp",
            ],
        ]


game = Game()
clients = {}


def send_to(client, message_lines):
    if isinstance(message_lines, str):
        client.queue.put_nowait(message_lines)
    else:
        client.queue.put_nowait("\n".join(message_lines))


def broadcast(message_lines):
    if isinstance(message_lines, str):
        payload = message_lines
    else:
        payload = "\n".join(message_lines)

    for client in clients.values():
        client.queue.put_nowait(payload)


async def writer_task(client):
    while True:
        message = await client.queue.get()
        client.writer.write((message + "\n\n").encode())
        await client.writer.drain()


def process_command(client, line):
    parts = shlex.split(line)
    if not parts:
        return

    cmd = parts[0]

    try:
        if cmd == "move":
            dx = int(parts[1])
            dy = int(parts[2])

            client.x = (client.x + dx) % W
            client.y = (client.y + dy) % H

            send_to(client, game.move(client))
            return

        if cmd == "addmon":
            name = parts[1]
            hello = parts[2]
            hp = int(parts[3])
            mx = int(parts[4])
            my = int(parts[5])

            lines = game.addmon(name, hello, hp, mx, my)
            broadcast([f"{client.name} " + lines[0]])
            if len(lines) > 1:
                send_to(client, lines[1])
            return

        if cmd == "attack":
            monster_name = parts[1]
            damage = int(parts[2])
            weapon_name = parts[3]

            success, lines = game.attack(
                client.name,
                client.x,
                client.y,
                monster_name,
                damage,
                weapon_name,
            )

            if success:
                broadcast(lines)
            else:
                send_to(client, lines)
            return

    except (IndexError, ValueError):
        send_to(client, "Invalid command")
        return

    send_to(client, "Invalid command")


async def handle_client(reader, writer):
    client = None
    sender = None

    try:
        login_line = await reader.readline()
        if not login_line:
            writer.close()
            await writer.wait_closed()
            return

        username = login_line.decode().rstrip("\n")

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

        client = ClientState(username, reader, writer)
        clients[username] = client

        writer.write(f"Successfully logged in as {username}\n\n".encode())
        await writer.drain()

        sender = asyncio.create_task(writer_task(client))

        broadcast(f"{username} entered the MUD")

        while True:
            data = await reader.readline()
            if not data:
                break

            line = data.decode().rstrip("\n")
            if not line:
                continue

            process_command(client, line)

    finally:
        if client is not None and clients.get(client.name) is client:
            del clients[client.name]
            broadcast(f"{client.name} left the MUD")

        if sender is not None:
            sender.cancel()
            try:
                await sender
            except asyncio.CancelledError:
                pass

        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())