#!/usr/bin/python

import os
import sys
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs


class SlowTimeout:
    def __init__(self):
        self.hardware = bs.Options().hardware

    def GetDuration(self):
        return 500

class DeqpLister(object):
    def __init__(self, binary, cts_tests):
        self.binary = binary
        self.o = bs.Options()
        self.pm = bs.ProjectMap()
        self.blacklist_txt = None
        self.cts_blacklist = cts_tests
        self.version = None
        bd = self.pm.project_build_dir()
        if "glk" in self.o.hardware:
            bd = self.pm.project_source_dir("prerelease") + "/deqp-test/"
        if "gles2" in self.binary:
            self.blacklist_txt = bd + self.o.hardware[:3] + "_expectations/gles2_unstable_tests.txt"
        if "gles3" in self.binary:
            self.blacklist_txt = bd + self.o.hardware[:3] + "_expectations/gles3_unstable_tests.txt"
        if "gles31" in self.binary:
            self.blacklist_txt = bd + self.o.hardware[:3] + "_expectations/gles31_unstable_tests.txt"
        if "egl" in self.binary:
            self.blacklist_txt = bd + self.o.hardware[:3] + "_expectations/egl_unstable_tests.txt"

    def tests(self, env):
        # don't execute tests that are part of the other suite
        whitelist_txt = None
        cases_xml = None
        if "gles2" in self.binary:
            whitelist_txt = self.pm.project_source_dir("deqp") + "/android/cts/master/gles2-master.txt"
            cases_xml = "dEQP-GLES2-cases.xml"
        if "gles3" in self.binary:
            whitelist_txt = self.pm.project_source_dir("deqp") + "/android/cts/master/gles3-master.txt"
            cases_xml = "dEQP-GLES3-cases.xml"
        if "gles31" in self.binary:
            whitelist_txt = self.pm.project_source_dir("deqp") + "/android/cts/master/gles31-master.txt"
            cases_xml = "dEQP-GLES31-cases.xml"
        if "egl" in self.binary:
            whitelist_txt = self.pm.project_source_dir("deqp") + "/android/cts/master/egl-master.txt"
            cases_xml = "dEQP-EGL-cases.xml"
        deqp_dir = os.path.dirname(self.binary)
        os.chdir(deqp_dir)
        cmd = [self.binary,
               "--deqp-runmode=xml-caselist"]
        bs.run_batch_command(cmd, env=env)
        all_tests = bs.DeqpTrie()
        all_tests.add_xml(cases_xml)
        whitelist = bs.DeqpTrie()
        whitelist.add_txt(whitelist_txt)
        all_tests.filter_whitelist(whitelist)
        os.chdir(self.pm.project_build_dir())
        return all_tests

    def blacklist(self, all_tests):
        if self.blacklist_txt:
            blacklist = bs.DeqpTrie()
            blacklist.add_txt(self.blacklist_txt)
            all_tests.filter(blacklist)
        all_tests.filter(self.cts_blacklist)
        if not self.version:
            self.version = bs.mesa_version()
        unsupported = []
        if "daily" != self.o.type and not self.o.retest_path:
            # these tests triple the run-time
            unsupported.append("dEQP-GLES31.functional.copy_image")
        if "13.0" in self.version:
            # Tapani's egl fixes not merged into 13.0 branch
            unsupported += ["dEQP-EGL.functional.create_context_ext",
                            "dEQP-EGL.functional.reusable_sync",
                            "dEQP-EGL.functional.thread_cleanup"]
            if "hsw" in self.o.hardware:
                unsupported += ["dEQP-GLES31.functional.debug.negative_coverage"]
            if "kbl" in self.o.hardware:
                unsupported += ["dEQP-EGL.functional.image.api.create_image_gles2_tex2d_luminance",
                                "dEQP-EGL.functional.image.api.create_image_gles2_tex2d_luminance_alpha"]
            if "bdw" in self.o.hardware:
                unsupported += ["dEQP-EGL.functional.buffer_age.no_preserve"]

        # filter immediately, since any unsupported tests under these
        # top-level categories will prevent them from being filtered.
        if "gles2" not in self.binary:
            all_tests.filter(["dEQP-GLES2"])
        if "gles31" not in self.binary:
            all_tests.filter(["dEQP-GLES31"])
        if "gles3" not in self.binary:
            all_tests.filter(["dEQP-GLES3"])
        if "egl" not in self.binary:
            all_tests.filter(["dEQP-EGL"])

        if "17.0" in self.version:
            if "byt" in self.o.hardware or "ivb" in self.o.hardware:
                unsupported += ["dEQP-GLES31.functional.debug.negative_coverage"]

        unsupported += ["dEQP-EGL.functional.robustness.reset_context.shaders.infinite_loop",
                        "dEQP-EGL.functional.render.multi_thread.gles3.rgb888_window",
                        "dEQP-EGL.functional.render.multi_thread.gles3.rgba8888_window",
                        "dEQP-EGL.functional.render.multi_thread.gles2_gles3.rgba8888_window",
                        "dEQP-EGL.functional.robustness.negative_context.invalid_robust_shared_context_creation"]

        all_tests.filter(unsupported)
        
class DeqpBuilder(object):
    def __init__(self):
        self.pm = bs.ProjectMap()
        self.o = bs.Options()
        self.env = {}
        self.version = None
    def build(self):
        pass
    def clean(self):
        pass
    def test(self):
        cts_blacklist = bs.CtsTestList().tests()
        for suite in ["ES32", "ES31", "ES3", "ES2"]:
            if suite + "-CTS" in cts_blacklist._trie:
                cts_blacklist._trie["dEQP-GL" + suite] = cts_blacklist._trie[suite + "-CTS"]
        if "hsw" in self.o.hardware or "byt" in self.o.hardware or "ivb" in self.o.hardware:
            self.env["MESA_GLES_VERSION_OVERRIDE"] = "3.1"
        t = bs.DeqpTester()
        all_results = bs.DeqpTrie()

        if not self.version:
            self.version = bs.mesa_version()
        if "glk" in self.o.hardware:
            if "13.0" in self.version or "17.0" in self.version:
                return

        modules = ["gles2", "gles3", "egl"]
        for hardware in ["skl", "bdw", "bsw", "hsw", "byt", "ivb"]:
            if hardware in self.o.hardware:
                modules += ["gles31"]
                break

        for module in modules:
            binary = self.pm.build_root() + "/opt/deqp/modules/" + module + "/deqp-" + module
            results = t.test(binary,
                             DeqpLister(binary, cts_blacklist),
                             [],
                             self.env)
            all_results.merge(results)

        config = bs.get_conf_file(self.o.hardware, self.o.arch, project=self.pm.current_project())
        t.generate_results(all_results, bs.ConfigFilter(config, self.o))
        
bs.build(DeqpBuilder(), time_limit=SlowTimeout())
        
