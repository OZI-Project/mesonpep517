VALID_OPTIONS = {
    "author": {"description": "Your name"},
    "author-email": {
        "description": """Your email address

e.g. for ozi-build itself:

``` toml
[tool.ozi-build.metadata]
author="Thibault Saunier"
author-email="tsaunier@gnome.org"
```"""
    },
    "classifiers": {
        "description": "A list of [classifiers](https://pypi.python.org/pypi?%3Aaction=list_classifiers)."
    },
    "description": {
        "description": "The description of the project as a string if you do not want to specify 'description-file'"
    },
    "description-file": {
        "description": """A path (relative to the .toml file) to a file containing a longer description
of your package to show on PyPI. This should be written in reStructuredText
  Markdown or plain text, and the filename should have the appropriate extension
  (`.rst`, `.md` or `.txt`)."""
    },
    "home-page": {
        "description": """A string containing the URL for the package's home page.

Example:

`http://www.example.com/~cschultz/bvote/`"""
    },
    "download-url": {
        "description": """A string containing the URL for the package's source, will replace '{version}' with the current version."""
    },
    "keywords": {
        "description": """Comma-separated keywords as a string."""
    },
    "license": {
        "description": """Text indicating the license covering the distribution. This text can be either a valid license expression as defined in [pep639](https://www.python.org/dev/peps/pep-0639/#id88) or any free text."""
    },
    "maintainer": {
        "description": "Name of current maintainer of the project (if different from author)"
    },
    "maintainer-email": {
        "description": """Maintainer email address

Example:

``` toml
[tool.ozi-build.metadata]
maintainer="Robin Goode"
maintainer-email="rgoode@example.org"
```"""
    },
    "meson-options": {
        "description": """A list of default meson options to set, can be overriden and expended through the `MESON_ARGS`
environement variable at build time."""
    },
    "meson-python-option-name": {
        "description": """The name of the meson options that is used in the meson build definition
to set the python installation when using
[`python.find_installation()`](http://mesonbuild.com/Python-module.html#find_installation)."""
    },
    "module": {
        "description": "The name of the module, will use the meson project name if not specified"
    },
    "obsoletes": {"description": """
A list of PyPI packages that this project should not be installed concurrently with.

``` toml
      obsoletes = [
        "OtherProject",
        "AnotherProject==3.4",
        'virtual_package; python_version >= "3.4"',
      ]
```
"""},
    "pkg-info-file": {
        "description": """Pass a PKG-INFO file direcly usable.

> ! NOTE: All other keys will be ignored if you pass an already prepared `PKG-INFO`
> file
"""
    },
    "platforms": {
        "description": "Supported Python platforms, can be 'any', py3, etc..."
    },
    "project-urls": {
        "description": """A list of `Type, url` as described in the
[pep345](https://www.python.org/dev/peps/pep-0345/#project-url-multiple-use).
For example:

``` toml
project-urls = [
    "Source, https://gitlab.com/OZI-Project/OZI.build",
]
```"""
    },
    "provides": {"description": """A list of PyPI packages that this project provides its own version of.

``` toml
      provides = [
        "OtherProject",
        "AnotherProject==3.4",
        'virtual_package; python_version >= "3.4"',
      ]
```"""},
    "pure-python-abi": {
        "description": """An override of the pure python abi build target e.g. ``py3-none``."""
    },
    "requires": {
        "description": """A list of other packages from PyPI that this package needs. Each package may
be followed by a version specifier like ``(>=4.1)`` or ``>=4.1``, and/or an
[environment marker](https://www.python.org/dev/peps/pep-0345/#environment-markers)
after a semicolon. For example:

``` toml
      requires = [
          "requests >=2.6",
          "configparser; python_version == '2.7'",
      ]
```"""
    },
    "requires-external": {"description": """A list of non-PyPI dependency packages. For example:

``` toml
      requires-external = [
          "git",
          "node",
      ]
```"""},
    "requires-python": {
        "description": """A version specifier for the versions of Python this requires, e.g. ``~=3.3`` or
``>=3.3,<4`` which are equivalents."""
    },
    "summary": {
        "description": "A one sentence summary about the package",
    },
}
