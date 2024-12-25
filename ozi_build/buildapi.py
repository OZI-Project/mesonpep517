"""PEP-517 compliant buildsystem API"""

import logging
import os
import shutil
import subprocess
import sysconfig
import tarfile
import tempfile
from gzip import GzipFile
from pathlib import Path

from wheel.wheelfile import WheelFile

from ._pyc_wheel import convert_wheel
from ._util import GET_CHECK
from ._util import _write_wheel_file
from ._util import cd
from ._util import install_files_path
from ._util import meson
from ._util import meson_configure
from .config import Config
from .metadata import get_python_bin
from .pep425tags import get_platform_tag

log = logging.getLogger(__name__)


def get_requires_for_build_wheel(config_settings=None):
    """Returns a list of requirements for building, as strings"""
    return Config().get('requires', [])


# For now, we require all dependencies to build either a wheel or an sdist.
get_requires_for_build_sdist = get_requires_for_build_wheel


def check_is_pure(installed):
    variables = sysconfig.get_config_vars()
    suffix = variables.get('EXT_SUFFIX') or variables.get('SO') or variables.get('.so')
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
        '{}-{}.dist-info'.format(config['module'].replace('-', '_'), config['version']),
    )
    dist_info.mkdir(exist_ok=True)

    is_pure = check_is_pure(config.installed)
    with (dist_info / 'WHEEL').open('w') as f:
        _write_wheel_file(f, False, is_pure)

    with (dist_info / 'METADATA').open('w') as f:
        f.write(config.get_metadata())

    for i in config.license_file:
        with (dist_info / i).open('w') as fw:
            with Path(i).open('r') as fr:
                fw.write(fr.read())

    if config.entry_points:
        with (dist_info / 'entry_points.txt').open('w') as f:
            f.write(config.entry_points)

    return dist_info.name


def get_abi(python):
    return subprocess.check_output([python, '-c', GET_CHECK]).decode('utf-8').strip('\n')


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
        config.builddir = self.builddir.name

        metadata_dir = prepare_metadata_for_build_wheel(
            wheel_directory, builddir=self.builddir.name, config=config
        )

        is_pure = check_is_pure(config.installed)
        platform_tag = config.get('platforms', 'any' if is_pure else get_platform_tag())
        python = get_python_bin(config)
        if not is_pure:
            abi = get_abi(python)
        else:
            abi = config.get('pure-python-abi', get_abi(python))
        target_fp = wheel_directory / '{}-{}-{}-{}.whl'.format(
            config['module'].replace('-', '_'),
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
        optimize, *_ = [
            i.get('value', -1)
            for i in config.options
            if i.get('name', '') == 'python.bytecompile'
        ]
        convert_wheel(Path(target_fp), optimize=optimize, **config.pyc_wheel)
        return str(target_fp)

    def pack_files(self, config):
        for _, installpath in config.installed.items():
            if "site-packages" in installpath:
                installpath = install_files_path(installpath, 'site-packages')
                self.wheel_zip.write_files(installpath)
                break
            elif "dist-packages" in installpath:
                installpath = install_files_path(installpath, 'dist-packages')
                self.wheel_zip.write_files(installpath)
                break


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """Builds a wheel, places it in wheel_directory"""
    return WheelBuilder().build(Path(wheel_directory), config_settings, metadata_directory)


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
            mesondisttar = tarfile.open(Path(builddir) / 'meson-dist' / mesondistfilename)
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
