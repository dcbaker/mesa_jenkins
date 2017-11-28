#!/usr/bin/python

import sys
import os
import subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), ".."))
import build_support as bs

def main():
    save_dir = os.getcwd()

    global_opts = bs.Options()

    options = [
        '-Dbuild-tests=true',
        '-Dgallium-drivers=r300,r600,radeonsi,nouveau,swrast,freedreno,vc4,pl111,etnaviv,imx,svga,virgl',
    ]
    if global_opts.config != 'debug':
        options.append('-Dbuildtype=release')
    b = bs.builders.MesonBuilder(extra_definitions=options, install=False)

    try:
        bs.build(b)
    except subprocess.CalledProcessError as e:
        # build may have taken us to a place where ProjectMap doesn't work
        os.chdir(save_dir)
        bs.Export().create_failing_test("mesa-meson-buildtest", str(e))

if __name__ == '__main__':
    main()
