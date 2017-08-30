#!/usr/bin/python

import os
import sys
import os.path as path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs


bs.build(bs.PerfBuilder("heaven", iterations=2,
                        env={"allow_glsl_extension_directive_midshader":"true",
                             "dual_color_blend_by_location":"true"}))

