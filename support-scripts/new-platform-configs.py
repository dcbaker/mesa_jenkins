#!/usr/bin/env python3
# Copyright © 2018 Intel Corporation

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

import argparse
import os
import subprocess
import textwrap


def arg_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('platform', type=str)
    parser.add_argument('--no-commit', action='store_true')
    return parser.parse_args()


def write_test_configs(platform: str, git_add: bool) -> None:
    suites = ['piglit-test', 'crucible-test', 'deqp-test', 'glescts-test',
              'vulkancts-test', 'glcts-test']
    template = textwrap.dedent('''\
    [expected-failures]

    [expected-crashes]

    [fixed-tests]
    ''')

    for s in suites:
        path = os.path.join(s, platform) + '.conf'
        with open(path, 'w') as f:
            f.write(template)
        if git_add:
            subprocess.run(['git', 'add', path], check=True)


def write_deqp_expectations(platform: str, git_add: bool) -> None:
    files = ['gles31_unstable_tests.txt', 'egl_unstable_tests.txt',
             'gles2_unstable_tests.txt', 'gles3_unstable_tests.txt']
    root = os.path.join('deqp-test', f'{platform}_expectations')
    os.mkdir(root)

    for file_ in files:
        path = os.path.join(root, file_)
        with open(path, 'w') as f:
            f.write('')
        if git_add:
            subprocess.run(['git', 'add', path], check=True)


def write_vk_expectations(platform: str, git_add: bool) -> None:
    root = os.path.join('vulkancts-test', f'{platform}_expectations')
    os.mkdir(root)

    path = os.path.join(root, 'vk_unstable_tests.txt')
    with open(path, 'w') as f:
        f.write('')
    if git_add:
        subprocess.run(['git', 'add', path], check=True)



def main():
    args = arg_parser()
    write_test_configs(args.platform, not args.no_commit)
    write_deqp_expectations(args.platform, not args.no_commit)
    write_vk_expectations(args.platform, not args.no_commit)
    if not args.no_commit:
        subprocess.run([
            'git', 'commit', '-m',
            f'Add empty test configruation files for {args.platform}'])


if __name__ == '__main__':
    main()
