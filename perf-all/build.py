#!/usr/bin/python

import glob
import json
import git
import os.path as path
import sys
import yaml
import numpy
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci")))
import build_support as bs

class MesaStats:
    def __init__(self):
        self.opts = bs.Options()


    def merge_scores(self, all_scores, score):
        for k,v in score.iteritems():
            if k not in all_scores:
                # initialize default
                if isinstance(v, list):
                    all_scores[k] = []
                else:
                    all_scores[k] = {}

            if isinstance(v, list):
                all_scores[k] += v
            else:
                self.merge_scores(all_scores[k], v)

    def test(self):
        # create per-benchmark-per-platform files containing all
        # scores to date

        # at a later point, we may want to combine data sets so
        # developers can see all skylake benchmarks together, for
        # example.

        # canoninical path is
        # /mnt/jenkins/results/perf/mesa={rev}/m64/scores/{benchmark}/{platform}/{date}.json:
        all_scores = {}
        score_glob = "/mnt/jenkins/results/perf/mesa=*/m64/scores/*/*/*.json"
        for a_score_file in glob.glob(score_glob):
            with open(a_score_file, "r") as f:
                a_score = json.load(f)
            self.merge_scores(all_scores, a_score)
        if not all_scores:
            print "WARN: no results to merge"
            return

        # canoninical windows path is
        # /mnt/jenkins/results/perf_win/scores/{benchmark}/{platform}/{date}.json:
        for a_score_file in glob.glob("/mnt/jenkins/results/perf_win/scores/*/*/*.json"):
            with open(a_score_file, "r") as f:
                a_score = json.load(f)
            self.merge_scores(all_scores, a_score)

        pm =  bs.ProjectMap()
        mesa_repo = git.Repo(pm.project_source_dir("mesa"))

        # add mean score and date to data set
        for benchmark, platform in all_scores.iteritems():
            for platform_name, pscores in platform.iteritems():
                scores_by_date = {}
                UFO_score = None
                for commit, series in pscores.iteritems():
                    accumulated_score = {}
                    runs = []
                    for run in series:
                        runs += run["score"]
                    if not runs:
                        continue
                    accumulated_score["score"] = numpy.mean(runs, dtype=numpy.float64)
                    accumulated_score["deviation"] = numpy.std(runs, dtype=numpy.float64) / accumulated_score["score"]
                    accumulated_score["commit"] = commit
                    if "UFO" in commit:
                        UFO_score = accumulated_score["score"]
                        continue
                    mesa_commit = None
                    try:
                        mesa_commit = mesa_repo.commit(commit.split("=")[1])
                    except:
                        print "WARN: commit not found: " + commit.split("=")[1]
                        continue
                    date = mesa_commit.committed_date
                    accumulated_score["date"] = date
                    pscores[commit] = accumulated_score
                    scores_by_date[date] = accumulated_score
                dates = scores_by_date.keys()
                dates.sort()
                platform[platform_name] = {"mesa": [scores_by_date[d] for d in dates]}
                if UFO_score:
                    platform[platform_name]["UFO"] = UFO_score

        with open("/mnt/jenkins/results/perf/scores.json", "w") as of:
            json.dump(all_scores, fp=of)

    def build(self):
        pass
    def clean(self):
        pass


bs.build(MesaStats())
