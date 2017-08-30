#!/usr/bin/python

import sys
import os.path as path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs

class SynmarkTimeout:
    def __init__(self):
        self._options = bs.Options()
    def GetDuration(self):
        if self._options.type == "daily":
            return 120
        return 30

def iterations(bench, hw):
    if bench == "OglHdrBloom":
        if hw == "skl":
            return 4
    if bench == "OglVSTangent":
        if hw == "bdw":
            return 4

high_variance_benchmarks = ["OglFillTexSingle",
                            "OglBatch3",
                            "OglDeferred",
                            "OglBatch1",
                            "OglBatch4",
                            "OglGeomPoint",
                            "OglBatch0",
                            "OglHdrBloom",
                            "OglCSCloth",
                            "OglShMapVsm",
                            "OglVSTangent",
                            "OglFillTexMulti",
                            "OglFillPixel",
                            "OglGeomTriList"]

bs.build(bs.PerfBuilder(high_variance_benchmarks, iterations=2,
                        custom_iterations_fn=iterations),
         time_limit=SynmarkTimeout())
