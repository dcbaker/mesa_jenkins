#!/usr/bin/python

import os
import os.path as path
import subprocess
import sys
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs

class NoTest(bs.AutoBuilder):
    def __init__(self, o, configure_options):
        bs.AutoBuilder.__init__(self,
                                o,
                                configure_options=configure_options,
                                install=False,
                                export=False)

    def test(self):
        # llvmpipe fails make test, and who cares?
        pass
    
def main():
    pm = bs.ProjectMap()
    sd = pm.project_source_dir(pm.current_project())
    with open(os.path.join(sd, 'VERSION'), 'r') as f:
        ver = f.read().strip().split('-devel')[0].split('.')
    ver = [int(v) for v in ver]

    global_opts = bs.Options()

    if ver >= [18, 1, 0]:
        global_opts.env += ' LLVM_CONFIG=/usr/bin/llvm-config-4.0'

    options = []
    if global_opts.arch == "m32":
        # m32 build not supported
        return

    options = options + ["--enable-gbm",
                         "--enable-llvm",
                         "--with-egl-platforms=x11,drm",
                         "--enable-glx-tls", 
                         "--enable-gles1",
                         "--enable-gles2",
                         "--with-gallium-drivers=svga,swrast,r300,r600,radeonsi,nouveau",
                         "--with-vulkan-drivers=intel,radeon"]

    if global_opts.config == 'debug':
        options.append('--enable-debug')

    # builder = bs.AutoBuilder(configure_options=options, export=False)
    builder = NoTest(global_opts, options)

    save_dir = os.getcwd()
    try:
        bs.build(builder)
    except subprocess.CalledProcessError as e:
        # build may have taken us to a place where ProjectMap doesn't work
        os.chdir(save_dir)  
        bs.Export().create_failing_test("mesa-buildtest", str(e))

if __name__ == '__main__':
    main()
