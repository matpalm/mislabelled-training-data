#!/usr/bin/env python
import sys,math

last_tid = None
errs = []
for line in sys.stdin:
    tid, err = line.strip().split()
    if tid != last_tid and last_tid != None:
        mean = float(sum(errs)) / len(errs)
        print "%s\t%.6f" % (last_tid, mean)
        errs = []
    err = float(err)
    errs.append(err*err)
    last_tid = tid

mean = float(sum(errs)) / len(errs)
print "%s\t%.6f" % (last_tid, mean)

