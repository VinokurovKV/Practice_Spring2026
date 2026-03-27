import shlex
import socket
import datetime

W = 10
H = 10
HOST = "127.0.0.1"
PORT = 1337


class Game:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.monsters = {}

    def log(self, message, level="INFO"):
        """Вывод логов сервера"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def move(self, dx, dy):
        old_x, old_y = self.x, self.y
        self.x = (self.x + dx) % W
        self.y = (self.y + dy) % H
        
        self.log(f"Player moved from ({old_x},{old_y}) to ({self.x},{self.y})")

        result = [f"moved {self.x} {self.y}"]

        monster = self.monsters.get((self.x, self.y))
        if monster is not None:
            self.log(f"Encountered monster '{monster['name']}' at ({self.x},{self.y})")
            result.append(f"encounter {monster['name']} {monster['hello']}")

        return result

    def addmon(self, name, hello, hp, mx, my):
        replaced = (mx, my) in self.monsters
        
        if replaced:
            old_name = self.monsters[(mx, my)]['name']
            self.log(f"Replaced monster '{old_name}' with '{name}' at ({mx},{my})")
        else:
            self.log(f"Added new monster '{name}' at ({mx},{my}) with HP={hp}")
        
        self.monsters[(mx, my)] = {
            "name": name,
            "hello": hello,
            "hp": hp,
        }

        result = [f"added {name} {mx} {my} {hello}"]
        if replaced:
            result.append("replaced")
        return result

    def attack(self, monster_name, damage):
        monster = self.monsters.get((self.x, self.y))

        if monster is None:
            self.log(f"Attack failed: no monster at ({self.x},{self.y})")
            if monster_name == "*":
                return ["nomonster"]
            return [f"nomonster {monster_name}"]

        if monster_name != "*" and monster["name"] != monster_name:
            self.log(f"Attack failed: monster '{monster_name}' not found at ({self.x},{self.y})")
            return [f"nomonster {monster_name}"]

        actual_damage = min(damage, monster["hp"])
        monster["hp"] -= actual_damage
        name = monster["name"]
        hp_left = monster["hp"]

        self.log(f"Attacked '{name}', damage {actual_damage}, HP left: {hp_left}")

        if hp_left == 0:
            self.log(f"Monster '{name}' died")
            del self.monsters[(self.x, self.y)]

        return [f"attacked {name} {actual_damage} {hp_left}"]


def handle_command(game, line):
    parts = shlex.split(line)
    if not parts:
        return [""]

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
            return game.attack(monster_name, damage)
            
    except (IndexError, ValueError) as e:
        game.log(f"Error parsing command: {e}", "ERROR")
        return [""]

    game.log(f"Unknown command: {cmd}", "WARNING")
    return [""]


def main():
    game = Game()
    game.log(f"Server started on {HOST}:{PORT}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)

        client_num = 1
        while True:
            game.log(f"Waiting for connection...")
            conn, addr = server.accept()
            game.log(f"Client #{client_num} connected from {addr}")
            
            with conn:
                fin = conn.makefile("r", encoding="utf-8")
                fout = conn.makefile("w", encoding="utf-8")

                for line in fin:
                    line = line.rstrip("\n")
                    if not line:
                        continue
                    
                    game.log(f"Received: {line}")
                    
                    reply = handle_command(game, line)
                    
                    for item in reply:
                        fout.write(item + "\n")
                    fout.write("\n")
                    fout.flush()
                
                game.log(f"Client #{client_num} disconnected")
                client_num += 1


if __name__ == "__main__":
    main()