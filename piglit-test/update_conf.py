#!/usr/bin/python

import argparse
import datetime
from email.mime.text import MIMEText
import git
import os
import smtplib
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci"))
import build_support as bs

parser = argparse.ArgumentParser(description="updates expected failures")

parser.add_argument('--blame_revision', type=str, required=True,
                    help='revision to specify as the cause of any config changes')
parser.add_argument('--result_path', metavar='result_path', type=str, default="",
                    help='path to build results')
parser.add_argument('--to', metavar='to', type=str, default="",
                    help='send resulting patch to this email')
args = parser.parse_args(sys.argv[1:])

# get revisions from out directory
test_dir = os.path.abspath(args.result_path + "/test")
if not os.path.exists(test_dir):
    print "ERROR: no tests in --result_path: " + test_dir
    sys.exit(-1)

dirnames = os.path.abspath(test_dir).split("/")
hash_dir = dirnames[5]
revs = hash_dir.split("_")

rev_hash = {}
for a_rev in revs:
    proj = a_rev.split("=")[0]
    rev = a_rev.split("=")[1]
    rev_hash[proj] = rev

blame = args.blame_revision.split("=")
if len(blame) != 2:
    print "ERROR: --blame_revision must be in the format: project=rev"
    sys.exit(-1)

if not rev_hash.has_key(blame[0]):
    print "ERROR: invalid project in --blame_revision: " + blame[0]
    print "ERROR: acceptable projects: " + ",".join(rev_hash.keys())
    sys.exit(-1)

rev_hash[blame[0]] = blame[1]


# retest the set of failed tests on the specified blame revision
repos = bs.RepoSet()
_revspec = bs.RevisionSpecification(from_cmd_line=[k + "=" + v for k,v in rev_hash.items()])
_revspec.checkout()
_revspec = bs.RevisionSpecification()

pm = bs.ProjectMap()
spec_xml = pm.build_spec()
results_dir = spec_xml.find("build_master").attrib["results_dir"]
hashstr = _revspec.to_cmd_line_param().replace(" ", "_")
bisect_dir = results_dir + "/update/" + hashstr
if os.path.exists(bisect_dir):
    print "Removing existing retest."
    mvdir = os.path.normpath(bisect_dir + "/../" + datetime.datetime.now().isoformat())
    os.rename(bisect_dir, mvdir)
    
cmd = ["rsync", "-rlptD", "/".join(dirnames[:-1]) +"/", bisect_dir]
bs.run_batch_command(cmd)
bs.rmtree(bisect_dir + "/test")
bs.rmtree(bisect_dir + "/piglit-test")
bs.rmtree(bisect_dir + "/deqp-test")
bs.rmtree(bisect_dir + "/cts-test")
bs.rmtree(bisect_dir + "/crucible-test")

j=bs.Jenkins(_revspec, bisect_dir)
o = bs.Options(["bisect_all.py"])
o.result_path = bisect_dir
o.retest_path = args.result_path
depGraph = bs.DependencyGraph(["piglit-gpu-all"], o)

print "Retesting mesa to: " + bisect_dir
try:
    j.build_all(depGraph, print_summary=False)
except bs.BuildFailure:
    print "ERROR: some builds failed"

# make sure there is enough time for the test files to sync to nfs
time.sleep(20)
reproduced_failures = bs.TestLister(bisect_dir + "/test/")

print "Found failures:"
reproduced_failures.Print()

for a_fail in reproduced_failures.Tests():
    a_fail.bisected_revision = " ".join(blame)
    a_fail.UpdateConf()

if args.to:
    patch_text = git.Repo().git.diff()
    print patch_text
    msg = MIMEText(patch_text)
    msg["Subject"] = "[PATCH] mesa jenkins updates due to " + args.blame_revision
    msg["From"] = "Do Not Reply <mesa_jenkins@intel.com>"
    msg["To"] = args.to
    s = smtplib.SMTP('or-out.intel.com')
    to = args.to.split(",")
    s.sendmail(msg["From"], to, msg.as_string())

    os.chdir(pm.source_root() + "/repos/prerelease")
    r = git.Repo()
    patch_text = r.git.diff()
    if not patch_text:
        sys.exit(0)
    print patch_text
    msg = MIMEText(patch_text)
    msg["Subject"] = "[PATCH] prerelease config updates due to " + args.blame_revision
    msg["From"] = "Do Not Reply <mesa_jenkins@intel.com>"
    msg["To"] = args.to
    s = smtplib.SMTP('or-out.intel.com')
    to = args.to.split(",")
    s.sendmail(msg["From"], to, msg.as_string())
    r.git.reset("--hard")
