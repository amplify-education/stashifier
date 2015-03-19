"""setup.py controls the build, testing, and distribution of the egg"""

from setuptools import setup, find_packages
import re
import os.path


VERSION_REGEX = re.compile(r"""
    ^__version__\s=\s
    ['"](?P<version>.*?)['"]
""", re.MULTILINE | re.VERBOSE)

VERSION_FILE = os.path.join("stash_client", "version.py")


def get_version():
    """Reads the version from the package"""
    with open(VERSION_FILE) as handle:
        lines = handle.read()
        result = VERSION_REGEX.search(lines)
        if result:
            return result.groupdict()["version"]
        else:
            raise ValueError("Unable to determine __version__")


def get_requirements():
    """Reads the installation requirements from requirements.pip"""
    with open("requirements.pip") as reqfile:
        return filter(lambda line: not line.startswith(('#', '-')), reqfile.read().split("\n"))

setup(name='stash_client',
    version=get_version(),
    description="Stash client library for Amplify utilities.",
    long_description="""\
""",
    # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='',
    author='Ben Warfield',
    author_email='bwarfield@amplify.com',
    url='',
    license='amplify',
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=True,
    dependency_links=[
    ],
    install_requires=get_requirements(),
    test_suite = 'nose.collector',
    entry_points="",
)
