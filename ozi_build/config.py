import json
import logging
import os
import sys

from ._util import check_pyproject_regexes
from .metadata import auto_python_version
from .metadata import check_pkg_info_file
from .metadata import check_requires_python
from .metadata import get_description_headers
from .metadata import get_download_url_headers
from .metadata import get_license_headers
from .metadata import get_optional_dependencies
from .metadata import get_python_bin
from .metadata import get_requirements_headers
from .metadata import get_simple_headers
from .schema import VALID_OPTIONS
from .schema import VALID_PYC_WHEEL_OPTIONS

if sys.version_info >= (3, 11):
    import tomllib as toml
elif sys.version_info < (3, 11):
    import tomli as toml

log = logging.getLogger(__name__)


class Config:
    def __init__(self, builddir=None):
        config = self.__get_config()
        check_pyproject_regexes(config)
        self.__metadata = config['tool']['ozi-build']['metadata']
        self.__entry_points = config['tool']['ozi-build'].get('entry-points', [])
        self.__extras = config.get('project', {}).get('optional_dependencies', None)
        if self.__extras is not None:
            log.warning(
                'pyproject.toml:project.optional_dependencies should be renamed to pyproject.toml:project.optional-dependencies'
            )
        else:
            self.__extras = config.get('project', {}).get('optional-dependencies', {})
        self.__requires = config.get('project', {}).get('dependencies', None)
        self.license_file = [config.get('project', {}).get('license', {}).get('file', None)]
        self.__min_python = '3.10'
        self.__max_python = '3.13'
        self.__pyc_wheel = config['tool']['ozi-build'].get('pyc_wheel', {})
        self.installed = []
        self.options = []
        if builddir:
            self.builddir = builddir

    @property
    def extras(self):
        return self.__extras

    @property
    def min_python(self):
        return self.__min_python

    @property
    def max_python(self):
        return self.__max_python

    @property
    def requirements(self):
        return self.__requires if self.__requires else []

    @property
    def pyc_wheel(self):
        return self.__pyc_wheel

    def __introspect(self, introspect_type):
        with open(
            os.path.join(
                self.__builddir,
                'meson-info',
                'intro-' + introspect_type + '.json',
            )
        ) as f:
            return json.load(f)

    @staticmethod
    def __get_config():
        with open('pyproject.toml', 'rb') as f:
            config = toml.load(f)
            try:
                config['tool']['ozi-build']['metadata']
            except KeyError:
                raise RuntimeError(
                    "`[tool.ozi-build.metadata]` section is mandatory "
                    "for the meson backend"
                )

            return config

    def __getitem__(self, key):
        return self.__metadata[key]

    def __setitem__(self, key, value):
        self.__metadata[key] = value

    def __contains__(self, key):
        return key in self.__metadata

    @property
    def entry_points(self):
        res = ''
        for group_name in sorted(self.__entry_points):
            res += '[{}]\n'.format(group_name)
            group = self.__entry_points[group_name]
            for entrypoint in sorted(group):
                res += '{}\n'.format(entrypoint)
            res += '\n'
        return res

    @property
    def builddir(self):
        return self.__builddir

    @builddir.setter
    def builddir(self, builddir):
        self.__builddir = builddir
        project = self.__introspect('projectinfo')

        self['version'] = project['version']
        if 'module' not in self:
            self['module'] = project['descriptive_name']
        if 'license-expression' not in self:
            self['license-expression'] = project.get('license', '')[0]
            if 'license-expression' == '':
                raise RuntimeError(
                    "license-expression metadata not found in pyproject.toml or meson.build"
                )
        if self.license_file[0] is None:
            self['license-file'] = self.license_file = project.get('license_files', [])
            if len(self.license_file) == 0:
                raise RuntimeError(
                    "license-file metadata not found in pyproject.toml or meson.build"
                )

        self.installed = self.__introspect('installed')
        self.options = self.__introspect('buildoptions')
        self.validate_options()

    def validate_options(self):
        options = VALID_OPTIONS.copy()
        options['version'] = {}
        options['module'] = {}
        for field, value in self.__metadata.items():
            if field not in options:
                raise RuntimeError(
                    "%s is not a valid option in the `[tool.ozi-build.metadata]` section, "
                    "got value: %s" % (field, value)
                )
            del options[field]
        for field, desc in options.items():
            if desc.get('required'):
                raise RuntimeError(
                    "%s is mandatory in the `[tool.ozi-build.metadata] section but was not found"
                    % field
                )
        pyc_whl_options = VALID_PYC_WHEEL_OPTIONS.copy()
        for field, value in self.__pyc_wheel.items():
            if field not in pyc_whl_options:
                raise RuntimeError(
                    "%s is not a valid option in the `[tool.ozi-build.pyc_wheel]` section, "
                    "got value: %s" % (field, value)
                )
            del pyc_whl_options[field]

    def get(self, key, default=None):
        return self.__metadata.get(key, default)

    def get_metadata(self):
        meta = {
            'name': self['module'],
            'version': self['version'],
        }
        pkg_info_file = check_pkg_info_file(self, meta)
        if pkg_info_file is not None:
            return pkg_info_file

        res = check_requires_python(
            self, auto_python_version(self, get_python_bin(self), meta)
        )
        res += get_optional_dependencies(self)
        res += get_simple_headers(self)
        res += get_license_headers(self)
        res += get_download_url_headers(self)
        res += get_requirements_headers(self)
        res += get_description_headers(self)

        return res
