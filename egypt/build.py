#!/usr/bin/python

import sys
import os.path as path
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), ".."))
import build_support as bs

bs.build(bs.PerfBuilder("egypt", iterations=12))

