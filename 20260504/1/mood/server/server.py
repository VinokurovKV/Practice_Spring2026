"""MOOD server logic."""

import asyncio
import datetime
import gettext
import random
import shlex
import sys
from pathlib import Path

from ..common import DEFAULT_HOST, DEFAULT_PORT, GRID_HEIGHT, GRID_WIDTH
from ..common import make_monster_message


def log(msg):
    """Print a log message with timestamp."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


class Client:
    """Connected player."""

    def __init__(self, name, reader, writer):
        """Create client session."""
        self.name = name
        self.reader = reader
        self.writer = writer
        self.x = 0
        self.y = 0
        self.locale = None


clients = {}
monsters = {}
moving_monsters_enabled = True

DIRECTIONS = {
    "right": (1, 0),
    "left": (-1, 0),
    "down": (0, 1),
    "up": (0, -1),
}

LOCALES_DIR = Path(__file__).resolve().parent / "po"
TEXTDOMAIN = "messages"


def get_translation(locale_name):
    """Return translation object for locale."""
    if locale_name not in {"ru_RU.UTF8", "ru_RU.UTF-8"}:
        return gettext.NullTranslations()

    return gettext.translation(
        TEXTDOMAIN,
        localedir=str(LOCALES_DIR),
        languages=["ru_RU.UTF8", "ru_RU.UTF-8", "ru_RU", "ru"],
        fallback=True,
    )


def tr(client, message):
    """Translate singular message for client."""
    return get_translation(client.locale).gettext(message)


def ntr(client, singular, plural, number):
    """Translate plural message for client."""
    return get_translation(client.locale).ngettext(singular, plural, number)


def hp_text(client, hp):
    """Return localized hp text."""
    return ntr(
        client,
        "{n} hit point",
        "{n} hit points",
        hp,
    ).format(n=hp)


async def send_to(client, message):
    """Send message to one client."""
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
    """Send message to all clients."""
    for c in list(clients.values()):
        await send_to(c, message)


def render_addmon_event(client, event):
    """Render localized addmon event."""
    result = [
        tr(
            client,
            '{player} added monster {monster} to ({x}, {y}) saying "{hello}" with {hp}',
        ).format(
            player=event["player"],
            monster=event["monster"],
            x=event["x"],
            y=event["y"],
            hello=event["hello"],
            hp=hp_text(client, event["hp"]),
        )
    ]

    if event["replaced"]:
        result.append(tr(client, "Replaced the old monster"))

    return result


def render_attack_event(client, event):
    """Render localized attack event."""
    result = [
        tr(
            client,
            "{player} attacked {monster} with {weapon}, damage {hp}",
        ).format(
            player=event["player"],
            monster=event["monster"],
            weapon=event["weapon"],
            hp=hp_text(client, event["damage"]),
        )
    ]

    if event["died"]:
        result.append(
            tr(client, "{monster} died").format(monster=event["monster"])
        )
    else:
        result.append(
            tr(client, "{monster} now has {hp}").format(
                monster=event["monster"],
                hp=hp_text(client, event["hp_left"]),
            )
        )

    return result


async def broadcast_event(event):
    """Send localized event to all clients."""
    for c in list(clients.values()):
        if event["type"] == "addmon":
            await send_to(c, render_addmon_event(c, event))
        elif event["type"] == "attack":
            await send_to(c, render_attack_event(c, event))


def encounter_messages(x, y):
    """Return monster message at cell."""
    monster = monsters.get((x, y))
    if monster:
        return [make_monster_message(monster["name"], monster["hello"])]
    return []


def clients_at(x, y):
    """Return clients at cell."""
    return [client for client in clients.values() if client.x == x and client.y == y]


def move(client, dx, dy):
    """Move client on field."""
    client.x = (client.x + dx) % GRID_WIDTH
    client.y = (client.y + dy) % GRID_HEIGHT

    result = [f"Moved to ({client.x}, {client.y})"]
    result.extend(encounter_messages(client.x, client.y))
    return result


def addmon(client, name, hello, hp, mx, my):
    """Add or replace monster."""
    replaced = (mx, my) in monsters

    monsters[(mx, my)] = {
        "name": name,
        "hello": hello,
        "hp": hp,
    }

    return {
        "type": "addmon",
        "player": client.name,
        "monster": name,
        "x": mx,
        "y": my,
        "hello": hello,
        "hp": hp,
        "replaced": replaced,
    }


def attack(client, monster_name, damage, weapon):
    """Attack monster in current cell."""
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

    if hp_left == 0:
        del monsters[(client.x, client.y)]
        return True, {
            "type": "attack",
            "player": client.name,
            "monster": name,
            "weapon": weapon,
            "damage": actual_damage,
            "hp_left": 0,
            "died": True,
        }

    return True, {
        "type": "attack",
        "player": client.name,
        "monster": name,
        "weapon": weapon,
        "damage": actual_damage,
        "hp_left": hp_left,
        "died": False,
    }


def set_moving_monsters(enabled):
    """Enable or disable wandering monsters mode."""
    global moving_monsters_enabled

    moving_monsters_enabled = enabled
    state = "on" if enabled else "off"
    return [f"Moving monsters: {state}"]


def move_random_monster():
    """Move random monster to free cell."""
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
    """Move monsters every 30 seconds."""
    while True:
        await asyncio.sleep(30)

        if not moving_monsters_enabled:
            continue

        moved = move_random_monster()
        if moved is None:
            continue

        monster_name, direction, x, y = moved
        await broadcast(f"{monster_name} moved one cell {direction}")

        for client in clients_at(x, y):
            await send_to(client, encounter_messages(x, y))


def process_command(client, line):
    """Handle one command."""
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

        if cmd == "movemonsters":
            if len(parts) != 2 or parts[1] not in {"on", "off"}:
                return "personal", ["Invalid arguments"]
            return "personal", set_moving_monsters(parts[1] == "on")

        if cmd == "locale":
            if len(parts) != 2:
                return "personal", ["Invalid arguments"]

            client.locale = parts[1]
            return "personal", [
                tr(client, "Set up locale: {locale}").format(locale=parts[1])
            ]

    except (IndexError, ValueError):
        return "personal", ["Invalid arguments"]

    return "personal", ["Unknown command"]


async def handle_client(reader, writer):
    """Serve one client connection."""
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

        await send_to(
            client,
            tr(client, "Successfully logged in as {name}").format(name=username),
        )

        for c in list(clients.values()):
            await send_to(
                c,
                tr(c, "{name} entered the MUD").format(name=username),
            )

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
                if isinstance(reply, dict):
                    await broadcast_event(reply)
                else:
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

            for c in list(clients.values()):
                await send_to(
                    c,
                    tr(c, "{name} left the MUD").format(name=username),
                )

        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def run_server(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """Start server."""
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


def start_server(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """Run server in a regular function for multiprocessing tests."""
    global moving_monsters_enabled

    clients.clear()
    monsters.clear()
    moving_monsters_enabled = True

    asyncio.run(run_server(host, port))


def main(argv=None):
    """Run server."""
    if argv is None:
        argv = sys.argv[1:]

    host = DEFAULT_HOST
    port = DEFAULT_PORT

    if len(argv) >= 1:
        host = argv[0]
    if len(argv) >= 2:
        port = int(argv[1])

    start_server(host, port)


if __name__ == "__main__":
    main()
