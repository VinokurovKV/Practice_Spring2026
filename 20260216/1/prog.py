import sys
import os

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

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <repo> [branch]", file=sys.stderr)
    sys.exit(2)

list_heads()

