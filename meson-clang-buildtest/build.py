#!/usr/bin/python

import sys
import os
import subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs

def main():
    pm = bs.ProjectMap()
    sd = pm.project_source_dir(pm.current_project())
    if not os.path.exists(os.path.join(sd, 'src/mesa/drivers/osmesa/meson.build')):
        return 0

    save_dir = os.getcwd()

    global_opts = bs.Options()

    options = [
        '-Dbuild-tests=true',
        '-Dgallium-drivers=r300,r600,radeonsi,nouveau,swrast,swr,freedreno,vc4,pl111,etnaviv,imx,svga,virgl',
        '-Dgallium-omx=true',
        '-Dgallium-vdpau=true',
        '-Dgallium-xvmc=true',
        '-Dgallium-xa=true',
        '-Dgallium-va=true',
        '-Dgallium-nine=true',
        '-Dgallium-opencl=standalone',
    ]
    if global_opts.config != 'debug':
        options.extend(['-Dbuildtype=release', '-Db_ndebug=true'])
    b = bs.builders.MesonBuilder(
        extra_definitions=options, compiler='clang', install=False)

    try:
        bs.build(b)
    except subprocess.CalledProcessError as e:
        # build may have taken us to a place where ProjectMap doesn't work
        os.chdir(save_dir)
        bs.Export().create_failing_test("mesa-meson-clang-buildtest", str(e))

if __name__ == '__main__':
    main()
