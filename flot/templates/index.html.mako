## encoding=utf-8
## Copyright © 2016 Intel Corporation
##
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in
## all copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.

<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Mesa Performance: Continuous Integration</title>
    <link rel="stylesheet" href="${url_for('static', filename='index.css')}">
    <script src="https://code.jquery.com/jquery-1.12.4.min.js"></script>
    <script src="${url_for('static', filename='scripts/jquery.collapse.js')}"></script>
  </head>
  <body>
    <div id="header">
      <h2>Mesa Performance</h2>
    </div>

    <div data-collapse>
      <h3>All Benchmarks</h3>
      <div>
        <ul>
          <li><a href="${url_for('all')}">One Big Page</a></li>
% for b in sorted(getter.by_name.keys()):
          <li><a href="${url_for('apps', benchmark=b)}">${b}</a></li>
% endfor
        <ul>
      </div>
% for c in sorted(getter.by_category.keys()):
      <h3>Category: ${c}</h3>
      <div>
        <ul>
          <li><a href="${url_for('categories', category=c)}">One Big Page</a></li>
  % for b in sorted(getter.by_category[c]):
          <li><a href="${url_for('apps', benchmark=b)}">${b}</a></li>
  % endfor
        <ul>
      </div>
% endfor
    </div>

    <div id="footer">
      Copyright &copy; 2016 Intel Corporation
    </div>
  </body>
</html>
