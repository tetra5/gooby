#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`errors` --- Application exceptions collection
===================================================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


class APIError(Exception):
    """
    .. class::`APIError`
    """

    pass


class GoobyError(Exception):
    pass


class PluginOutputError(GoobyError):
    pass


class PluginError(GoobyError):
    pass
