#!/usr/bin/env python
"""
Yaco provides a configuration object that can be saved to disk as a YAML
file. Yaco can be used to store program configuration and make the
configuration data easily accessible. Keys of a Yaco object can be
accessed both as regular dict keys (`a['key']`) or as attributes
(`a.key`). Lower level dictionaries are automatically converted to
Yaco objects allowing similar access (`a.key.subkey`). Lists are
(recursively) parsed and dictionaries in list are converted to Yaco
objects allowing access allong the lines of `a.key[3].subkey`."""

from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys

class Tox(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import tox
        errno = tox.cmdline(self.test_args)
        sys.exit(errno)

DESCRIPTION = "YAML serializable dict like object with attribute style access and implicit branch creation"

setup(name='Yaco',
      version='0.1.23',
      description=DESCRIPTION,
      author='Mark Fiers',
      author_email='mark.fiers42@gmail.com',
      url='https://github.com/mfiers/Yaco',
      include_package_data=True,
      packages=['Yaco'],
      install_requires = ['PyYAML>=3.0'],
      tests_require = ['tox'],
      cmdclass = {'test': Tox},
      classifiers = [
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          ]
     )
