import sys
from pathlib import Path

for obj in Path(sys.argv[1]).glob(".git/objects/??/*"):
    print(obj)
