#!/usr/bin/python

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs

bs.build(bs.CtsBuilder(suite="gl"))
