import os
import urllib2
import ast
import time
import sys

if __name__=="__main__":
    sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])))

from . import ProjectInvoke, DependencyGraph
from . import Options
from . import ProjectMap
from . import BuildSpecification
from . import RevisionSpecification
#from clean_server import CleanServer
import export

class AlreadyBuilt(Exception):
    def __init__(self, invoke):
        Exception.__init__(self)
        self.invoke = invoke

    def __str__(self):
        return "Already Built: " + str(self.invoke)

class BuildInProgress(Exception):
    def __init__(self, invoke, revision):
        Exception.__init__(self)
        self.invoke = invoke
        self.revision = revision
    def __str__(self):
        return "Error: build in progress.  Remove the following file to " \
            "rebuild: " + self.invoke.info_file()

class BuildFailure(Exception):
    def __init__(self, invoke, url):
        Exception.__init__(self)
        self.invoke = invoke
        self.url = url

    def __str__(self):
        return "Error: build failure: " + str(self.invoke) + "\nError: " + \
            self.url

class BuildAborted(Exception):
    def __init__(self):
        Exception.__init__(self)

    def __str__(self):
        return "Error: build aborted from jenkins"

class BuildStatus():
    def __init__(self, invoke, url, status):
        self.invoke = invoke
        self.url = url
        self.status = status

class Jenkins:
    """Manages invocation and status of builds on CI server
    """
    status_colors = {
                'success':'#66FF33',    # light green
                'failure':'#CD5555',     # light red
                'aborted':'#FFA54F',  # light orange
                'prebuilt':'#FFFFFF',   # white
                'unstable':'#F7FE2E',   # yellow
                'unknown':'#EE82EE'}    # purple

    def __init__(self, revspec, result_path):
        if os.environ.has_key("http_proxy"):
            del os.environ["http_proxy"]
        
        spec = ProjectMap().build_spec()
        self._server = spec.find("build_master").attrib["host"]

        # list of buildinvoke objects that have been triggered
        self._jobs = []

        self._revspec = revspec
        self._result_path = result_path
        self._time = str(time.time())
        self._job_url = "http://" + self._server + "/job/project"
    # this function is common to jenkins.py
    def _reliable_url_open(self, url):
        # We use a loop to open the url because of DE3123
        failcount = 0
        while True:
            try:
                f = urllib2.urlopen(url)
                return f
            except (urllib2.HTTPError, urllib2.URLError):
                print "failure urllib2.urlopen(\"{0}\")".format(url)
                failcount += 1
                if failcount == 5:
                    raise
                time.sleep(5)

    def build(self, project_invoke, branch=""):
        status = project_invoke.get_info("status", block=False)
        if status == "building":
            raise BuildInProgress(project_invoke, self._revspec)

        if status == "failure":
            # raise BuildFailure(project_invoke, self._revision)
            # for now, let's attempt to rebuild failure projects
            pass

        project_invoke.set_info("status", "building")
        project_invoke.set_info("url", "")
        self._jobs.append(project_invoke)

        url = "{0}/buildWithParameters?{1}&branch={2}".format(
            self._job_url,
            self._jenkins_params(project_invoke),
            branch
        )

        f = self._reliable_url_open(url)
        f.read()
        return True

    def abort(self, project_invoke):
        if project_invoke.get_info("status") != "building":
            return
        build_link = self.get_build_link(project_invoke, block=False)
        if not build_link:
            return False
        build_link += "stop"

        f = self._reliable_url_open(build_link)
        f.read()
        project_invoke.set_info("status", "aborted")
        return True
            
        
    def _jenkins_params(self, invoke):
        p = []
        o = invoke.options
        p.append("project=" + invoke.project)
        p.append("arch=" + o.arch)
        p.append("config=" + o.config)
        p.append("type=" + o.type)
        p.append("revision=" + \
                 urllib2.quote(invoke.revision_spec.to_cmd_line_param()))
        p.append("result_path=" + o.result_path)
        p.append("hardware=" + o.hardware)
        p.append("hash=" + invoke.hash(self._time))

        label = o.hardware
        p.append("label=" + label)

        # this branch has a old test spec
        p.append("build_support_branch=origin/mesa_10.2")

        return "&".join(p)

    def print_builds(self):
        if not self._jobs:
            return
        print "The following builds are executing on the build system:"
        for a_job in self._jobs:
            job_url = a_job.get_info("url")
            if not job_url:
                job_url = "enqueued"
            print "\t" + a_job.to_short_string() + " : " + job_url

    def wait_for_build(self):
        if not self._jobs:
            return None

        # iterate _jobs, searching for matching job on jenkins.
        # Return any job that is complete.  Raise error if matching
        # job failure.
        first_round = True
        while True:
            # moderate the rate of polling, but do not add any latency
            # to the first attempt to find a finished build.
            if not first_round:
                time.sleep(15)
            first_round = False

            for i in range(len(self._jobs)):
                a_job = self._jobs[i]
                # get the url from the build_info file, if possible
                job_url = a_job.get_info("url")

                abuild_page = None
                if not job_url:
                    abuild_page = self.get_matching_build(a_job)
                    if not abuild_page:
                        # job not yet scheduled
                        continue
                    # cache the url in the build_info, so we don't
                    # have to keep searching for it.
                    job_url = abuild_page["url"]
                    a_job.set_info("url", job_url)
                    print job_url + " found for " + a_job.to_short_string()

                if not abuild_page:
                    try:
                        f = urllib2.urlopen(job_url + "/api/python")
                    except:
                        continue
                    abuild_page = ast.literal_eval(f.read())

                if not abuild_page["result"]:
                    # build not complete yet
                    continue

                end_time = a_job.get_info("end_time")
                
                if not end_time or (time.time() - end_time < 10):
                    # build will temporarily report success until
                    # warnings are parsed.  This takes just a few
                    # seconds.  Re-read the status page to ensure we
                    # have the final status.  Only incur delays if the
                    # build finished less than 10 seconds ago.
                    time.sleep(10 )
                try:
                    f = urllib2.urlopen(job_url + "/api/python")
                except:
                    continue
                abuild_page = ast.literal_eval(f.read())

                a_job.set_info("collect_time", time.time())
                if (abuild_page["result"] == "SUCCESS" or 
                    abuild_page["result"] == "UNSTABLE"):

                    return BuildStatus(self._jobs.pop(i), 
                                       abuild_page["url"], 
                                       abuild_page["result"].lower())
                self._jobs.pop(i)
                raise BuildFailure(a_job, abuild_page["url"])

    def get_matching_build(self, project_invoke):
        f = None
        try:
            f = urllib2.urlopen(self._job_url + "/api/python")
        except:
            return None

        job_page = ast.literal_eval(f.read())
        max_job = job_page["nextBuildNumber"]
        # check last 100 builds
        for abuild_number in range(max_job-1, max_job - 401, -1):
            try:
                f = urllib2.urlopen(self._job_url + "/" + 
                                    str(abuild_number) + "/api/python")
            except:
                continue
            abuild_page = ast.literal_eval(f.read())
            if not self.match_project_invoke(project_invoke, abuild_page):
                # not the matching build for the job that we are looking for
                continue
            return abuild_page

        # see if there are newer builds that haven't shown up in the history
        while True:
            try:
                max_job += 1
                url = self._job_url + "/" + str(max_job) + "/api/python"
                f = urllib2.urlopen(url)
                abuild_page = ast.literal_eval(f.read())
                if self.match_project_invoke(project_invoke, abuild_page):
                    return abuild_page
            except:
                # got a 404, build doesn't exist
                return None
                

    def match_project_invoke(self, project_invoke, build_dict):
        """true if the dict matches the invoke"""

        # get build_params
        build_params = []
        for an_action in build_dict["actions"]:
            if an_action.has_key("parameters"):
                build_params = an_action["parameters"]
                break
        assert build_params
        hash_str = ""
        for a_param in build_params:
            if a_param["name"] == "hash":
                hash_str = a_param["value"]
                break
        return hash_str == project_invoke.hash(self._time)

    def get_build_link(self, project_invoke, block=True):
        # first check to see if the url is already known
        url = project_invoke.get_info("url")
        if url:
            return url
        while True:
            build_page = self.get_matching_build(project_invoke)
            if build_page:
                url = build_page["url"]
                project_invoke.set_info("url", url)
                return url
            if not block:
                return None
            time.sleep(1)


def generate_color_key(ljen):
    out_key = r'<field name="Key" titlecolor="black" value="" ' \
              r'detailcolor="" href="" /><table><tr>'

    for status in sorted(ljen.status_colors):
        out_key += '<td value="" bgcolor="' + ljen.status_colors[status] + \
                   '" fontcolor="black" fontattribute="normal" ' \
                   'align="center" width="200"/>'

    out_key += r'</tr>'
    out_key += r'<tr>'
    for status in sorted(ljen.status_colors):
        out_key += '<td value="' + status + \
                   '" bgcolor="" fontcolor="black" fontattribute="normal" '\
                   'align="center" width="200"/>'

    out_key += r'</tr></table>'
    return out_key

def generate_summary_row(build, ljen, header=False):
    if header:
        options_dict = {}
        bg_color = '#C6E2FF'
        font_attr = 'bold'
        link = ''
    else:
        font_attr = 'normal'
        bg_color = ljen.status_colors.get(build.get_info("status"), 
                                          ljen.status_colors['unknown'])
        options_dict = vars(build.options)
        link = ljen.get_build_link(build, block=False)
        options_dict['project'] = build.project
        #options_dict['platform'] = build.platform
        duration = hours_minutes_seconds(build.get_info("collect_time"), 
                                         build.get_info("trigger_time"))
        options_dict['duration'] = duration
                                   
        if not link:
            bg_color = ljen.status_colors['prebuilt']  
    out_row = r'<tr>'
    for afield in ['project', 'arch', 'hardware',
                   'type', 'config', 'duration']:
        add_url = ''
        if afield == 'project' and link:
            add_url = 'href="' + link + '"'

        out_row += '<td value="' + options_dict.get(afield, afield) + \
                   '" bgcolor="' + bg_color + \
                   '" fontcolor="black" fontattribute="' + \
                   font_attr + '" align="center" ' + add_url + \
                   ' width="200"/>'

    out_row += r'</tr>'
    return out_row

def hours_minutes_seconds(finish_time, start_time):
    if not finish_time or not start_time:
        return ""
    duration = finish_time - start_time
    seconds = int(duration % 60)
    minutes = int((duration / 60) % 60)
    hours = int(duration / 3600)
    return "%02d:%02d:%02d" % (hours, minutes, seconds)

def refresh_status(build):
    build_page = None
    url = build.get_info("url")
    for _ in range(0,10):
        try:
            f = urllib2.urlopen(url + "/api/python")
            build_page = ast.literal_eval(f.read())
            break
        except:
            print "Retrying read of build page: " + url
            time.sleep(1)
            continue

    if not build_page:
        return
    if not build_page["result"]:
        return
    build.set_info("status",  build_page["result"].lower())

def write_summary(out_dir, completed_builds, ljen, failure=False):
    build_status = 'success'
    if failure:
        build_status = 'failure'
    outf = open(os.path.join(out_dir, "summary.xml"), "w")
    outf.write("""\
<section name="" fontcolor="">
    <field name="Build """ + build_status + '" titlecolor="'+ ljen.status_colors.get(build_status) + """" value="" detailcolor="" href="" />
    <table sorttable="yes">""")
    outf.write(generate_summary_row(None, ljen, header=True))
    for build in completed_builds:
        refresh_status(build)
        outf.write(generate_summary_row(build, ljen))
    outf.write("""\
    </table>
    <br />""")
    outf.write(generate_color_key(ljen))
    long_pole_row_txt = """
<tr>
    <td value="{project}" bgcolor="{color}" fontcolor="black" fontattribute="bold" align="center" width="200" href="{url}"/>
    <td value="{duration}" bgcolor="{color}" fontcolor="black" fontattribute="bold" align="center" width="200"/>
    <td value="{waiting}" bgcolor="{color}" fontcolor="black" fontattribute="bold" align="center" width="200"/>
    <td value="{building}" bgcolor="{color}" fontcolor="black" fontattribute="bold" align="center" width="200"/>
    <td value="{finishing}" bgcolor="{color}" fontcolor="black" fontattribute="bold" align="center" width="200"/>
</tr> """
    outf.write("""\
<br/>
<field name="Long Pole Builds" titlecolor="black" value="" detailcolor="" href="" />
<table sorttable="yes">""" + \
               long_pole_row_txt.format(project="project", 
                                        duration="total duration", 
                                        waiting="waiting for machine", 
                                        building="building", 
                                        finishing="summarizing results", 
                                        color="#C6E2FF",
                                        url=""))

    long_pole_builds = DependencyGraph.long_pole(completed_builds[-1])
    long_pole_builds.reverse()
    for a_build in long_pole_builds:
        link = ljen.get_build_link(a_build, block=False)
        duration=hours_minutes_seconds(a_build.get_info("collect_time"), 
                                       a_build.get_info("trigger_time"))
        waiting = hours_minutes_seconds(a_build.get_info("start_time"), 
                                        a_build.get_info("trigger_time"))
        building = hours_minutes_seconds(a_build.get_info("end_time"), 
                                         a_build.get_info("start_time"))
        finishing = hours_minutes_seconds(a_build.get_info("collect_time"), 
                                          a_build.get_info("end_time"))
        outf.write(long_pole_row_txt.format(project=a_build.project, 
                                            duration=duration, 
                                            waiting=waiting, 
                                            building=building, 
                                            finishing=finishing, 
                                            url=link,
                                            color="#66FF33"))

    outf.write("""\
</table>
<br/>
    <field name="Test Results" titlecolor="black" value="" detailcolor="" href="" />
</section>""")
    outf.close()

