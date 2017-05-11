Django-SKOSXL
===============================================

The W3C SKOS specification allows us to define schemes of related Concepts, and the XL extension to the SKOS RDF vocabulary allow us to specify different labels in different languages, so you can have a "preferred label" for english, for french, and alternative or hidden labels too.

SKOS XL now supports both labels and notations (codes) - with codes having URI based namespaces.

The module allows django based user control over editing, which could be extended to per-vocabulary finer grained control. Terms may be linked within a vocabulary, or to other vocabularies (potentially external) using URI references, using the SKOS relations (broader, narrower, related).

What is django-skosxl good for?
------------------------------------

This module addresses the broad range of needs around controlled vocabularies - whether the control is through loose user interaction (tags) or formal standard vocabularies.

Websites often need to categorize things, but when time comes for agregating all the data and gather them by tags or categories, we often have face the fact that we have differents systems. Term reconciliation is a hard task.

Data translation exercises typically need to translate both schemas and content - for example a country code "AUS" (ISO 3 letters) may need to be translated to "AU" (ISO 2 letter code). SKOS is a standard for describing inter- and intra- vocabulary relationships.

The label management part of this app was originally built around django-taggit, in order to ease end-user input of the labels. The goal is here is to allow free tagging of objects (folksonomy), but then regroup similar terms into common concepts.  This dependency has currently been removed however, pending emergence of a clear standard for hierarchical tag management.

The django admin site allows an administrator to link labels to concepts and model its SKOS concept tree.

Funky extras
-----------
This module can be used in conjunction with the django-rdf-io [https://github.com/rob-metalinkage/django-rdf-io] module to populate an RDF store with the vocabularies. The RDF store can then perform all the reasoning to fill in all the implied transitive relationships or do other useful work.


TODO
----
The user interface is still very crude - better visualisation, browse, search and validation.
Bulk import of RDF SKOS files 

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
