import cowsay

W = 10
H = 10

x, y = 0, 0
monsters = {}

def encounter(x, y):
    hello = monsters.get((x, y))
    if hello is not None:
        print(cowsay.cowsay(hello))


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
        if len(inp) != 4:
            print("Invalid arguments")
            continue

        sx, sy, hello = inp[1], inp[2], inp[3]

        if (not sx.isdigit()) or (not sy.isdigit()):
            print("Invalid arguments")
            continue

        mx = int(sx)
        my = int(sy)

        if not (0 <= mx < W and 0 <= my < H):
            print("Invalid arguments")
            continue

        replaced = (mx, my) in monsters
        monsters[(mx, my)] = hello

        print(f"Added monster to ({mx}, {my}) saying {hello}")
        if replaced:
            print("Replaced the old monster")
        continue

    print("Invalid command")
