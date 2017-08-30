#!/usr/bin/python

import os
import sys
import re
import xml.etree.ElementTree  as ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs

            
class CtsBuilder:
    def __init__(self):
        o = bs.Options()
        pm = bs.ProjectMap()
        self.build_root = pm.build_root()
        libdir = "x86_64-linux-gnu"
        self.version = None
        if o.arch == "m32":
            libdir = "i386-linux-gnu"
        self.env = { "LD_LIBRARY_PATH" : self.build_root + "/lib:" + \
                     self.build_root + "/lib/" + libdir + ":" + self.build_root + "/lib/dri",
                     "LIBGL_DRIVERS_PATH" : self.build_root + "/lib/dri",
                     "GBM_DRIVERS_PATH" : self.build_root + "/lib/dri",
                     # fixes dxt subimage tests that fail due to a
                     # combination of unreasonable tolerances and possibly
                     # bugs in debian's s2tc library.  Recommended by nroberts
                     "S2TC_DITHER_MODE" : "NONE",

                     # without this, Xorg limits frame rate to 1 FPS
                     # when display sleeps, cratering tests execution
                     "vblank_mode": "0"
        }

        self.env["MESA_GL_VERSION_OVERRIDE"] = "4.5"
        self.env["MESA_GLSL_VERSION_OVERRIDE"] = "450"
        o.update_env(self.env)

    def build(self):
        pass

    def clean(self):
        pass

    def test(self):
        o = bs.Options()
        pm = bs.ProjectMap()

        if not self.version:
            self.version = bs.mesa_version()

        conf_file = bs.get_conf_file(o.hardware, o.arch, "cts-test")

        # invoke piglit
        self.env["PIGLIT_CTS_GL_BIN"] = self.build_root + "/bin/gl/cts/glcts"
        out_dir = self.build_root + "/test/" + o.hardware

        include_tests = []
        if o.retest_path:
            testlist = bs.TestLister(o.retest_path + "/test/")
            include_tests = testlist.RetestIncludes(project="cts-test")
            if not include_tests:
                # we were supposed to retest failures, but there were none
                return

        # this test is flaky in glcts.  It passes enough for
        # submission, but as per Ken, no developer will want to look
        # at it to figure out why the test is flaky.
        extra_excludes = ["packed_depth_stencil.packed_depth_stencil_copyteximage"]

        suite_names = []
        # disable gl cts on stable versions of mesa, which do not
        # support the feature set.
        if "13.0" in self.version:
            return
        if "17.0" in self.version and "glk" in o.hardware:
            # glk not supported by stable mesa
            return
        suite_names.append("cts_gl")
        # as per Ian, only run gl45
        extra_excludes += ["gl30-cts",
                           "gl31-cts",
                           "gl32-cts",
                           "gl33-cts",
                           "gl40-cts",
                           "gl41-cts",
                           "gl42-cts",
                           "gl43-cts",
                           "gl44-cts"]
        if "hsw" in o.hardware:
            # flaky cts_gl tests
            extra_excludes += ["shader_image_load_store.multiple-uniforms",
                               "shader_image_size.basic-nonms-fs",
                               "shader_image_size.advanced-nonms-fs",
                               "texture_gather.gather-tesselation-shader",
                               "vertex_attrib_binding.basic-inputl-case1",
                               "gpu_shader_fp64.named_uniform_blocks",
                               # gpu hang
                               "gl45-cts.tessellation_shader.vertex_spacing",
                               "gl45-cts.tessellation_shader.vertex_ordering",
                               "gl45-cts.tessellation_shader.tessellation_control_to_tessellation_evaluation.gl_maxpatchvertices_position_pointsize"]

        exclude_tests = []
        for  a in extra_excludes:
            exclude_tests += ["--exclude-tests", a]
        if not suite_names:
            # for master, on old hardware, this component will not
            # test anything.  The gles tests are instead targeted with
            # the gles32 cts, in the glescts-test component
            return
        cmd = [self.build_root + "/bin/piglit",
               "run",
               #"-p", "gbm",
               "-b", "junit",
               "--config", conf_file,
               "-c",
               "--exclude-tests", "esext-cts",
               "--junit_suffix", "." + o.hardware + o.arch] + \
               exclude_tests + \
               include_tests + suite_names + [out_dir]

        bs.run_batch_command(cmd, env=self.env,
                             expected_return_code=None,
                             streamedOutput=True)
        single_out_dir = self.build_root + "/../test"
        if not os.path.exists(single_out_dir):
            os.makedirs(single_out_dir)

        if os.path.exists(out_dir + "/results.xml"):
            # Uniquely name all test files in one directory, for
            # jenkins
            filename_components = ["/piglit-cts",
                                   o.hardware,
                                   o.arch]
            if o.shard != "0":
                # only put the shard suffix on for non-zero shards.
                # Having _0 suffix interferes with bisection.
                filename_components.append(o.shard)

            revisions = bs.RepoSet().branch_missing_revisions()
            print "INFO: filtering tests from " + out_dir + "/results.xml"
            self.filter_tests(revisions,
                              out_dir + "/results.xml",
                              single_out_dir + "_".join(filename_components) + ".xml")

            # create a copy of the test xml in the source root, where
            # jenkins can access it.
            cmd = ["cp", "-a", "-n",
                   self.build_root + "/../test", pm.source_root()]
            bs.run_batch_command(cmd)
        else:
            print "ERROR: no results at " + out_dir + "/results.xml"

        bs.check_gpu_hang()
        bs.Export().export_tests()

    def filter_tests(self, revisions, infile, outfile):
        """this method is ripped bleeding from builders.py / PiglitTester"""
        t = ET.parse(infile)
        for a_suite in t.findall("testsuite"):
            # remove skipped tests, which uses ram on jenkins when
            # displaying and provides no value.  
            for a_skip in a_suite.findall("testcase/skipped/.."):
                if a_skip.attrib["status"] in ["crash", "fail"]:
                    continue
                a_suite.remove(a_skip)

            # for each failure, see if there is an entry in the config
            # file with a revision that was missed by a branch
            for afail in a_suite.findall("testcase/failure/..") + a_suite.findall("testcase/error/.."):
                piglit_test = bs.PiglitTest("foo", "foo", afail)
                regression_revision = piglit_test.GetConfRevision()
                abbreviated_revisions = [a_rev[:6] for a_rev in revisions]
                for abbrev_rev in abbreviated_revisions:
                    if abbrev_rev in regression_revision:
                        print "stripping: " + piglit_test.test_name + " " + regression_revision
                        a_suite.remove(afail)
                        # a test may match more than one revision
                        # encoded in a comment
                        break

            # strip unneeded output from passing tests
            for apass in a_suite.findall("testcase"):
                if apass.attrib["status"] != "pass":
                    continue
                if apass.find("failure") is not None:
                    continue
                out_tag = apass.find("system-out")
                if out_tag is not None:
                    apass.remove(out_tag)
                err_tag = apass.find("system-err")
                if err_tag is not None and err_tag.text is not None:
                    found = False
                    for a_line in err_tag.text.splitlines():
                        m = re.match("pid: ([0-9]+)", a_line)
                        if m is not None:
                            found = True
                            err_tag.text = a_line
                            break
                    if not found:
                        apass.remove(err_tag)
                
        t.write(outfile)

class SlowTimeout:
    def __init__(self):
        self.hardware = bs.Options().hardware

    def GetDuration(self):
        return 500

bs.build(CtsBuilder(), time_limit=SlowTimeout())
        
