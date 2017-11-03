# -*- coding:utf-8 -*-
#from django.conf.urls.defaults import *
from django.conf.urls import url

from . import views

app_name = 'skosxl'
urlpatterns = [
    url(r'^admin_scheme_tree/(?P<scheme_id>\d+)/$',views.json_scheme_tree,{'admin_url': True},'json_admin_scheme_tree'),
    url(r'^json_scheme_tree/(?P<scheme_id>\d+)/$',views.json_scheme_tree, {'admin_url': False},'json_scheme_tree'),

    url(r'^scheme/(?P<slug>[\w-]+)/$', views.scheme_detail, {}, name="scheme_detail"),
    url(r'^concept/(?P<id>\d+)/$', views.concept_detail, {}, name='concept_detail'),
    url(r'^label/(?P<slug>[\w-]+)/$', views.tag_detail, {} , name="tag_detail"),
    
    url(r'^sparql/$', views.sparql_query, name="sparql_query"),
    url(r'manage/init$', views.loadinit, name='loadinit'),
        
]
