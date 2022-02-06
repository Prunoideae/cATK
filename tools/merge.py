#!/usr/bin/env python3

from collections import defaultdict
import fileinput

existed = defaultdict(int)
for line in map(str.rstrip, fileinput.input()):
    line: str
    striped, depth = line.rsplit(maxsplit=1, sep="\t")
    existed[striped] += int(depth)
sorted = list(existed.items())
# sorted.sort(key=lambda x: x[1], reverse=True)
for x in sorted:
    print(x[0], x[1], sep="\t")
