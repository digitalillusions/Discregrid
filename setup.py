import os
import re
import sys
import platform
import subprocess
import argparse

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from distutils.version import LooseVersion

# Extract cmake arguments
parser = argparse.ArgumentParser()
parser.add_argument("-D", action='append', dest='cmake',
                    help="CMake Options")
args, other_args = parser.parse_known_args(sys.argv)
cmake_clargs = args.cmake
sys.argv = other_args

sourcedir = os.path.dirname(os.path.abspath(__file__))

pybind_url = "https://github.com/pybind/pybind11.git"
pybind_ver = "v2.5.0"
pybind_dir = os.path.join(sourcedir, 'pydiscregrid/pybind11')
eigen_url = "https://gitlab.com/libeigen/eigen.git"
eigen_ver = "3.3.7"
eigen_dir = os.path.join(sourcedir, 'pydiscregrid/eigen')

external_modules = {"pybind": {"url": pybind_url, "ver": pybind_ver, "dir": pybind_dir},
                    "eigen": {"url": eigen_url, "ver": eigen_ver, "dir": eigen_dir}}

class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['git', '--version'])
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("CMake and git must be in PATH to build the following extensions: " +
                               ", ".join(e.name for e in self.extensions))

        if platform.system() == "Windows":
            cmake_version = LooseVersion(re.search(r'version\s*([\d.]+)', out.decode()).group(1))
            if cmake_version < '3.1.0':
                raise RuntimeError("CMake >= 3.1.0 is required on Windows")

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        # required for auto-detection of auxiliary "native" libs
        if not extdir.endswith(os.path.sep):
            extdir += os.path.sep

        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
                      '-DPYTHON_EXECUTABLE=' + sys.executable]

        cmake_args += ['-DEIGEN3_INCLUDE_DIR={}'.format(os.path.join(sourcedir, 'pydiscregrid/eigen'))]

        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]

        # Add cmake command line arguments
        if cmake_clargs is not None:
            cmake_args += ['-D{}'.format(arg) for arg in cmake_clargs]

        if platform.system() == "Windows":
            cmake_args += ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), extdir)]
            if sys.maxsize > 2**32:
                cmake_args += ['-A', 'x64']
            build_args += ['--', '/m']
        else:
            cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
            build_args += ['--', '-j4']

        # Add position independent code flags if using gcc on linux probably
        if platform.system() == "Linux":
            cmake_args += ['-DCMAKE_CXX_FLAGS=-fPIC', '-DCMAKE_C_FLAGS=-fPIC']

        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(env.get('CXXFLAGS', ''),
                                                              self.distribution.get_version())
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        # Update submodules if .git folder is present. Otherwise clone them manually
        try:
            subprocess.check_call(['git', 'submodule', 'update', '--init', '--recursive'], cwd=sourcedir)
        except subprocess.CalledProcessError:
            for module in external_modules:
                if len(os.listdir(external_modules[module]["dir"])) > 0:
                    continue
                url, ver, dir = external_modules[module]["url"], external_modules[module]["ver"], external_modules[module]["dir"]
                subprocess.check_call(['git', 'clone', url, '--branch', ver, '--single-branch', dir], cwd=sourcedir)

        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env)
        subprocess.check_call(['cmake', '--build', '.', "--target", "pydiscregrid"] + build_args, cwd=self.build_temp)

setup(
    name='Discregrid',
    version='0.0.1',
    author='Dan Koschier',
    author_email='',
    description='Discregrid is a static C++ library for the parallel discretization of (preferably smooth) functions on regular grids.',
    license="MIT",
    ext_modules=[CMakeExtension('Discregrid')],
    cmdclass=dict(build_ext=CMakeBuild),
    zip_safe=False,
)
