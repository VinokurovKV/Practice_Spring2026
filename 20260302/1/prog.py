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

        name = inp[1]
        params = inp[2:]

        hello = None
        hp = None
        x = None
        y = None

        i = 0
        while i < len(params):
            if params[i] == "hello":
                hello = params[i+1]
                i += 2
            elif params[i] == "hp":
                hp = int(params[i+1])
                i += 2
            elif params[i] == "coords":
                x = int(params[i+1])
                y = int(params[i+2])
                i += 3
            else:
                print("Invalid arguments")
                break

        if None in (hello, hp, x, y):
            print("Invalid arguments")
            continue

        if name not in cowsay.list_cows() and name != "jgsbat":
            print("Cannot add unknown monster")
            continue

        replaced = (x, y) in monsters
        monsters[(x, y)] = (name, hello, hp)

        print(f"Added monster {name} to ({x}, {y}) saying {hello}")
        if replaced:
            print("Replaced the old monster")
        continue

    print("Invalid command")
