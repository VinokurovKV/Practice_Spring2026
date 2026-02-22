import sys
import os
import zlib

def list_heads():
    heads = sys.argv[1] + "/.git/refs/heads"
    out = []
    if os.path.isdir(heads):
        for root, _, files in os.walk(heads):
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, heads).replace(os.sep, "/")
                out.append(rel)
    out.sort()
    for b in out:
        print(b)

def head_of(branch):
    p = sys.argv[1] + "/.git/refs/heads/" + branch
    if not os.path.isfile(p):
        print("No such branch:", branch, file=sys.stderr)
        sys.exit(1)
    return open(p, "r", encoding="utf-8", errors="replace").read().strip()

def read_obj(sha):
    p = sys.argv[1] + "/.git/objects/" + sha[:2] + "/" + sha[2:]
    if not os.path.isfile(p):
        print("Object not found (loose):", sha, file=sys.stderr)
        sys.exit(1)
    raw = zlib.decompress(open(p, "rb").read())
    hdr, _, body = raw.partition(b"\x00")
    typ = hdr.split(b" ", 1)[0].decode()
    return typ, body

if len(sys.argv) == 2:
    list_heads()
    sys.exit(0)

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <repo> [branch]", file=sys.stderr)
    sys.exit(2)

last = head_of(sys.argv[2])
typ, body = read_obj(last)

if typ != "commit":
    print("Tip is not a commit:", last, file=sys.stderr)
    sys.exit(1)

sys.stdout.write(body.decode("utf-8", errors="replace"))

