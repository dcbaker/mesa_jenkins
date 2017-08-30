#!/usr/bin/python

import sys
import os
import os.path as path
import xml.etree.ElementTree as ET
import ConfigParser
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs


def post_process_results(xml):
    t = ET.parse(xml)
    o = bs.Options()
    conf = None
    try:
        conf = bs.get_conf_file(o.hardware, o.arch, project="crucible-test")
    except bs.NoConfigFile:
        pass
    if conf:
        # key=name, value=status
        expected_status = {}
        c = ConfigParser.SafeConfigParser(allow_no_value=True)
        c.read(conf)
        for section in c.sections():
            for (test, _) in c.items(section):
                if test in expected_status:
                    raise Exception("test has multiple entries: " + test)
                expected_status[test] = section
        for atest in t.findall(".//testcase"):
            if atest.attrib["name"] not in expected_status:
                continue
            if atest.attrib["status"] == "lost":
                atest.attrib["status"] = "crash"

            expected = expected_status[atest.attrib["name"]]
            if expected == "expected-failures":
                # change fail to pass
                if atest.attrib["status"] == "fail":
                    for ftag in atest.findall("failure"):
                        atest.remove(ftag)
                    so = ET.Element("system-out")
                    so.text = "Passing test as an expected failure"
                    atest.append(so)
                elif atest.attrib["status"] == "crash":
                    atest.append(ET.Element("failure"))
                    so = ET.Element("system-out")
                    so.text = "ERROR: this test crashed when it expected failure"
                    atest.append(so)
                elif atest.attrib["status"] == "pass":
                    atest.append(ET.Element("failure"))
                    so = ET.Element("system-out")
                    so.text = "ERROR: this test passed when it expected failure"
                    atest.append(so)
                elif atest.attrib["status"] == "skip":
                    atest.append(ET.Element("failure"))
                    so = ET.Element("system-out")
                    so.text = "ERROR: this test skipped when it expected failure"
                    atest.append(so)
                else:
                    raise Exception("test has unknown status: " + atest.attrib["name"]
                                    + " " + atest.attrib["status"])
            elif expected == "expected-crashes":
                # change error to pass
                if atest.attrib["status"] == "crash":
                    for ftag in atest.findall("error"):
                        atest.remove(ftag)
                    so = ET.Element("system-out")
                    so.text = "Passing test as an expected crash"
                    atest.append(so)
                elif atest.attrib["status"] == "fail":
                    atest.append(ET.Element("failure"))
                    so = ET.Element("system-out")
                    so.text = "ERROR: this test failed when it expected crash"
                    atest.append(so)
                elif atest.attrib["status"] == "pass":
                    atest.append(ET.Element("failure"))
                    so = ET.Element("system-out")
                    so.text = "ERROR: this test passed when it expected crash"
                    atest.append(so)
                elif atest.attrib["status"] == "skip":
                    atest.append(ET.Element("failure"))
                    so = ET.Element("system-out")
                    so.text = "ERROR: this test skipped when it expected crash"
                    atest.append(so)
                else:
                    raise Exception("test has unknown status: " + atest.attrib["name"]
                                    + " " + atest.attrib["status"])

    for atest in t.findall(".//testcase"):
        atest.attrib["name"] = atest.attrib["name"] + "." + o.hardware + o.arch
    t.write(xml)

class CrucibleTester(object):
    def __init__(self):
        pass
    def build(self):
        pass
    def clean(self):
        pass


    def test(self):
        pm = bs.ProjectMap()
        build_root = pm.build_root()
        global_opts = bs.Options()
        if global_opts.arch == "m64":
            icd_name = "intel_icd.x86_64.json"
        elif global_opts.arch == "m32":
            icd_name = "intel_icd.i686.json"
        env = { "LD_LIBRARY_PATH" : build_root + "/lib",
                "VK_ICD_FILENAMES" : build_root + "/share/vulkan/icd.d/" + icd_name,
                "ANV_ABORT_ON_DEVICE_LOSS" : "true"}
        o = bs.Options()
        o.update_env(env)
        br = bs.ProjectMap().build_root()
        out_dir = br + "/../test"
        if not path.exists(out_dir):
            os.makedirs(out_dir)
        out_xml = out_dir + "/piglit-crucible_" + o.hardware + "_"  + o.arch + ".xml"
        include_tests = []
        if o.retest_path:
            include_tests = bs.TestLister(o.retest_path + "/test/").RetestIncludes("crucible-test")

        # flaky
        excludes = ["!func.query.timestamp",
                    "!func.ssbo.interleve",
                    # https://bugs.freedesktop.org/show_bug.cgi?id=102267
                    "!func.sync.semaphore-fd.opaque-fd"]

        parallelism = []

        if "hsw" in o.hardware:
            # issue 4
            excludes += ["!func.copy.copy-buffer.large",
                         "!func.interleaved-cmd-buffers.end1*",
                         "!func.miptree.d32-sfloat.aspect-depth.view*",
                         "!func.miptree.r8g8b8a8-unorm.aspect-color.view*",
                         "!func.miptree.s8-uint.aspect-stencil*",
                         "!func.renderpass.clear.color08",
                         "!func.ssbo.interleve"]
        if "ivb" in o.hardware:
            # issue 5
            excludes += ["!func.depthstencil*",
                         "!func.miptree.r8g8b8a8-unorm.aspect-color.view*",
                         "!func.miptree.s8-uint.aspect-stencil*",
                         "!func.miptree.d32-sfloat.aspect-depth.view*",
                         "!stress.lots-of-surface-state.fs.static"]
            parallelism = ['-j', '1']
            
        if "byt" in o.hardware:
            # issue 6
            excludes += ["!func.miptree.d32-sfloat.aspect-depth.view-3d.levels0*",
                         "!func.depthstencil*",
                         "!func.miptree.s8-uint.aspect-stencil*",
                         "!stress.lots-of-surface-state.fs.static"]
            parallelism = ['-j', '1']

        if "bsw" in o.hardware:
            excludes += ["!func.event.cmd_buffer"] # intermittent fail/crash


        if "bxt" in o.hardware:
            excludes += ["!func.miptree.s8-uint.aspect-stencil*",
                         "!stress.lots-of-surface-state.fs.static"]

        bs.run_batch_command([ br + "/bin/crucible",
                               "run", "--fork", "--log-pids",
                               "--junit-xml=" + out_xml] + parallelism + include_tests + excludes,
                             env=env,
                             expected_return_code=None)
        post_process_results(out_xml)
        bs.run_batch_command(["cp", "-a", "-n",
                              out_dir, pm.source_root()])

        bs.check_gpu_hang()
        bs.Export().export_tests()

bs.build(CrucibleTester())
