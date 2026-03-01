import cowsay

W = 10
H = 10

x, y = 0, 0
monsters = {}

def encounter(x, y):
    m = monsters.get((x, y))
    if m is not None:
        name, hello = m
        print(cowsay.cowsay(hello, cow=name))


while inp := input().split():
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
        if len(inp) != 5:
            print("Invalid arguments")
            continue

        name, sx, sy, hello = inp[1], inp[2], inp[3], inp[4]

        if (not sx.isdigit()) or (not sy.isdigit()):
            print("Invalid arguments")
            continue

        mx = int(sx)
        my = int(sy)

        if not (0 <= mx < W and 0 <= my < H):
            print("Invalid arguments")
            continue

        if name not in cowsay.list_cows():
            print("Cannot add unknown monster")
            continue

        replaced = (mx, my) in monsters
        monsters[(mx, my)] = (name, hello)

        print(f"Added monster {name} to ({mx}, {my}) saying {hello}")
        if replaced:
            print("Replaced the old monster")
        continue

    print("Invalid command")
