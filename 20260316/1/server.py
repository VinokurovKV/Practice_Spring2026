import shlex
import socket

W = 10
H = 10
HOST = "127.0.0.1"
PORT = 1337


class Game:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.monsters = {}

    def move(self, dx, dy):
        self.x = (self.x + dx) % W
        self.y = (self.y + dy) % H

        result = [f"moved {self.x} {self.y}"]

        monster = self.monsters.get((self.x, self.y))
        if monster is not None:
            result.append(
                f"encounter {shlex.quote(monster['name'])} {shlex.quote(monster['hello'])}"
            )

        return result

    def addmon(self, name, hello, hp, mx, my):
        replaced = (mx, my) in self.monsters
        self.monsters[(mx, my)] = {
            "name": name,
            "hello": hello,
            "hp": hp,
        }

        result = [f"added {shlex.quote(name)} {mx} {my} {shlex.quote(hello)}"]
        if replaced:
            result.append("replaced")
        return result

    def attack(self, monster_name, damage):
        monster = self.monsters.get((self.x, self.y))

        if monster is None:
            if monster_name == "*":
                return ["nomonster"]
            return [f"nomonster {shlex.quote(monster_name)}"]

        if monster_name != "*" and monster["name"] != monster_name:
            return [f"nomonster {shlex.quote(monster_name)}"]

        actual_damage = min(damage, monster["hp"])
        monster["hp"] -= actual_damage
        name = monster["name"]
        hp_left = monster["hp"]

        if hp_left == 0:
            del self.monsters[(self.x, self.y)]

        return [f"attacked {shlex.quote(name)} {actual_damage} {hp_left}"]


def handle_command(game, line):
    parts = shlex.split(line)
    if not parts:
        return [""]

    cmd = parts[0]

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
        return game.attack(monster_name, damage)

    return [""]


def main():
    game = Game()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)

        while True:
            conn, _ = server.accept()
            with conn:
                fin = conn.makefile("r", encoding="utf-8")
                fout = conn.makefile("w", encoding="utf-8")

                for line in fin:
                    line = line.rstrip("\n")
                    reply = handle_command(game, line)

                    for item in reply:
                        fout.write(item + "\n")
                    fout.write("\n")
                    fout.flush()


if __name__ == "__main__":
    main()
