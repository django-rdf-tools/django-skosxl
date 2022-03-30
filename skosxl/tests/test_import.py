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

CONCEPT1A = """
 test:Concept1a owl:sameAs test:Concept ;
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
    skos:prefLabel "Collection with Concept members" ;
    skos:member test:Concept ;
    test:meta1 "string", "string"@en, "string"^^test:datatype,"string2", "string2"@en, "string2"^^test:datatype , 1, 2.3;
    test:meta2  "string", "string"@en ;
    .
"""

COLLECTION1A = """
test:Collection1A owl:sameAs test:Collection1 ;
    .
"""

COLLECTION2 = """
test:Collection2 a skos:Collection ;
    skos:prefLabel "Collection with Collection member" ;
    skos:member test:Collection1 ;
    .
"""


SUITE_TEST = "".join(( PREFIX, SCHEME1, CONCEPT1, CONCEPT2, COLLECTION1))




class SchemeImportTestCase(TestCase):
    """ Test case for importing a concept scheme """
    
    def setUp(self):
        pass
        
    def test_scheme_in_file(self):
        loadtest = ImportedConceptScheme(id=1, resource_type=ImportedConceptScheme.TYPE_INSTANCE, force_bulk_only=False, force_refresh=True)
        loadtest.file = SimpleUploadedFile('test.ttl', "".join( (PREFIX,SCHEME1,CONCEPT1) ))
        loadtest.save()
        cs = Scheme.objects.get(uri="http://example.org/scheme1")
        concepts= list(cs.concept_set.all())
        self.assertEqual(cs.uri,"http://example.org/scheme1")
        self.assertEqual(len(concepts), 1)
        self.assertEqual(concepts[0].pref_label, u'A label in default language')

    def test_scheme_set(self):
        """ tests scheme defined by metadata, file only has concepts """
        loadtest = ImportedConceptScheme(id=1, resource_type=ImportedConceptScheme.TYPE_INSTANCE, force_bulk_only=False, force_refresh=True)
        loadtest.target_scheme = 'http://example.org/scheme1'
        loadtest.file = SimpleUploadedFile('test.ttl', "".join( (PREFIX,CONCEPT1) ))
        loadtest.save()
        cs = Scheme.objects.get(uri="http://example.org/scheme1")
        concepts= list(cs.concept_set.all())
        self.assertEqual(cs.uri,"http://example.org/scheme1")
        self.assertEqual(len(concepts), 1)
        self.assertEqual(concepts[0].pref_label, u'A label in default language')

    def test_scheme_multiple(self):
        """ test loads concept from one of multiple schemes declared in file """
        loadtest = ImportedConceptScheme(id=1, resource_type=ImportedConceptScheme.TYPE_INSTANCE, force_bulk_only=False, force_refresh=True)
        loadtest.target_scheme = 'http://example.org/scheme1'
        loadtest.file = SimpleUploadedFile('test.ttl', "".join( (PREFIX,SCHEME1, SCHEME2, CONCEPT1, CONCEPT_S2) ))
        loadtest.save()
        cs = Scheme.objects.get(uri="http://example.org/scheme1")
        concepts= list(cs.concept_set.all())
       
        self.assertEqual(cs.uri,"http://example.org/scheme1")
        self.assertEqual(len(concepts), 1)
        self.assertEqual(concepts[0].pref_label, u'A label in default language')
        
        
        
class ConceptDetailsTestCase(TestCase):
    """ Loads a complete set of features, then tests each individual one """
    def setUp(self):
        loadtest = ImportedConceptScheme(id=1, resource_type=ImportedConceptScheme.TYPE_INSTANCE, force_bulk_only=False, force_refresh=True)
        loadtest.file = SimpleUploadedFile('test.ttl', SUITE_TEST)
        loadtest.save() 

    def test_preflabel_defaultlang(self):
        """ tests a pref label is set using the default language if lang not specified """
        l = Label.objects.get(concept__term="Concept_defaultlang", label_text="A label in default language")
        self.assertEqual(l.language, DEFAULT_LANG)

    def test_preflabel_specificlang(self):
        """ tests a pref label is set using the default language if lang not specified """
        l = Label.objects.get(concept__term="Concept_specificlang", language="fr")
        self.assertEqual(l.language, "fr")
        
    def test_preflabel_specificlang(self):
        """ tests a pref label is set using the default language if lang not specified """
        l = Label.objects.get(concept__term="Concept_specificlang", language="fr")
        self.assertEqual(l.language, "fr")
        
    def test_metaprops(self):
        
        metaprops = CollectionMeta.objects.filter(subject__uri="http://example.org/Collection1")
        
        self.assertEqual ( len(metaprops.filter(metaprop__uri='http://example.org/meta1')), 8 )
        self.assertEqual ( len(metaprops.filter(metaprop__uri='http://example.org/meta2')), 2 )
       
class SameAsTestCase(TestCase):
    """ Ltests a sameAs generates an extra object of the right type if nothing else declared  """
    def setUp(self):
        loadtest = ImportedConceptScheme(id=1, resource_type=ImportedConceptScheme.TYPE_INSTANCE, force_bulk_only=False, force_refresh=True)
        loadtest.file = SimpleUploadedFile('test.ttl', "".join(( PREFIX, SCHEME1, CONCEPT1, CONCEPT1A, COLLECTION1,  COLLECTION1A )))
        import pdb; pdb.set_trace()
        loadtest.save() 

    def test_collectionSameAs(self):
        """ sameAs for a Collection """  
        owl,created = Namespace.objects.get_or_create(prefix="owl", uri="http://www.w3.org/2002/07/owl#")
        owlSameAs,created = GenericMetaProp.objects.get_or_create(namespace=owl, propname="sameAs")        
        c1 = Collection.objects.get(uri="http://example.org/Collection1")
        try:
            cm1 = CollectionMeta.objects.get(subject=c1, metaprop=owlSameAs ) 
            self.assertEqual(cm1.value, "<http://example.org/Collection1A>")
        except:
            self.assertFalse(True, msg="sameAs not registered as a metadata property of Collection1")
        
        try:
            c1a = Collection.objects.get(uri="http://example.org/Collection1A")
            cm1a = CollectionMeta.objects.get(subject=c1a, metaprop=owlSameAs )
            self.assertEqual(cm1a.value, "<http://example.org/Collection1>")
        except:
            self.assertFalse(True, msg="sameAs not registered as a metadata property of Collection1A" if c1a else "collection1A not registered")    
       