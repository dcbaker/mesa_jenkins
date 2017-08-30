#!/usr/bin/python

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs

class ShadercBuilder(object):
    def __init__(self):
        self._pm = bs.ProjectMap()
        self._options = bs.Options()
        self._src_dir = self._pm.project_source_dir()
        self._build_dir = self._src_dir + "/build_" + self._options.arch
        self._build_root = self._pm.build_root()

    def build(self):
        glslang = self._src_dir + "/third_party/glslang"
        if not os.path.exists(glslang):
            os.symlink("../../glslang", glslang)
        gmock = self._src_dir + "/third_party/gmock-1.7.0"
        if not os.path.exists(gmock):
            os.symlink("../../gmock", gmock)
        gtest = self._src_dir + "/third_party/gtest"
        if not os.path.exists(gtest):
            os.symlink("../../gtest", gtest)
        spirv = self._src_dir + "/third_party/spirv-tools"
        if not os.path.exists(spirv):
            os.symlink("../../spirvtools", spirv)
        spirvheaders = self._src_dir + "/third_party/spirv-tools/external/spirv-headers"
        if not os.path.exists(spirvheaders):
            os.symlink("../../spirvheaders", spirvheaders)

        if not os.path.exists(self._build_dir):
            os.makedirs(self._build_dir)
        os.chdir(self._build_dir)
        btype = "Release"
        if self._options.type == "debug":
            btype = "RelDeb"
        flags = "-m64"
        if self._options.arch == "m32":
            flags = "-m32"
        cmd = ["cmake", "-GNinja", "-DCMAKE_BUILD_TYPE=" + btype,
               "-DSHADERC_SKIP_TESTS=1",
               "-DCMAKE_C_FLAGS=" + flags, "-DCMAKE_CXX_FLAGS=" + flags,
               "-DCMAKE_INSTALL_PREFIX:PATH=" + self._build_root, ".."]
        bs.run_batch_command(cmd)
        bs.run_batch_command(["ninja"])
        bin_dir = self._build_root + "/bin/"
        if not os.path.exists(bin_dir):
            os.makedirs(bin_dir)
        
        bs.run_batch_command(["cp", "-a", "-n",
                              self._build_dir + "/glslc/glslc",
                              bin_dir])
        bs.Export().export()

    def clean(self):
        bs.git_clean(self._src_dir)

    def test(self):
        pass

bs.build(ShadercBuilder())
