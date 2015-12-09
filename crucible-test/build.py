#!/usr/bin/python

import sys
import os
import os.path as path
import xml.etree.ElementTree as ET
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), ".."))
import build_support as bs


class CrucibleTester(object):
    def __init__(self):
        pass
    def build(self):
        pass
    def clean(self):
        pass

    def post_process_results(self, xml):
        t = ET.parse(xml)
        o = bs.Options()
        for atest in t.findall(".//testcase"):
            atest.attrib["name"] = atest.attrib["name"] + "." + o.hardware + o.arch
        t.write(xml)

    def test(self):
        pm = bs.ProjectMap()
        build_root = pm.build_root()
        env = { "LD_LIBRARY_PATH" : build_root + "/lib"}
        o = bs.Options()
        o.update_env(env)
        br = bs.ProjectMap().build_root()
        out_dir = br + "/../test"
        if not path.exists(out_dir):
            os.makedirs(out_dir)
        out_xml = out_dir + "/piglit-crucible_" + o.hardware + "_"  + o.arch + ".xml"
        bs.run_batch_command([ br + "/bin/crucible",
                              "run",
                               "--junit-xml=" + out_xml],
                             env=env,
                             expected_return_code=None)
        self.post_process_results(out_xml)
        bs.run_batch_command(["cp", "-a", "-n",
                              out_dir, pm.source_root()])

        bs.Export().export_tests()

bs.build(CrucibleTester())
