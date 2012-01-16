Django-SKOSXL
===============================================


What is django-skosxl good for?
------------------------------------
django-coop is a set of several apps to make different websites cooperate. It is based on Django.

Websites often need to categorize things, but when time comes for agregating all the data and gather Things by tags or categories, we often face the fact that we have differents systems and that term reconciliation will be a hard task.

The W3C SKOS specification allows us to define Scheme of related Concepts, and the XL extension to this RDF vocabulary allow us to specify different labels in different languages, so you can have a "preferred label" in english, another for french, and alternative or hidden labels for every language too.

The label management part of this app is built around django-taggit, in order to ease end-user input of the labels.
The django admin site then allows an administrator to link labels to concepts and model its SKOS concept tree.


License
=======

coop_bar uses the same license as Django (BSD-like).
