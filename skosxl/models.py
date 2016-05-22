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

#from taggit.models import TagBase, GenericTaggedItemBase
#from taggit.managers import TaggableManager
from rdf_io.models import Namespace, GenericMetaProp

import json


LABEL_TYPES = Choices(
    ('prefLabel',    0,  u'preferred'),
    ('altLabel',     1, u'alternative'),
    ('hiddenLabel',  2,  u'hidden'),
)

REL_TYPES = Choices(
    # ('broaderTransitive',   0,  u'Has a broader (transitive) concept'),
    # ('narrowerTransitive',  1,  u'Has a narrower (transitive) concept'),
    ('broader',             0,  u'has a broader concept'),
    ('narrower',            1,  u'has a narrower concept'),
    ('related',             2,  u'has a related concept'),    
)

reverse_map = {   
    # REL_TYPES.narrowerTransitive    : REL_TYPES.broaderTransitive,
    # REL_TYPES.broaderTransitive     : REL_TYPES.narrowerTransitive,
    REL_TYPES.narrower              : REL_TYPES.broader,
    REL_TYPES.broader               : REL_TYPES.narrower,
    REL_TYPES.related               : REL_TYPES.related
}

MATCH_TYPES = Choices(
    ('exactMatch',   0,  u'matches exactly'),
    ('closeMatch',   1,  u'matches closely'),
    ('broadMatch',   2,  u'has a broader match'),
    ('narrowMatch',  3,  u'has a narrower match'),
    ('relatedMatch', 4,  u'has a related match'),    
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

DEFAULT_LANG = 'en'

REVIEW_STATUS = Choices(
    ('active',  0,  u'Active'),
    ('draft',   1,  u'Draft'),
    ('doubled', 2,  u'Double'),
    ('dispute', 3,  u'Dispute'),
    ('todo',    4,  u'Not classified'),
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
        return json.dumps(ja_tree)

class SchemeMeta(models.Model):
    """
        extensible metadata using rdf_io managed reusable generic metadata properties
    """
    scheme      = models.ForeignKey(Scheme) 
    metaprop   =  models.ForeignKey(GenericMetaProp) 
    value = models.CharField(_(u'value'),max_length=500)
    
class ConceptManager(models.Manager):
    def get_by_natural_key(self, scheme, term):
        return self.get( scheme__uri = scheme, term=term)
        
class Concept(models.Model):
    objects = ConceptManager()
    # this will be the 
    term = models.CharField(_(u'term'),blank=True,null=True,max_length=255)
    # not sure we will need this - SKOS names should enforce slug compatibility.
    slug        = exfields.AutoSlugField(populate_from=('term'))
    pref_label = models.CharField(_(u'preferred label'),blank=True,null=True,max_length=255)

    
    definition  = models.TextField(_(u'definition'), blank=True)
#    notation    = models.CharField(blank=True, null=True, max_length=100)
    scheme      = models.ForeignKey(Scheme, blank=True, null=True)
    changenote  = models.TextField(_(u'change note'),blank=True)
    created     = exfields.CreationDateTimeField(_(u'created'))
    modified    = exfields.ModificationDateTimeField(_(u'modified'))
    status      = models.PositiveSmallIntegerField( _(u'review status'),
                                                    choices=REVIEW_STATUS.CHOICES, 
                                                    default=REVIEW_STATUS.active)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,blank=True,null=True,verbose_name=_(u'django user'),editable=False)
    uri         = models.CharField(blank=True,max_length=250,verbose_name=_(u'main URI'),editable=False)    
    author_uri  = models.CharField(blank=True,max_length=250,verbose_name=_(u'main URI'),editable=False)    

    top_concept = models.BooleanField(default=False, verbose_name=_(u'is top concept'))
    sem_relatons = models.ManyToManyField( "self",symmetrical=False,
                                            through='SemRelation',
                                            verbose_name=(_(u'semantic relations')))
    def __unicode__(self):
        return "/".join(self.natural_key())
    
    def natural_key(self):
        return ( self.scheme.natural_key(), self.term, )
    natural_key.dependencies = ['scheme']
        
    def get_absolute_url(self):
        return reverse('concept_detail', args=[self.id])
    def save(self,skip_name_lookup=False, *args, **kwargs):
        if self.scheme is None:
            self.scheme = Scheme.objects.get(slug=DEFAULT_SCHEME_SLUG)
        if not skip_name_lookup: #updating the pref_label
            try:
                lookup_label = self.labels.get(language=DEFAULT_LANG,label_type=LABEL_TYPES.prefLabel)
                label = lookup_label.label_text
            except Label.DoesNotExist:
                label =  '< no label >'
            self.pref_label = label
            #self.save(skip_name_lookup=True)
        super(Concept, self).save(*args, **kwargs) 
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
    namespace = models.ForeignKey(Namespace,verbose_name=_(u'namespace(type)'))
    def __unicode__(self):
        return self.code + '^^<' + self.namespace.uri + '>'  
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
    label_type  = models.PositiveSmallIntegerField(_(u'label type'), choices=tuple(LABEL_TYPES.CHOICES), default= LABEL_TYPES.prefLabel)
    label_text  = models.CharField(_(u'label text'),max_length=100, null=False)
    language    = models.CharField(_(u'language'),max_length=10, choices=LANG_LABELS, default='fr')
 
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
        if self.label_type == LABEL_TYPES.prefLabel:
            if Label.objects.filter(concept=self.concept,
                                             label_type=LABEL_TYPES.prefLabel,
                                             language=self.language
                                             ).exists():
                raise ValidationError(_(u'There can be only one preferred label by language'))
            if not self.concept.pref_label or self.concept.pref_label == '<no label>' :
                self.concept.pref_label = self.label_text
                self.concept.save()
        super(Label, self).save()
        
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
    rel_type = models.PositiveSmallIntegerField( _(u'Type of semantic relation'),choices=REL_TYPES.CHOICES, 
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
                                                     choices=MATCH_TYPES.CHOICES, 
                                                     default=MATCH_TYPES.closeMatch)
    class Meta: 
        verbose_name = _(u'Mapping relation')
        verbose_name_plural = _(u'Mapping relations')
#     

