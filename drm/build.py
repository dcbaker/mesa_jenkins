#!/usr/bin/python


import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs

class DrmBuilder(bs.AutoBuilder):
    def __init__(self):
        bs.AutoBuilder.__init__(self)

    def test(self):
        # libdrm now has a 2-minute long test, which is too long to
        # wait for.
        pass

bs.build(DrmBuilder())

