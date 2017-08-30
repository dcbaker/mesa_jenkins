#!/usr/bin/python

import sys, os, importlib, git
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs

class DeqpBuilder(bs.CMakeBuilder):
    def __init__(self, extra_definitions=None, compiler="gcc"):
        bs.CMakeBuilder.__init__(self,
                                 extra_definitions=extra_definitions, 
                                 compiler=compiler, install=False)
        self._o = bs.Options()
        self._pm = bs.ProjectMap()

    def build(self):
        has_vulkan = os.path.exists(self._src_dir + "/external/spirv-tools")
        if has_vulkan:
            spirvtools = self._src_dir + "/external/spirv-tools/src"
            if not os.path.islink(spirvtools):
                bs.rmtree(spirvtools)
            if not os.path.exists(spirvtools):
                os.symlink("../../../spirvtools", spirvtools)
            glslang = self._src_dir + "/external/glslang/src"
            if not os.path.islink(glslang):
                bs.rmtree(glslang)
            if not os.path.exists(glslang):
                os.symlink("../../../glslang", glslang)
            spirvheaders_dir = self._src_dir + "/external/spirv-headers"
            if not os.path.exists(spirvheaders_dir):
                os.makedirs(spirvheaders_dir)
            spirvheaders = spirvheaders_dir + "/src"
            if not os.path.islink(spirvheaders):
                bs.rmtree(spirvheaders)
            if not os.path.exists(spirvheaders):
                os.symlink("../../../spirvheaders", spirvheaders)

            # change spirv-tools and glslang to use the commits specified
            # in the vulkancts sources
            sys.path = [os.path.abspath(os.path.normpath(s)) for s in sys.path]
            sys.path = [gooddir for gooddir in sys.path if "deqp" not in gooddir]
            sys.path.append(self._src_dir + "/external/")
            fetch_sources = importlib.import_module("fetch_sources", ".")
            for package in fetch_sources.PACKAGES:
                try:
                    if not isinstance(package, fetch_sources.GitRepo):
                        continue
                except:
                    continue
                repo_path = self._src_dir + "/external/" + package.baseDir + "/src/"
                print "Cleaning: " + repo_path + " : " + package.revision
                savedir = os.getcwd()
                os.chdir(repo_path)
                bs.run_batch_command(["git", "clean", "-xfd"])
                bs.run_batch_command(["git", "reset", "--hard", "HEAD"])
                os.chdir(savedir)
                print "Checking out: " + repo_path + " : " + package.revision
                repo = git.Repo(repo_path)
                repo.git.checkout(package.revision, force=True)

        bs.CMakeBuilder.build(self)
        dest = self._pm.build_root() + "/opt/deqp/"
        if not os.path.exists(dest):
            os.makedirs(dest)
        bs.run_batch_command(["rsync", "-rlptD",
                              self._pm.project_source_dir() + "/build_" + self._o.arch + "/modules",
                              dest])
        bs.Export().export()

bs.build(DeqpBuilder(extra_definitions=["-DDEQP_TARGET=x11_egl",
                                        "-DDEQP_GLES1_LIBRARIES=/tmp/build_root/"
                                        + bs.Options().arch + "/lib/libGL.so"]))

