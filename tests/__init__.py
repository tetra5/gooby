#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import logging


path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, path)


# Set default logging handler to avoid "No handler found" warnings.
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass


logging.getLogger("Gooby").addHandler(NullHandler())
