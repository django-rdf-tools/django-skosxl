# -*- coding:utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',

    url(r'^concept_tree/(?P<scheme_id>\d+)/$','skosxl.views.concept_tree', name='json_concept_tree'),

    url(r'^all/$', 'skosxl.views.tag_list', name="tag_list"),
    #url(r'^(?P<slug>[\w-]+)/$', 'skosxl.views.tag_detail', name="tag_detail"),
        
)