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
    if bench == "OglTexFilterAniso":
        if hw == "bdw":
            return 4
    if bench == "OglTexFilterTri":
        if hw == "bdw":
            return 10
    if bench == "OglTerrainPanTess":
        if hw == "bdw":
            return 5
    if bench == "OglTexMem128":
        if hw == "bdw":
            return 4
    if bench == "OglVSDiffuse8":
        if hw == "bdw":
            return 8
    

low_variance_benchmarks = ["OglPSBump8",
                           "OglDeferredAA",
                           "OglTexMem128",
                           "OglTerrainPanTess",
                           "OglPSPhong",
                           "OglVSDiffuse1",
                           "OglPSPom",
                           "OglGeomTriStrip",
                           "OglPSBump2",
                           "OglTexMem512",
                           "OglTexFilterAniso",
                           "OglVSDiffuse8",
                           "OglTexFilterTri",
                           "OglShMapPcf"]

bs.build(bs.PerfBuilder(low_variance_benchmarks, iterations=3),
         time_limit=SynmarkTimeout())

