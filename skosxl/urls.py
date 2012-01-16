# -*- coding:utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',

    url(r'^$', 'skosxl.views.tag_list', name="tag_list"),
    url(r'^(?P<slug>[\w-]+)/$', 'skosxl.views.tag_detail', name="tag_detail"),
        
)