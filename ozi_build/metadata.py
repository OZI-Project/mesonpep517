import logging
import string
import subprocess
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

log = logging.getLogger(__name__)


def check_pkg_info_file(config, meta):
    if 'pkg-info-file' in config:
        if not Path(config['pkg-info-file']).exists():
            builddir = tempfile.TemporaryDirectory().name
            meson_configure(builddir)
            meson('compile', '-C', builddir)
            pkg_info_file = Path(builddir) / 'PKG-INFO'
        else:
            pkg_info_file = config['pkg-info-file']
        res = '\n'.join(PKG_INFO_NO_REQUIRES_PYTHON.split('\n')[:3]).format(**meta) + '\n'
        with open(pkg_info_file, 'r') as f:
            orig_lines = f.readlines()
            for line in orig_lines:
                if (
                    line.startswith('Metadata-Version:')
                    or line.startswith('Version:')
                    or line.startswith('Name:')
                ):
                    res += config._parse_project()
                    continue
                res += line
        return res


def auto_python_version(config, python_bin: str, meta):
    python_version = Version(
        subprocess.check_output([python_bin, '-c', GET_PYTHON_VERSION])
        .decode('utf-8')
        .strip('\n')
    )
    if python_version < Version(config.min_python):
        meta.update(
            {
                'min_python': str(python_version),
                'max_python': config.max_python,
            }
        )
    elif python_version >= Version(config.max_python):
        meta.update(
            {
                'min_python': config.min_python,
                'max_python': '{}.{}'.format(
                    python_version.major, str(python_version.minor + 1)
                ),
            }
        )
    else:
        meta.update(
            {
                'min_python': config.min_python,
                'max_python': config.max_python,
            }
        )
    return meta


def check_requires_python(config, meta):
    if config['module'] == 'OZI.build':
        meta.pop('min_python')
        meta.pop('max_python')
        res = PKG_INFO_NO_REQUIRES_PYTHON.format(**meta)
    elif config.get('requires-python'):
        meta.pop('min_python')
        meta.pop('max_python')
        meta.update({'requires_python': config.get('requires-python')})
        res = PKG_INFO_CONFIG_REQUIRES_PYTHON.format(**meta)
    else:
        res = PKG_INFO.format(**meta)
    return res


def get_python_bin(config):
    option_build = config.get('meson-python-option-name')
    python = 'python3'
    if not option_build:
        log.warning(
            "meson-python-option-name not specified in the "
            + "[tool.ozi-build.metadata] section, assuming `python3`"
        )
    else:
        for opt in config.options:
            if opt['name'] == option_build:
                python = opt['value']
                break
    return python


def _parse_project_optional_dependencies(config, k: str, v: str):
    metadata = ''
    if any(
        i not in string.ascii_uppercase + string.ascii_lowercase + '-[],0123456789'
        for i in v
    ):
        raise ValueError(
            'pyproject.toml:project.optional-dependencies has invalid character in nested key "{}"'.format(
                k
            )
        )
    for j in (name for name in v.strip('[]').rstrip(',').split(',')):
        if len(j) > 0 and j[0] in string.ascii_uppercase + string.ascii_lowercase:
            for package in config.extras.get(j, []):
                metadata += 'Requires-Dist: {}; extra=="{}"\n'.format(package, k)
        else:
            raise ValueError(
                'pyproject.toml:project.optional-dependencies nested key target value "{}" invalid'.format(
                    j
                )
            )
    return metadata


def get_optional_dependencies(config):
    res = ''
    for k, v in config.extras.items():
        res += "Provides-Extra: {}\n".format(k)
        if isinstance(v, list):
            for i in v:
                if i.startswith('['):
                    res += _parse_project_optional_dependencies(config, k, i)
                else:
                    res += 'Requires-Dist: {}; extra=="{}"\n'.format(i, k)
        elif isinstance(v, str):
            res += config._parse_project_optional_dependencies(config, k, v)
            log.warning(
                'pyproject.toml:project.optional-dependencies nested key type should be a toml array, like a=["[b,c]", "[d,e]", "foo"], parsed string "{}"'.format(
                    v
                )
            )
    return res


def get_simple_headers(config):
    res = ''
    for key in [
        'summary',
        'home-page',
        'author',
        'author-email',
        'maintainer',
        'maintainer-email',
        'license',
    ]:
        if key in config:
            res += '{}: {}\n'.format(key.capitalize(), config[key])
    for key, mdata_key in [
        ('provides', 'Provides-Dist'),
        ('obsoletes', 'Obsoletes-Dist'),
        ('classifiers', 'Classifier'),
        ('project-urls', 'Project-URL'),
        ('requires-external', 'Requires-External'),
        ('dynamic', 'Dynamic'),
        ('license-file', 'License-File'),
    ]:
        vals = config.get(key, [])
        if key == 'dynamic':
            for i in vals:
                if i in {'Name', 'Version', 'Metadata-Version'}:
                    raise ValueError('{} is not a valid value for dynamic'.format(key))
        for val in vals:
            res += '{}: {}\n'.format(mdata_key, val)
    return res


def get_license_headers(config):
    res = ''
    key = 'license-expression'
    if key in config:
        if key == 'license-expression' and 'license' in config:
            raise ValueError('license and license-expression are mutually exclusive')
        header = '-'.join(map(str.capitalize, key.split('-')))
        res += '{}: {}\n'.format(header, config[key])
    return res


def get_download_url_headers(config):
    res = ''
    if 'download-url' in config:
        if '{version}' in config['download-url']:
            res += f'Download-URL: {config["download-url"].replace("{version}", config["version"])}\n'
        else:
            log.warning(
                'pyproject.toml:tools.ozi-build.metadata.download-url missing {version} replace pattern'
            )
            res += f'Download-URL: {config["download-url"]}\n'
    return res


def get_requirements_headers(config):
    res = ''
    if config.requirements:
        for package in config.requirements:
            res += 'Requires-Dist: {}\n'.format(package)
    if config.get('requires', None):
        raise ValueError(
            'pyproject.toml:tools.ozi-build.metadata.requires is deprecated as of OZI.build 1.3'
        )
    return res


def get_description_headers(config):
    res = ''
    description = ''
    description_content_type = 'text/plain'
    if 'description-file' in config:
        description_file = Path(config['description-file'])
        with open(description_file, 'r') as f:
            description = f.read()

        description_content_type = readme_ext_to_content_type.get(
            description_file.suffix.lower(), description_content_type
        )
    elif 'description' in config:
        description = config['description']

    if description:
        res += 'Description-Content-Type: {}\n'.format(description_content_type)
        res += 'Description:\n\n' + description
    return res
