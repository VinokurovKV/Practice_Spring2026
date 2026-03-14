import cmd
import cowsay
import shlex

W = 10
H = 10

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


class Game:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.monsters = {}

    def encounter(self):
        monster = self.monsters.get((self.x, self.y))
        if monster is None:
            return

        name, hello, hp = monster
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
        self.monsters[(mx, my)] = (name, hello, hp)

        print(f"Added monster {name} to ({mx}, {my}) saying {hello}")
        if replaced:
            print("Replaced the old monster")


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
        parts = shlex.split(arg)
        if len(parts) < 7:
            print("Invalid arguments")
            return

        name = parts[0]
        params = parts[1:]

        hello = None
        hp = None
        mx = None
        my = None

        i = 0
        ok = True
        while i < len(params):
            if params[i] == "hello":
                if i + 1 >= len(params):
                    ok = False
                    break
                hello = params[i + 1]
                i += 2
            elif params[i] == "hp":
                if i + 1 >= len(params) or not params[i + 1].isdigit():
                    ok = False
                    break
                hp = int(params[i + 1])
                i += 2
            elif params[i] == "coords":
                if i + 2 >= len(params):
                    ok = False
                    break
                if not params[i + 1].isdigit() or not params[i + 2].isdigit():
                    ok = False
                    break
                mx = int(params[i + 1])
                my = int(params[i + 2])
                i += 3
            else:
                ok = False
                break

        if not ok or None in (hello, hp, mx, my):
            print("Invalid arguments")
            return

        if not (0 <= mx < W and 0 <= my < H):
            print("Invalid arguments")
            return

        if name not in cowsay.list_cows() and name != "jgsbat":
            print("Cannot add unknown monster")
            return

        self.game.addmon(name, hello, hp, mx, my)

    def default(self, line):
        print("Invalid command")


if __name__ == "__main__":
    MUD().cmdloop()