#!/usr/bin/python

import os
import sys
import os.path as path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs

class WarsowTimeout:
    def __init__(self):
        self._options = bs.Options()
    def GetDuration(self):
        base_time = 20
        if "bsw" in self._options.hardware:
            base_time = base_time * 2
        if self._options.type == "daily":
            base_time = base_time * 5
        return base_time

bs.build(bs.PerfBuilder("warsow", iterations=15,
                        env={"allow_glsl_extension_directive_midshader":"true"}),
         time_limit=WarsowTimeout())

