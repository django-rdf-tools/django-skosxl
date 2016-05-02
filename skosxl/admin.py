#-*- coding:utf-8 -*-
from django.contrib import admin
from skosxl.models import *
from django.utils.translation import ugettext_lazy as _

from skosxl.utils.autocomplete_admin import FkAutocompleteAdmin, InlineAutocompleteAdmin, NoLookupsForeignKeyAutocompleteAdmin


# class LabelInline(InlineAutocompleteAdmin):
#     model = LabelProperty
#     fields = ('label','label_type',)
#     related_search_fields = {'label' : ('name','slug')}
#     extra=1
#     
    
class LabelInline(InlineAutocompleteAdmin):
    model = Label
    readonly_fields = ('slug','created')
    fields = ('language','label_type','name','slug','created')
    related_search_fields = {'label' : ('name','slug')}
    extra=1    

class NotationInline(InlineAutocompleteAdmin):
    model = Notation
    # readonly_fields = ('slug','created')
    fields = ('code','namespace')
    # related_search_fields = {'label' : ('name','slug')}
    extra=1    
    
    
class SKOSMappingInline(admin.TabularInline):
    model = MapRelation
    fk_name = 'origin_concept'
    fields = ('match_type','uri')
#    related_search_fields = {'target_concept' : ('labels__name','definition')}
    extra=1    

class RelInline(InlineAutocompleteAdmin):
    model = SemRelation
    fk_name = 'origin_concept'
    fields = ('rel_type', 'target_concept')
    related_search_fields = {'target_concept' : ('labels__name','definition')}
    extra = 1

def create_action(scheme):
    fun = lambda modeladmin, request, queryset: queryset.update(scheme=scheme)
    name = "moveto_%s" % (scheme.slug,)
    return (name, (fun, name, _(u'Make selected concept part of the "%s" scheme') % (scheme,)))


class ConceptAdmin(FkAutocompleteAdmin):
    readonly_fields = ('created','modified')
    search_fields = ['pref_label','slug','definition']
    list_display = ('pref_label','status','scheme','top_concept','created')
    list_editable = ('status','scheme','top_concept')

    list_filter = ('scheme','status')
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
            scheme_id = int(request.GET['scheme__id__exact'])
        except KeyError :
            scheme_id = 1 # FIXME: if no scheme filter is called, get the first (or "General") : a fixture to create one ?
        return super(ConceptAdmin, self).changelist_view(request, 
                                        extra_context={'scheme_id':scheme_id})
            
    fieldsets = (   (_(u'Scheme'), {'fields':('scheme','pref_label','top_concept')}),
                    (_(u'Meta-data'),
                    {'fields':(('definition','changenote'),'created','modified'),
                     'classes':('collapse',)}),
                     )
    inlines = [   NotationInline, LabelInline, RelInline, SKOSMappingInline]
    def get_actions(self, request):
        return dict(create_action(s) for s in Scheme.objects.all())

admin.site.register(Concept, ConceptAdmin)



def create_concept_command(modeladmin, request, queryset):
    for label in queryset:
        label.create_concept_from_label()
create_concept_command.short_description = _(u"Create concept(s) from selected label(s)")


class ConceptInline(InlineAutocompleteAdmin):
    model = Concept
    # readonly_fields = ('pref_label',)
    fields = ('pref_label','top_concept','status')
    related_search_fields = {'concept' : ('prefLabel','definition')}
    extra = 0

class LabelAdmin(FkAutocompleteAdmin):
    list_display = ('label_text','slug','label_type','concept')
    fields = ('label_text','language','label_type','concept')
    related_search_fields = {'concept' : ('pref_label','definition')}
    actions = [create_concept_command]
    #list_editable = ('name','slug')
    search_fields = ['name','slug']    

admin.site.register(Label, LabelAdmin)    

class NamespaceAdmin(FkAutocompleteAdmin):
    list_display = ('uri','prefix','notes','tags')
    fields = ('uri','prefix','notes','tags')
#    related_search_fields = {'concept' : ('pref_label','definition')}
    #list_editable = ('name','slug')
    search_fields = ['uri','prefix']    

    
admin.site.register(Namespace, NamespaceAdmin)  
    

class SchemeAdmin(FkAutocompleteAdmin):
    readonly_fields = ('created','modified')
    inlines = [  ConceptInline, ]
  
admin.site.register(Scheme, SchemeAdmin)




