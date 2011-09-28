#!/usr/bin/env python
import sys
for line in sys.stdin:
    for char in line.decode('utf-8'):
        print char.encode('utf-8')
