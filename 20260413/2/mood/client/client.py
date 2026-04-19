"""MOOD client logic."""

import cmd
import readline
import shlex
import socket
import sys
import threading
import time

from ..common import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    GRID_HEIGHT,
    GRID_WIDTH,
    WEAPONS,
    available_monsters,
)


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


def parse_movemonsters_args(arg):
    parts = shlex.split(arg)
    if len(parts) != 1 or parts[0] not in {"on", "off"}:
        return None
    return parts[0]


def parse_locale_args(arg):
    parts = shlex.split(arg)
    if len(parts) != 1:
        return None
    return parts[0]


def parse_client_args(argv):
    """Parse command line arguments."""
    script_file = None
    positional = []

    i = 0
    while i < len(argv):
        if argv[i] == "--file":
            if script_file is not None or i + 1 >= len(argv):
                return None
            script_file = argv[i + 1]
            i += 2
        else:
            positional.append(argv[i])
            i += 1

    if len(positional) < 1 or len(positional) > 3:
        return None

    username = positional[0]
    host = DEFAULT_HOST
    port = DEFAULT_PORT

    if len(positional) >= 2:
        host = positional[1]
    if len(positional) >= 3:
        try:
            port = int(positional[2])
        except ValueError:
            return None

    return username, host, port, script_file


def get_current_input():
    """Get the current input."""
    return readline.get_line_buffer()


def redraw_prompt(cmdline, message):
    """Show a message and redraw the prompt."""
    current_input = get_current_input()
    clear_width = len(cmdline.prompt) + len(current_input)
    print(
        f"\r{' ' * clear_width}\r{message}\n{cmdline.prompt}{current_input}",
        end="",
        flush=True,
    )


class Client:
    def __init__(self, host, port, username, send_delay=0):
        self.sock = socket.create_connection((host, port))
        self.fin = self.sock.makefile("r", encoding="utf-8")
        self.fout = self.sock.makefile("w", encoding="utf-8")
        self.send_delay = send_delay
        self.last_send_time = 0

        self.fout.write(username + "\n")
        self.fout.flush()

    def send(self, line):
        try:
            if self.send_delay > 0:
                now = time.monotonic()
                wait_time = self.send_delay - (now - self.last_send_time)
                if wait_time > 0:
                    time.sleep(wait_time)

            self.fout.write(line + "\n")
            self.fout.flush()
            self.last_send_time = time.monotonic()
        except OSError:
            pass

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
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            self.fin.close()
        except OSError:
            pass

        try:
            self.fout.close()
        except OSError:
            pass

        try:
            self.sock.close()
        except OSError:
            pass


def receiver(cmdline):
    while cmdline.alive:
        try:
            message = cmdline.client.read_block()
        except OSError:
            break

        if message is None:
            break

        if message:
            redraw_prompt(cmdline, message)

    cmdline.alive = False


class MUDClient(cmd.Cmd):
    intro = "<<< Welcome to Python-MUD 0.1 >>>"
    prompt = "(mud) "

    def __init__(
        self,
        username,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        script_file=None,
    ):
        super().__init__()
        send_delay = 1 if script_file is not None else 0
        self.client = Client(host, port, username, send_delay=send_delay)
        self.alive = True
        self.script_file = script_file

        login_reply = self.client.read_block()
        if login_reply is None:
            print("Connection closed")
            raise SystemExit(1)

        print(login_reply)

        if not login_reply.startswith("Successfully logged in as "):
            self.client.close()
            raise SystemExit(1)

        self.receiver_thread = threading.Thread(
            target=receiver, args=(self,), daemon=True
        )
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

        if not (0 <= mx < GRID_WIDTH and 0 <= my < GRID_HEIGHT):
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

    def do_sayall(self, arg):
        try:
            parts = shlex.split(arg)
        except ValueError:
            print("Invalid arguments")
            return

        if len(parts) != 1:
            print("Invalid arguments")
            return

        message = parts[0]
        self.client.send("sayall {}".format(shlex.quote(message)))

    def do_movemonsters(self, arg):
        mode = parse_movemonsters_args(arg)
        if mode is None:
            print("Invalid arguments")
            return

        self.client.send(f"movemonsters {mode}")

    def do_locale(self, arg):
        locale_name = parse_locale_args(arg)
        if locale_name is None:
            print("Invalid arguments")
            return

        self.client.send("locale {}".format(shlex.quote(locale_name)))

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

    def complete_movemonsters(self, text, line, begidx, endidx):
        parts = shlex.split(line[:begidx])

        if parts == ["movemonsters"]:
            return [mode for mode in ("on", "off") if mode.startswith(text)]

        return []

    def complete_locale(self, text, line, begidx, endidx):
        options = ["ru_RU.UTF8"]
        return [opt for opt in options if opt.startswith(text)]

    def do_EOF(self, arg):
        print()
        self.alive = False

        self.client.close()

        if self.receiver_thread.is_alive():
            self.receiver_thread.join(timeout=1)

        return True

    def run_script(self):
        """Run commands from a script file."""
        try:
            with open(self.script_file, encoding="utf-8") as script:
                for raw_line in script:
                    line = raw_line.strip()

                    if not line or line.startswith("#"):
                        continue

                    stop = self.onecmd(line)
                    if stop:
                        break
        except OSError as exc:
            print(f"Cannot open script file: {exc}")
            self.do_EOF("")
            raise SystemExit(1)

        time.sleep(1)
        self.do_EOF("")


def main(argv=None):
    """Start the client."""
    if argv is None:
        argv = sys.argv[1:]

    parsed = parse_client_args(argv)
    if parsed is None:
        print(
            "Usage: python -m mood.client <username> [host] [port] "
            "[--file script.mood]"
        )
        raise SystemExit(1)

    username, host, port, script_file = parsed

    client = MUDClient(username, host, port, script_file=script_file)
    if script_file is not None:
        client.run_script()
    else:
        client.cmdloop()


if __name__ == "__main__":
    main()
