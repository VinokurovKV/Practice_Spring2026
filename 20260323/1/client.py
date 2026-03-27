import cmd
import cowsay
import shlex
import socket
import io
import sys
import threading

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
    def __init__(self, host, port, username):
        self.sock = socket.create_connection((host, port))
        self.fin = self.sock.makefile("r", encoding="utf-8")
        self.fout = self.sock.makefile("w", encoding="utf-8")

        self.fout.write(username + "\n")
        self.fout.flush()

    def send(self, line):
        self.fout.write(line + "\n")
        self.fout.flush()

    def read_block(self):
        result = []
        while True:
            reply = self.fin.readline()
            if reply == "":
                return None
            reply = reply.rstrip("\n")
            if reply == "":
                break
            result.append(reply)
        return "\n".join(result)

    def close(self):
        self.fin.close()
        self.fout.close()
        self.sock.close()


def receiver(cmdline):
    while cmdline.alive:
        try:
            message = cmdline.client.read_block()
        except OSError:
            break

        if message is None:
            break

        if message:
            print()
            print(message)

    cmdline.alive = False


class MUDClient(cmd.Cmd):
    intro = "<<< Welcome to Python-MUD 0.1 >>>"
    prompt = "(mud) "

    def __init__(self, username):
        super().__init__()
        self.client = Client(HOST, PORT, username)
        self.alive = True

        login_reply = self.client.read_block()
        if login_reply is None:
            print("Connection closed")
            raise SystemExit(1)

        print(login_reply)

        if not login_reply.startswith("Successfully logged in as "):
            self.client.close()
            raise SystemExit(1)

        self.receiver_thread = threading.Thread(target=receiver, args=(self,), daemon=True)
        self.receiver_thread.start()

    def emptyline(self):
        pass

    def default(self, line):
        print("Invalid command")

    def do_up(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.client.send("move 0 -1")

    def do_down(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.client.send("move 0 1")

    def do_left(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.client.send("move -1 0")

    def do_right(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.client.send("move 1 0")

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
        self.client.send(request)

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
        request = "attack {} {} {}".format(
            shlex.quote(monster),
            damage,
            shlex.quote(weapon),
        )
        self.client.send(request)

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
        self.alive = False
        self.client.close()
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python client.py <username> [host] [port]")
        raise SystemExit(1)

    username = sys.argv[1]

    if len(sys.argv) >= 3:
        HOST = sys.argv[2]
    if len(sys.argv) >= 4:
        PORT = int(sys.argv[3])

    MUDClient(username).cmdloop()