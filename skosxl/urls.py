# -*- coding:utf-8 -*-
#from django.conf.urls.defaults import *
from django.conf.urls import *

urlpatterns = patterns('skosxl.views',

    url(r'^admin_scheme_tree/(?P<scheme_id>\d+)/$','json_scheme_tree',{'admin_url': True},'json_admin_scheme_tree'),
    url(r'^json_scheme_tree/(?P<scheme_id>\d+)/$','json_scheme_tree', {'admin_url': False},'json_scheme_tree'),

    url(r'^scheme/(?P<slug>[\w-]+)/$', 'scheme_detail', name="scheme_detail"),
    url(r'^concept/(?P<id>\d+)/$', 'concept_detail', name="concept_detail"),
    url(r'^label/(?P<slug>[\w-]+)/$', 'tag_detail', name="tag_detail"),
    
    url(r'^sparql/$', 'sparql_query', name="sparql_query")
    
        
)