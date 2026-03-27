import io
import shlex
import socket
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


class Game:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.monsters = {}

    def move(self, dx, dy):
        self.x = (self.x + dx) % W
        self.y = (self.y + dy) % H

        result = [f"Moved to ({self.x}, {self.y})"]

        monster = self.monsters.get((self.x, self.y))
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
            f"Added monster {name} to ({mx}, {my}) saying {hello} with {hp} hp"
        ]
        if replaced:
            result.append("Replaced the old monster")
        return result

    def attack(self, monster_name, damage, weapon_name):
        monster = self.monsters.get((self.x, self.y))

        if monster is None:
            if monster_name == "*":
                return ["No monster here"]
            return [f"No {monster_name} here"]

        if monster_name != "*" and monster["name"] != monster_name:
            return [f"No {monster_name} here"]

        actual_damage = min(damage, monster["hp"])
        monster["hp"] -= actual_damage
        name = monster["name"]
        hp_left = monster["hp"]

        result = [f"Attacked {name} with {weapon_name}, damage {actual_damage} hp"]

        if hp_left == 0:
            del self.monsters[(self.x, self.y)]
            result.append(f"{name} died")
        else:
            result.append(f"{name} now has {hp_left} hp")

        return result


def handle_command(game, line):
    parts = shlex.split(line)
    if not parts:
        return []

    cmd = parts[0]

    try:
        if cmd == "move":
            dx = int(parts[1])
            dy = int(parts[2])
            return game.move(dx, dy)

        if cmd == "addmon":
            name = parts[1]
            hello = parts[2]
            hp = int(parts[3])
            mx = int(parts[4])
            my = int(parts[5])
            return game.addmon(name, hello, hp, mx, my)

        if cmd == "attack":
            monster_name = parts[1]
            damage = int(parts[2])
            weapon_name = parts[3]
            return game.attack(monster_name, damage, weapon_name)

    except (IndexError, ValueError):
        return ["Invalid command"]

    return ["Invalid command"]


def send_block(fout, lines):
    for line in lines:
        fout.write(line + "\n")
    fout.write("\n")
    fout.flush()


def main():
    game = Game()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)

        while True:
            conn, addr = server.accept()

            with conn:
                fin = conn.makefile("r", encoding="utf-8")
                fout = conn.makefile("w", encoding="utf-8")

                username = fin.readline().rstrip("\n")
                if not username or any(ch.isspace() for ch in username):
                    send_block(fout, ["Invalid username"])
                    continue

                send_block(fout, [f"Successfully logged in as {username}"])

                for line in fin:
                    line = line.rstrip("\n")
                    if not line:
                        continue

                    reply = handle_command(game, line)
                    send_block(fout, reply)


if __name__ == "__main__":
    main()