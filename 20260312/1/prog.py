import cmd
import cowsay
import shlex

W = 10
H = 10
CUSTOM_MONSTERS = ["jgsbat"]

jgsbat = cowsay.read_dot_cow(r"""
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\--//|.'-._  (
     )'   .'\/o\/o\/'.   `(
      ) .' . \====/ . '. (
       )  / <<    >> \  (
        '-._/``  ``\_.-'
  jgs     __\\'--'//__
         (((""`  `"")))
""")


def available_monsters():
    return cowsay.list_cows() + CUSTOM_MONSTERS


def parse_addmon_args(arg):
    parts = shlex.split(arg)
    if len(parts) < 7:
        return None

    name = parts[0]
    params = parts[1:]

    hello = None
    hp = None
    mx = None
    my = None

    i = 0
    while i < len(params):
        if params[i] == "hello":
            if i + 1 >= len(params):
                return None
            hello = params[i + 1]
            i += 2
        elif params[i] == "hp":
            if i + 1 >= len(params) or not params[i + 1].isdigit():
                return None
            hp = int(params[i + 1])
            i += 2
        elif params[i] == "coords":
            if i + 2 >= len(params):
                return None
            if not params[i + 1].isdigit() or not params[i + 2].isdigit():
                return None
            mx = int(params[i + 1])
            my = int(params[i + 2])
            i += 3
        else:
            return None

    if None in (hello, hp, mx, my):
        return None

    return name, hello, hp, mx, my


def parse_attack_args(arg):
    parts = shlex.split(arg)
    if len(parts) == 0:
        return None
    if len(parts) == 1:
        return parts[0]
    return "INVALID"


class Game:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.monsters = {}

    def encounter(self):
        monster = self.monsters.get((self.x, self.y))
        if monster is None:
            return

        name = monster["name"]
        hello = monster["hello"]

        if name == "jgsbat":
            print(cowsay.cowsay(hello, cowfile=jgsbat))
        else:
            print(cowsay.cowsay(hello, cow=name))

    def move(self, direction):
        if direction == "up":
            self.y = (self.y - 1) % H
        elif direction == "down":
            self.y = (self.y + 1) % H
        elif direction == "left":
            self.x = (self.x - 1) % W
        elif direction == "right":
            self.x = (self.x + 1) % W

        print(f"Moved to ({self.x}, {self.y})")
        self.encounter()

    def addmon(self, name, hello, hp, mx, my):
        replaced = (mx, my) in self.monsters
        self.monsters[(mx, my)] = {
            "name": name,
            "hello": hello,
            "hp": hp,
        }

        print(f"Added monster {name} to ({mx}, {my}) saying {hello}")
        if replaced:
            print("Replaced the old monster")

    def attack(self, monster_name=None):
        monster = self.monsters.get((self.x, self.y))
        if monster is None:
            if monster_name is None:
                print("No monster here")
            else:
                print(f"No {monster_name} here")
            return

        if monster_name is not None and monster["name"] != monster_name:
            print(f"No {monster_name} here")
            return

        damage = min(10, monster["hp"])
        monster["hp"] -= damage

        print(f"Attacked {monster['name']}, damage {damage} hp")

        if monster["hp"] == 0:
            print(f"{monster['name']} died")
            del self.monsters[(self.x, self.y)]
        else:
            print(f"{monster['name']} now has {monster['hp']}")

    def current_monster(self):
        return self.monsters.get((self.x, self.y))


class MUD(cmd.Cmd):
    intro = "<<< Welcome to Python-MUD 0.1 >>>"
    prompt = "(mud) "

    def __init__(self):
        super().__init__()
        self.game = Game()

    def emptyline(self):
        pass

    def do_up(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.game.move("up")

    def do_down(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.game.move("down")

    def do_left(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.game.move("left")

    def do_right(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.game.move("right")

    def do_addmon(self, arg):
        parsed = parse_addmon_args(arg)
        if parsed is None:
            print("Invalid arguments")
            return

        name, hello, hp, mx, my = parsed

        if not (0 <= mx < W and 0 <= my < H):
            print("Invalid arguments")
            return

        if name not in available_monsters():
            print("Cannot add unknown monster")
            return

        self.game.addmon(name, hello, hp, mx, my)

    def do_attack(self, arg):
        result = parse_attack_args(arg)
        if result == "INVALID":
            print("Invalid arguments")
            return
        self.game.attack(result)

    def complete_attack(self, text, line, begidx, endidx):
        parts = shlex.split(line[:begidx])
        if parts == ["attack"]:
            return [m for m in available_monsters() if m.startswith(text)]
        return []

    def default(self, line):
        print("Invalid command")


if __name__ == "__main__":
    MUD().cmdloop()