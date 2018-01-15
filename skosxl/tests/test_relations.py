from skosxl.models import *
from django.core.files.uploadedfile import SimpleUploadedFile



from django.test import TestCase

PREFIX = """@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix test: <http://example.org/> .
"""

SCHEME1 = """
test:scheme1 a skos:ConceptScheme ;
    rdfs:label "Test concept scheme"@en.
"""

SCHEME2 = """
test:scheme2 a skos:ConceptScheme .
"""

CONCEPT1 = """
test:Concept_defaultlang a skos:Concept ;
    skos:prefLabel "A label in default language" ;
    skos:inScheme test:scheme1 ;
    .

"""

CONCEPT_S2 = """
test:ConceptS2_1 a skos:Concept ;
    skos:prefLabel "A concept in another scheme" ;
    skos:inScheme test:scheme2 ;
    .

"""

CONCEPT2 = """
test:Concept_specificlang a skos:Concept ;
    skos:prefLabel "Incroyable"@fr ;
    skos:inScheme test:scheme1 ;
    .

"""

COLLECTION1 = """
test:Collection1 a skos:Collection ;
    skos:pref_label "Collection with Concept members" ;
    skos:member test:Concept ;
    .
"""

COLLECTION2 = """
test:Collection2 a skos:Collection ;
    skos:pref_label "Collection with Collection member" ;
    skos:member test:Collection1 ;
    .
"""

COLLECTION3 = """
test:Collection3 a skos:Collection ;
    skos:pref_label "Collection with shared Collection members" ;
    skos:member test:Collection1 ;
    .
"""

COLLECTION4 = """
test:Collection4 a skos:Collection ;
    skos:pref_label "Collection with Collection members" ;
    skos:member test:Collection2, test:Collection3 ;
    .
"""

COLLECTION5 = """

test:Collection2 skos:member test:Collection5 .

test:Collection5 a skos:Collection ;
    skos:pref_label "Collection with illegal self reference" ;
    skos:member  test:Collection6 ;
    .
"""

COLLECTION6 = """
test:Collection6 a skos:Collection ;
    skos:pref_label "Collection with illegal self reference" ;
    skos:member test:Collection2, test:Collection5 ;
    .
"""

DAG_TEST = "".join(( PREFIX, SCHEME1, CONCEPT1, CONCEPT2, COLLECTION1, COLLECTION2, COLLECTION3, COLLECTION4))
CYCLE_TEST = "".join(( PREFIX, SCHEME1, CONCEPT1, CONCEPT2, COLLECTION1, COLLECTION2, COLLECTION3, COLLECTION4, COLLECTION5, COLLECTION6))

class CollectionTestCase(TestCase):
    """ Test case for importing a concept scheme """
    
    def setUp(self):
        print "setup in CollectionTestCase"
        pass
        
    def xtest_DAG(self):
        loadtest = ImportedConceptScheme(id=1, resource_type=ImportedConceptScheme.TYPE_INSTANCE, force_bulk_only=False, force_refresh=True)
        loadtest.file = SimpleUploadedFile('test.ttl', DAG_TEST )
        loadtest.save()
        cs = Scheme.objects.get(uri="http://example.org/scheme1")
        cols = cs.getCollectionGraphs()
        print cols
        Scheme.objects.all().delete()
    
    def test_tree_cycle_safe(self):
        #import pdb; pdb.set_trace()
        loadtest = ImportedConceptScheme(id=1, resource_type=ImportedConceptScheme.TYPE_INSTANCE, force_bulk_only=False, force_refresh=True)
        loadtest.file = SimpleUploadedFile('test2.ttl', CYCLE_TEST )
        loadtest.save()
        cs = Scheme.objects.get(uri="http://example.org/scheme1")
        cols = cs.getCollectionGraphs()
        print cols
        Scheme.objects.all().delete()
        