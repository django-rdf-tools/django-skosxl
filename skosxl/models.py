# -*- coding:utf-8 -*-

# Modified from original unmaintained example as part of the django.coop eco-system
# Based on SKOS an SKOS-XL ontologies
# http://www.w3.org/2004/02/skos/core
# http://www.w3.org/2008/05/skos-xl
# 
# now synced with a configurable RDF mapping and export module django-rdf-io

from django.db import models
from django_extensions.db import fields as exfields
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_lazy
from extended_choices import Choices
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
# update this to use customisable setting
# from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save

from django.contrib.contenttypes.models import ContentType
        
#from taggit.models import TagBase, GenericTaggedItemBase
#from taggit.managers import TaggableManager
from rdf_io.models import Namespace, GenericMetaProp, ImportedResource, CURIE_Field
from rdflib import Graph,namespace
from rdflib.term import URIRef, Literal

import json

rdftype=URIRef(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
concept=URIRef(u'http://www.w3.org/2004/02/skos/core#Concept')
scheme=URIRef(u'http://www.w3.org/2004/02/skos/core#ConceptScheme')
collection=URIRef(u'http://www.w3.org/2004/02/skos/core#Collection')

PLACEHOLDER = '< no label >'

LABEL_TYPES = Choices(
    ('prefLabel',    0,  _(u'preferred')),
    ('altLabel',     1, _(u'alternative')),
    ('hiddenLabel',  2,  _(u'hidden')),
)

REL_TYPES = Choices(
    # ('broaderTransitive',   0,  u'Has a broader (transitive) concept'),
    # ('narrowerTransitive',  1,  u'Has a narrower (transitive) concept'),
    ('broader',             0,  _(u'has a broader concept')),
    ('narrower',            1,  _(u'has a narrower concept')),
    ('related',             2,  _(u'has a related concept')),    
)

reverse_map = {   
    # REL_TYPES.narrowerTransitive    : REL_TYPES.broaderTransitive,
    # REL_TYPES.broaderTransitive     : REL_TYPES.narrowerTransitive,
    REL_TYPES.narrower              : REL_TYPES.broader,
    REL_TYPES.broader               : REL_TYPES.narrower,
    REL_TYPES.related               : REL_TYPES.related
}

MATCH_TYPES = Choices(
    ('exactMatch',   0,  _(u'matches exactly')),
    ('closeMatch',   1,  _(u'matches closely')),
    ('broadMatch',   2,  _(u'has a broader match')),
    ('narrowMatch',  3,  _(u'has a narrower match')),
    ('relatedMatch', 4,  _(u'has a related match')),    
)

# TODO - allow these to be defined by the environment - or extended as needed.
LANG_LABELS = (
    ('fr',_(u'French')),
    ('de',_(u'German')),
    ('en',_(u'English')),
    ('es',_(u'Spanish')),
    ('it',_(u'Italian')),
    ('pt',_(u'Portuguese'))
)

DEFAULT_LANG = getattr(settings, 'SKOSXL_DEFAULT_LANG', 'en')

REVIEW_STATUS = Choices(
    ('active',  0,  _(u'Active')),
    ('draft',   1,  _(u'Draft')),
    ('doubled', 2,  _(u'Double')),
    ('dispute', 3,  _(u'Dispute')),
    ('todo',    4,  _(u'Not classified')),
)

DEFAULT_SCHEME_SLUG = 'general'

    
class SchemeManager(models.Manager):
    def get_by_natural_key(self, uri):
        return self.get( uri = uri)

class Scheme(models.Model):
    objects = SchemeManager()
    
    pref_label  = models.CharField(_(u'label'),blank=True,max_length=255)#should just be called label
    slug        = exfields.AutoSlugField(populate_from=('pref_label'))
    # URI doesnt need to be a registered Namespace unless you want to use prefix:term expansion for it
    uri         = models.CharField(blank=True,max_length=250,verbose_name=_(u'main URI'),editable=True)   
    created     = exfields.CreationDateTimeField(_(u'created'),null=True)
    modified    = exfields.ModificationDateTimeField(_(u'modified'),null=True)
    definition  = models.TextField(_(u'definition'), blank=True)
    meta  = models.TextField(_(u'additional metadata'), help_text=_(u'(<predicate> <object> ; list) '), blank=True)
    def __unicode__(self):
        return self.pref_label
        
           
    def natural_key(self):
        return( self.uri )
        
    def get_absolute_url(self):
        return reverse('scheme_detail', args=[self.slug])
    def tree(self):
        tree = (self, [])  # result is a tuple(scheme,[child concepts])
        for concept in Concept.objects.filter(scheme=self,top_concept=True):
            tree[1].append((concept,concept.get_narrower_concepts())) 
            #with nested tuple(concept, [child concepts])
        return tree 
    def test_tree(self):
        i = self.tree()
        print i[0]
        for j in i[1]:
            print u'--' +unicode(j[0])
            for k in j[1]:
                print u'----' + unicode(k[0])
                for l in k[1]:
                    print u'------' + unicode(l[0])
                    for m in l[1]:
                        print u'--------' + unicode(m[0])         
   
                        for idx, val in enumerate(ints):
                            print idx, val
   
    # needs fixing - has limited depth of traversal - probably want an option to paginate and limit.
    def json_tree(self,admin_url=False):
        i = self.tree()
        prefix = '/admin' if admin_url else ''
        ja_tree = {'name' : i[0].pref_label, 'children' : []}
        for jdx, j in enumerate(i[1]):#j[0] is a concept, j[1] a list of child concepts
            ja_tree['children'].append({'name':j[0].pref_label,
                                        'url':prefix+'/skosxl/concept/'+str(j[0].id)+'/',
                                        'children':[]})
            for kdx, k in enumerate(j[1]):
                ja_tree['children'][jdx]['children'].append({'name':k[0].pref_label,
                                            'url':prefix+'/skosxl/concept/'+str(k[0].id)+'/',
                                            'children':[]})
                for ldx,l in enumerate(k[1]):
                    ja_tree['children'][jdx]['children'][kdx]['children'].append({'name':l[0].pref_label,
                                                'url':prefix+'/skosxl/concept/'+str(l[0].id)+'/',
                                                'children':[]})
                    for mdx, m in enumerate(l[1]):
                        ja_tree['children'][jdx]['children'][kdx]['children'][ldx]['children'].append({'name':m[0].pref_label,
                                                    'url':prefix+'/skosxl/concept/'+str(m[0].id)+'/',
                                                    #'children':[] #stop
                                                    })
        return json.dumps(ja_tree, sort_keys=True,
                          indent=4, separators=(',', ': '))

class SchemeMeta(models.Model):
    """
        extensible metadata using rdf_io managed reusable generic metadata properties
    """
    scheme      = models.ForeignKey(Scheme) 
    metaprop   =  models.ForeignKey(GenericMetaProp) 
    value = models.CharField(_(u'value'),max_length=500)
    
class ConceptManager(models.Manager):
    def get_by_natural_key(self, uri):
        return self.get( uri = uri)
        
class Concept(models.Model):
    objects = ConceptManager()
    # this will be the 
    term = models.CharField(_(u'term'),help_text=_(u'Required - must be valid SKOS term - ie. a URL-friendly QNAME - TODO include validation for this.'),blank=True,null=True,max_length=255)
    # not sure we will need this - SKOS names should enforce slug compatibility.
    slug        = exfields.AutoSlugField(populate_from=('term'))
    pref_label = models.CharField(_(u'preferred label'),blank=True,null=True,help_text=_(u'Will be automatically set to the preferred label in the default language - which will be automatically created using this field only if not present'),max_length=255)

    
    definition  = models.TextField(_(u'definition'), blank=True)
#    notation    = models.CharField(blank=True, null=True, max_length=100)
    scheme      = models.ForeignKey(Scheme, blank=True, null=True, help_text=_(u'Note - currently only membership of a single scheme supported'))
    changenote  = models.TextField(_(u'change note'),blank=True)
    created     = exfields.CreationDateTimeField(_(u'created'))
    modified    = exfields.ModificationDateTimeField(_(u'modified'))
    status      = models.PositiveSmallIntegerField( _(u'review status'),
                                                    choices=REVIEW_STATUS, 
                                                    default=REVIEW_STATUS.active)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,blank=True,null=True,verbose_name=_(u'django user'),editable=False)
    uri         = models.CharField(blank=True,max_length=250,verbose_name=_(u'main URI'),editable=True, help_text=_(u'Leave blank to inherit namespace from containing scheme'))    
    author_uri  = models.CharField(blank=True,max_length=250,verbose_name=_(u'main URI'),editable=False)    

    top_concept = models.BooleanField(default=False, verbose_name=_(u'is top concept'))
    sem_relations = models.ManyToManyField( "self",symmetrical=False,
                                            through='SemRelation',
                                            verbose_name=(_(u'Semantic relations')),
                                            help_text=_(u'SKOS semantic relations are links between SKOS concepts, where the link is inherent in the meaning of the linked concepts.'))
    # map_relations = models.OneToManyField( "self",symmetrical=False,
                                            # through='MapRelation',
                                            # verbose_name=(_(u'semantic relations'))
                                            # ,
                                            # help_text=_(u'These properties are used to state mapping (alignment) links between SKOS concepts in different concept schemes'))
                                            
    def __unicode__(self):
        return "".join((self.term, "(", self.uri , ")" ))
    
    def natural_key(self):
        return ( self.uri )
#    natural_key.dependencies = ['scheme']
    

    def get_absolute_url(self):
        """
            URL of the representation document generated by Django - note this is not the same as the uri based on a term within a scheme
        """
        return reverse('concept_detail', args=[self.id])
        
    def save(self,skip_name_lookup=False, *args, **kwargs):
        if self.scheme is None:
            self.scheme = Scheme.objects.get(slug=DEFAULT_SCHEME_SLUG)
        if not self.term :
            if not self.uri:
                raise ValidationError("Term or URI must be present")
            try: 
                term=self.uri[ self.uri.rindex('#')+1:]
            except :
                term=self.uri[ self.uri.rindex('/')+1:]
            self.term=term

        if not skip_name_lookup: #updating the pref_label
            try:
                lookup_label = self.labels.get(language=DEFAULT_LANG,label_type=LABEL_TYPES.prefLabel)
                label = lookup_label.label_text
            except Label.DoesNotExist:
                if not self.pref_label  or self.pref_label == PLACEHOLDER :
                    label =  PLACEHOLDER
                else:
                    label = self.pref_label
            self.pref_label = label
            #self.save(skip_name_lookup=True)
        if not self.uri:
            if self.scheme.uri[:-1] in ('#','/') :
                sep = self.scheme.uri[:-1]
            else:
                sep = '/'
            print "sep",sep,"suri",self.scheme.uri
            self.uri = sep.join((self.scheme.uri,self.term))
        super(Concept, self).save(*args, **kwargs) 
        #now its safe to  add new label to the concept for the prefLabel
        if self.pref_label and not self.pref_label == PLACEHOLDER:
            try:
                lookup_label = self.labels.get(language=DEFAULT_LANG,label_type=LABEL_TYPES.prefLabel)
            except Label.DoesNotExist:
                Label.objects.create(concept=self,language=DEFAULT_LANG,label_type=LABEL_TYPES.prefLabel,label_text=self.pref_label)
                    
        
    def get_narrower_concepts(self):
        childs = []
        if SemRelation.objects.filter(origin_concept=self,rel_type=1).exists():
            for narrower in SemRelation.objects.filter(origin_concept=self,rel_type=1):
                childs.append(( narrower.target_concept,
                                narrower.target_concept.get_narrower_concepts()
                                ))
        return childs
        
    def get_related_term(self, ns) :
        """
            dumb - just finds first related term - assumes a 1:1 skos:closeMatch semantics
        """
        mr = MapRelation.objects.filter(origin_concept = self, uri__startswith = ns )
        if mr :
            return(mr[0].uri[mr[0].uri.rfind('/')+1:])
        return None
    
    class Meta :
        unique_together = (('scheme', 'term'),)

class Notation(models.Model):
    concept     = models.ForeignKey(Concept,blank=True,null=True,verbose_name=_(u'main concept'),related_name='notations')
    code =  models.CharField(_(u'notation'),max_length=10, null=False)
    codetype = CURIE_Field(max_length=200,verbose_name=_(u'(datatype)'),default='xsd:string')
    def __unicode__(self):
        return self.code + '^^<' + self.codetype + '>'  
    
    def clean(self):
        # TODO check prefix
        pass
        
    def save(self, *args, **kwargs):
        self.concept.save()                
        super(Notation, self).save()
        
    class Meta: 
        verbose_name = _(u'SKOS notation')
        verbose_name_plural = _(u'notations')

    
class Label(models.Model):
    '''
    Defines a SKOS-XL Label Class, and also a Tag in django-taggit
    '''
    # FIELDS name and slug are defined in TagBase  - they are forced to be unique
    # so if a concept is to be made available as a tag then it must conform to this constraint - generating a label without a Concept implies its is a tag generation - and name will be forced to be unique.
    concept     = models.ForeignKey(Concept,blank=True,null=True,verbose_name=_(u'main concept'),related_name='labels')
    label_type  = models.PositiveSmallIntegerField(_(u'label type'), choices=tuple(LABEL_TYPES), default= LABEL_TYPES.prefLabel)
    label_text  = models.CharField(_(u'label text'),max_length=100, null=False)
    language    = models.CharField(_(u'language'),max_length=10, default=DEFAULT_LANG)
 
    #metadata
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,blank=True,null=True,verbose_name=_(u'django user'),editable=False)
    uri         = models.CharField(_(u'author URI'),blank=True,max_length=250,editable=True)    
    author_uri  = models.CharField(u'main URI',blank=True,max_length=250,editable=True)    
    created     = exfields.CreationDateTimeField(_(u'created'))
    modified    = exfields.ModificationDateTimeField(_(u'modified'))
    
    
    def get_absolute_url(self):
        return reverse('tag_detail', args=[self.slug])
    def __unicode__(self):
         return unicode(self.label_text)
    def create_concept_from_label(self):
        if not self.concept:
            # self.label_text = self.name
            c = Concept(pref_label=self.__unicode__(),
                        changenote=unicode(ugettext_lazy(u'Created from tag "')+self.__unicode__()+u'"'))
            c.save(skip_name_lookup=True)# because we just set it
            self.concept = c
            self.save()
            
    def save(self, *args, **kwargs):
#        if not self.name :
#            self.name = self.label_text
#        import pdb; pdb.set_trace()
        concept_saved = False
        if self.label_type == LABEL_TYPES.prefLabel:
            Label.objects.filter(concept=self.concept, label_type=LABEL_TYPES.prefLabel,language=self.language).delete()
#            if Label.objects.exclude(id=self.id).filter( concept=self.concept,
#                                             label_type=LABEL_TYPES.prefLabel,
#                                             language=self.language
#                                             ).exists():
#                raise ValidationError(_(u'There can be only one preferred label by language'))

         
        super(Label, self).save()
        # have to update concept's prefLabel to match _after_ label is save - otherwise it gets overwritten
        if self.label_type == LABEL_TYPES.prefLabel and self.language == DEFAULT_LANG:
            if self.concept.pref_label != self.label_text :
                self.concept.pref_label = self.label_text
                self.concept.save()
                concept_saved = True
        if not concept_saved :
            post_save.send(Concept, instance=self.concept, created=False) 
            
#class LabelledItem(GenericTaggedItemBase):
#    tag = models.ForeignKey(Label, related_name="skosxl_label_items")

 
def create_reverse_relation(concept,rel_type):
    print 'creating inverse relation'
    new_rel = SemRelation(  origin_concept=concept.target_concept, 
                            target_concept=concept.origin_concept,
                            rel_type=rel_type)
    new_rel.save(skip_inf=True)                        


class SemRelation(models.Model):
    '''
    A model linking two skos:Concept
    Defines a sub-property of skos:semanticRelation property from the origin concept to the target concept
    '''
    origin_concept = models.ForeignKey(Concept,related_name='rel_origin',verbose_name=(_(u'Origin')))
    target_concept = models.ForeignKey(Concept,related_name='rel_target',verbose_name=(_(u'Target')))
    rel_type = models.PositiveSmallIntegerField( _(u'Type of semantic relation'),choices=REL_TYPES, 
                                                    default=REL_TYPES.narrower)

    #    rel_type = models.ForeignKey(RelationType, related_name='curl', verbose_name=_(u'Type of semantic relation'))
    class Meta: 
        verbose_name = _(u'Semantic relation')
        verbose_name_plural = _(u'Semantic relations')

    def save(self,skip_inf=False, *args, **kwargs):
        if not skip_inf:
            if self.rel_type in reverse_map :
                create_reverse_relation(self,reverse_map[self.rel_type])
                
        super(SemRelation, self).save(*args, **kwargs)
    

# 
# class Vocabulary(models.Model):
#     '''
#     A remote SKOS Thesaurus
#     '''
#     name = models.CharField(_(u'Name'),max_length=100)
#     info_url = models.URLField(_(u'URL'),blank=True, verify_exists=False)
#     class Meta: 
#         verbose_name = _(u'SKOS Thesaurus')
#         verbose_name_plural = _(u'SKOS Thesaurii')
#     def __unicode__(self):
#         return self.name
#         
class MapRelation(models.Model):

    origin_concept = models.ForeignKey(Concept,related_name='map_origin',verbose_name=(_(u'Local concept to map')))
#     target_concept = models.ForeignKey(Concept,related_name='map_target',verbose_name=(_(u'Remote concept')),blank=True, null=True)
#     target_label = models.CharField(_(u'Preferred label'),max_length=255)#nan nan il faut un autre concept stocké dans un scheme
    uri = models.CharField(_(u'Target Concept URI'), max_length=250)
#     voc = models.ForeignKey(Vocabulary, verbose_name=(_(u'SKOS Thesaurus')))
    match_type = models.PositiveSmallIntegerField( _(u'Type of mapping relation'),
                                                     choices=MATCH_TYPES, 
                                                     default=MATCH_TYPES.closeMatch)
    class Meta: 
        verbose_name = _(u'Mapping relation')
        verbose_name_plural = _(u'Mapping relations')

#     

class ImportedConceptScheme(ImportedResource):

    target_scheme = models.URLField(blank=True, verbose_name=(_(u'target scheme - leave blank to use default defined in resource')))
    force_refresh = models.BooleanField(default=False, verbose_name=(_(u'force purge of target concept scheme')), help_text='Allows for incremental load of a single concept scheme from multiple files - e.g. collections')
    
    def save(self,*args,**kwargs):  
        # save first - to make file available
        self.repo = None
        super(ImportedConceptScheme, self).save(*args,**kwargs)
        self.importScheme(self.get_graph(),self.target_scheme, self.force_refresh)
                
    class Meta: 
        verbose_name = _(u'ImportedConceptScheme')
        verbose_name_plural = _(u'ImportedConceptScheme')

    def importScheme(self,gr, target_scheme, force_refresh):
        """ Import a concept scheme from a parsed RDF graph 
        
        Uses generic RDF graph management to avoid having to do consistency checks and resource management here.
        Will generate the target ConceptScheme if not present.
        Push to triple store is via the post_save triggers and RDF_IO mappings if defined.
        """
        if not gr:
            raise Exception ( _(u'No RDF graph available for resource'))
        
        target_map_scheme = {
            URIRef(u'http://www.w3.org/2004/02/skos/core#prefLabel'): { 'text_field': 'pref_label'} ,
            URIRef(u'http://www.w3.org/2000/01/rdf-schema#label'): { 'text_field': 'pref_label'} ,
            URIRef(u'http://purl.org/dc/elements/1.1/description'): { 'text_field': 'definition'} ,
#@prefix dcterms: <http://purl.org/dc/terms/> .
            URIRef(u'http://www.w3.org/2004/02/skos/core#hasTopConcept'): {'ignore': True} ,
            }
        target_map_concept = {
            URIRef(u'http://www.w3.org/2000/01/rdf-schema#label'): { 'text_field': 'pref_label'} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#definition'): { 'text_field': 'definition'} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#topConceptOf'): { 'bool_field': 'top_concept'} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#prefLabel'): {'related_object':'Label', 'related_field': 'concept', 'text_field': 'label_text', 'lang_field':'language', 'set_fields': (('label_type',0),)} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#altLabel'): {'related_object':'Label', 'related_field': 'concept', 'text_field': 'label_text', 'lang_field':'language', 'set_fields': (('label_type',1),)} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#hiddenLabel'): {'related_object':'Label', 'related_field': 'concept', 'text_field': 'label_text', 'lang_field':'language', 'set_fields': (('label_type',2),)} , 
            URIRef(u'http://www.w3.org/2004/02/skos/core#notation'): {'related_object':'Notation', 'related_field': 'concept', 'text_field': 'code', 'datatype_field':'codetype'} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#broader'): {'related_object':'SemRelation', 'related_field': 'origin_concept', 'object_field': 'target_concept', 'set_fields': (('rel_type',REL_TYPES.broader),)} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#narrower'): {'related_object':'SemRelation', 'related_field': 'origin_concept', 'object_field': 'target_concept', 'set_fields': (('rel_type',REL_TYPES.narrower),)} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#related'): {'related_object':'SemRelation', 'related_field': 'origin_concept', 'object_field': 'target_concept', 'set_fields': (('rel_type',REL_TYPES.related),)} ,
            URIRef(u'http://www.w3.org/2002/07/owl#sameAs'): {'related_object':'MapRelation', 'related_field': 'origin_concept', 'text_field': 'uri', 'set_fields': (('match_type',0),)} ,
            URIRef(u'http://www.w3.org/2004/02/skos/exactMatch#'): {'related_object':'MapRelation', 'related_field': 'origin_concept', 'text_field': 'uri', 'set_fields': (('match_type',0),)} ,              }
        import pdb; pdb.set_trace()
 
        
        if not target_scheme:
           for conceptscheme in gr.subjects(predicate=rdftype, object=scheme) :
                if target_scheme :
                    raise Exception('Multiple concept schemes found in source document - specify target first')
                target_scheme = str(conceptscheme)
                s = conceptscheme
        else:
            s = URIRef(target_scheme)
            
        if force_refresh :
            Scheme.objects.filter(uri=target_scheme).delete()

        (scheme_obj,new) = Scheme.objects.get_or_create(uri=target_scheme)
        related_objects = _set_object_properties(gr=gr,uri=s,obj=scheme_obj,target_map=target_map_scheme)
        scheme_obj.save()
        # now process any related objects
        
        for c in gr.subjects(predicate=rdftype, object=concept):
            url = str(c)
            try: 
                term=url[ url.rindex('#')+1:]
            except :
                term=url[ url.rindex('/')+1:]
            (concept_obj,new) = Concept.objects.get_or_create(scheme=scheme_obj, uri=str(c), term=term)
            related_objects = _set_object_properties(gr=gr,uri=c,obj=concept_obj,target_map=target_map_concept)
            concept_obj.save()
            _set_relatedobject_properties(gr=gr,uri=c,obj=concept_obj,target_map=target_map_concept,related_objects=related_objects)
            
def _set_object_properties(gr,uri,obj,target_map) :       
        # loop over scheme properties and set
        related_objects = ()
        for (p,o) in gr.predicate_objects(subject=uri) :
            # get mapped properties
            prop = target_map.get(p)
            if prop:
                if prop.get('ignore') :
                    # print "suppressing %s"% p
                    continue
                actual_obj = obj #default
                obj_type_name = prop.get('related_object')
                if obj_type_name:
                    related_objects += ( (p,o,obj_type_name),)
                elif prop.get('bool_field'):
                    setattr(obj,prop['bool_field'],True)
                else:
                    setattr(obj,prop['text_field'],unicode(o))
                    print "setting ",prop['text_field'],unicode(o)
            else:
                # print 'General meta %s ' % p
                continue                
        return related_objects
        
def _set_relatedobject_properties(gr,uri,obj,target_map, related_objects) :                   
        # process all the related objects
        for (p,o,obj_type_name) in related_objects :
            prop = target_map.get(p)
            try:
                reltype = ContentType.objects.get(model=obj_type_name.lower())
            except ContentType.DoesNotExist as e :
                raise ValueError("Could not locate attribute or related model '{}' for predicate '{}'".format(obj_type_name, str(p)) )
            values = { prop.get('related_field') : obj }
            if prop.get('text_field') : 
                values[prop['text_field']] = unicode(o) 
            if prop.get('lang_field') :
                values[prop.get('lang_field') ] = o.language
            if prop.get('datatype_field') :
                values[prop.get('datatype_field') ] = o.datatype 
            if prop.get('object_field') :
                # find a matching object 
                object_prop = prop['object_field']
                # find a way to pass in an override for this sort of specific thing if we generalised this
                (linked_object,new) = Concept.objects.get_or_create(uri=unicode(o), scheme=obj.scheme)
                values[object_prop] = linked_object
            if prop.get('set_fields') :
                for (fname,val) in prop.get('set_fields') :
                    values[fname] = val
                
            (actual_obj,new)= reltype.model_class().objects.get_or_create(**values)
            