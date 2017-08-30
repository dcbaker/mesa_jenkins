#!/usr/bin/python

import sys
import os
import os.path as path
import subprocess
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs

class SconsBuilder(object):
    def __init__(self):
        self.src_dir = bs.ProjectMap().source_root() + "/repos/mesa"

    def clean(self):
        pass
    
    def test(self):
        pass

    def build(self):
        save_dir = os.getcwd()
        os.chdir(self.src_dir)

        # scons build is broken, will occasionally fail if temporaries
        # are still around.  Use git's nuclear clean method instead of
        # the clean targets.
        bs.run_batch_command(["git", "clean", "-dfx"])

        env = {}
        bs.Options().update_env(env)
        bs.run_batch_command(["scons", "-j",
                              str(bs.cpu_count())], env=env)

        bs.run_batch_command(["git", "clean", "-dfx"])
        os.chdir(save_dir)
        
def main():
    b = SconsBuilder()
    save_dir = os.getcwd()
    try:
        bs.build(b)
    except subprocess.CalledProcessError as e:
        # build may have taken us to a place where ProjectMap doesn't work
        os.chdir(save_dir)  
        bs.Export().create_failing_test("mesa-scons-buildtest", str(e))

if __name__ == '__main__':
    main()
