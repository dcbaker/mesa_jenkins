#!/usr/bin/python3
# encoding=utf-8
# Copyright © 2016 Intel Corporation

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

"""Flask webpage for performance data."""

import itertools

# pylint: disable=import-error
import flask
from flask_mako import MakoTemplates, render_template
# pylint: enable=import-error

APP = flask.Flask(__name__)
_ = MakoTemplates(APP)

# pylint: disable=bad-whitespace
_BENCHMARKS = [
    ('OglBatch0',          'micro-benchmark'    ),
    ('OglBatch1',          'micro-benchmark'    ),
    ('OglBatch2',          'micro-benchmark'    ),
    ('OglBatch3',          'micro-benchmark'    ),
    ('OglBatch4',          'micro-benchmark'    ),
    ('OglBatch5',          'micro-benchmark'    ),
    ('OglBatch6',          'micro-benchmark'    ),
    ('OglBatch7',          'micro-benchmark'    ),
    ('OglCSCloth',         'micro-benchmark'    ),
    ('OglCSDof',           'micro-benchmark'    ),
    ('OglDeferred',        'micro-benchmark'    ),
    ('OglDeferredAA',      'micro-benchmark'    ),
    ('OglDrvRes',          'micro-benchmark'    ),
    ('OglDrvShComp',       'micro-benchmark'    ),
    ('OglDrvState',        'micro-benchmark'    ),
    ('OglFillPixel',       'micro-benchmark'    ),
    ('OglFillTexMulti',    'micro-benchmark'    ),
    ('OglFillTexSingle',   'micro-benchmark'    ),
    ('OglGeomPoint',       'micro-benchmark'    ),
    ('OglGeomTriList',     'micro-benchmark'    ),
    ('OglGeomTriStrip',    'micro-benchmark'    ),
    ('OglHdrBloom',        'micro-benchmark'    ),
    ('OglMultithread',     'micro-benchmark'    ),
    ('OglPSBump2',         'micro-benchmark'    ),
    ('OglPSBump8',         'micro-benchmark'    ),
    ('OglPSPhong',         'micro-benchmark'    ),
    ('OglPSPom',           'micro-benchmark'    ),
    ('OglShMapPcf',        'micro-benchmark'    ),
    ('OglShMapVsm',        'micro-benchmark'    ),
    ('OglTerrainFlyInst',  'micro-benchmark'    ),
    ('OglTerrainPanInst',  'micro-benchmark'    ),
    ('OglTerrainFlyTess',  'micro-benchmark'    ),
    ('OglTerrainPanTess',  'micro-benchmark'    ),
    ('OglTexFilterAniso',  'micro-benchmark'    ),
    ('OglTexFilterTri',    'micro-benchmark'    ),
    ('OglTexMem128',       'micro-benchmark'    ),
    ('OglTexMem512',       'micro-benchmark'    ),
    ('OglVSDiffuse1',      'micro-benchmark'    ),
    ('OglVSDiffuse8',      'micro-benchmark'    ),
    ('OglVSInstancing',    'micro-benchmark'    ),
    ('OglVSTangent',       'micro-benchmark'    ),
    ('OglZBuffer',         'micro-benchmark'    ),
    ('egypt',              'synthetic-benchmark'),
    ('egypt_o',            'synthetic-benchmark'),
    ('fill',               'micro-benchmark'    ),
    ('fill_o',             'micro-benchmark'    ),
    ('fur',                'micro-benchmark'    ),
    ('heaven',             'engine-demo'        ),
    ('manhattan',          'synthetic-benchmark'),
    ('manhattan_o',        'synthetic-benchmark'),
    ('plot3d',             'micro-benchmark'    ),
    ('trex',               'synthetic-benchmark'),
    ('trex_o',             'synthetic-benchmark'),
    ('triangle',           'micro-benchmark'    ),
    ('valley',             'engine-demo'        ),
    ('warsow',             'game-demo'          ),
    ('xonotic',            'game-demo'          ),
]
# pylint: enable=bad-whitespace


class _Getter(object):
    """A container for making working with benchmark data easier.

    Stores dictionaries relating each element to each other, allowing for fast
    searches.

    """
    def __init__(self):
        self.by_name = dict(iter(_BENCHMARKS))
        self.by_category = {c: list(b) for c, b in
                            itertools.groupby(_BENCHMARKS, lambda x: x)}


GETTER = _Getter()


@APP.route('/')
def front():
    return render_template('index.html.mako', benchmarks=_BENCHMARKS)


@APP.route('/apps/all')
def all():  # pylint: disable=redefined-builtin
    return render_template('apps.html.mako', benchmarks=_BENCHMARKS,
                           category="All Benchmarks")


@APP.route('/apps/<benchmark>')
def apps(benchmark):
    return render_template(
        'apps.html.mako',
        benchmarks=GETTER.by_name[benchmark],
        category=None)


@APP.route('/categories/<category>')
def categories(category):
    return render_template(
        'apps.html.mako',
        benchmarks=GETTER.by_category[category],
        category=category)


if __name__ == '__main__':
    APP.run()
