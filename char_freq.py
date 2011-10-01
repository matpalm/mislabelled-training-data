#!/usr/bin/env python
# can't use sort|uniq -c where there are uber weird characters

import sys
from collections import *

freq = defaultdict(int)
for line in sys.stdin:
    for char in line.decode('utf-8'):
        freq[char] += 1

for key in freq:
    print "%d\t%s" % (freq[key],key.encode('utf-8'))


