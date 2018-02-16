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
    packages=['skosxl','skosxl.utils'],
    include_package_data=True,
    author='Dominique Guardiola',
    author_email='dguardiola@quinode.fr',
    license='BSD',
    long_description=read('README.rst'),
    #download_url = "https://github.com/quinode/django-skosxl/tarball/%s" % (VERSION),
    #download_url='git://github.com/quinode/django-skosxl.git',
    zip_safe=False,
    install_requires = ['django-taggit>=0.9.3',
                        'SPARQLWrapper>=1.5.0',
                        'django-extensions>=0.7.1',
                        'django-admin-tools>=0.4.1',
                        'django-extended-choices',
                        'django-model-utils,
                        ],
    dependency_links = [
        'https://github.com/flupke/django-taggit-templatetags.git#egg=taggit_templatetags',
        'https://github.com/twidi/django-extended-choices.git#egg=extended_choices',
    ],
)

