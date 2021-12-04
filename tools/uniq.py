#!/usr/bin/env python3

import fileinput

printed = set()
for line in map(str.rstrip, fileinput.input()):
    # ignore the read names
    striped = "\t".join(line.split("\t")[:3])
    if striped not in printed:
        printed.add(striped)
        print(line)
