#!/usr/bin/python
import json
import yaml
import sys
import glob
import numpy
import os.path as path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "repos", "mesa_ci"))
import build_support as bs


class UpdateScale:
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

    def build(self):
        all_scores = {}
        for a_score_file in glob.glob(self.opts.result_path +
                                      "/../*/m64/scores/*/*/*.json"):
            with open(a_score_file, "r") as f:
                a_score = json.load(f)
            self.merge_scores(all_scores, a_score)
        scale_file = bs.ProjectMap().project_build_dir("sixonix") + "/scale.yml"
        with open(scale_file, 'r') as inf:
            scale = yaml.load(inf)
        for benchmark, platform in all_scores.iteritems():
            for platform_name, pscores in platform.iteritems():
                for _, series in pscores.iteritems():
                    runs = []
                    for run in series:
                        runs += [ r for r in run["score"]]
                    mean = numpy.mean(runs, dtype=numpy.float64)
                    scale[benchmark][platform_name] = float(mean)
                    print benchmark + " " + platform_name + ": " + str(mean) + " " + str(numpy.std(runs, dtype=numpy.float64) / mean)

        with open(scale_file, 'w') as of:
            yaml.dump(scale, of)

    def test(self):
        pass
    def clean(self):
        pass
bs.build(UpdateScale())
