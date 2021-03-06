#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`utils` --- Utilities
==========================
"""


__docformat__ = "restructuredtext en"

__all__ = ["camelcase_to_underscore", "retry_on_exception",
           "get_current_file_path", ]


import os
import sys
import re
import time


def camelcase_to_underscore(s):
    """
    Converts CamelCased string to lower-cased string with underscores.

    :param s: a CamelCased string to convert
    :type s: `str` or `unicode`

    :return: converted underscored string
    :rtype: `unicode`

    >>> camelcase_to_underscore(u"ThisIsACamelCasedString")
    u'this_is_a_camel_cased_string'
    """

    pattern = ur"(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))"
    return re.sub(pattern, u"_\\1", s).lower().strip(u"_")


class retry_on_exception(object):
    """
    Decorator.

    Retries a function until it stops raising specified exception(s) or reaches
    a certain number of tries.

    :param exception: exception(s) to be risen by decorated function
    :type exception: Exception class or a tuple of Exceptions classes

    :param tries: number of tries
    :type tries: `int`

    :param delay: delay between tries in seconds
    :type delay: `int`

    :param backoff: factor by which the delay should lengthen after each
        failure
    :type backoff: `int`

    Usage:

    >>> # IDE code hinting fix.
    >>> retry_on_exception = retry_on_exception
    >>> # The following useless function will be consecutively called 2 times.
    >>> @retry_on_exception((Exception, IOError), tries=2, delay=0, backoff=0)
    ... def useless_function():
    ...     print "derp"
    ...     raise Exception
    ...
    >>> useless_function()
    derp
    derp
    """

    def __init__(self, exception, tries=10, delay=3, backoff=1):
        self._exception = exception
        self._tries = tries
        self._delay = delay
        self._backoff = backoff

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            mtries, mdelay = self._tries, self._delay
            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except self._exception:
                    time.sleep(self._delay)
                    mtries -= 1
                    mdelay += self._backoff
            return
        return wrapper


def get_current_file_path():
    """
    py2exe / py2app workaround. Returns current file path based on script's
    frozen state, current system platform and encoding.

    :return: current file path
    :rtype: `unicode`
    """

    encoding = sys.getfilesystemencoding()
    frozen = hasattr(sys, "frozen")
    if not frozen:
        return unicode(__file__, encoding)
    if frozen in ("dll", "console_exe", "windows_exe"):
        return unicode(sys.executable, encoding)
    if frozen == "macosx_app":
        return unicode(os.environ["RESOURCEPATH"], encoding)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
