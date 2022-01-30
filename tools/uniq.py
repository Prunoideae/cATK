#!/usr/bin/env python3

from collections import defaultdict
import fileinput

existed = defaultdict(int)
for line in map(str.rstrip, fileinput.input()):
    # ignore the read names
    striped = "\t".join(line.split("\t")[:3])
    # tag all the reads
    existed[striped] += 1

for k, v in existed.items():
    print(k, v, sep="\t")
