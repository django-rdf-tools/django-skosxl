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
from django.contrib.auth.models import Group
from django.conf import settings
from django.db.models.signals import post_save

from django.contrib.contenttypes.models import ContentType
        
#from taggit.models import TagBase, GenericTaggedItemBase
#from taggit.managers import TaggableManager
from rdf_io.models import Namespace, GenericMetaProp, ImportedResource, CURIE_Field, RDFpath_Field, AttachedMetadata, makenode
from rdflib import Graph,namespace
from rdflib.term import URIRef, Literal
import itertools
import json


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
    ('doubled', 2,  _(u'Duplicate')),
    ('dispute', 3,  _(u'Dispute')),
    ('todo',    4,  _(u'Not classified')),
)

DEFAULT_SCHEME_SLUG = 'general'

    
class SchemeManager(models.Manager):
    def get_by_natural_key(self, uri):
        return self.get( uri = uri)

class SchemeMeta(AttachedMetadata):
    """
        extensible metadata using rdf_io managed reusable generic metadata properties
    """
    subject      = models.ForeignKey('Scheme', related_name="metaprops") 
 
        
class Scheme(models.Model):
    objects = SchemeManager()
    skip_post_save = False
    pref_label  = models.CharField(_(u'label'),blank=True,max_length=255)#should just be called label
    slug        = exfields.AutoSlugField(populate_from=('pref_label'))
    # URI doesnt need to be a registered Namespace unless you want to use prefix:term expansion for it
    uri         = models.CharField(blank=True,max_length=250,verbose_name=_(u'main URI'),editable=True)   
    created     = exfields.CreationDateTimeField(_(u'created'),null=True)
    modified    = exfields.ModificationDateTimeField(_(u'modified'),null=True)
    definition  = models.TextField(_(u'definition'), blank=True)
    changenote = models.TextField(_(u'change note'), blank=True)
    authgroup = models.ForeignKey(Group,blank=True,null=True,verbose_name=_(u'Authorised maintainers'),
        help_text=_('Leave blank to allow only superuser control. Members of group with staff level access will be able to use admin interface'))
    
    # metaprops = models.ManyToManyField(
    
    def __unicode__(self):
        return self.pref_label
        
    def save(self,*args,**kwargs):
        if not self.pref_label :
            self.pref_label = str(self.uri)
        super(Scheme, self).save(*args,**kwargs)
        
    def bulk_save(self):
        """ turns back on processing of signals and re-saves object - to trigger suppressed post-saves """
        self.skip_post_save = False
        self.save()
        for c in Concept.objects.filter(scheme=self) :
            c.skip_post_save = False
            c.save()
       
    def natural_key(self):
        return( self.uri )
        
    def get_absolute_url(self):
        #import pdb; pdb.set_trace()
        return reverse('skosxl:scheme_detail', args=[self.id])
        
    def getCollectionGraphs(self,**filters):
        """ builds a forest (list) of trees of Collections,starting at root nodes 
        
        raises Validation Error if recursion found """ 
        collections = Collection.objects.filter(scheme=self,**filters)
        tree = {}
        for col in collections:
            tree[ col.id ] = [col,[], True ]
            for member in CollectionMember.objects.filter(collection=col):
                tree[col.id][1].append( member.subcollection or member.concept )
        # now traverse and set top=False for all children nodes.
        for node in tree:
            for child in tree[node][1]:
                if type(child) == Collection:
                    tree[child.id][2] = False
        # now traverse again recursively to build each tree
        
        forest = []
        for node in tree:
            if tree[node][2] : # a root node
                path = set() 
                forest.append ( self._getMembers(tree, node, path) )
        return forest

    
    
    def _getMembers(self,treedict,node,path):
        tree = ( treedict[node][0], [])
        path.add(node)
        for member in treedict[node][1]:
 
            if type(member) == Collection:
                if member.id in path :
                    # raise ValidationError(" Recursion discovered in Collections %s member %s has already been visited " % (node,member.id) )
                    tree[1].append( (" Recursion discovered in Collections %s member %s %s has already been visited " % (node,member.id,str(member)) ,[] ))
                else:
                    tree[1].append( self._getMembers(treedict, member.id,path) )
            else:
                tree[1].append( (member, []))
        path.remove(node)        
        return tree
        
    def tree(self):
        MAXLEAFS = 20
        #import pdb; pdb.set_trace()
        tree = (self, [])  # result is a tuple(scheme,[child concepts])
        try:
            collections = self.getCollectionGraphs()
        except ValidationError as e :
            collections = [( str(e), [] )]
 
        topConcepts, num, numleafs = self.getTopConcepts()
 
        if collections and topConcepts or numleafs < num and num > MAXLEAFS :
            if collections:
                tree[1].append(("Collections",collections))           
            tree[1].append(("TopConcepts",topConcepts))
            if numleafs < num and num > MAXLEAFS :
                rootConcepts = []
                for c in topConcepts:
                    if c[1] :
                        rootConcepts.append(c)
                tree[1].append(("Hierarchies", rootConcepts ))
            
        else :
            tree= (self,topConcepts)
                
                #with nested tuple(concept, [child concepts])
        return tree 
    
    def getTopConcepts(self):
        tree = []
        topConcepts = Concept.objects.filter(scheme=self,top_concept=True)
        if not topConcepts :
            topConcepts = Concept.objects.filter(scheme=self).exclude(rel_origin__rel_type=REL_TYPES.broader)
        nleafs = 0 # number of leaf nodes in topConcepts
        total = 0
        for concept in topConcepts: 
            total = total + 1
            children = concept.get_narrower_concepts()
            if not children:
                nleafs = nleafs + 1
            tree.append((concept,children))     
        return tree, total, nleafs
        
    @staticmethod                      
    def _recurse_json_tree(obj_tree,prefix):
        """ takes a tree with a an object and a list of child objects and makes it into a json D3 tree with strings """
        try:
            label = obj_tree[0].pref_label
        except:
            label = str(obj_tree[0])
        ja_tree = {'name' : label, 'children' : []}
        if type(obj_tree[0]) == Concept :
            ja_tree['url']= prefix+'/skosxl/concept/'+str(obj_tree[0].id)+'/'
        elif type(obj_tree[0]) == Collection :
            ja_tree['url']= prefix+'/skosxl/collection/'+str(obj_tree[0].id)+'/'
      
        for jdx, j in enumerate(obj_tree[1]):#j[0] is a concept, j[1] a list of children
            ja_tree['children'].append(Scheme._recurse_json_tree(j,prefix))
        
        return ja_tree
        
    def json_tree(self,admin_url=False):
        i = self.tree()
        prefix = '/admin' if admin_url else ''
        ja_tree = Scheme._recurse_json_tree(i,prefix)
        return json.dumps(ja_tree, sort_keys=True,
                          indent=4, separators=(',', ': '))
 
    

        
class ConceptRank(models.Model):
    """ a ordered, labelled ranking and typing mechanism for Concept Hierarchies. 
    
    The numerical ordering may be post-calculated on bulk import from broader-narrower relationships amongst ranked concepts.
    Ranking systems are Scheme specific. """
    scheme=models.ForeignKey(Scheme)
    level= models.PositiveSmallIntegerField(blank=True, null=True, help_text=_(u'the depth this type of concept represents'))
    pref_label = models.CharField(_(u'preferred label'),blank=True,null=True,help_text=_(u'Label of concept'),max_length=255)
    uri= models.URLField(_(u'definition reference'),blank=True,null=True,help_text=_(u'URI of definition'),max_length=255)
    prefStyle = models.CharField(max_length=255, blank=True, null=True, help_text=u'Preferred style - either a #RGB colour or a CSS style string')

    def __unicode__(self):
        return self.pref_label
        
    @staticmethod
    def calcLevels(scheme, topRank=None):
        """ find top concepts, then traverse a sample down hierarchy using broader/narrower SemRelations 
        
        Once passed down an arbitrary chain, then look for additional ranks that were not covered."""
        if topRank:
            topconcepts = Concept.objects.filter(scheme=scheme, rank__pref_label=topRank)
        else:
            topconcepts = Concept.objects.filter(scheme=scheme, top_concept=True, rank__isnull = False)
        for topc in topconcepts:
            if not ConceptRank.objects.filter(scheme=scheme, level__isnull=True) :
                break
            nextconcept = topc
            lvl = 1 # 0 is the scheme itself
            while nextconcept :
                nextconcept.rank.level = lvl
                nextconcept.rank.save()
                lvl = lvl + 1
                rel = SemRelation.objects.filter(origin_concept=nextconcept,rel_type=REL_TYPES.narrower).first()
                if rel:
                    nextconcept=rel.target_concept
                else:    
                    rel = SemRelation.objects.filter(target_concept=nextconcept,rel_type=REL_TYPES.broader).first()
                    if rel:
                        nextconcept=rel.origin_concept
                    else:
                        nextconcept = None
        # now look for missing ranks using broader relationships
        missedRank = SemRelation.objects.filter(origin_concept__rank__level__isnull=False, target_concept__rank__level__isnull=True, rel_type=REL_TYPES.broader).first()        
        while missedRank :
            missedRank.target_concept.rank.level = missedRank.origin_concept.rank.level + 1
            missedRank.target_concept.rank.save()
            missedRank = SemRelation.objects.filter(origin_concept__rank__level__isnull=False, target_concept__rank__level__isnull=True, rel_type=REL_TYPES.broader).first()        
        
       # now look for missing ranks using broader relationships
        missedRank = SemRelation.objects.filter(target_concept__rank__level__isnull=False, origin_concept__rank__level__isnull=True, rel_type=REL_TYPES.narrower).first()        
        while missedRank  :
            missedRank.origin_concept.rank.level = missedRank.target_concept.rank.level + 1
            missedRank.origin_concept.rank.save()
            missedRank = SemRelation.objects.filter(target_concept__rank__level__isnull=False, origin_concept__rank__level__isnull=True, rel_type=REL_TYPES.narrower).first()        
        

class ConceptMeta(AttachedMetadata):
    """
        extensible metadata using rdf_io managed reusable generic metadata properties
    """
    subject       = models.ForeignKey("Concept", related_name="metaprops")     

            
class ConceptManager(models.Manager):    
    def get_by_natural_key(self, uri):
        return self.get( uri = uri)
        
class Concept(models.Model):
    objects = ConceptManager()
    skip_post_save = False
    # this will be the 
    term = models.CharField(_(u'term'),help_text=_(u'Required - must be valid SKOS term - ie. a URL-friendly QNAME - TODO include validation for this.'),blank=True,null=True,max_length=255)
    # not sure we will need this - SKOS names should enforce slug compatibility.
    slug        = exfields.AutoSlugField(populate_from=('term'))
    pref_label = models.CharField(_(u'preferred label'),blank=True,null=True,help_text=_(u'Will be automatically set to the preferred label in the default language - which will be automatically created using this field only if not present'),max_length=255)

    
    definition  = models.TextField(_(u'definition'), blank=True)
#    notation    = models.CharField(blank=True, null=True, max_length=100)
    scheme      = models.ForeignKey(Scheme, blank=True, null=True, help_text=_(u'Note - currently only membership of a single scheme supported'))
    rank          = models.ForeignKey(ConceptRank, blank=True,null=True, help_text=_(u'Rank (depth) of Concept in ranked hierarchy, if applicable'))
    prefStyle = models.CharField(max_length=255, blank=True, null=True, help_text=u'Preferred style - either a #RGB colour or a CSS style string')
    changenote  = models.TextField(_(u'change note'),blank=True)
    created     = exfields.CreationDateTimeField(_(u'created'))
    modified    = exfields.ModificationDateTimeField(_(u'modified'))
    status      = models.PositiveSmallIntegerField( _(u'review status'),
                                                    choices=REVIEW_STATUS, 
                                                    default=REVIEW_STATUS.active)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,blank=True,null=True,verbose_name=_(u'django user'),editable=False)
    uri         = models.CharField(blank=True,max_length=250,verbose_name=_(u'main URI'),editable=True, help_text=_(u'Leave blank to inherit namespace from containing scheme'))    
    author_uri  = models.CharField(blank=True,max_length=250,verbose_name=_(u'main URI'),editable=False)    

 #
    top_concept = models.BooleanField(default=False, verbose_name=_(u'is top concept'))
    sem_relations = models.ManyToManyField( "self",symmetrical=False,
                                            through='SemRelation',
                                            related_name='concept',
                                            verbose_name=(_(u'Semantic relations')),
                                            help_text=_(u'SKOS semantic relations are links between SKOS concepts, where the link is inherent in the meaning of the linked concepts.'))
    # map_relations = models.OneToManyField( "self",symmetrical=False,
                                            # through='MapRelation',
                                            # verbose_name=(_(u'semantic relations'))
                                            # ,
                                            # help_text=_(u'These properties are used to state mapping (alignment) links between SKOS concepts in different concept schemes'))
                                            
    def __unicode__(self):
        return "".join((self.term, " (", self.uri , ")" ))
    
    def natural_key(self):
        return ( self.uri )
#    natural_key.dependencies = ['scheme']
    

    def get_absolute_url(self):
        """
            URL of the representation document generated by Django - note this is not the same as the uri based on a term within a scheme
        """
        return reverse('skosxl:concept_detail', args=[self.id])
        
    def save(self,skip_name_lookup=False, *args, **kwargs):
        # import pdb; pdb.set_trace()
        print "saving %s" % self.uri
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
        if SemRelation.objects.filter(origin_concept=self,rel_type=REL_TYPES.narrower).exists():
            for narrower in SemRelation.objects.filter(origin_concept=self,rel_type=REL_TYPES.narrower):
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
        # unique_together = (('scheme', 'term'),)
        pass

class CollectionMember(models.Model):
    """ potentially ordered membership of collection """
    collection = models.ForeignKey('Collection')
    index = models.PositiveSmallIntegerField(blank=True,null=True)
    concept = models.ForeignKey('Concept',blank=True,null=True)
    subcollection = models.ForeignKey('Collection',related_name='subcollection', blank=True,null=True)
    class Meta :
        ordering = [ 'index', ]
        unique_together = ['collection','concept','subcollection']
        # check index is unique if present.. unique_together = (('scheme', 'term'),)
        pass
    def clean(self):
        if not ( self.concept or self.subcollection ) :
            raise ValidationError(_('Either a Concept or Collection member must be specified'))
            
    def __unicode__(self):
        if self.subcollection:
            return "".join(('Subcollection:',self.subcollection.pref_label if self.subcollection.pref_label else 'No label'))
        elif self.concept:
            return "".join(('Concept:',self.concept.pref_label))
        else:
            return 'what the?'

class CollectionMeta(AttachedMetadata):
    """
        extensible metadata using rdf_io managed reusable generic metadata properties
    """
    subject      = models.ForeignKey('Collection', related_name="metaprops") 
             
class Collection(models.Model):
    """ SKOS Collection """
    pref_label = models.CharField(_(u'preferred label'),blank=True,null=True,help_text=_(u'Collections only support single label currently'),max_length=255)
    uri         = models.CharField(blank=True,max_length=250,verbose_name=_(u'main URI'),editable=True, help_text=_(u'Collection URI'))    
    scheme  = models.ForeignKey(Scheme, help_text=_(u'Scheme containing Collection'))
    ordered = models.BooleanField(default=False, verbose_name=_(u'Collection is ordered'))
    members = models.ManyToManyField( "self",symmetrical=False,
                                            through='CollectionMember',
                                            verbose_name=(_(u'Members')),
                                            help_text=_(u'Members are optional indexed references to Concepts'))
                                            
    def __unicode__(self):
        return "".join(filter(None,(self.pref_label, " (", self.uri , ")" )))
                                            
class Notation(models.Model):
    concept     = models.ForeignKey(Concept,blank=True,null=True,verbose_name=_(u'main concept'),related_name='notations')
    code =  models.CharField(_(u'notation'),max_length=100, null=False)
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


class PrefLabelManager(models.Manager):
   def get_queryset(self):
        return super(PrefLabelManager, self).get_queryset().filter(label_type=LABEL_TYPES.prefLabel)

class AltLabelManager(models.Manager):
   def get_queryset(self):
        return super(AltLabelManager, self).get_queryset().filter(label_type=LABEL_TYPES.altLabel)

        
class Label(models.Model):
    '''
    Defines a SKOS-XL Label Class, and also a Tag in django-taggit
    '''
    # FIELDS name and slug are defined in TagBase  - they are forced to be unique
    # so if a concept is to be made available as a tag then it must conform to this constraint - generating a label without a Concept implies its is a tag generation - and name will be forced to be unique.
    # temporary replacement while disconected from taggit..
    slug        = exfields.AutoSlugField(populate_from=('label_text'))

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
    objects = models.Manager()
    preflabels = PrefLabelManager()
    altlabels= AltLabelManager()
    
    def get_absolute_url(self):
        #import pdb; pdb.set_trace()
        return reverse('skosxl:tag_detail', args=[self.id])
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
                print self.concept.pref_label,self.label_text
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


RDFTYPE_NODE=URIRef(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
CONCEPT_NODE=URIRef(u'http://www.w3.org/2004/02/skos/core#Concept')
SCHEME_NODE=URIRef(u'http://www.w3.org/2004/02/skos/core#ConceptScheme')
COLLECTION_NODE=URIRef(u'http://www.w3.org/2004/02/skos/core#Collection')
HASTOPCONCEPT_NODE=URIRef(u'http://www.w3.org/2004/02/skos/core#hasTopConcept')


class ImportedConceptScheme(ImportedResource):

    target_scheme = models.URLField(blank=True, verbose_name=(_(u'target scheme - leave blank to use default defined in resource')))
    import_all = models.BooleanField(default=True, verbose_name=(_(u'Import all schemes found')), help_text='Set false and specify target schem if only one of multiple Concept Schemes is required.')
    force_bulk_only = models.BooleanField(default=False, verbose_name=(_(u'bulk-load target repo from source file only')), help_text='Allows for bulk load of original source file, instead of publishing just the subset loaded into SKOSXL model.')
    force_refresh = models.BooleanField(default=False, verbose_name=(_(u'force purge of target concept scheme')), help_text='Allows for incremental load of a single concept scheme from multiple files - e.g. collections')
    rankNameProperty = RDFpath_Field(null=True, blank=True, max_length=1000, verbose_name=(_(u'property path of rank name')), help_text='Property path, relative to Concept object, of label for rank descriptor, if present')
    rankDepthProperty = RDFpath_Field(null=True, blank=True, max_length=1000,verbose_name=(_(u'property path of rank level ')), help_text='Property path, relative to Concept object, of rank depth(level), (integer starting with 0) if present')
    rankURIProperty = RDFpath_Field(null=True, blank=True,  max_length=1000,verbose_name=(_(u'property path of rank URI reference')), help_text='Property path, relative to Concept object, of label for rank descriptor, if present')
    rankTopName = models.CharField(null=True, blank=True,  max_length=100, verbose_name=(_(u'name of TopRank')), help_text='If not set, then the rank of designated topConcepts will be used to define the root of the ranking hierarchy. skos:topConcept will be ignored, and nodes matching this wil be set as topConcept.')

    schemes = models.ManyToManyField(Scheme, blank=True, verbose_name=(_(u'Concept Schemes derived from this resource')))
    
    importerrors = []
    
    def save(self,*args,**kwargs):  
        # save first - to make file available
        # import pdb; pdb.set_trace()
        if not self.force_bulk_only :
            target_repo = self.target_repo
            self.target_repo = None
            super(ImportedConceptScheme, self).save(*args,**kwargs)
            self.target_repo = target_repo
        else:
            super(ImportedConceptScheme, self).save(*args,**kwargs)
        if type(self) == ImportedConceptScheme :
            scheme_obj = self.importSchemes(self.get_graph(),self.target_scheme, self.force_refresh)
            # update any references to imported schemes
            super(ImportedConceptScheme, self).save(*args,**kwargs)
        
    class Meta: 
        verbose_name = _(u'ImportedConceptScheme')
        verbose_name_plural = _(u'ImportedConceptScheme')

    def importSchemes(self,gr, target_scheme, force_refresh, schemeClass=Scheme, conceptClass=Concept,schemeDefaults={}, classDefaults={} ):
        """ Import a single or set of concept schemes from a parsed RDF graph 
        
        Uses generic RDF graph management to avoid having to do consistency checks and resource management here.
        Will generate the target ConceptScheme if not present.
        Push to triple store is via the post_save triggers and RDF_IO mappings if defined.
        """
        if not gr:
            raise Exception ( _(u'No RDF graph available for resource'))
        self.importerrors = []
        self.schemes.all().delete()
        if not target_scheme:
            s = None
            for conceptscheme in gr.subjects(predicate=RDFTYPE_NODE, object=SCHEME_NODE) :
                if not self.import_all :
                    raise Exception('Multiple concept schemes found in source document - specify target first')
                target_scheme = str(conceptscheme)
                s = conceptscheme
                scheme = self.importScheme(gr, target_scheme, force_refresh ,s,schemeClass, conceptClass,schemeDefaults, classDefaults)
                self.schemes.add(scheme)
            if not s:
                raise Exception('No concept schemes found in source document - specify target first')
        else:
            s = URIRef(target_scheme)
            scheme = self.importScheme(gr, target_scheme, force_refresh ,s ,schemeClass, conceptClass,schemeDefaults, classDefaults )
            self.schemes.add(scheme)

    def importScheme(self,gr, target_scheme,  force_refresh, schemegraph, schemeClass=Scheme, conceptClass=Concept,schemeDefaults={}, classDefaults={} ):
        """ Import a single or set of concept schemes from a parsed RDF graph 
        
        Uses generic RDF graph management to avoid having to do consistency checks and resource management here.
        Will generate the target ConceptScheme if not present.
        Push to triple store is via the post_save triggers and RDF_IO mappings if defined.
        """
        
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
            URIRef(u'http://www.w3.org/2004/02/skos/core#inScheme'):  {'ignore': True} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#topConceptOf'): {'ignore': True} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#prefLabel'): {'related_object':'Label', 'related_field': 'concept', 'text_field': 'label_text', 'lang_field':'language', 'set_fields': (('label_type',0),)} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#altLabel'): {'related_object':'Label', 'related_field': 'concept', 'text_field': 'label_text', 'lang_field':'language', 'set_fields': (('label_type',1),)} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#hiddenLabel'): {'related_object':'Label', 'related_field': 'concept', 'text_field': 'label_text', 'lang_field':'language', 'set_fields': (('label_type',2),)} , 
            URIRef(u'http://www.w3.org/2004/02/skos/core#notation'): {'related_object':'Notation', 'related_field': 'concept', 'text_field': 'code', 'datatype_field':'codetype'} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#broader'): {'related_object':'SemRelation', 'related_field': 'origin_concept', 'object_field': 'target_concept', 'set_fields': (('rel_type',REL_TYPES.broader),)} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#narrower'): {'related_object':'SemRelation', 'related_field': 'origin_concept', 'object_field': 'target_concept', 'set_fields': (('rel_type',REL_TYPES.narrower),)} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#related'): {'related_object':'SemRelation', 'related_field': 'origin_concept', 'object_field': 'target_concept', 'set_fields': (('rel_type',REL_TYPES.related),)} ,
            URIRef(u'http://www.w3.org/2002/07/owl#sameAs'): {'related_object':'MapRelation', 'related_field': 'origin_concept', 'text_field': 'uri', 'set_fields': (('match_type',0),)} ,
            URIRef(u'http://www.w3.org/2004/02/skos#exactMatch'): {'related_object':'MapRelation', 'related_field': 'origin_concept', 'text_field': 'uri', 'set_fields': (('match_type',0),)} ,              }
 
        target_map_collection = {
            URIRef(u'http://www.w3.org/2000/01/rdf-schema#label'): { 'text_field': 'pref_label'} ,
            # URIRef(u'http://www.w3.org/2004/02/skos/core#definition'): { 'text_field': 'definition'} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#member'): {'related_object':'CollectionMember', 'related_field': 'collection', 'object_field': 'concept'} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#prefLabel'): { 'text_field': 'pref_label'} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#memberList'): { 'related_object':'CollectionMember', 'index_field':'index', 'related_field': 'collection', 'object_field': 'concept'} ,
        }
        target_map_subcollections = {
            URIRef(u'http://www.w3.org/2000/01/rdf-schema#label'): { 'text_field': 'pref_label'} ,
            # URIRef(u'http://www.w3.org/2004/02/skos/core#definition'): { 'text_field': 'definition'} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#member'): {'related_object':'CollectionMember', 'related_field': 'collection', 'object_field': 'subcollection'} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#prefLabel'): { 'text_field': 'pref_label'} ,
            URIRef(u'http://www.w3.org/2004/02/skos/core#memberList'): { 'related_object':'CollectionMember', 'index_field':'index', 'related_field': 'collection', 'object_field': 'subcollection'} ,
        }
        if not self.rankTopName :
                target_map_concept[URIRef(u'http://www.w3.org/2004/02/skos/core#topConceptOf')] =  { 'bool_field': 'top_concept'} 
        
        
        if not gr:
            raise Exception ( _(u'No RDF graph available for resource'))
             
        if force_refresh :
            Scheme.objects.filter(uri=target_scheme).delete()

        (scheme_obj,new) = schemeClass.objects.get_or_create(uri=target_scheme, defaults=schemeDefaults)
        scheme_obj.skip_post_save = True
        scheme_obj.changenote = "Bulk import via SKOSXL manager on %s by %s from source %s" % ( str(self.uploaded_at), 'superuser', self.file.name if self.file else self.remote ) 
        related_objects = _set_object_properties(gr=gr,uri=schemegraph,obj=scheme_obj,target_map=target_map_scheme, metapropClass=SchemeMeta)
        scheme_obj.save()
        # now process any related objects - concepts first then any collections
        #import pdb; pdb.set_trace()
        for c in self.getConcepts(schemegraph,gr):
            url = str(c)
            try: 
                term=url[ url.rindex('#')+1:]
            except :
                term=url[ url.rindex('/')+1:]

            (concept_obj,new) = conceptClass.objects.get_or_create(scheme=scheme_obj, uri=str(c), term=term, defaults=classDefaults)
            concept_obj.skip_post_save = True
            #
            rankuri = None
            rankname = None
            rankdepth = None
            if self.rankURIProperty :           
                try:
                    rankuri = self.getPathVal(gr,c,self.rankURIProperty) 
                    # assert rankuri
                except:

                    raise ValueError ("Unable to resolve rank URI reference, if specified must be present for all Concepts")    
            if self.rankNameProperty :
                try:
                    rankname = self.getPathVal(gr,c,self.rankNameProperty) 
                    # assert rankname
                except:
                    raise ValueError ("Unable to resolve rank Name reference, if specified must be present for all Concepts")
            elif rankuri :
                rankname = rankuri.replace('#','/').split('/')[-1]
            if self.rankDepthProperty :
                try:
                    rankdepth = self.getPathVal(gr,c,self.rankDepthProperty) 
                    # assert rankdepth
                except:
                    raise ValueError ("Unable to resolve rank Name reference, if specified must be present for all Concepts")
                if not rankname :
                    rankname = str(rankdepth)
            if rankname :    
                concept_obj.rank, new  = ConceptRank.objects.get_or_create(scheme=scheme_obj, uri=rankuri, pref_label=rankname, level=rankdepth)
            
            # now all the rest of the properties
            related_objects = _set_object_properties(gr=gr,uri=c,obj=concept_obj,target_map=target_map_concept,metapropClass=ConceptMeta)
            concept_obj.save()
            try:
                _set_relatedobject_properties(gr=gr,uri=c,obj=concept_obj,target_map=target_map_concept,related_objects=related_objects,conceptClass=conceptClass, classDefaults=classDefaults)
            except Exception as e:
                print "Error in concept building: %s" % str(e)
                self.importerrors.append(e)
        
        ConceptRank.calcLevels(scheme=scheme_obj, topRank = self.rankTopName)
        if self.rankTopName :
            Concept.objects.filter(scheme=scheme_obj, rank__pref_label=self.rankTopName).update(top_concept=True)
            # and also any sub-trees whose roots start below this level
            Concept.objects.filter(scheme=scheme_obj,top_concept=False,rank__isnull=False).exclude(rel_origin__rel_type=REL_TYPES.broader).update(top_concept=True)
        else :
            topConcepts = gr.objects(predicate=HASTOPCONCEPT_NODE, subject=schemegraph)
            for tc in topConcepts :
                Concept.objects.filter(uri=str(tc)).update(top_concept=True) 
        # import pdb; pdb.set_trace()               
        # now process collections
        for row in gr.query("SELECT DISTINCT ?collection WHERE {   ?collection a skos:Collection . {?collection skos:member ?member } UNION {?collection skos:memberList ?member } }" ):
            col = row[0]
            try:
                (collection_obj,new) = Collection.objects.get_or_create(scheme=scheme_obj, uri=col, ordered=False )
                members = _set_object_properties(gr=gr,uri=col,obj=collection_obj,target_map=target_map_collection,metapropClass=CollectionMeta)
                collection_obj.save()
                # two passes - for related concepts and related collections

                members = gr.query("SELECT DISTINCT ?member WHERE { <%s> skos:member ?member .  ?member a skos:Collection }" % col )
                related_objects = ()
                for m in members:
                    related_objects += ((URIRef(u'http://www.w3.org/2004/02/skos/core#member'),m[0],'CollectionMember'),)
                if related_objects:
                    _set_relatedobject_properties(gr=gr,uri=col,obj=collection_obj,target_map=target_map_subcollections,related_objects=related_objects, conceptClass=Collection, classDefaults=classDefaults)
                members = gr.query("SELECT DISTINCT ?member WHERE { <%s> skos:member ?member .  ?member a skos:Concept }" % col )
                related_objects = ()
                for m in members:
                    related_objects += ((URIRef(u'http://www.w3.org/2004/02/skos/core#member'),m[0],'CollectionMember'),)
                if related_objects: 
                 _set_relatedobject_properties(gr=gr,uri=col,obj=collection_obj,target_map=target_map_collection,related_objects=related_objects, conceptClass=Concept, classDefaults=classDefaults)
            except Exception as e:
                print "Error in collection building: %s" % str(e)
                self.importerrors.append(e)
     
        scheme_obj.bulk_save()
        return scheme_obj
    
    def getConcepts(self,s,gr):
        found,conceptList = _has_items(gr.subjects(predicate=URIRef(u'http://www.w3.org/2004/02/skos/core#inScheme'), object=s))
        if not found:
            conceptList = gr.subjects(predicate=RDFTYPE_NODE, object=CONCEPT_NODE)
        return conceptList
        
def _has_items(iterable):
    try:
        return True, itertools.chain([next(iterable)], iterable)
    except StopIteration:
        return False, []
        
def _set_object_properties(gr,uri,obj,target_map,metapropClass) : 
        """ sets object properties, and returns a list of related objects that need to be created if missing """
        
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
                    #print "setting ",prop['text_field'],unicode(o)
            elif metapropClass and not (p == RDFTYPE_NODE and o in (CONCEPT_NODE, SCHEME_NODE, COLLECTION_NODE )):
                #import pdb; pdb.set_trace()
                metaprop,created = GenericMetaProp.objects.get_or_create(uri=str(p))
                metapropClass.objects.get_or_create(subject=obj, metaprop=metaprop, value=o.n3())
                               
        return related_objects
        
def _set_relatedobject_properties(gr,uri,obj,target_map, related_objects,conceptClass,classDefaults) :                   
        # process all the related objects

        for (p,o,obj_type_name) in related_objects :
            prop = target_map.get(p)
            if not prop:
                continue
            try:
                reltype = ContentType.objects.get(model=obj_type_name.lower())
            except ContentType.DoesNotExist as e :
                raise ValueError("Could not locate attribute or related model '{}' for predicate '{}'".format(obj_type_name, str(p)) )
            # if related_field 
            values = { prop.get('related_field') : obj }
            if prop.get('text_field') : 
                values[prop['text_field']] = unicode(o) 
            if prop.get('lang_field') :
                values[prop.get('lang_field') ] = o.language or DEFAULT_LANG
            if prop.get('datatype_field') :
                values[prop.get('datatype_field') ] = o.datatype or URIRef("xsd:string")
            if prop.get('object_field') :
                # find a matching object 
                object_prop = prop['object_field']
                # find a way to pass in an override for this sort of specific thing if we generalised this
                (linked_object,new) = conceptClass.objects.get_or_create(uri=unicode(o), scheme=obj.scheme, defaults=classDefaults)
                values[object_prop] = linked_object
            if prop.get('set_fields') :
                for (fname,val) in prop.get('set_fields') :
                    values[fname] = val
            try:
                (actual_obj,new)= reltype.model_class().objects.get_or_create(**values)
            except Exception as e:
                raise ValueError("Cannot create %s object with values %s : exception %s" % (str(reltype.model_class()),str(values), str(e))) 
            