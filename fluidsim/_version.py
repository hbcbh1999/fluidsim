"""
Module where the version is written.

It is executed in setup.py and imported in fluidsim/__init__.py.

See:

http://en.wikipedia.org/wiki/Software_versioning
http://legacy.python.org/dev/peps/pep-0386/

'a' or 'alpha' means alpha version (internal testing),
'b' or 'beta' means beta version (external testing).

PEP 440 also permits the use of local version identifiers. This is initialized
using the setuptools_scm module, if available.

See:
https://www.python.org/dev/peps/pep-0440/#local-version-identifiers
https://github.com/pypa/setuptools_scm#setuptools_scm

"""

__version__ = "0.3.2"

__all__ = ["__version__", "get_local_version", "__about__"]

try:
    from pyfiglet import figlet_format

    __about__ = figlet_format("fluidsim", font="big")
except ImportError:
    __about__ = r"""
  __ _       _     _     _
 / _| |     (_)   | |   (_)
| |_| |_   _ _  __| |___ _ _ __ ___
|  _| | | | | |/ _` / __| | '_ ` _ \
| | | | |_| | | (_| \__ \ | | | | | |
|_| |_|\__,_|_|\__,_|___/_|_| |_| |_|
"""

__about__ = __about__.rstrip() + f"\n\n{28 * ' '} v. {__version__}\n"

_loc_version = None


def get_local_version():
    """Get a long "local" version."""

    global _loc_version

    if _loc_version is None:
        from setuptools_scm import get_version

        try:
            _loc_version = get_version(root="..", relative_to=__file__)
        except (LookupError, AssertionError):
            _loc_version = __version__

    return _loc_version
