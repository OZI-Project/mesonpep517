# Configuration

OZI.build only supports reading configuration from `pyproject.toml`.
This file lives at the root of the module/package, at the same place
as the toplevel `meson.build` file.

## Build system section

This tells tools like pip to build your project with flit. It's a standard
defined by PEP 517. For any project using OZI.build, it will look something like this:

``` toml
    [build-system]
    requires = ["OZI.build[core]~=1.9"]
    build-backend = "ozi_build.buildapi"
```

## Project section

This holds the essential project metadata that is outside of the ``meson.build`` file.
Some keys remain in the project table for improved cross-compatibility.
It should look similar to this in an OZI.build project:

``` toml
    [project]
    dynamic = ["version"]
    dependencies = [
    'TAP-Producer~=1.0.4',
    ]

    [project.license]
    file = "LICENSE.txt"

    [project.optional-dependencies]
    ...
```

## Metadata section

> NOTE: The project version and name are extracted from the `meson.build`
> [`project()`](http://mesonbuild.com/Reference-manual.html#project) section.

This section is called `[tool.ozi-build.metadata]` in the file.

### `author`

Your name

### `author-email`

Your email address

e.g. for ozi-build itself:

``` toml
[tool.ozi-build.metadata]
author="Thibault Saunier"
author-email="tsaunier@gnome.org"
```

### `classifiers`

A list of [classifiers](https://pypi.python.org/pypi?%3Aaction=list_classifiers).

### `description`

The description of the project as a string if you do not want to specify 'description-file'

### `description-file`

A path (relative to the .toml file) to a file containing a longer description
of your package to show on PyPI. This should be written in reStructuredText
  Markdown or plain text, and the filename should have the appropriate extension
  (`.rst`, `.md` or `.txt`).

### `home-page`

A string containing the URL for the package's home page.

Example:

`http://www.example.com/~cschultz/bvote/`

### `download-url`

A string containing the URL for the package's source, will replace '{version}' with the current version.

### `dynamic`

A list of other headers to be treated as dynamic fields.

### `keywords`

Comma-separated keywords as a string.

### `license`

Text indicating the license covering the distribution. This text can be either a valid license expression as defined in [pep639](https://www.python.org/dev/peps/pep-0639/#id88) or any free text.

### `license-expression`

A SPDX license expression.

### `license-file`

The license filename.

### `maintainer`

Name of current maintainer of the project (if different from author)

### `maintainer-email`

Maintainer email address

Example:

``` toml
[tool.ozi-build.metadata]
maintainer="Robin Goode"
maintainer-email="rgoode@example.org"
```

### `meson-options`

A list of default meson options to set, can be overriden and expended through the `MESON_ARGS`
environement variable at build time.

### `meson-python-option-name`

The name of the meson options that is used in the meson build definition
to set the python installation when using
[`python.find_installation()`](http://mesonbuild.com/Python-module.html#find_installation).

### `module`

The name of the module, will use the meson project name if not specified

### `obsoletes`


A list of PyPI packages that this project should not be installed concurrently with.

``` toml
      obsoletes = [
        "OtherProject",
        "AnotherProject==3.4",
        'virtual_package; python_version >= "3.4"',
      ]
```


### `pkg-info-file`

Pass a PKG-INFO file direcly usable.

> ! NOTE: All other keys will be ignored if you pass an already prepared `PKG-INFO`
> file


### `platforms`

Supported Python platforms, can be 'any', py3, etc...

### `project-urls`

A list of `Type, url` as described in the
[pep345](https://www.python.org/dev/peps/pep-0345/#project-url-multiple-use).
For example:

``` toml
project-urls = [
    "Source, https://gitlab.com/OZI-Project/OZI.build",
]
```

### `provides`

A list of PyPI packages that this project provides its own version of.

``` toml
      provides = [
        "OtherProject",
        "AnotherProject==3.4",
        'virtual_package; python_version >= "3.4"',
      ]
```

### `pure-python-abi`

An override of the pure python abi build target e.g. ``py3-none``.

### `requires`

:::{deprecated} 1.3.0
Use project.dependencies instead.
:::
A list of other packages from PyPI that this package needs. Each package may
be followed by a version specifier like ``(>=4.1)`` or ``>=4.1``, and/or an
[environment marker](https://www.python.org/dev/peps/pep-0345/#environment-markers)
after a semicolon. For example:

``` toml
      requires = [
          "requests >=2.6",
          "configparser; python_version == '2.7'",
      ]
```

### `requires-external`

A list of non-PyPI dependency packages. For example:

``` toml
      requires-external = [
          "git",
          "node",
      ]
```

### `requires-python`

A version specifier for the versions of Python this requires, e.g. ``~=3.3`` or
``>=3.3,<4`` which are equivalents.

### `summary`

A one sentence summary about the package


## ``pyc_wheel`` configuration

This section is called `[tool.ozi-build.pyc_wheel]` in the file.

### `exclude`

A regular expression of files for pyc_wheel to ignore.

### `quiet`

Quiet non-error output of pyc_wheel.


## Entry points section (Optional)

You can declare [entry points](http://entrypoints.readthedocs.io/en/latest/)
in the `[tools.ozi-build.entry-points]` section. It is a list of
'entrypointname = module:funcname` strings, for example for console
scripts entry points:

``` toml
[tool.ozi-build.entry-points]
console_scripts = [
    'otioview = opentimelineview.console:main',
    'otiocat = opentimelineio.console.otiocat:main',
    'otioconvert = opentimelineio.console.otioconvert:main',
    'otiostat = opentimelineio.console.otiostat:main',
    'otioautogen_serialized_schema_docs = opentimelineio.console.autogen_serialized_datamodel:main',
]
```
