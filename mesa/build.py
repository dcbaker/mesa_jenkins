 #!/usr/bin/python

import os
import sys
import os.path as path
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs


class MesaBuilder(bs.AutoBuilder):
    """Provides mesa-specific customizations to AutoBuilder"""
    def __init__(self):
        global_opts = bs.Options()

        options = []
        options = options + ["--enable-gbm",
                             "--with-egl-platforms=x11,drm",
                             "--enable-glx-tls", 
                             "--enable-gles1",
                             "--enable-gles2",
                             "--with-dri-drivers=i965,swrast,i915",

                             # disable video drivers:
                             # bbe6f7f865cd4316b5f885507ee0b128a20686eb
                             # caused build failure unrelated to intel mesa
                             # team.
                             "--disable-xvmc",
                             "--disable-vdpau",

                             # gallium tested with mesa-buildtest
                             "--without-gallium-drivers"]
        if os.path.exists(bs.ProjectMap().project_source_dir() + "/src/intel/vulkan"):
            options.append("--with-vulkan-drivers=intel")

        if global_opts.config == 'debug':
            options.append('--enable-debug')

        # always enable optimizations in mesa because tests are too slow
        # without them.
        bs.AutoBuilder.__init__(self, configure_options=options, opt_flags="-O2")

    def test(self):
        """Provide gtests as available"""
        # override the test method, because tests have moved
        gtests = ["src/glx/tests/glx-test",
                  "src/mesa/main/tests/main-test",
                  "./src/mapi/shared-glapi-test",
                  "src/compiler/glsl/tests/general-ir-test",
                  "src/compiler/glsl/tests/sampler-types-test",
                  "src/compiler/glsl/tests/uniform-initializer-test"]

        if path.exists(self._src_dir + "/src/intel/compiler/test_vec4_copy_propagation.cpp"):
            gtests += ["src/intel/compiler/test_vec4_copy_propagation",
                       "src/intel/compiler/test_vec4_register_coalesce"]
        self.SetGtests(gtests)
        bs.AutoBuilder.test(self)


def meson_build():
    global_opts = bs.Options()
    pm = bs.ProjectMap()
    sd = pm.project_source_dir(pm.current_project())

    options = [
        '-Dgallium-drivers=',
        '-Ddri-drivers=i965,i915',
        '-Dvulkan-drivers=intel',
        '-Dplatforms=x11,drm',
    ]
    # For a few days durring the commit cyle the 'auto' option was removed from
    # omx and it defaulted to tizonia. during that time we need this to set the
    # -Dgallium-omx=disabled. This can be removed after we're sure we don't
    # need to bisect across that.
    with open(os.path.join(sd, 'meson_options.txt')) as f:
        for l in f:
            if 'tizonia' in l:
                options.append('-Dgallium-omx=disabled')
                break

    if global_opts.config != 'debug':
        options.extend(['-Dbuildtype=release', '-Db_ndebug=true'])
    b = bs.builders.MesonBuilder(extra_definitions=options, install=True)
    bs.build(b)


def main():
    pm = bs.ProjectMap()
    sd = pm.project_source_dir(pm.current_project())
    if os.path.exists(os.path.join(sd, 'src/mesa/drivers/osmesa/meson.build')):
        meson_build()
    else:
        bs.build(MesaBuilder())


if __name__ == '__main__':
    main()
