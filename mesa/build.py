#!/usr/bin/python


import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), ".."))
import build_support as bs

options = []
if bs.Options().arch == "m32":
    # gallium requires llvm, which breaks on i386
    # expat pkg-config fails for some reason on i386
    options = ['EXPAT_LIBS="-L/usr/lib/i386-linux-gnu -lexpat"',
               "--with-gallium-drivers=", 
               "--disable-gallium-egl", 
               "--disable-gallium-gbm"]

options = options + [ "--enable-gbm",
                      "--with-egl-platforms=x11,drm" ]

builder = bs.AutoBuilder(configure_options = options)

gtests = ["src/glsl/tests/general-ir-test",
          "src/glsl/tests/sampler-types-test",
          "src/glsl/tests/uniform-initializer-test",
          "src/glx/tests/glx-test",
          "src/mesa/main/tests/main-test",
          "src/mesa/drivers/dri/i965/test_vec4_copy_propagation",
          "src/mesa/drivers/dri/i965/test_vec4_register_coalesce",
          "./src/mapi/shared-glapi/tests/shared-glapi-test"]

builder.AddGtests(gtests)

bs.build(builder)
