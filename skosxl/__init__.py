# -*- coding: utf-8 -*-

VERSION = (0, 2)

def get_version():
    return '%s.%s' % (VERSION[0], VERSION[1])

__version__ = get_version()