#!/usr/bin/python2
# encoding=utf-8
# Copyright © 2017 Intel Corporation

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Attempt to fetch build_support repository, then fetch additional
repositories.
"""

from __future__ import print_function
import argparse
import os
import sys

import git

build_support_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "repos", "mesa_ci"))

def try_clone(repo):
    print('Trying to clone build support from {}'.format(repo))
    git.Repo.clone_from(repo, build_support_dir)


if not os.path.exists(build_support_dir):
    repo_dir = os.path.dirname(build_support_dir)
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)

    try:
        try_clone("git://otc-mesa-ci.local/git/mesa_ci/origin")
    except git.exc.GitCommandError:
        try:
            try_clone("git://otc-mesa-ci.jf.intel.com/git/mesa_ci/origin")
        except git.exc.GitCommandError:
            try:
                try_clone("git://github.com/janesma/mesa_ci.git")
            except git.exc.GitCommandError:
                print("ERROR: could not clone sources")
                sys.exit(1)

sys.path.insert(0, build_support_dir)
import build_support as bs


def main():
    parser = argparse.ArgumentParser(description="checks out branches and commits")
    parser.add_argument('--branch', type=str, default="mesa_master",
                        help="The branch to base the checkout on. (default: %(default)s)")
    parser.add_argument('commits', metavar='commits', type=str, nargs='*',
                        help='commits to check out, in repo=sha format')
    args = parser.parse_args()

    repos = bs.RepoSet(clone=True)
    repos.fetch()
    bs.BuildSpecification().checkout(args.branch, args.commits)


if __name__ == '__main__':
    main()
