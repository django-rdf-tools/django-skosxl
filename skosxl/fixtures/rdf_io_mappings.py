from __future__ import print_function

from rdf_io.models import Namespace, ObjectType,ObjectMapping,AttributeMapping , ChainedMapping
from django.contrib.contenttypes.models import ContentType
from skosxl.models import Scheme



def loaddata(url_base):
    """
    run loading for module
    """
    load_base_namespaces(url_base)
    load_rdf_mappings(url_base)
    return ( {'skosxl': 'loaded standard namespaces and SKOSXL object mappings'} )
    
def load_base_namespaces(url_base):
    """
        load namespaces for the meta model
    """
    Namespace.objects.get_or_create( uri='http://www.w3.org/1999/02/22-rdf-syntax-ns#', defaults = { 'prefix' : 'rdf' , 'notes': 'RDF' } )
    Namespace.objects.get_or_create( uri='http://www.w3.org/2000/01/rdf-schema#', defaults = { 'prefix' : 'rdfs' , 'notes': 'RDFS' } )
    Namespace.objects.get_or_create( uri='http://www.w3.org/2004/02/skos/core#', defaults = { 'prefix' : 'skos' , 'notes': 'SKOS' } )
    Namespace.objects.get_or_create( uri='http://www.w3.org/2008/05/skos-xl#', defaults = { 'prefix' : 'skosxl' , 'notes': 'SKOSXL' } )
    Namespace.objects.get_or_create( uri='http://xmlns.com/foaf/0.1/', defaults = { 'prefix' : 'foaf' , 'notes': 'FOAF' } )
    Namespace.objects.get_or_create( uri='http://purl.org/dc/terms/', defaults = { 'prefix' : 'dct' , 'notes': 'Dublin Core Terms' } )
    Namespace.objects.get_or_create( uri='http://purl.org/dc/elements/1.1/', defaults = { 'prefix' : 'dc' , 'notes': 'Dublin Core Elements' } ) 
    Namespace.objects.get_or_create( uri='http://www.w3.org/ns/dcat#', defaults = { 'prefix' : 'dcat' , 'notes': 'DCAT' } )
    Namespace.objects.get_or_create( uri='http://www.w3.org/2001/XMLSchema#', defaults = { 'prefix' : 'xsd' , 'notes': 'XSD' } )
    Namespace.objects.get_or_create( uri='http://www.w3.org/2002/07/owl#', defaults = { 'prefix' : 'owl' , 'notes': 'OWL' } )

    print("loading base namespaces for SKOSXL")
    
def load_urirules(url_base) :
    """
        Load uriredirect rules for these object types.
    """
    pass

def load_rdf_mappings(url_base):
    """
        load RDF mappings for SKOS XL Objects
    """
    
    (object_type,created) = ObjectType.objects.get_or_create(uri="skos:ConceptScheme", defaults = { "label" : "SKOS ConceptScheme" })

    sm = ObjectMapping.new_mapping(object_type, "skosxl:Scheme", "skosxl: SKOS ConceptScheme", "uri", "uri" , auto_push=True)
    # specific mapping
    am = AttributeMapping(scope=sm, attr="definition", predicate="skos:definition", is_resource=False).save()
    am = AttributeMapping(scope=sm, attr="pref_label", predicate="skos:prefLabel", is_resource=False).save()
    am = AttributeMapping(scope=sm, attr="metaprops.value", predicate=":metaprops.metaprop", is_resource=False).save()
    am = AttributeMapping(scope=sm, attr="changenote", predicate="skos:changeNote", is_resource=False).save()
     
    (object_type,created) = ObjectType.objects.get_or_create(uri="skos:Collection", defaults = { "label" : "SKOS Collection" })
    pm = ObjectMapping.new_mapping(object_type, "skosxl:Collection", "skosxl: SKOS Collection", "uri", "uri" , auto_push=True)
    # specific mapping
    am = AttributeMapping(scope=pm, attr="pref_label", predicate="skos:prefLabel", is_resource=False).save()
    am = AttributeMapping(scope=pm, attr="metaprops.value", predicate=":metaprops.metaprop", is_resource=False).save()
    am = AttributeMapping(scope=pm, attr="collectionmember.concept.uri", predicate="skos:member", is_resource=True).save()
    am = AttributeMapping(scope=pm, attr="collectionmember.subcollection.uri", predicate="skos:member", is_resource=True).save()
    
    # chain collection mapping to ConceptScheme parent
    cm = ChainedMapping(scope=sm,attr="collection",predicate="rdfs:seeAlso", chainedMapping= pm ).save()
    
    (object_type,created) = ObjectType.objects.get_or_create(uri="skos:Concept", defaults = { "label" : "SKOS Concept" })
    pm = ObjectMapping.new_mapping(object_type, "skosxl:Concept", "skosxl: SKOS Concept", "uri", "uri" )
    am = AttributeMapping(scope=pm, attr="definition", predicate="skos:definition", is_resource=False).save()
    am = AttributeMapping(scope=pm, attr="scheme.uri", predicate="skos:inScheme", is_resource=True).save()    
    #labels
    am = AttributeMapping(scope=pm, attr="labels[label_type=0].label_text@language", predicate="skos:prefLabel", is_resource=False).save()
    am = AttributeMapping(scope=pm, attr="labels[label_type=1].label_text@language", predicate="skos:altLabel", is_resource=False).save()
    am = AttributeMapping(scope=pm, attr="notations.code^^codetype", predicate="skos:notation", is_resource=False).save()
    
    # semantic relations
    am = AttributeMapping(scope=pm, attr="semrelation(origin_concept)[rel_type='1'].target_concept.uri", predicate="skos:narrower", is_resource=True).save()
    am = AttributeMapping(scope=pm, attr="semrelation(origin_concept)[rel_type='0'].target_concept.uri", predicate="skos:broader", is_resource=True).save()
    am = AttributeMapping(scope=pm, attr="maprelation(origin_concept)[match_type='1'].uri", predicate="skos:closeMatch", is_resource=True).save()
    am = AttributeMapping(scope=pm, attr="maprelation(origin_concept)[match_type='0'].uri", predicate="skos:exactMatch", is_resource=True).save()
    am = AttributeMapping(scope=pm, attr="maprelation(origin_concept)[match_type='2'].uri", predicate="skos:broadMatch", is_resource=True).save()
    am = AttributeMapping(scope=pm, attr="maprelation(origin_concept)[match_type='3'].uri", predicate="skos:narrowMatch", is_resource=True).save()
    am = AttributeMapping(scope=pm, attr="maprelation(origin_concept)[match_type='4'].uri", predicate="skos:relatedMatch", is_resource=True).save()
    am = AttributeMapping(scope=pm, attr="metaprops.value", predicate=":metaprops.metaprop", is_resource=False).save()
    am = AttributeMapping(scope=pm, attr="supersedes.uri", predicate="policy:supersedes", is_resource=True).save()
    
#    chain concept mapping to ConceptScheme parent
    cm = ChainedMapping(scope=sm,attr="concept",predicate="rdfs:seeAlso", chainedMapping= pm ).save()
    
    pm = ObjectMapping.new_mapping(object_type, "skosxl:Concept", "skosxl: skos:Concept - add topConcepts to Scheme" ,"uri", "uri" ,filter="top_concept=True")
    am = AttributeMapping(scope=pm, attr="scheme.uri", predicate="skos:topConceptOf",   is_resource=True).save()
 #    chain topconcept mapping to ConceptScheme parent
    cm = ChainedMapping(scope=sm,attr="concept",predicate="rdfs:seeAlso", chainedMapping= pm ).save()
    


