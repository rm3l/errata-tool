import os
import re
import subprocess
import sys
from setuptools.command.test import test as TestCommand
from setuptools import Command
try:
    # Python 2 backwards compat
    from __builtin__ import raw_input as input
except ImportError:
    pass

readme = os.path.join(os.path.dirname(__file__), 'README.rst')
LONG_DESCRIPTION = open(readme).read()


def read_module_contents():
    with open('errata_tool/__init__.py') as app_init:
        return app_init.read()


def read_spec_contents():
    with open('python-errata-tool.spec') as spec:
        return spec.read()

module_file = read_module_contents()
metadata = dict(re.findall("__([a-z]+)__\s*=\s*'([^']+)'", module_file))
version = metadata['version']


class BumpCommand(Command):
    """ Bump the __version__ number and commit all changes. """

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        version = metadata['version'].split('.')
        version[-1] = str(int(version[-1]) + 1)  # Bump the final part

        print('old version: %s  new version: %s' %
              (metadata['version'], '.'.join(version)))
        try:
            input('Press enter to confirm, or ctrl-c to exit >')
        except KeyboardInterrupt:
            raise SystemExit("\nNot proceeding")

        old = "__version__ = '%s'" % metadata['version']
        new = "__version__ = '%s'" % '.'.join(version)
        module_file = read_module_contents()
        with open('errata_tool/__init__.py', 'w') as fileh:
            fileh.write(module_file.replace(old, new))

        old = 'Version:        %s' % metadata['version']
        new = 'Version:        %s' % '.'.join(version)
        spec_file = read_spec_contents()
        with open('python-errata-tool.spec', 'w') as fileh:
            fileh.write(spec_file.replace(old, new))

        # Commit everything with a standard commit message
        cmd = ['git', 'commit', '-a', '-m', 'version %s' % '.'.join(version)]
        print(' '.join(cmd))
        subprocess.check_call(cmd)


class ReleaseCommand(Command):
    """ Tag and push a new release. """

    user_options = [('sign', 's', 'GPG-sign the Git tag and release files')]

    def initialize_options(self):
        self.sign = False

    def finalize_options(self):
        pass

    def run(self):
        # Create Git tag
        tag_name = 'v%s' % version
        cmd = ['git', 'tag', '-a', tag_name, '-m', 'version %s' % version]
        if self.sign:
            cmd.append('-s')
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        # Push Git tag to origin remote
        cmd = ['git', 'push', 'origin', tag_name]
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        # Push package to pypi
        # cmd = ['python', 'setup.py', 'sdist', 'upload']
        # if self.sign:
        #    cmd.append('--sign')
        # print(' '.join(cmd))
        # subprocess.check_call(cmd)


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main('errata_tool --flake8 ' + self.pytest_args)
        sys.exit(errno)


from setuptools import setup

setup(
    name='errata-tool',
    description='Python API for Red Hat Errata Tool',
    packages=['errata_tool'],
    author='Ken Dreyer',
    author_email='kdreyer [at] redhat.com',
    url='https://github.com/ktdreyer/errata-tool',
    version=metadata['version'],
    license='MIT',
    zip_safe=False,
    keywords='packaging, build',
    long_description=LONG_DESCRIPTION,
    install_requires=[
        'jsonpath_rw',
        'requests',
        'urllib3',
        'requests_kerberos',
    ],
    tests_require=[
        'pytest',
        'pytest-flake8',
        'httpretty',
    ],
    cmdclass={'test': PyTest, 'bump': BumpCommand, 'release': ReleaseCommand},
)