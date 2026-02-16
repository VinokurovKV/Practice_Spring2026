import sys
from pathlib import Path

for obj in Path(sys.argv[1]).glob(".git/objects/??/*"):
    print(obj)
    data = zlib.decompress(obj.read_bytes())
    head, _, tail = data.partition(b'\x00')
    kind, size = head.split()
    match kind.decode():
        case 'commit':
            print(tail.decode())

