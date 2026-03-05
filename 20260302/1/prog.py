import cowsay
import shlex

W = 10
H = 10

x, y = 0, 0
monsters = {}

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

def encounter(x, y):
    m = monsters.get((x, y))
    if m is not None:
        name, hello, hp = m

        if name == "jgsbat":
            print(cowsay.cowsay(hello, cowfile=jgsbat))
        else:
            print(cowsay.cowsay(hello, cow=name))


print("<<< Welcome to Python-MUD 0.1 >>>")

while inp := shlex.split(input()):
    cmd = inp[0]

    if cmd in ("up", "down", "left", "right"):
        if len(inp) != 1:
            print("Invalid arguments")
            continue

        if cmd == "up":
            y = (y - 1) % H
        elif cmd == "down":
            y = (y + 1) % H
        elif cmd == "left":
            x = (x - 1) % W
        else:
            x = (x + 1) % W

        print(f"Moved to ({x}, {y})")
        encounter(x, y)
        continue

    if cmd == "addmon":

        if len(inp) < 8:
            print("Invalid arguments")
            continue

        name = inp[1]
        params = inp[2:]

        hello = None
        hp = None
        mx = None
        my = None

        i = 0
        while i < len(params):

            if params[i] == "hello":
                hello = params[i+1]
                i += 2

            elif params[i] == "hp":
                if not params[i+1].isdigit():
                    print("Invalid arguments")
                    break
                hp = int(params[i+1])
                i += 2

            elif params[i] == "coords":
                if not params[i+1].isdigit() or not params[i+2].isdigit():
                    print("Invalid arguments")
                    break
                mx = int(params[i+1])
                my = int(params[i+2])
                i += 3

            else:
                print("Invalid arguments")
                break

        if None in (hello, hp, mx, my):
            print("Invalid arguments")
            continue

        if not (0 <= mx < W and 0 <= my < H):
            print("Invalid arguments")
            continue

        if name not in cowsay.list_cows() and name != "jgsbat":
            print("Cannot add unknown monster")
            continue

        replaced = (mx, my) in monsters
        monsters[(mx, my)] = (name, hello, hp)

        print(f"Added monster {name} to ({mx}, {my}) saying {hello}")
        if replaced:
            print("Replaced the old monster")

        continue

    print("Invalid command")
