import argparse
import git
import os
import random
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci"))
import build_support as bs

def main():
    # reuse the options from the gasket
    o = bs.Options([sys.argv[0]])
    description="builds a component on jenkins"
    parser= argparse.ArgumentParser(description=description, 
                                    parents=[o._parser], 
                                    conflict_handler="resolve")
    parser.add_argument('--project', dest='project', type=str, default="",
                        help='Project to build. Default project is specified '\
                        'for the branch in build_specification.xml')

    parser.add_argument('--revision', type=str, default="",
                        help="mesa revision to test.")

    args = parser.parse_args()
    projects = []
    if args.project:
        projects = args.project.split(",")
    revision = args.revision

    bspec = bs.BuildSpecification()
    bspec.checkout("mesa_perf")
    mesa_repo = git.Repo(bs.ProjectMap().project_source_dir("mesa"))

    if ":" in revision:
        (start_rev, end_rev) = revision.split(":")
        if not end_rev:
            # user selected the last point in a plot.  Build current master
            revision = "mesa=" + mesa_repo.git.rev_parse("HEAD", short=True)
        elif not start_rev:
            print "ERROR: user-generated perf builds cannot add older data points to the plot"
            sys.exit(-1)
        else:
            commits = []
            start_commit = mesa_repo.commit(start_rev)
            found = False
            for commit in mesa_repo.iter_commits(end_rev, max_count=8000):
                if commit == start_commit:
                    found = True
                    break
                commits.append(commit.hexsha)
            if not found:
                print "ERROR: " + start_rev + " not found in history of " + end_rev
                sys.exit(-1)
            revision = "mesa=" + commits[len(commits)/2]

    # some build_local params are not handled by the Options, which is
    # used by other modules.  This code strips out incompatible args
    o = bs.Options(["bogus"])
    vdict = vars(args)
    del vdict["project"]
    del vdict["revision"]
    o.__dict__.update(vdict)
    sys.argv = ["bogus"] + o.to_list()

    pm = bs.ProjectMap()
    bs.rmtree(pm.source_root() + "/test_summary.txt")

    # checkout the desired revision on top of recent revisions
    if not revision:
        # randomly select a commit post 11.2
        branch_commit = mesa_repo.tags["17.0-branchpoint"].commit.hexsha
        commits = []
        for commit in mesa_repo.iter_commits('origin/master', max_count=8000):
            if commit.hexsha == branch_commit:
                break
            commits.append(commit.hexsha)
        revision = "mesa=" + str(commits[int(random.random() * len(commits))])
        
    revspec = bs.RevisionSpecification(from_cmd_line=revision.split())
    revspec.checkout()

    revspec = bs.RevisionSpecification()
    hashstr = "mesa=" + revspec.revision("mesa")
    print "Building revision: " + hashstr

    # create a result_path that is unique for this set of builds
    spec_xml = pm.build_spec()
    results_dir = spec_xml.find("build_master").attrib["results_dir"]
    result_path = "/".join([results_dir, "perf", hashstr])
    o.result_path = result_path

    if not projects:
        projects = ["perf-all"]

    # use a global, so signal handler can abort builds when scheduler
    # is interrupted
    global jen

    jen = bs.Jenkins(result_path=result_path,
                     revspec=revspec)

    depGraph = bs.DependencyGraph(projects, o)
    for i in depGraph.all_builds():
        if i.project != "mesa-perf":
            i.set_info("status", "rebuild")

    # use a global, so signal handler can abort builds when scheduler
    # is interrupted
    try:
        jen.build_all(depGraph, branch="mesa_master")
    except Exception as e:
        print "ERROR: encountered failure: " + str(e)
        raise

if __name__=="__main__":
    try:
        main()
    except SystemExit:
        # Uncomment to determine which version of argparse is throwing
        # us under the bus.

        #  Word of Wisdom: Don't call sys.exit
        #import traceback
        #for x in traceback.format_exception(*sys.exc_info()):
        #    print x
        raise
