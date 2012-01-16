#-*- coding:utf-8 -*-
from django.contrib import admin
from skosxl.models import *
from django.utils.translation import ugettext_lazy as _

from coop.autocomplete_admin import FkAutocompleteAdmin,InlineAutocompleteAdmin, NoLookupsForeignKeyAutocompleteAdmin

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
#related_search_fields = {'label' : ('name','slug')}
    extra=1    
    
# class SKOSMappingInline(admin.TabularInline):
#     model = MapRelation
#     fields = ('voc','target_label','match_type',)
#     readonly_fields = ('target_label','uri')
#     extra=1    

class RelInline(InlineAutocompleteAdmin):
    model = SemRelation
    fk_name = 'origin_concept'
    fields = ('rel_type', 'target_concept')
    related_search_fields = {'target_concept' : ('labels__name','definition')}#c.labels.all()[0].term.literal
    extra = 1

def create_action(scheme):
    fun = lambda modeladmin, request, queryset: queryset.update(scheme=scheme)
    name = "moveto_%s" % (scheme.slug,)
    return (name, (fun, name, _(u'Make selected concept part of the "%s" scheme') % (scheme,)))


class ConceptAdmin(NoLookupsForeignKeyAutocompleteAdmin):
    readonly_fields = ('created','modified')
    search_fields = ['pref_label','slug','definition']
    list_display = ('pref_label','notation','status','scheme','top_concept','created')
    list_editable = ('status','scheme','top_concept')
    list_filter = ('scheme','status')
    change_form_template = 'admin_concept_change.html'
    fieldsets = (   (_(u'Scheme'), {'fields':('scheme','top_concept')}),
                    (_(u'Meta-data'),
                    {'fields':('notation',('definition','changenote'),'created','modified'),
                     'classes':('collapse',)}),
                     )
    inlines = [  LabelInline, RelInline, ]
    def get_actions(self, request):
        return dict(create_action(s) for s in Scheme.objects.all())



def create_concept_command(modeladmin, request, queryset):
    for label in queryset:
        label.create_concept_from_label()
create_concept_command.short_description = _(u"Create concept(s) from selected label(s)")


class LabelAdmin(admin.ModelAdmin):
    list_display = ('name','slug','label_type','concept')
    fields = ('name','language','label_type','concept')
    actions = [create_concept_command]
    #list_editable = ('name','slug')
    search_fields = ['name','slug']
    

class ConceptInline(InlineAutocompleteAdmin):
    model = Concept
    readonly_fields = ('pref_label',)
    fields = ('pref_label','top_concept','status')
    related_search_fields = {'concept' : ('prefLabel','definition')}
    extra = 0

class SchemeAdmin(FkAutocompleteAdmin):
    readonly_fields = ('created','modified')
    inlines = [  ConceptInline, ]
   
admin.site.register(Label, LabelAdmin)

admin.site.register(Concept, ConceptAdmin)

admin.site.register(Scheme, SchemeAdmin)




