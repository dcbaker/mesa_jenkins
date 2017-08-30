#!/usr/bin/python

import os
import sys
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs

# HACK
# repeatedly invoking build() will overwrite the start times.  Record
# it now and write the correct value when the last build() has
# finished.  build() was not intended to be used this way.

start_time = time.time()

bs.build(bs.PiglitTester(_suite="cpu", device_override="byt"))
bs.build(bs.PiglitTester(_suite="cpu", device_override="g45"), import_build=False)
bs.build(bs.PiglitTester(_suite="cpu", device_override="g965"), import_build=False)
bs.build(bs.PiglitTester(_suite="cpu", device_override="ilk"), import_build=False)
bs.build(bs.PiglitTester(_suite="cpu", device_override="ivbgt2"), import_build=False)

options = bs.Options()
if (options.result_path):
    bs.ProjectInvoke(options).set_info("start_time", start_time)
