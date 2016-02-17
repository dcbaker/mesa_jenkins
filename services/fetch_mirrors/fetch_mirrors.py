#!/usr/bin/python2

import hashlib
import os
import signal
import subprocess
import sys
import time

import git

sys.path.append("/var/lib/git/mesa_jenkins/services/")
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), ".."))
from daemon import Daemon

sys.path.append("/var/lib/git/mesa_jenkins/")
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "../.."))
import build_support as bs

sys.argv[0] = os.path.abspath(sys.argv[0])

class TimeoutException(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self._msg = msg

    def __str__(self):
        return self._msg

def signal_handler(signum, frame):
    raise TimeoutException("Fetch timed out.")

def signal_handler_quit(signum, frame):
    sys.exit(-1)


class RepoSyncer(Daemon):
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        Daemon.__init__(self, pidfile, stdin, stdout, stderr)

    def robust_clone(self, url, directory):
        success = False
        while not success:
            try:
                bs.run_batch_command(["/usr/local/bin/git", "clone", "--mirror",
                                      url, directory])
                success = True
            except(subprocess.CalledProcessError):
                print "Error: could not clone " + url
                time.sleep(10)

    def robust_update(self):
        _success = False
        while not _success:
            try:
                _repo = git.Repo("/var/lib/git/mesa_jenkins")
                _repo.remotes.origin.pull()
                _success = True
            except:
                print "Error: could not update buildsupport"
                time.sleep(10)
                
    def file_checksum(self, fname):
        with open(fname, 'rb') as f:
            return hashlib.md5(f.read()).digest()

    def run(self):
        signal.signal(signal.SIGALRM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler_quit)
        signal.signal(signal.SIGTERM, signal_handler_quit)

        # running a service through intel's proxy requires some
        # annoying settings.
        os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = "/usr/local/bin/git"
        # without this, git-remote-https spins at 100%
        os.environ["http_proxy"] = "http://proxy.jf.intel.com:911/"
        os.environ["https_proxy"] = "http://proxy.jf.intel.com:911/"

        try:
            bs.ProjectMap()
        except:
            sys.argv[0] = "/var/lib/git/mesa_jenkins/foo.py"

        pm = bs.ProjectMap()
        spec_file = pm.source_root() + "/build_specification.xml"
        new_spec_hash = None

        while True:
            orig_spec_hash = self.file_checksum(spec_file)
            if new_spec_hash is not None:
                print "Build Specification updated"
            new_spec_hash = self.file_checksum(spec_file)

            while new_spec_hash == orig_spec_hash:
                buildspec = bs.ProjectMap().build_spec()

                repo_dir = "/var/lib/git/"

                # build up a list of git repo objects for all known repos.  If the
                # origin or the remotes are not already cloned, clone them.
                repos = []
                repo_tags = buildspec.find("repos")
                for tag in repo_tags:
                    url = tag.attrib["repo"]
                    project = tag.tag
                    origin_dir = repo_dir + project + "/origin"
                    if not os.path.exists(origin_dir):
                        self.robust_clone(url, origin_dir)
                        bs.run_batch_command(["touch", origin_dir + "/git-daemon-export-ok"])
                    repos.append(git.Repo(origin_dir))
                    for a_remote in tag.findall("remote"):
                        remote_dir = repo_dir + project + "/" + a_remote.attrib["name"]
                        if not os.path.exists(remote_dir):
                            self.robust_clone(a_remote.attrib["repo"], remote_dir)
                            bs.run_batch_command(["touch", remote_dir + "/git-daemon-export-ok"])
                        repos.append(git.Repo(remote_dir))

                for repo in repos:
                    try:
                        signal.alarm(300)   # 5 minutes
                        repo.git.fetch()
                        signal.alarm(0)
                    except git.GitCommandError as e:
                        print "error fetching, ignoring: " + str(e)
                        signal.alarm(0)
                    except AssertionError as e:
                        print "assertion while fetching: " + str(e)
                        signal.alarm(0)
                    except TimeoutException as e:
                        print str(e)
                        signal.alarm(0)
                # pause a bit before fetching the next round
                time.sleep(20)
                self.robust_update()
                new_spec_hash = self.file_checksum(spec_file)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        daemon = RepoSyncer('/var/run/fetch_mesa_mirrors.pid')
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
