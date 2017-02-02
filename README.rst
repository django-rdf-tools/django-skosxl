Django-SKOSXL
===============================================


What is django-skosxl good for?
------------------------------------
django-coop is a set of several apps to make different websites cooperate. It is based on Django.

Websites often need to categorize things, but when time comes for agregating all the data and gather them by tags or categories, we often have face the fact that we have differents systems. Term reconciliation is a hard task.

The W3C SKOS specification allows us to define schemes of related Concepts, and the XL extension to the SKOS RDF vocabulary allow us to specify different labels in different languages, so you can have a "preferred label" for english, for french, and alternative or hidden labels too.

The goal is here is to allow free tagging of objects (folksonomy), but then regroup similar terms into common concepts. And finally link the concepts between them, using the SKOS relations (broader, narrower, related).

The label management part of this app is built around django-taggit, in order to ease end-user input of the labels.
The django admin site then allows an administrator to link labels to concepts and model its SKOS concept tree.

Settings
^^^^^^^^
Default language
""""""""""""""""

To define the default language to be used for SKOS Concept and Label you can add and specify SKOSXL_DEFAULT_LANG in your project settings.py.
For example:

.. code:: python

    SKOSXL_DEFAULT_LANG = 'fr'

Possible values are:

- 'fr' : French
- 'de': German
- 'en': English
- 'es': Spanish
- 'it': Italian
- 'pt': Portuguese

*Default value is set to English 'en'.*



License
=======

django-skosxl uses the same license as Django (BSD-like).
