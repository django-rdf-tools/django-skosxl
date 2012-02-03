#
#    Autocomplete feature for admin panel
#
#    Most of the code has been written by Jannis Leidel, then updated a bit
#    for django_extensions, finally reassembled and extended by Mikele Pasin. 
# 
#    http://jannisleidel.com/2008/11/autocomplete-form-widget-foreignkey-model-fields/
#    http://code.google.com/p/django-command-extensions/
#    http://magicrebirth.wordpress.com/
#
#    to_string_function, Satchmo adaptation and some comments added by emes
#    (Michal Salaban)
#




#  ==============
#  HOW-TO
#  ==============

# 1.Put this file somewhere in your application folder

# 2.Add the 'autocomplete' folder with the media files to your usual media folder

# 3.Add the 'admin/autocomplete' folder to your templates folder

# 4.Add the extrafilters.py file in the templatetags directory of your application (or just add its contents to 
#   your custom template tags if you already have some).
#  All is needed is the 'cut' filter, for making the code used in the inline-autocomplete form javascript friendly

# 5. When defining your models admin, import the relevant admin and use it:
#  .....
# from myproject.mypackage.autocomplete_admin import FkAutocompleteAdmin
#  .....
#  .....
# class Admin (FkAutocompleteAdmin):
#   related_search_fields = { 'person': ('name',)}
#  .....


#  ==============
# TROUBLE SHOOTING:
#  ==============

# ** sometimes things don't work cause you have to add 'from django.conf.urls.defaults import *' to the modules where you use the autocomplete 
# ** if you're using the inline-autocompletion, make sure that the main admin class the inline belong to is a subclass FkAutocompleteAdmin
# ** you may need to hack it a bit to make it work for you - it's been done in a rush!


#  ==============
# the code now....
#  ==============


from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.text import truncate_words
from django.template.loader import render_to_string
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
import operator
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib import admin
from django.db import models
from django.db.models.query import QuerySet
from django.utils.encoding import smart_str
from django.utils.translation import ugettext as _
from django.utils.text import get_text_list
# added by mikele
from django.conf.urls.defaults import *




class FkSearchInput(ForeignKeyRawIdWidget):
    """
    A Widget for displaying ForeignKeys in an autocomplete search input 
    instead in a <select> box.
    """

    # Set in subclass to render the widget with a different template
    widget_template = None
    # Set this to the patch of the search view
    search_path = '../foreignkey_autocomplete/'

    class Media:
        css = {
            'all': ('autocomplete/css/jquery.autocomplete.css',)
        }
        js = (
            #'autocomplete/js/jquery.js',
            'autocomplete/js/jquery.bgiframe.min.js',
            'autocomplete/js/jquery.ajaxQueue.js',
            'autocomplete/js/jquery.autocomplete.js',
        )

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        obj = self.rel.to._default_manager.get(**{key: value})
        return truncate_words(obj, 14)

    def __init__(self, rel, search_fields, attrs=None):
        self.search_fields = search_fields
        super(FkSearchInput, self).__init__(rel, attrs)

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        output = [super(FkSearchInput, self).render(name, value, attrs)]
        opts = self.rel.to._meta
        app_label = opts.app_label
        model_name = opts.object_name.lower()
        related_url = '../../../%s/%s/' % (app_label, model_name)
        params = self.url_parameters()
        if params:
            url = '?' + '&amp;'.join(['%s=%s' % (k, v) for k, v in params.items()])
        else:
            url = ''
        if not attrs.has_key('class'):
            attrs['class'] = 'vForeignKeyRawIdAdminField'
        # Call the TextInput render method directly to have more control
        output = [forms.TextInput.render(self, name, value, attrs)]
        if value:
            label = self.label_for_value(value)
        else:
            label = u''
        context = {
            'url': url,
            'related_url': related_url,
            'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
            'search_path': self.search_path,
            'search_fields': ','.join(self.search_fields),
            'model_name': model_name,
            'app_label': app_label,
            'label': label,
            'name': name,
        }


        output.append(render_to_string(self.widget_template or (
            '%s/%s/fk_searchinput.html' % (app_label, model_name),
            '%s/fk_searchinput.html' % app_label,
            'admin/autocomplete/fk_searchinput.html',
        ), context))
        output.reverse()
        return mark_safe(u''.join(output))






class NoLookupsForeignKeySearchInput(ForeignKeyRawIdWidget):
    """
    A Widget for displaying ForeignKeys in an autocomplete search input 
    instead in a <select> box.
    """

    # Set in subclass to render the widget with a different template
    widget_template = None
    # Set this to the patch of the search view
    search_path = '../foreignkey_autocomplete/'

    class Media:
        css = {
            'all': ('autocomplete/css/jquery.autocomplete.css',)
        }
        js = (
            #'autocomplete/js/jquery.js',
            'autocomplete/js/jquery.bgiframe.min.js',
            'autocomplete/js/jquery.ajaxQueue.js',
            'autocomplete/js/jquery.autocomplete.js',
        )

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        obj = self.rel.to._default_manager.get(**{key: value})
        return truncate_words(obj, 14)

    def __init__(self, rel, search_fields, attrs=None):
        self.search_fields = search_fields
        super(NoLookupsForeignKeySearchInput, self).__init__(rel, attrs)

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        output = [super(NoLookupsForeignKeySearchInput, self).render(name, value, attrs)]
        opts = self.rel.to._meta
        app_label = opts.app_label
        model_name = opts.object_name.lower()
        related_url = '../../../%s/%s/' % (app_label, model_name)
        params = self.url_parameters()
        if params:
            url = '?' + '&amp;'.join(['%s=%s' % (k, v) for k, v in params.items()])
        else:
            url = ''
        if not attrs.has_key('class'):
            attrs['class'] = 'vForeignKeyRawIdAdminField'
        # Call the TextInput render method directly to have more control
        output = [forms.TextInput.render(self, name, value, attrs)]
        if value:
            label = self.label_for_value(value)
        else:
            label = u''
        context = {
            'url': url,
            'related_url': related_url,
            'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
            'search_path': self.search_path,
            'search_fields': ','.join(self.search_fields),
            'model_name': model_name,
            'app_label': app_label,
            'label': label,
            'name': name,
        }

# tried to change widget_template but it needs a subclass (of what?) not a string

        output.append(render_to_string(self.widget_template or (
            '%s/%s/foreignkey_searchinput.html' % (app_label, model_name),
            '%s/foreignkey_searchinput.html' % app_label,
            'admin/autocomplete/nolookups_foreignkey_searchinput.html',
        ), context))
        output.reverse()
        return mark_safe(u''.join(output))



class InlineSearchInput(ForeignKeyRawIdWidget):
    """
    A Widget for displaying ForeignKeys in an autocomplete search input 
    instead in a <select> box.
    """

    # Set in subclass to render the widget with a different template
    widget_template = None
    # Set this to the patch of the search view
    search_path = '../foreignkey_autocomplete/'

    class Media:
        css = {
            'all': ('autocomplete/css/jquery.autocomplete.css',)
        }
        js = (
            #'autocomplete/js/jquery.js',
            'autocomplete/js/jquery.bgiframe.min.js',
            'autocomplete/js/jquery.ajaxQueue.js',
            'autocomplete/js/jquery.autocomplete.js',
        )

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        obj = self.rel.to._default_manager.get(**{key: value})
        return truncate_words(obj, 14)

    def __init__(self, rel, search_fields, attrs=None):
        self.search_fields = search_fields
        super(InlineSearchInput, self).__init__(rel, attrs)

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        output = [super(InlineSearchInput, self).render(name, value, attrs)]
        opts = self.rel.to._meta
        app_label = opts.app_label
        model_name = opts.object_name.lower()
        related_url = '../../../%s/%s/' % (app_label, model_name)
        params = self.url_parameters()
        if params:
            url = '?' + '&amp;'.join(['%s=%s' % (k, v) for k, v in params.items()])
        else:
            url = ''
        if not attrs.has_key('class'):
            attrs['class'] = 'vForeignKeyRawIdAdminField'
        # Call the TextInput render method directly to have more control
        output = [forms.TextInput.render(self, name, value, attrs)]
        if value:
            label = self.label_for_value(value)
        else:
            label = u''
        context = {
            'url': url,
            'related_url': related_url,
            'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
            'search_path': self.search_path,
            'search_fields': ','.join(self.search_fields),
            'model_name': model_name,
            'app_label': app_label,
            'label': label,
            'name': name,
        }

# tried to change widget_template but it needs a subclass (of what?) not a string

        output.append(render_to_string(self.widget_template or (
            '%s/%s/inline_searchinput.html' % (app_label, model_name),
            '%s/inline_searchinput.html' % app_label,
            'admin/autocomplete/inline_searchinput.html',
        ), context))
        output.reverse()
        return mark_safe(u''.join(output))









# ====================================
# ====================================
#  standard FK autocomplete
#  ===================================
#  ===================================




class FkAutocompleteAdmin(admin.ModelAdmin):
    """ 
    Admin class for models using the autocomplete feature.

    There are two additional fields:
       - related_search_fields: defines fields of managed model that
         have to be represented by autocomplete input, together with
         a list of target model fields that are searched for
         input string, e.g.:

         related_search_fields = {
            'author': ('first_name', 'email'),
         }

       - related_string_functions: contains optional functions which
         take target model instance as only argument and return string
         representation. By default __unicode__() method of target
         object is used.
    """

    related_search_fields = {}
    related_string_functions = {}

    # def __call__(self, request, url):
    #     if url is None:
    #         pass
    #     elif url == 'foreignkey_autocomplete':
    #         return self.foreignkey_autocomplete(request)
    #     return super(ForeignKeyAutocompleteAdmin, self).__call__(request, url)

    def get_urls(self):
        urls = super(FkAutocompleteAdmin,self).get_urls()
        search_url = patterns('',
            (r'^foreignkey_autocomplete/$', self.admin_site.admin_view(self.foreignkey_autocomplete))
        )
        return search_url + urls

    def foreignkey_autocomplete(self, request):
        """
        Searches in the fields of the given related model and returns the 
        result as a simple string to be used by the jQuery Autocomplete plugin
        """
        query = request.GET.get('q', None)
        app_label = request.GET.get('app_label', None)
        model_name = request.GET.get('model_name', None)
        search_fields = request.GET.get('search_fields', None)
        object_pk = request.GET.get('object_pk', None)
        try:
            to_string_function = self.related_string_functions[model_name]
        except KeyError:
            to_string_function = lambda x: x.__unicode__()
        if search_fields and app_label and model_name and (query or object_pk):
            def construct_search(field_name):
                # use different lookup methods depending on the notation
                if field_name.startswith('^'):
                    return "%s__istartswith" % field_name[1:]
                elif field_name.startswith('='):
                    return "%s__iexact" % field_name[1:]
                elif field_name.startswith('@'):
                    return "%s__search" % field_name[1:]
                else:
                    return "%s__icontains" % field_name
            model = models.get_model(app_label, model_name)
            queryset = model._default_manager.all()
            data = ''
            if query:
                for bit in query.split():
                    or_queries = [models.Q(**{construct_search(
                        smart_str(field_name)): smart_str(bit)})
                            for field_name in search_fields.split(',')]
                    other_qs = QuerySet(model)
                    other_qs.dup_select_related(queryset)
                    other_qs = other_qs.filter(reduce(operator.or_, or_queries))
                    queryset = queryset & other_qs
                data = ''.join([u'%s|%s\n' % (
                    to_string_function(f), f.pk) for f in queryset])
            elif object_pk:
                try:
                    obj = queryset.get(pk=object_pk)
                except:
                    pass
                else:
                    data = to_string_function(obj)
            return HttpResponse(data)
        return HttpResponseNotFound()

    def get_help_text(self, field_name, model_name):
        searchable_fields = self.related_search_fields.get(field_name, None)
        if searchable_fields:
            help_kwargs = {
                'model_name': model_name,
                'field_list': get_text_list(searchable_fields, _('and')),
            }
            return _('Use the left field to do %(model_name)s lookups in the fields %(field_list)s.') % help_kwargs
        return ''


# this method gets called when creating the formfields - probably this is what you need to extend
#  in the replicated version of ForeignKeyAutocompleteAdmin

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Overrides the default widget for Foreignkey fields if they are
        specified in the related_search_fields class attribute.
        """
        if (isinstance(db_field, models.ForeignKey) and 
            db_field.name in self.related_search_fields):
            model_name = db_field.rel.to._meta.object_name
            help_text = self.get_help_text(db_field.name, model_name)
            if kwargs.get('help_text'):
                help_text = u'%s %s' % (kwargs['help_text'], help_text)
            kwargs['widget'] = FkSearchInput(db_field.rel,
                                    self.related_search_fields[db_field.name])
            kwargs['help_text'] = help_text
        return super(FkAutocompleteAdmin,
            self).formfield_for_dbfield(db_field, **kwargs)




# ====================================
# ====================================
#  an autocomplete that doesn't display the raw_id links
#  ===================================
#  ===================================



class NoLookupsForeignKeyAutocompleteAdmin(admin.ModelAdmin):
    """ 
        In certain cases you do not want to have the usual raw_id lenses for related items lookup.
        Code mostly as above, changes only the template that renders it.
    """

    related_search_fields = {}
    related_string_functions = {}

    # def __call__(self, request, url):
    #     if url is None:
    #         pass
    #     elif url == 'foreignkey_autocomplete':
    #         return self.foreignkey_autocomplete(request)
    #     return super(ForeignKeyAutocompleteAdmin, self).__call__(request, url)

    def get_urls(self):
        urls = super(NoLookupsForeignKeyAutocompleteAdmin,self).get_urls()
        search_url = patterns('',
            (r'^foreignkey_autocomplete/$', self.admin_site.admin_view(self.foreignkey_autocomplete))
        )
        return search_url + urls

    def foreignkey_autocomplete(self, request):
        """
        Searches in the fields of the given related model and returns the 
        result as a simple string to be used by the jQuery Autocomplete plugin
        """
        query = request.GET.get('q', None)
        app_label = request.GET.get('app_label', None)
        model_name = request.GET.get('model_name', None)
        search_fields = request.GET.get('search_fields', None)
        object_pk = request.GET.get('object_pk', None)
        try:
            to_string_function = self.related_string_functions[model_name]
        except KeyError:
            to_string_function = lambda x: x.__unicode__()
        if search_fields and app_label and model_name and (query or object_pk):
            def construct_search(field_name):
                # use different lookup methods depending on the notation
                if field_name.startswith('^'):
                    return "%s__istartswith" % field_name[1:]
                elif field_name.startswith('='):
                    return "%s__iexact" % field_name[1:]
                elif field_name.startswith('@'):
                    return "%s__search" % field_name[1:]
                else:
                    return "%s__icontains" % field_name
            model = models.get_model(app_label, model_name)
            queryset = model._default_manager.all()
            data = ''
            if query:
                for bit in query.split():
                    or_queries = [models.Q(**{construct_search(
                        smart_str(field_name)): smart_str(bit)})
                            for field_name in search_fields.split(',')]
                    other_qs = QuerySet(model)
                    other_qs.dup_select_related(queryset)
                    other_qs = other_qs.filter(reduce(operator.or_, or_queries))
                    queryset = queryset & other_qs
                data = ''.join([u'%s|%s\n' % (
                    to_string_function(f), f.pk) for f in queryset])
            elif object_pk:
                try:
                    obj = queryset.get(pk=object_pk)
                except:
                    pass
                else:
                    data = to_string_function(obj)
            return HttpResponse(data)
        return HttpResponseNotFound()

    def get_help_text(self, field_name, model_name):
        searchable_fields = self.related_search_fields.get(field_name, None)
        if searchable_fields:
            help_kwargs = {
                'model_name': model_name,
                'field_list': get_text_list(searchable_fields, _('and')),
            }
            return _('Use the left field to do %(model_name)s lookups in the fields %(field_list)s.') % help_kwargs
        return ''


# this method gets called when creating the formfields - probably this is what you need to extend
#  in the replicated version of ForeignKeyAutocompleteAdmin

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Overrides the default widget for Foreignkey fields if they are
        specified in the related_search_fields class attribute.
        """
        if (isinstance(db_field, models.ForeignKey) and 
            db_field.name in self.related_search_fields):
            model_name = db_field.rel.to._meta.object_name
            help_text = self.get_help_text(db_field.name, model_name)
            if kwargs.get('help_text'):
                help_text = u'%s %s' % (kwargs['help_text'], help_text)
            kwargs['widget'] = NoLookupsForeignKeySearchInput(db_field.rel,
                                    self.related_search_fields[db_field.name])
            kwargs['help_text'] = help_text
        return super(NoLookupsForeignKeyAutocompleteAdmin,
            self).formfield_for_dbfield(db_field, **kwargs)






#  ======================================
#  ======================================
#  an autocomplete for INLINES
#  ======================================
#  ======================================




class InlineAutocompleteAdmin(admin.TabularInline):
    """ 
    Admin class for models using the autocomplete feature in inlines.

    At the moment, this autocomplete works only if the admin of the model including the inline-admin is
    itself a subclass of an autocomplete Admin (e.g., ForeignKeyAutocompleteAdmin)
    
    """

    related_search_fields = {}
    related_string_functions = {}

    # def __call__(self, request, url):
    #     if url is None:
    #         pass
    #     elif url == 'foreignkey_autocomplete':
    #         return self.foreignkey_autocomplete(request)
    #     return super(ForeignKeyAutocompleteAdmin, self).__call__(request, url)

    def get_urls(self):
        urls = super(InlineAutocompleteAdmin,self).get_urls()
        search_url = patterns('',
            (r'^foreignkey_autocomplete/$', self.admin_site.admin_view(self.foreignkey_autocomplete))
        )
        return search_url + urls

    def foreignkey_autocomplete(self, request):
        """
        Searches in the fields of the given related model and returns the 
        result as a simple string to be used by the jQuery Autocomplete plugin
        """
        query = request.GET.get('q', None)
        app_label = request.GET.get('app_label', None)
        model_name = request.GET.get('model_name', None)
        search_fields = request.GET.get('search_fields', None)
        object_pk = request.GET.get('object_pk', None)
        try:
            to_string_function = self.related_string_functions[model_name]
        except KeyError:
            to_string_function = lambda x: x.__unicode__()
        if search_fields and app_label and model_name and (query or object_pk):
            def construct_search(field_name):
                # use different lookup methods depending on the notation
                if field_name.startswith('^'):
                    return "%s__istartswith" % field_name[1:]
                elif field_name.startswith('='):
                    return "%s__iexact" % field_name[1:]
                elif field_name.startswith('@'):
                    return "%s__search" % field_name[1:]
                else:
                    return "%s__icontains" % field_name
            model = models.get_model(app_label, model_name)
            queryset = model._default_manager.all()
            data = ''
            if query:
                for bit in query.split():
                    or_queries = [models.Q(**{construct_search(
                        smart_str(field_name)): smart_str(bit)})
                            for field_name in search_fields.split(',')]
                    other_qs = QuerySet(model)
                    other_qs.dup_select_related(queryset)
                    other_qs = other_qs.filter(reduce(operator.or_, or_queries))
                    queryset = queryset & other_qs
                data = ''.join([u'%s|%s\n' % (
                    to_string_function(f), f.pk) for f in queryset])
            elif object_pk:
                try:
                    obj = queryset.get(pk=object_pk)
                except:
                    pass
                else:
                    data = to_string_function(obj)
            return HttpResponse(data)
        return HttpResponseNotFound()

    def get_help_text(self, field_name, model_name):
        searchable_fields = self.related_search_fields.get(field_name, None)
        if searchable_fields:
            help_kwargs = {
                'model_name': model_name,
                'field_list': get_text_list(searchable_fields, _('and')),
            }
            return _('Use the left field to do %(model_name)s lookups in the fields %(field_list)s.') % help_kwargs
        return ''


# this method gets called when creating the formfields - probably this is what you need to extend
#  in the replicated version of ForeignKeyAutocompleteAdmin

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Overrides the default widget for Foreignkey fields if they are
        specified in the related_search_fields class attribute.
        """
        if (isinstance(db_field, models.ForeignKey) and 
            db_field.name in self.related_search_fields):
            model_name = db_field.rel.to._meta.object_name
            help_text = self.get_help_text(db_field.name, model_name)
            if kwargs.get('help_text'):
                help_text = u'%s %s' % (kwargs['help_text'], help_text)
            kwargs['widget'] = InlineSearchInput(db_field.rel,
                                    self.related_search_fields[db_field.name])
            kwargs['help_text'] = help_text
        return super(InlineAutocompleteAdmin,
            self).formfield_for_dbfield(db_field, **kwargs)





#  ===========
# using the autocomplete admin with other custom admin classes: 
# just mix and match as you like.... 
#  e.g. in my case I used it with the admin for trees provided by FeinCms:

try:
    from feincms.admin import editor
    #  just merging the effects of the two classes..
    class AutocompleteTreeEditor(FkAutocompleteAdmin, editor.TreeEditor):
        def __init__(self, *args, **kwargs):
            super(AutocompleteTreeEditor, self).__init__(*args, **kwargs)
except ImportError:
    pass
#  ===========








