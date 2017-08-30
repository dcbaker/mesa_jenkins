#!/usr/bin/python

import ConfigParser
import multiprocessing
import os
import subprocess
import sys
import time
import xml.sax.saxutils as saxutils

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs

# needed to preserve case in the options
class CaseConfig(ConfigParser.SafeConfigParser):
    def optionxform(self, optionstr):
        return optionstr


class GLESCTSTester(object):
    def __init__(self):
        self.o = bs.Options()
        self.pm = bs.ProjectMap()

        self.env = {"MESA_GLES_VERSION_OVERRIDE" : ""}
        if self._gles_32():
            self.env["MESA_GLES_VERSION_OVERRIDE"] = "3.2"
        elif self._gles_31():
            self.env["MESA_GLES_VERSION_OVERRIDE"] = "3.1"

    def _gles_32(self):
        return ("skl" in self.o.hardware or
                "kbl" in self.o.hardware or
                "bxt" in self.o.hardware)

    def _gles_31(self):
        return ("hsw" in self.o.hardware or
                "bdw" in self.o.hardware or
                "bsw" in self.o.hardware or
                "byt" in self.o.hardware or
                "ivb" in self.o.hardware)

    def test(self):
        t = bs.DeqpTester()
        version = bs.mesa_version()
        if "bxt" in self.o.hardware:
            if "13.0" in version:
                # unsupported platforms
                return
        if "glk" in self.o.hardware:
            if "17.0" in version:
                # unsupported platforms
                return

        results = t.test(self.pm.build_root() + "/bin/es/cts/glcts",
                         bs.CtsTestList(),
                         [],
                         self.env)

        o = bs.Options()
        config = bs.get_conf_file(self.o.hardware, self.o.arch, project=self.pm.current_project())
        t.generate_results(results, bs.ConfigFilter(config, o))

    def build(self):
        pass
    def clean(self):
        pass

class SlowTimeout:
    def __init__(self):
        self.hardware = bs.Options().hardware

    def GetDuration(self):
        return 120

bs.build(GLESCTSTester(), time_limit=SlowTimeout())
