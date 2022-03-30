#-*- coding:utf-8 -*-
from django.contrib import admin
from skosxl.models import *
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from itertools import chain
from rdf_io.views import *
from rdf_io.admin import publish_set_action
from rdf_io.models import ConfigVar

from django.forms import ModelForm, ModelChoiceField
#from django.core.urlresolvers import resolve # < Django 1.11
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import Group
#import autocomplete_light.shortcuts as al
from django.contrib.admin import widgets
from django.contrib import messages
from django.shortcuts import render
from django.utils.safestring import mark_safe
try:
    from django.urls import resolve  
except:
    from django.core.urlresolvers import resolve    
#from skosxl.utils.autocomplete_admin import FkAutocompleteAdmin, InlineAutocompleteAdmin


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
            qs= qs.filter(id=request.GET['scheme_id'])
        except:
            pass
        if request.user.is_superuser:
            return qs
        return qs.filter(authgroup__in=request.user.groups.all()) 
        
class OwnedParentSchemeListFilter(admin.SimpleListFilter):
    title=_('Concept Scheme')
    parameter_name = 'scheme_id'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            schemes = Scheme.objects.all()
        else:  
            schemes = Scheme.objects.filter(authgroup__in=request.user.groups.all())        
        return [(c.id, c.pref_label) for c in schemes]
        
    def queryset(self, request, qs):
        #import pdb; pdb.set_trace()
        try:
            qs= qs.filter(scheme__id=request.GET['scheme_id'])
        except:
            pass
        if request.user.is_superuser:
            return qs
        return qs.filter(scheme__authgroup__in=request.user.groups.all()) 
    
class LabelInline(admin.TabularInline):
    model = Label
    readonly_fields = ('created',)
    fields = ('language','label_type','label_text','created')
    related_search_fields = {'label' : ('label_text',)}
    extra=1    

class NotationInline(admin.TabularInline):
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


# class RelAutocomplete(al.AutocompleteModelBase):
    # search_fields= ['pref_label',]
    # model = Concept
    
# al.register(Concept,search_fields= ['pref_label',] ,attrs={
        # # This will set the input placeholder attribute:
        # 'placeholder': 'Start typing ',
        # # This will set the yourlabs.Autocomplete.minimumCharacters
        # # options, the naming conversion is handled by jQuery.
        # 'data-autocomplete-minimum-characters': 1,
    # },widget_attrs={
        # 'data-widget-maximum-values': 4,
        # # Enable modern-style widget !
        # 'class': 'modern-style',
    # },)
    
# class RelSelectForm(ModelForm):
    # target_concept = ModelChoiceField(
        # queryset=Concept.objects.all(),
        # #widget=autocomplete.ModelSelect2(url='skosxl:concept-autocomplete')
    # )    
    # class Meta:
        # model = SemRelation
        # fields = ('__all__')

        
    #def __init__(self, *args, **kwargs):
    #    super(RelSelectForm, self).__init__(*args, **kwargs)
        
        # access object through self.instance...
        #import pdb; pdb.set_trace()
        #try:
        #    self.fields['target_concept'].queryset = Concept.objects.filter(scheme=self.instance.origin_concept.scheme)
        #except Exception as e:
        #    print e
        #    pass

class RelatedConceptRawIdWidget(widgets.ForeignKeyRawIdWidget):

    url_params = []

    def __init__(self, rel, admin_site, attrs=None, \
        using=None, url_params=[]):
        super(RelatedConceptRawIdWidget, self).__init__(
            rel, admin_site, attrs=attrs, using=using)
        self.url_params = url_params

 
            
    def url_parameters(self):
        res = super(RelatedConceptRawIdWidget, self).url_parameters()
        # DO YOUR CUSTOM FILTERING HERE!

        res.update(**self.url_params)
        return res
 
        
class RelInline(admin.TabularInline):
    model = SemRelation
    # form = RelSelectForm
    #form = al.modelform_factory(SemRelation, fields='__all__')
    fk_name = 'origin_concept'

    fields = ('rel_type', 'target_concept')
    #raw_id_fields = ( 'target_concept', )
    related_search_fields = {'target_concept' : ('pref_label','labels__name','definition')}
    extra = 1
    
    parent = None 
    
    def get_parent_object_from_request(self, request):
        """
        Returns the parent object from the request or None.

        Note that this only works for Inlines, because the `parent_model`
        is not available in the regular admin.ModelAdmin as an attribute.
        """

        resolved = resolve(request.path_info)
        if resolved.args:
            return self.parent_model.objects.get(pk=resolved.args[0])
        return None
    
    def has_add_permission(self, request, obj=None):
        self.parent = self.get_parent_object_from_request(request)

        # No parent - return original has_add_permission() check
        return super(RelInline, self).has_add_permission(request,self.parent)
    
    
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        
        field = super(RelInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'target_concept' and request._obj_ and request._obj_.scheme and request._obj_.id :
            field.queryset = field.queryset.filter(scheme=request._obj_.scheme).exclude(id=request._obj_.id) 

#            try:
#                field.widget = RelatedConceptRawIdWidget(SemRelation._meta.get_field('target_concept').rel, admin.site,url_params={'scheme_id': self.parent.scheme.id})
#            except:
#                pass
            #import pdb; pdb.set_trace()
        return field

def create_action(scheme):
    fun = lambda modeladmin, request, queryset: queryset.update(scheme=scheme)
    name = "moveto_%s" % (scheme.slug,)
    return (name, (fun, name, _(u'Make selected concept part of the "%s" scheme') % (scheme,)))


class ConceptMetaInline(admin.TabularInline):
    model = ConceptMeta
    verbose_name = 'Additional property'
    verbose_name_plural = 'Additional properties'
#    list_fields = ('pref_label', )
    show_change_link = True
    max_num = 20
    fields = ('subject','metaprop','value')
 #   list_display = ('pref_label',)
    extra = 0

class ConceptAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ConceptAdminForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['supersedes'].queryset = Concept.objects.filter(scheme=self.instance.scheme)
        else:
            self.fields['supersedes'].queryset = Concept.objects.filter(scheme=None)
        
class ConceptAdmin(admin.ModelAdmin):
    form = ConceptAdminForm
    readonly_fields = ('created','modified')
    search_fields = ['term','uri','pref_label','slug','definition', 'rank__pref_label']
    list_display = ('term','pref_label','uri','scheme','top_concept','rank')
    #list_editable = ('status','term','scheme','top_concept')
    list_filter=(OwnedParentSchemeListFilter,'status')
    change_form_template = 'admin_concept_change.html'
    change_list_template = 'admin_concept_list.html'
    
    def get_form(self, request, obj=None, **kwargs):
        # just save obj reference for future processing in Inline
        request._obj_ = obj
        return super(ConceptAdmin, self).get_form(request, obj, **kwargs)
        
    def changelist_view(self, request, extra_context=None):
        request.GET._mutable=True
        try:
            self.origin_id = request.GET.pop('origin_id')[0]
        except KeyError:
            self.origin_id = None
        try:
            self.scheme_id = request.GET.pop('scheme_id')[0]
        except KeyError:
            self.scheme_id = None
            
        request.GET._mutable=False
        
        try :
            scheme_id = int(request.GET['scheme_id'])
        except KeyError :
            scheme_id = None # FIXME: if no scheme filter is called, get the first (or "General") : a fixture to create one ?
        return super(ConceptAdmin, self).changelist_view(request, 
                                        extra_context={'scheme_id':scheme_id})
            
    fieldsets = (   (_(u'Scheme'), {'fields':('term','uri','scheme','pref_label','rank','top_concept','definition')}),
                    (_(u'Meta-data'),
                    {'fields':('status','supersedes','prefStyle','changenote','created','modified'),
                     'classes':('collapse',)}),
                     )
    inlines = [   ConceptMetaInline , NotationInline, LabelInline, RelInline, SKOSMappingInline]
    def get_actions(self, request):
        actions = super(ConceptAdmin, self).get_actions(request)
        actions.update(dict(create_action(s) for s in Scheme.objects.all()))
        return actions

    def get_queryset(self, request):

        qs = super(ConceptAdmin, self).get_queryset(request)
        try:
            if self.scheme_id :
                qs = qs.filter(scheme__id=self.scheme_id)
        except:
            pass
        if request.user.is_superuser:
            return qs
        return qs.filter(scheme__authgroup__in=request.user.groups.all())
        
    def save_model(self, request, obj, form, change):
        # can we find the scheme and link it here in all cases?
        # import pdb; pdb.set_trace()
        super(ConceptAdmin,self).save_model(request, obj, form, change)
        
    def get_parent_object_from_request(self, request):
        """
        Returns the parent object from the request or None.

        Note that this only works for Inlines, because the `parent_model`
        is not available in the regular admin.ModelAdmin as an attribute.
        """
        resolved = resolve(request.path_info)
        if resolved.args:
            return self.parent_model.objects.get(pk=resolved.args[0])
        return None
        
    def response_add(self, request, obj, post_url_continue=None):
        #import pdb; pdb.set_trace()
        if '_addanother' in request.POST:
            url = reverse("admin:skosxl_concept_add")
            scheme_id = request.POST['scheme']
            qs = '?scheme=%s' % scheme_id
            return HttpResponseRedirect(''.join((url, qs)))
        else:
            return super(ConceptAdmin, self).response_add(request, obj)
            
    def response_change(self, request, obj, post_url_continue=None):
        """This makes the response go to the newly created model's change page
        without using reverse"""
        if '_addanother' in request.POST:
            url = reverse("admin:skosxl_concept_add")
            scheme_id = request.POST['scheme']
            qs = '?scheme=%s' % scheme_id
            return HttpResponseRedirect(''.join((url, qs)))
        else:
            return super(ConceptAdmin, self).response_change(request, obj)
    
admin.site.register(Concept, ConceptAdmin)



def create_concept_command(modeladmin, request, queryset):
    for label in queryset:
        label.create_concept_from_label()
create_concept_command.short_description = _(u"Create concept(s) from selected label(s)")



class SchemeMetaInline(admin.TabularInline):
    model = SchemeMeta
#    list_fields = ('pref_label', )
    show_change_link = True
    max_num = 20
    fields = ('subject','metaprop','value')
 #   list_display = ('pref_label',)
    extra = 0
    verbose_name = 'Additional property'
    verbose_name_plural = 'Additional properties'
#  
class ConceptInline(admin.TabularInline):
    model = Concept
#    list_fields = ('pref_label', )
    show_change_link = True
    max_num = 0
    fields = ('top_concept','pref_label','term','rank')
    ordering = ('-top_concept','rank','pref_label')
 #   list_display = ('pref_label',)
    related_search_fields = {'concept' : ('prefLabel','definition')}
    extra = 1
    

class CollectionInline(admin.TabularInline):
    model = Collection
#    list_fields = ('pref_label', )
    show_change_link = True
    max_num = 20
    fields = ('pref_label',)
 #   list_display = ('pref_label',)
    #related_search_fields = {'concept' : ('prefLabel','definition')}
    extra = 0
    
class LabelAdmin(admin.ModelAdmin):
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


def fill_defaultlabel(modeladmin, request, queryset):
    #import pdb; pdb.set_trace()
    for scheme in queryset:
        Concept.propagate_term2label(scheme=scheme)
        Collection.propagate_term2label(scheme=scheme)
    modeladmin.message_user(request,"done this")
    
fill_defaultlabel.short_description = "Propagate base terms to default label where not set."       

class OwnedByFilter(admin.SimpleListFilter):
    title=_('Owner')
    parameter_name = 'authgroup_id'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
             owners=Scheme.objects.values_list('authgroup', flat=True).distinct()
             return [('None','None'),] +  [ (c, Group.objects.get(id=c).name ) for c in filter(None,owners)]
        else:  
             return [] 
        
    def queryset(self, request, qs):
        #import pdb; pdb.set_trace()
        try:
            if request.user.is_superuser:
                if request.GET['authgroup_id'] != "None" :
                    qs= qs.filter(authgroup__id=request.GET['authgroup_id'])
                else:
                    qs= qs.filter(authgroup__isnull=True)
        except:
            pass              
        return qs

class SchemeBase(Scheme):
    verbose_name = 'Scheme without its member concepts - use Scheme if list is small'
    #fields = ('uri')
    class Meta:
        proxy = True

       
class SchemeAdmin(admin.ModelAdmin):
    readonly_fields = ('created','modified')
    inlines = [  SchemeMetaInline, ]  
    model=SchemeBase
    search_fields = ['pref_label','uri',]
    actions= ['publish_options', 'fill_defaultlabel', 'set_batch_owner']
    verbose_name = 'Scheme with its member concepts - use Scheme bases if this may be a inconveniently large list'
    # list_filter=('importedconceptscheme__description',)
    list_filter=(OwnedByFilter,)
    list_display = ('pref_label','authgroup')
    
    def set_batch_owner(self,request,queryset):
        """batch update manager group"""
        if 'apply' in request.POST:
            # The user clicked submit on the intermediate form.
            # Perform our update action:
            if not request.POST.get('group') :
                self.message_user(request,
                              "Cancelled action")
            else:               
                queryset.update(authgroup=Group.objects.get(id=request.POST.get('group')))
                self.message_user(request,
                              "Updated authorised group for selected schemes")
            return HttpResponseRedirect(request.get_full_path())
        return render(request,
                      'admin/admin_batch_set_owner.html',
                      context={'schemes':queryset, 'groups':Group.objects.all()
                        })
    def publish_options(self,request,queryset):
        """Batch publish with a set of mode options"""
        if 'apply' in request.POST:
            # The user clicked submit on the intermediate form.
            # Perform our update action:
            if request.POST.get('mode') == "CANCEL" :
                self.message_user(request,
                              "Cancelled publish action")
            else:
                checkuri = 'checkuri' in request.POST
                logfile= publish_set_action(queryset,'scheme',check=checkuri,mode=request.POST.get('mode'))
                self.message_user(request,
                              mark_safe('started publishing in {} mode for {} schemes at <A HREF="{}" target="_log">{}</A>'.format(request.POST.get('mode'),queryset.count(),logfile,logfile) ) )
            return HttpResponseRedirect(request.get_full_path())
        return render(request,
                      'admin/admin_publish.html',
                      context={'schemes':queryset, 
                        'pubvars': ConfigVar.getvars('PUBLISH') ,
                        'reviewvars': ConfigVar.getvars('REVIEW') ,
                        })


    def save_model(self, request, obj, form, change):
        if not obj.authgroup:
            if not request.user.is_superuser:
             obj.authgroup = request.user.groups.first()
        super(SchemeAdmin,self).save_model(request, obj, form, change)
        
    def get_queryset(self, request):
        qs = super(SchemeAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(authgroup__in=request.user.groups.all())

admin.site.register(SchemeBase, SchemeAdmin)

    

class SchemeConceptAdmin(SchemeAdmin):
    
    readonly_fields = ('created','modified')
    inlines = [  SchemeMetaInline, CollectionInline, ConceptInline, ]
  
admin.site.register(Scheme, SchemeConceptAdmin)

class ConceptRankAdmin(admin.ModelAdmin):
    list_display = ('pref_label','level','scheme')
    list_filter = (('scheme',admin.RelatedOnlyFieldListFilter),)
    pass
  
admin.site.register(ConceptRank, ConceptRankAdmin)

class CollectionMetaInline(admin.TabularInline):
    model = CollectionMeta
#    list_fields = ('pref_label', )
    show_change_link = True
    max_num = 20
    fields = ('subject','metaprop','value')
 #   list_display = ('pref_label',)
 #   extra = 1
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

            
class CollectionMemberInline(admin.TabularInline):
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
    list_filter=(OwnedParentSchemeListFilter,)
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

class DerivedSchemesInline(admin.TabularInline):
    readonly_fields = ('label',)
    model = ImportedConceptScheme.schemes.through
    fields = ('label',)
    #model=Scheme
    extra = 0
    can_delete = False
    def label(self,instance):
        return mark_safe('<a href="/admin/skosxl/scheme/%s/change/" target="_new">%s</a>' % (instance.scheme.id, instance.scheme.pref_label))
    label.allow_tags = True

def bulk_resave(modeladmin, request, queryset):
    #import pdb; pdb.set_trace()
    for obj in queryset:
        obj.save()
        
bulk_resave.short_description = "Post-save process all selected resources"       


    
class ImportedConceptSchemeAdmin(admin.ModelAdmin):
    exclude = [ 'resource_type', 'target_repo', 'schemes']
    inlines = [  DerivedSchemesInline , ]
    actions= [bulk_resave,]
    list_filter = ('resource_type', 'target_repo')
    search_fields = ['description', 'remote', 'graph', 'schemes__pref_label']
    resourcetype = 'scheme'
    def save_model(self, request, obj, form, change):
        if not obj.authgroup:
            if not request.user.is_superuser:
             obj.authgroup = request.user.groups.first()
        super(ImportedConceptSchemeAdmin,self).save_model(request, obj, form, change)
        
    def get_queryset(self, request):
        qs = super(ImportedConceptSchemeAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(authgroup__in=request.user.groups.all())

admin.site.register(ImportedConceptScheme, ImportedConceptSchemeAdmin)


