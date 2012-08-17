#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Created on 10.07.2012

@author: razor
"""


def camelcase_to_underscore(string):
    """
    Converts CamelCased string to lowercased string with underscores.

    Example: "CamelCase" turns into "camel_case".

    @param string: (string) a string to convert.
    """
    import re

    pattern = "(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))"
    return re.sub(pattern, "_\\1", string).lower().strip("_")
