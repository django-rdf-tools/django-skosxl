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
This module can be used in conjunction with the django-rdf-io [https://github.com/rob-metalinkage/django-rdf-io] module to populate an RDF store with the vocabularies. A default mappings is provided, which can be loaded using the 
management API /skosxl/manage/init.

The RDF store (or potentially another helper managed by the rdf_io module) can then perform all the reasoning to fill in all the implied transitive relationships or do other useful work. 

Bulk import of RDF SKOS files is now handled via RDF_IO module, extended by the SKOSXL.ImportedConceptScheme object.  

Some initial visualisation based on the D3 javascript library is embedded.

Authority/registry control
--------------------------

Concept schemes are the basis for delegating authority to manage SKOS assets.  Additional applications with finer-grained control can be added if required.

Concept schemes may be optionally bound to a standard django user Group. Users must have "isStaff" attributes turned on to access the django admin interface provided. Access to Schemes, Concepts, Labels and Collections
is all controlled by these access. 

Concepts have an inbuilt publication review status, (Active, Draft, Duplicate, Dispute, Not classified) which may be linked to a final status via custom RDF-IO mappings.  Alternatively, extensible "Generic Metadata Properties" may be attached to each Concept to provide an explicit status.
At this stage no workflow logic is enforced using these values.

Managing a coherent RDF repository
----------------------------------

Because SKOS vocabularies may be imported from different sources, and attached metadata properties may be extensive, the question arises around coherence of a managed RDF repository. 

The key issue is namespace management - namespaces are URIs - if the same URI exists in multiple sources these need to be consistent with each other.  Namespaces can be registered in the RDF_IO.namespaces module
to bind a preferred prefix - this affects data output - input data may use any prefix, as per the RDF standards.

Generic metadata properties will have CURIE forms (prefix:term) only if a namespace is registered. These can be bulk updated in the admin form by selecting a set of properties in "/admin/rdf_io/genericmetaprop/" and
applying the provided action "update selected metaprops to use CURIEs" - this will match all selected properties to the registered namespaces an update any for which a namespace prefix is available.

Actions on the ConceptScheme allow a selected set of ConceptSchemes to be published to via configured service chains (typically via RDF inferencing stores to target persistence stores).


TODO
----
The user interface is still very crude - better visualisation, browse, search and validation.

Of course - see and contribute to the issues list :-)

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

TODO: generalise this to all the languages supported by Django



License
=======

django-skosxl uses the same license as Django (BSD-like).
