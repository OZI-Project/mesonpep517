import json
import logging
import os
import string
import subprocess
import sys
import tempfile
from pathlib import Path

from packaging.version import Version

from ._util import GET_PYTHON_VERSION
from ._util import PKG_INFO
from ._util import PKG_INFO_CONFIG_REQUIRES_PYTHON
from ._util import PKG_INFO_NO_REQUIRES_PYTHON
from ._util import meson
from ._util import meson_configure
from ._util import readme_ext_to_content_type
from .schema import VALID_OPTIONS

if sys.version_info >= (3, 11):
    import tomllib as toml
elif sys.version_info < (3, 11):
    import tomli as toml

log = logging.getLogger(__name__)


class Config:
    def __init__(self, builddir=None):
        config = self.__get_config()
        self.__metadata = config['tool']['ozi-build']['metadata']
        self.__entry_points = config['tool']['ozi-build'].get(
            'entry-points', []
        )
        self.__extras = config.get('project', {}).get('optional_dependencies', None)
        if self.__extras is not None:
            log.warning('pyproject.toml:project.optional_dependencies should be renamed to pyproject.toml:project.optional-dependencies')
        else:
            self.__extras = config.get('project', {}).get('optional-dependencies', {})
        self.__requires = config.get('project', {}).get('dependencies', None)
        self.license_file = config.get('project', {}).get('license', {}).get('file', '')
        if self.license_file == '':
            log.warning('pyproject.toml:project.license.file key-value pair was not found')
        self.__min_python = '3.10'
        self.__max_python = '3.13'
        self.__pyc_wheel = config['tool']['ozi-build'].get('pyc_wheel', {})
        self.installed = []
        self.options = []
        self.builddir = None
        if builddir:
            self.set_builddir(builddir)

    @property
    def requirements(self):
        return self.__requires if self.__requires else []

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

    def __introspect(self, introspect_type):
        with open(
            os.path.join(
                self.__builddir,
                'meson-info',
                'intro-' + introspect_type + '.json',
            )
        ) as f:
            return json.load(f)

    def set_builddir(self, builddir):
        self.__builddir = builddir
        project = self.__introspect('projectinfo')

        self['version'] = project['version']
        if 'module' not in self:
            self['module'] = project['descriptive_name']

        self.installed = self.__introspect('installed')
        self.options = self.__introspect('buildoptions')
        self.validate_options()

    def __getitem__(self, key):
        return self.__metadata[key]

    def __setitem__(self, key, value):
        self.__metadata[key] = value

    def __contains__(self, key):
        return key in self.__metadata

    def _parse_project_optional_dependencies(self, k: str, v: str):
        metadata = ''
        if any(i not in string.ascii_uppercase + string.ascii_lowercase + '-[],0123456789' for i in v):
            raise ValueError('pyproject.toml:project.optional-dependencies has invalid character in nested key "{}"'.format(k))
        for j in (name for name in v.strip('[]').rstrip(',').split(',')):
            if len(j) > 0 and j[0] in string.ascii_uppercase + string.ascii_lowercase:
                for package in self.__extras.get(j, []):
                    metadata += 'Requires-Dist: {}; extra=="{}"\n'.format(package, k)
            else:
                raise ValueError('pyproject.toml:project.optional-dependencies nested key target value "{}" invalid'.format(j))
        return metadata

    def _parse_project(self):
        res = ''
        for k, v in self.__extras.items():
            res += "Provides-Extra: {}\n".format(k)
            if isinstance(v, list):
                for i in v:
                    if i.startswith('['):
                        res += self._parse_project_optional_dependencies(k, i)
                    else:
                        res += 'Requires-Dist: {}; extra=="{}"\n'.format(i, k)
            elif isinstance(v, str):
                res += self._parse_project_optional_dependencies(k, v)
                log.warning('pyproject.toml:project.optional-dependencies nested key type should be a toml array, like a=["[b,c]", "[d,e]", "foo"], parsed string "{}"'.format(v))
        return res

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

    def get(self, key, default=None):
        return self.__metadata.get(key, default)

    def auto_python_version(self, meta):
        python = 'python3'
        python_version = Version(subprocess.check_output([python, '-c', GET_PYTHON_VERSION]).decode('utf-8').strip('\n'))
        if python_version < Version(self.__min_python):
            meta.update({
                'min_python': str(python_version),
                'max_python': self.__max_python,
            })
        elif python_version >= Version(self.__max_python):
            meta.update({
                'min_python': self.__min_python,
                'max_python': '{}.{}'.format(python_version.major, str(python_version.minor + 1))
            })
        else:
            meta.update({
                'min_python': self.__min_python,
                'max_python': self.__max_python,
            })
        return meta

    def get_metadata(self):
        meta = {
            'name': self['module'],
            'version': self['version'],
        }
        if 'pkg-info-file' in self:
            if not Path(self['pkg-info-file']).exists():
                builddir = tempfile.TemporaryDirectory().name
                meson_configure(builddir)
                meson('compile', '-C', builddir)
                pkg_info_file = Path(builddir) / 'PKG-INFO'
            else:
                pkg_info_file = self['pkg-info-file']
            res = '\n'.join(PKG_INFO_NO_REQUIRES_PYTHON.split('\n')[:3]).format(**meta) + '\n'
            with open(pkg_info_file, 'r') as f:
                orig_lines = f.readlines()
                for line in orig_lines:
                    if line.startswith(
                        'Metadata-Version:'
                    ) or line.startswith(
                        'Version:'
                    ) or line.startswith(
                        'Name:'
                    ):
                        res += self._parse_project()
                        continue
                    res += line
            return res
        option_build = self.get('meson-python-option-name')
        if not option_build:
            log.warning(
                "meson-python-option-name not specified in the "
                + "[tool.ozi-build.metadata] section, assuming `python3`"
            )
        else:
            for opt in self.options:
                if opt['name'] == option_build:
                    python = opt['value']
                    break
        meta = self.auto_python_version(meta)
        if self['module'] == 'OZI.build':
            meta.pop('min_python')
            meta.pop('max_python')
            res = PKG_INFO_NO_REQUIRES_PYTHON.format(**meta)
        elif self.get('requires-python'):
            meta.pop('min_python')
            meta.pop('max_python')
            meta.update({'requires_python': self.get('requires-python')})
            res = PKG_INFO_CONFIG_REQUIRES_PYTHON.format(**meta)
        else:
            res = PKG_INFO.format(**meta)
        res += self._parse_project()

        for key in [
            'summary',
            'home-page',
            'author',
            'author-email',
            'maintainer',
            'maintainer-email',
            'license',
        ]:
            if key in self:
                res += '{}: {}\n'.format(key.capitalize(), self[key])

        for key in [
            'license-expression',
            'license-file',
        ]:
            if key in self:
                if key == 'license-expression' and 'license' in self:
                    raise ValueError('license and license-expression are mutually exclusive')
                header = '-'.join(map(str.capitalize, key.split('-')))
                if header in {'Name', 'Version', 'Metadata-Version'}:
                    raise ValueError('{} is not a valid value for dynamic'.format(key))
                res += '{}: {}\n'.format(header, self[key])

        if 'dynamic' in self:
            for i in self['dynamic']:
                header = '-'.join(map(str.capitalize, i.split('-')))
                res += f'Dynamic: {header}\n'

        if 'download-url' in self:
            if '{version}' in self['download-url']:
                res += f'Download-URL: {self["download-url"].replace("{version}", self["version"])}\n'
            else:
                log.warning('pyproject.toml:tools.ozi-build.metadata.download-url missing {version} replace pattern')
                res += f'Download-URL: {self["download-url"]}\n'

        if self.__requires:
            for package in self.__requires:
                res += 'Requires-Dist: {}\n'.format(package)

        if self.get('requires', None):
            raise ValueError('pyproject.toml:tools.ozi-build.metadata.requires is deprecated as of OZI.build 1.3')

        for key, mdata_key in [
            ('provides', 'Provides-Dist'),
            ('obsoletes', 'Obsoletes-Dist'),
            ('classifiers', 'Classifier'),
            ('project-urls', 'Project-URL'),
            ('requires-external', 'Requires-External'),
        ]:
            vals = self.get(key, [])
            for val in vals:
                res += '{}: {}\n'.format(mdata_key, val)
        description = ''
        description_content_type = 'text/plain'
        if 'description-file' in self:
            description_file = Path(self['description-file'])
            with open(description_file, 'r') as f:
                description = f.read()

            description_content_type = readme_ext_to_content_type.get(
                description_file.suffix.lower(), description_content_type
            )
        elif 'description' in self:
            description = self['description']

        if description:
            res += 'Description-Content-Type: {}\n'.format(
                description_content_type
            )
            res += 'Description:\n\n' + description

        return res

    def get_entry_points(self):
        res = ''
        for group_name in sorted(self.__entry_points):
            res += '[{}]\n'.format(group_name)
            group = self.__entry_points[group_name]
            for entrypoint in sorted(group):
                res += '{}\n'.format(entrypoint)
            res += '\n'

        return res

