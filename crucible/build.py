#!/usr/bin/python

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs

class CrucibleBuilder(bs.AutoBuilder):
    def __init__(self):
        self._pm = bs.ProjectMap()
        glslc = "GLSLC=" + self._pm.build_root() + "/bin/glslc"
        mesa_lib = "MESA_LDFLAGS=-L" + self._pm.build_root() + "/lib"
        mesa_include = "MESA_CPPFLAGS=-I" + os.path.abspath(self._pm.project_source_dir() + "/../mesa/include")
        bs.AutoBuilder.__init__(self, configure_options=[glslc, mesa_lib, mesa_include])
        self._build_dir = self._src_dir

    def build(self):
        bs.AutoBuilder.build(self)
        bin_dir = self._build_root + "/bin/"
        if not os.path.exists(bin_dir):
            os.makedirs(bin_dir)
        bs.run_batch_command(["cp", "-a", "-n",
                              self._build_dir + "/bin/crucible",
                              bin_dir])
        bs.run_batch_command(["cp", "-a", "-n",
                              self._build_dir + "/data/",
                              self._build_root])
        bs.Export().export()

bs.build(CrucibleBuilder())


