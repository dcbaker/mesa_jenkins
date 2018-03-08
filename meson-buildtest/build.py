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
        '-Dgallium-vdpau=true',
        '-Dgallium-xvmc=true',
        '-Dgallium-xa=true',
        '-Dgallium-va=true',
        '-Dgallium-nine=true',
        '-Dgallium-opencl=standalone',
    ]

    # the knob for omx changed durring the 18.1 cycle, if tizonia support is
    # present we need to use bellagio, otherwise we need true.
    with open(os.path.join(sd, 'meson_options.txt')) as f:
        for l in f:
            if 'tizonia' in l:
                options.append('-Dgallium-omx=bellagio')
                break
        else:
            options.append('-Dgallium-omx=true')
    if global_opts.config != 'debug':
        options.extend(['-Dbuildtype=release', '-Db_ndebug=true'])
    b = bs.builders.MesonBuilder(extra_definitions=options, install=False)

    b.tests += [
        # TODO: These need runtime discovery, probably using `find` or to point
        # at the DSOs in the install directory
        #
        #'es1-ABI-check',
        #'es2-ABI-check',
        #'gbm-symbols-check',
        #'wayland-egl-symbols-check',
        #'wayland-egl-abi-check',
        #'egl-symbols-check',
        #'egl-entrypoint-check',

        'anv_block_pool_no_free',
        'anv_state_pool',
        'anv_state_pool_free_list_only',
        'anv_state_pool_no_free',
        'blob_test',
        'cache_test',
        'clear',
        'collision',
        'delete_and_lookup',
        'delete_management',
        'destroy_callback',
        'eu_compact',
        'glx-dispatch-index-check',
        'insert_and_lookup',
        'insert_many',
        'isl_surf_get_image_offset',
        'lp_test_arit',
        'lp_test_blend',
        'lp_test_conv',
        'lp_test_format',
        'lp_test_printf',
        'mesa-sha1',
        'null_destroy',
        'random_entry',
        'remove_null',
        'replacement',
        'roundeven',
        'u_atomic',
    ]

    b.gtests += [
        'eu_validate',
        'fs_cmod_propagation',
        'fs_copy_propagation',
        'fs_saturate_propagation',
        'general_ir_test',
        'glx-test',
        'main-test',
        'nir_control_flow',
        'sampler_types_test',
        'shared-glapi-test',
        'string_buffer',
        'uniform_initializer_test',
        'vec4_cmod_propagation',
        'vec4_copy_propagation',
        'vec4_register_coalesce',
        'vf_float_conversions',
    ]

    try:
        bs.build(b)
    except subprocess.CalledProcessError as e:
        # build may have taken us to a place where ProjectMap doesn't work
        os.chdir(save_dir)
        bs.Export().create_failing_test("mesa-meson-buildtest", str(e))

if __name__ == '__main__':
    main()
