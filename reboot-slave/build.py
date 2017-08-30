#!/usr/bin/python

import os
import sys
import urllib2
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs

# Leeroy runs the builds inside of a user namespace, so it can bind
# mount on /tmp.  This prevents the use of sudo.  This build just
# triggers the "single_reboot" job, which does not run in a user
# namespace.

server = bs.ProjectMap().build_spec().find("build_master").attrib["host"]
url = "http://" + server + "/job/reboot_single/buildWithParameters?token=noauth&label=" + bs.Options().hardware
print "opening: " + url
urllib2.urlopen(url)
