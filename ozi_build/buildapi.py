"""PEP-517 compliant buildsystem API"""

import contextlib
import json
import logging
import os
import shutil
import string
import subprocess
import sys
import sysconfig
import tarfile
import tempfile
from gzip import GzipFile
from pathlib import Path

from wheel.wheelfile import WheelFile
from packaging.version import Version

if sys.version_info >= (3, 11):
    import tomllib as toml
elif sys.version_info < (3, 11):
    import tomli as toml

from ._pyc_wheel import convert_wheel
from .pep425tags import get_abbr_impl
from .pep425tags import get_abi_tag
from .pep425tags import get_impl_ver
from .pep425tags import get_platform_tag
from .schema import VALID_OPTIONS

log = logging.getLogger(__name__)


def meson(*args, config_settings=None, builddir=''):
    try:
        return subprocess.check_output(['meson'] + list(args))
    except subprocess.CalledProcessError as e:
        stdout = ''
        stderr = ''
        if e.stdout:
            stdout = e.stdout.decode()
        if e.stderr:
            stderr = e.stderr.decode()
        print(
            "Could not run meson: %s\n%s" % (stdout, stderr), file=sys.stderr
        )
        try:
            fulllog = os.path.join(builddir, 'meson-logs', 'meson-log.txt')
            with open(fulllog) as f:
                print("Full log: %s" % f.read())
        except IOError:
            print("Could not open %s" % fulllog)
            pass
        raise e


def meson_configure(*args, config_settings=None):
    if 'MESON_ARGS' in os.environ:
        args = os.environ.get('MESON_ARGS').split(' ') + list(args)
        print("USING MESON_ARGS: %s" % args)
    args = list(args)
    args.append('-Dlibdir=lib')

    meson(*args, builddir=args[0], config_settings=config_settings)


PKG_INFO = """\
Metadata-Version: 2.1
Requires-Python: >={min_python}, <{max_python}
Name: {name}
Version: {version}
"""

PKG_INFO_CONFIG_REQUIRES_PYTHON = """\
Metadata-Version: 2.1
Requires-Python: {requires_python}
Name: {name}
Version: {version}
"""

PKG_INFO_NO_REQUIRES_PYTHON = """\
Metadata-Version: 2.1
Name: {name}
Version: {version}
"""

readme_ext_to_content_type = {
    '.rst': 'text/x-rst',
    '.md': 'text/markdown',
    '.txt': 'text/plain',
    '': 'text/plain',
}

GET_PYTHON_VERSION = 'import sys;print("{}.{}".format(*sys.version_info[:2]))'
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
        self.__min_python = '3.10'
        self.__max_python = '3.13'
        self.installed = []
        self.options = []
        self.builddir = None
        if builddir:
            self.set_builddir(builddir)

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
        python = 'python3'
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


@contextlib.contextmanager
def cd(path):
    CWD = os.getcwd()

    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(CWD)


def get_requires_for_build_wheel(config_settings=None):
    """Returns a list of requirements for building, as strings"""
    return Config().get('requires', [])


# For now, we require all dependencies to build either a wheel or an sdist.
get_requires_for_build_sdist = get_requires_for_build_wheel


wheel_file_template = """\
Wheel-Version: 1.0
Generator: ozi_build
Root-Is-Purelib: {}
"""


def _write_wheel_file(f, supports_py2, is_pure):
    f.write(wheel_file_template.format(str(is_pure).lower()))
    if is_pure:
        if supports_py2:
            f.write("Tag: py2-none-any\n")
        f.write("Tag: py3-none-any\n")
    else:
        f.write(
            "Tag: {0}{1}-{2}-{3}\n".format(
                get_abbr_impl(),
                get_impl_ver(),
                get_abi_tag(),
                get_platform_tag(),
            )
        )


def check_is_pure(installed):
    variables = sysconfig.get_config_vars()
    suffix = (
        variables.get('EXT_SUFFIX')
        or variables.get('SO')
        or variables.get('.so')
    )
    # msys2's python3 has "-cpython-36m.dll", we have to be clever
    split = suffix.rsplit('.', 1)
    suffix = split.pop(-1)

    for installpath in installed.values():
        if "site-packages" in installpath or "dist-packages" in installpath:
            if installpath.split('.')[-1] == suffix:
                return False

    return True


def prepare_metadata_for_build_wheel(
    metadata_directory, config_settings=None, builddir=None, config=None
):
    """Creates {metadata_directory}/foo-1.2.dist-info"""
    if not builddir:
        builddir = tempfile.TemporaryDirectory().name
        meson_configure(builddir, config_settings=config_settings)
    if not config:
        config = Config(builddir)

    dist_info = Path(
        metadata_directory,
        '{}-{}.dist-info'.format(config['module'].replace('-','_'), config['version']),
    )
    dist_info.mkdir(exist_ok=True)

    is_pure = check_is_pure(config.installed)
    with (dist_info / 'WHEEL').open('w') as f:
        _write_wheel_file(f, False, is_pure)

    with (dist_info / 'METADATA').open('w') as f:
        f.write(config.get_metadata())

    entrypoints = config.get_entry_points()
    if entrypoints:
        with (dist_info / 'entry_points.txt').open('w') as f:
            f.write(entrypoints)

    return dist_info.name


GET_CHECK = """
from ozi_build import pep425tags
tag = pep425tags.get_abbr_impl() + pep425tags.get_impl_ver()
if tag != pep425tags.get_abi_tag():
    print("{0}-{1}".format(tag, pep425tags.get_abi_tag()))
else:
    print("{0}-none".format(tag))
"""


def get_abi(python):
    return (
        subprocess.check_output([python, '-c', GET_CHECK])
        .decode('utf-8')
        .strip('\n')
    )


class WheelBuilder:
    def __init__(self):
        self.wheel_zip = None  # type: ignore
        self.builddir = tempfile.TemporaryDirectory()
        self.installdir = tempfile.TemporaryDirectory()

    def build(self, wheel_directory, config_settings, metadata_dir):
        config = Config()

        args = [
            self.builddir.name,
            '--prefix',
            self.installdir.name,
        ] + config.get('meson-options', [])
        meson_configure(*args, config_settings=config_settings)
        config.set_builddir(self.builddir.name)

        metadata_dir = prepare_metadata_for_build_wheel(
            wheel_directory, builddir=self.builddir.name, config=config
        )

        is_pure = check_is_pure(config.installed)
        platform_tag = config.get(
            'platforms', 'any' if is_pure else get_platform_tag()
        )
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
        if not is_pure:
            abi = get_abi(python)
        else:
            abi = config.get('pure-python-abi', get_abi(python))
        target_fp = wheel_directory / '{}-{}-{}-{}.whl'.format(
            config['module'].replace('-','_'),
            config['version'],
            abi,
            platform_tag,
        )

        self.wheel_zip: WheelFile = WheelFile(str(target_fp), 'w')
        for f in os.listdir(str(wheel_directory / metadata_dir)):
            self.wheel_zip.write(
                str(wheel_directory / metadata_dir / f),
                arcname=str(Path(metadata_dir) / f),
            )
        shutil.rmtree(Path(wheel_directory) / metadata_dir)

        # Make sure everything is built
        meson('install', '-C', self.builddir.name)
        self.pack_files(config)
        self.wheel_zip.close()
        if not config.get('pure-python-abi'):
            convert_wheel(Path(target_fp))
        return str(target_fp)

    def pack_files(self, config):
        for _, installpath in config.installed.items():
            if "site-packages" in installpath:
                while os.path.basename(installpath) != 'site-packages':
                    installpath = os.path.dirname(installpath)
                self.wheel_zip.write_files(installpath)
                break
            elif "dist-packages" in installpath:
                while os.path.basename(installpath) != 'dist-packages':
                    installpath = os.path.dirname(installpath)
                self.wheel_zip.write_files(installpath)
                break


def build_wheel(
    wheel_directory, config_settings=None, metadata_directory=None
):
    """Builds a wheel, places it in wheel_directory"""
    return WheelBuilder().build(
        Path(wheel_directory), config_settings, metadata_directory
    )


def build_sdist(sdist_directory, config_settings=None):
    """Builds an sdist, places it in sdist_directory"""
    distdir = Path(sdist_directory)
    with tempfile.TemporaryDirectory() as builddir:
        with tempfile.TemporaryDirectory() as installdir:
            meson(
                builddir,
                '--prefix',
                installdir,
                config_settings=config_settings,
                builddir=builddir,
            )

            config = Config(builddir)
            meson('dist', '--no-tests', '-C', builddir)

            tf_dir = '{}-{}'.format(config['module'], config['version'])
            mesondistfilename = '%s.tar.xz' % tf_dir
            mesondisttar = tarfile.open(
                Path(builddir) / 'meson-dist' / mesondistfilename
            )
            for entry in mesondisttar:
                # GOOD: Check that entry is safe
                if os.path.isabs(entry.name) or ".." in entry.name:
                    raise ValueError("Illegal tar archive entry")
                mesondisttar.extract(entry, installdir)
            # OZI uses setuptools_scm to create PKG-INFO
            pkg_info = config.get_metadata()
            distfilename = '{}-{}.tar.gz'.format(config['module'], config['version'])
            target = distdir / distfilename
            source_date_epoch = os.environ.get('SOURCE_DATE_EPOCH', '')
            mtime = int(source_date_epoch) if source_date_epoch else None
            with GzipFile(str(target), mode='wb', mtime=mtime) as gz:
                with cd(installdir):
                    with tarfile.TarFile(
                        str(target),
                        mode='w',
                        fileobj=gz,
                        format=tarfile.PAX_FORMAT,
                    ) as tf:
                        tf.add(tf_dir, recursive=True)
                        pkginfo_path = Path(installdir) / tf_dir / 'PKG-INFO'
                        if not pkginfo_path.exists():
                            with open(pkginfo_path, mode='w') as fpkginfo:
                                fpkginfo.write(pkg_info)
                                fpkginfo.flush()
                                tf.add(Path(tf_dir) / 'PKG-INFO')
    return target.name
