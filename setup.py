#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

VERSION = __import__('skosxl').__version__

import os
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='django-skosxl',
    version = VERSION,
    description='Pluggable django application for managing a SKOS-XL Thesaurus, based on a tag folksonomy',
    packages=['skosxl',],
    include_package_data=True,
    author='Dominique Guardiola',
    author_email='dguardiola@quinode.fr',
    license='BSD',
    long_description=read('README.rst'),
    #download_url = "https://github.com/quinode/django-skosxl/tarball/%s" % (VERSION),
    #download_url='git://github.com/quinode/django-skosxl.git',
    zip_safe=False,
    install_requires = ['django-taggit==0.9.3',
                        'django-livesettings==1.4-7',
                        'sorl-thumbnail==11.09',
                        ],
    dependency_links = [
        'http:://github.com/jonasgeiregat/django-templatetag-sugar.git#egg=templatetag_sugar'
    ],
)

