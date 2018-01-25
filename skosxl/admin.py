#-*- coding:utf-8 -*-
from django.contrib import admin
from skosxl.models import *
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from itertools import chain

from django.forms import ModelForm

from skosxl.utils.autocomplete_admin import FkAutocompleteAdmin, InlineAutocompleteAdmin


# class LabelInline(InlineAutocompleteAdmin):
#     model = LabelProperty
#     fields = ('label','label_type',)
#     related_search_fields = {'label' : ('name','slug')}
#     extra=1
#     

class OwnedSchemeListFilter(admin.SimpleListFilter):
    title=_('Concept Scheme')
    parameter_name = 'scheme_id'
    
    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            schemes = Scheme.objects.all()
        else:  
            schemes = Scheme.objects.filter(authgroup__in=request.user.groups.all())        
        return [(c.id, c.pref_label) for c in schemes]
        
    def queryset(self, request, qs):
        try:
            qs= qs.filter(scheme__id=request.GET['scheme_id'])
        except:
            pass
        if request.user.is_superuser:
            return qs
        return qs.filter(scheme__authgroup__in=request.user.groups.all()) 
    
class LabelInline(InlineAutocompleteAdmin):
    model = Label
    readonly_fields = ('created',)
    fields = ('language','label_type','label_text','created')
    related_search_fields = {'label' : ('label_text',)}
    extra=1    

class NotationInline(InlineAutocompleteAdmin):
    model = Notation
    # readonly_fields = ('slug','created')
    fields = ('code','codetype')
    # related_search_fields = {'label' : ('name','slug')}
    extra=1    
    
    
class SKOSMappingInline(admin.TabularInline):
    model = MapRelation
    fk_name = 'origin_concept'
    fields = ('match_type','uri')
#    related_search_fields = {'target_concept' : ('labels__name','definition')}
    extra=1    

class RelSelectForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(RelSelectForm, self).__init__(*args, **kwargs)
        # access object through self.instance...
        #import pdb; pdb.set_trace()
        try:
            self.fields['target_concept'].queryset = Concept.objects.filter(scheme=self.instance.origin_concept.scheme)
        except:
            pass
        
class RelInline(InlineAutocompleteAdmin):
    model = SemRelation
    form = RelSelectForm
    fk_name = 'origin_concept'
    fields = ('rel_type', 'target_concept')
    related_search_fields = {'target_concept' : ('labels__name','definition')}
    extra = 1

def create_action(scheme):
    fun = lambda modeladmin, request, queryset: queryset.update(scheme=scheme)
    name = "moveto_%s" % (scheme.slug,)
    return (name, (fun, name, _(u'Make selected concept part of the "%s" scheme') % (scheme,)))


class ConceptMetaInline(InlineAutocompleteAdmin):
    model = ConceptMeta
    verbose_name = 'Additional property'
    verbose_name_plural = 'Additional properties'
#    list_fields = ('pref_label', )
    show_change_link = True
    max_num = 20
    fields = ('subject','metaprop','value')
 #   list_display = ('pref_label',)
    extra = 1
    
class ConceptAdmin(FkAutocompleteAdmin):
    readonly_fields = ('created','modified')
    search_fields = ['term','uri','pref_label','slug','definition', 'rank__pref_label']
    list_display = ('term','pref_label','uri','scheme','top_concept','rank')
    #list_editable = ('status','term','scheme','top_concept')
    list_filter=(OwnedSchemeListFilter,'status')
    change_form_template = 'admin_concept_change.html'
    change_list_template = 'admin_concept_list.html'
    # def change_view(self, request, object_id, extra_context=None):
    #     from SPARQLWrapper import SPARQLWrapper,JSON, XML
    #     #import pdb; pdb.set_trace()
    #     obj = Concept.objects.get(id=object_id)
    #     my_context = {'lists' : []}
    #     endpoints = (   
    #                     #('AGROVOC','http://202.73.13.50:55824/catalogs/performance/repositories/agrovoc'),
    #                     #('ISIDORE','http://www.rechercheisidore.fr/sparql?format=application/sparql-results+json'),
    #                     ('GEMET','http://cr.eionet.europa.eu/sparql'),
    #                 )
    #     for endpoint in endpoints :
    #         try:
    #             sparql = SPARQLWrapper(endpoint[1])
    #             sparql.setQuery(u"""
    #                 PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    #                 PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    #                 PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    #                 SELECT ?label ?uri WHERE {
    #                   ?uri a skos:Concept .
    #                   ?uri skos:prefLabel ?label .
    #                   FILTER(regex(str(?label),""" + u'"'+obj.pref_label+u'"' + u""","i"))
    #                   FILTER( lang(?label) = "fr" )
    #                 }
    #             """)
    #             sparql.setReturnFormat(JSON)
    #             results = sparql.query().convert()
    #             # for result in results["results"]["bindings"]:            
    #             #     print result["label"]["value"]
    #     
    #             my_context['lists'].append({'name': endpoint[0],'items':results["results"]["bindings"]})
    #         except Exception,e :
    #             print "Caught:", e            
    #         
    #     return super(ConceptAdmin, self).change_view(request, object_id, extra_context=my_context)
        
    def changelist_view(self, request, extra_context=None):
        try :
            scheme_id = int(request.GET['scheme_id'])
        except KeyError :
            scheme_id = None # FIXME: if no scheme filter is called, get the first (or "General") : a fixture to create one ?
        return super(ConceptAdmin, self).changelist_view(request, 
                                        extra_context={'scheme_id':scheme_id})
            
    fieldsets = (   (_(u'Scheme'), {'fields':('term','uri','scheme','pref_label','rank','top_concept','definition')}),
                    (_(u'Meta-data'),
                    {'fields':('prefStyle','changenote','created','modified'),
                     'classes':('collapse',)}),
                     )
    inlines = [   ConceptMetaInline , NotationInline, LabelInline, RelInline, SKOSMappingInline]
    def get_actions(self, request):
        actions = super(ConceptAdmin, self).get_actions(request)
        actions.update(dict(create_action(s) for s in Scheme.objects.all()))
        return actions

    def get_queryset(self, request):
        qs = super(ConceptAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(scheme__authgroup__in=request.user.groups.all())
admin.site.register(Concept, ConceptAdmin)



def create_concept_command(modeladmin, request, queryset):
    for label in queryset:
        label.create_concept_from_label()
create_concept_command.short_description = _(u"Create concept(s) from selected label(s)")



class SchemeMetaInline(InlineAutocompleteAdmin):
    model = SchemeMeta
#    list_fields = ('pref_label', )
    show_change_link = True
    max_num = 20
    fields = ('subject','metaprop','value')
 #   list_display = ('pref_label',)
    extra = 1
    verbose_name = 'Additional property'
    verbose_name_plural = 'Additional properties'
#  
class ConceptInline(InlineAutocompleteAdmin):
    model = Concept
#    list_fields = ('pref_label', )
    show_change_link = True
    max_num = 20
    fields = ('term','pref_label','rank','top_concept','status')
 #   list_display = ('pref_label',)
    related_search_fields = {'concept' : ('prefLabel','definition')}
    extra = 1

class LabelAdmin(FkAutocompleteAdmin):
    list_display = ('label_text','label_type','concept')
    fields = ('label_text','language','label_type','concept')
    related_search_fields = {'concept' : ('pref_label','definition')}
#    actions = [create_concept_command]
    #list_editable = ('name','slug')
    search_fields = ['label_text',]    
    def get_queryset(self, request):
        qs = super(LabelAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(concept__scheme__authgroup__in=request.user.groups.all())
admin.site.register(Label, LabelAdmin)

class SchemeBase(Scheme):
    verbose_name = 'Scheme without its member concepts - use Scheme if list is small'
    class Meta:
        proxy = True

       
class SchemeAdmin(FkAutocompleteAdmin):
    readonly_fields = ('created','modified')
    inlines = [  SchemeMetaInline, ]  
    model=SchemeBase
    search_fields = ['pref_label','uri',]
    verbose_name = 'Scheme with its member concepts - use Scheme bases if this may be a inconveniently large list'
    def get_queryset(self, request):
        qs = super(SchemeAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(authgroup__in=request.user.groups.all())

admin.site.register(SchemeBase, SchemeAdmin)

    

class SchemeConceptAdmin(SchemeAdmin):
    
    readonly_fields = ('created','modified')
    inlines = [  SchemeMetaInline, ConceptInline, ]
  
admin.site.register(Scheme, SchemeConceptAdmin)

class ConceptRankAdmin(FkAutocompleteAdmin):
    list_display = ('pref_label','level','scheme')
    list_filter = (('scheme',admin.RelatedOnlyFieldListFilter),)
    pass
  
admin.site.register(ConceptRank, ConceptRankAdmin)

class CollectionMetaInline(InlineAutocompleteAdmin):
    model = CollectionMeta
#    list_fields = ('pref_label', )
    show_change_link = True
    max_num = 20
    fields = ('subject','metaprop','value')
 #   list_display = ('pref_label',)
    extra = 1
    verbose_name = 'Additional property'
    verbose_name_plural = 'Additional properties'
    
class CollectionMemberInlineForm(ModelForm):
    fields = ('index','concept','subcollection')
    class Meta:
        model = CollectionMember
        fields = ('index','concept','subcollection')
        
    def __init__(self, *args, **kwargs):
        super(CollectionMemberInlineForm, self).__init__(*args, **kwargs)
        if self.instance.id and self.instance.subcollection:
            q =  Q(id=self.instance.subcollection.id)
            unassigned_collections = self.fields['subcollection'].queryset
            self.fields['subcollection'].queryset =  Collection.objects.filter(q) | unassigned_collections
        else:
            pass

            
class CollectionMemberInline(InlineAutocompleteAdmin):
    model = CollectionMember
    form = CollectionMemberInlineForm
#    list_fields = ('pref_label', )
    show_change_link = True
    max_num = 20
    fields = ('index','concept','subcollection')
    fk_name = 'collection'
 #   list_display = ('pref_label',)
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_obj = obj
        # import pdb; pdb.set_trace()
        return super(CollectionMemberInline, self).get_formset(request, obj, **kwargs)

 
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(CollectionMemberInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        
        if db_field.name == 'subcollection':
            if request._obj_ is not None:
                sc =  CollectionMember.objects.filter(subcollection__scheme=request._obj_.scheme).values_list('subcollection__id',flat=True)
                field.queryset = field.queryset.filter(scheme=request._obj_.scheme).exclude(id__in=sc).exclude(id=request._obj_.id) 
            else:
                field.queryset = field.queryset.none()

        return field
    
class CollectionAdmin(admin.ModelAdmin):
    list_filter=(OwnedSchemeListFilter,)
    search_fields = ['pref_label','uri']    
    
    def get_form(self, request, obj=None, **kwargs):
        # just save obj reference for future processing in Inline
        request._obj_ = obj
        return super(CollectionAdmin, self).get_form(request, obj, **kwargs)
    
    def get_queryset(self, request):
        qs = super(CollectionAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(scheme__authgroup__in=request.user.groups.all())
        
    inlines = [  CollectionMetaInline, CollectionMemberInline, ]
    pass

admin.site.register(Collection, CollectionAdmin)

class ImportedConceptSchemeAdmin(admin.ModelAdmin):
    pass

admin.site.register(ImportedConceptScheme, ImportedConceptSchemeAdmin)


