#!/usr/bin/env python3

from collections import defaultdict
import fileinput

existed = defaultdict(int)
redundant = set()
for line in map(str.rstrip, fileinput.input()):
    line: str

    # ignore the read names
    striped = line.rsplit(maxsplit=1, sep="\t")[0]
    if line not in redundant:
        # tag all the reads
        existed[striped] += 1
        redundant.add(line)

for k, v in existed.items():
    print(k, v, sep="\t")
