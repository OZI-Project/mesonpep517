=========
OZI.build
=========

This is the `OZI-Project <https://github.com/OZI-Project>`_ maintained fork of the mesonpep517 0.2 tag.

This is a module that implements PEP-517 for the meson build system.

This means that you only need to provide a ``pyproject.toml`` and a
``meson.build`` in your project source root to be able to create a wheel
for the project and to publish your project on PyPI.

Other features include:

* compiling modules to bytecode with pyc_wheel
* scanning ``pyproject.toml`` for exploitable ReDoS patterns with regexploit

For more information have a look at `the documentation <https://docs.oziproject.dev/en/stable/ozi_build.html>`_

License
-------

OZI.build is licensed under Apache-2.0 and includes ``regexploit``,
``pyc_wheel`` and portions of ``wheel`` whose copyright information is
reproduced here.

Apache-2.0 contributors
^^^^^^^^^^^^^^^^^^^^^^^

``regexploit`` Copyright (c) 2021 Ben Caller <REMOVETHISPREFIX.ben@doyensec.com>

``pyc_wheel`` Copyright (c) 2016 Grant Patten <grant@gpatten.com>

``pyc_wheel`` Copyright (c) 2019-2021 Adam Karpierz <adam@karpierz.net>

MIT contributors
^^^^^^^^^^^^^^^^

``wheel`` Copyright (c) 2012-2014 Daniel Holth <dholth@fastmail.fm> and contributors.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


See Also:

https://oziproject.dev
https://mesonbuild.com
