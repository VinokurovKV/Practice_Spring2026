import cmd
import cowsay
import shlex
import socket
import io

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

    monster = "*"
    weapon = "sword"

    if not parts:
        return monster, weapon

    if parts[0] == "with":
        if len(parts) != 2:
            return "INVALID"
        weapon = parts[1]
        return monster, weapon

    monster = parts[0]

    if len(parts) == 1:
        return monster, weapon

    if len(parts) == 3 and parts[1] == "with":
        weapon = parts[2]
        return monster, weapon

    return "INVALID"


class Client:
    def __init__(self, host, port):
        self.sock = socket.create_connection((host, port))
        self.fin = self.sock.makefile("r", encoding="utf-8")
        self.fout = self.sock.makefile("w", encoding="utf-8")

    def request(self, line):
        self.fout.write(line + "\n")
        self.fout.flush()

        result = []
        while True:
            reply = self.fin.readline()
            if reply == "":
                break
            reply = reply.rstrip("\n")
            if reply == "":
                break
            result.append(reply)
        return result

    def close(self):
        self.fin.close()
        self.fout.close()
        self.sock.close()


class MUDClient(cmd.Cmd):
    intro = "<<< Welcome to Python-MUD 0.1 >>>"
    prompt = "(mud) "

    def __init__(self):
        super().__init__()
        self.client = Client(HOST, PORT)

    def emptyline(self):
        pass

    def default(self, line):
        print("Invalid command")

    def print_reply(self, reply):
        for line in reply:
            parts = shlex.split(line)

            if not parts:
                continue

            if parts[0] == "moved":
                print(f"Moved to ({parts[1]}, {parts[2]})")

            elif parts[0] == "encounter":
                name = parts[1]
                hello = parts[2]
                if name == "jgsbat":
                    print(cowsay.cowsay(hello, cowfile=jgsbat))
                else:
                    print(cowsay.cowsay(hello, cow=name))

            elif parts[0] == "added":
                name, x, y, hello = parts[1], parts[2], parts[3], parts[4]
                print(f"Added monster {name} to ({x}, {y}) saying {hello}")

            elif parts[0] == "replaced":
                print("Replaced the old monster")

            elif parts[0] == "nomonster":
                if len(parts) == 1:
                    print("No monster here")
                else:
                    print(f"No {parts[1]} here")


            elif parts[0] == "attacked":
                name = parts[1]
                damage = parts[2]
                hp_left = int(parts[3])

                print(f"Attacked {name}, damage {damage} hp")

                if hp_left == 0:
                    print(f"{name} died")
                else:
                    print(f"{name} now has {hp_left}")

    def do_up(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.print_reply(self.client.request("move 0 -1"))

    def do_down(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.print_reply(self.client.request("move 0 1"))

    def do_left(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.print_reply(self.client.request("move -1 0"))

    def do_right(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.print_reply(self.client.request("move 1 0"))

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

        request = "addmon {} {} {} {} {}".format(
            shlex.quote(name),
            shlex.quote(hello),
            hp,
            mx,
            my,
        )
        self.print_reply(self.client.request(request))

    def do_attack(self, arg):
        parsed = parse_attack_args(arg)
        if parsed == "INVALID":
            print("Invalid arguments")
            return

        monster, weapon = parsed

        if weapon not in WEAPONS:
            print("Unknown weapon")
            return

        damage = WEAPONS[weapon]
        request = f"attack {shlex.quote(monster)} {damage}"
        self.print_reply(self.client.request(request))

    def complete_attack(self, text, line, begidx, endidx):
        parts = shlex.split(line[:begidx])

        if parts == ["attack"]:
            return [m for m in available_monsters() if m.startswith(text)]

        if parts == ["attack", "with"]:
            return [w for w in WEAPONS if w.startswith(text)]

        if len(parts) == 2 and parts[0] == "attack":
            options = []
            if "with".startswith(text):
                options.append("with")
            return options

        if len(parts) == 3 and parts[0] == "attack" and parts[2] == "with":
            return [w for w in WEAPONS if w.startswith(text)]

        return []

    def do_EOF(self, arg):
        print()
        self.client.close()
        return True


if __name__ == "__main__":
    MUDClient().cmdloop()
