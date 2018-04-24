# # -*- coding:utf-8 -*-
from django.shortcuts import render_to_response, redirect
from skosxl.models import *
from django.template import RequestContext
from django.shortcuts import get_object_or_404
# deprecated since 1.3
# from django.views.generic.list_detail import object_list
# but not used anyway?
# if needed.. from django.views.generic import ListView

from django.http import HttpResponse
import json

from skosxl.models import Scheme,Concept,SemRelation

from SPARQLWrapper import SPARQLWrapper,JSON, XML

import pprint


from importlib import import_module


def loadinit(req) :
    """
        ought to move this to rdf_io, and put in a module register process that triggers these for all modules rdf_io knows about
    """
    messages = {}
    if req.GET.get('pdb') :
        import pdb; pdb.set_trace()
    url_base = req.build_absolute_uri("/");
    loadlist = import_module('skosxl.fixtures.loadlist', 'skosxl.fixtures')
    for cfgname in loadlist.INITIAL_FIXTURES :
        cm = import_module("".join(('skosxl.fixtures.',cfgname)), 'dataweb.fixtures')
        messages.update( cm.loaddata(url_base) )
    return HttpResponse("loaded configurations:" + str(messages))  




def scheme_detail(request,id):
    context = {}
#    import pdb; pdb.set_trace()
    scheme = Scheme.objects.get(id=id)
    context['object'] = scheme
    context['concepts'] = Concept.objects.filter(scheme=scheme)
    return render_to_response('scheme_detail.html',context,RequestContext(request))

def concept_detail(request,id):
    concept= Concept.objects.get(id=id)
    context = {}
    context['object'] = Concept.objects.get(id=id)
    context['preflabels'] = Label.preflabels.filter(concept=concept)
    context['altlabels'] = Label.altlabels.filter(concept=concept)
    context['notations'] = Notation.objects.filter(concept=concept)
    return render_to_response('concept_detail.html',context,RequestContext(request))


def tag_detail(request,id):
    context = {}
    tag = Label.objects.get(id=id)
    context['object'] = tag
    # example
    # context['initiatives'] = Initiative.objects.filter(tags=tag)
    return render_to_response('tag_detail.html',context,RequestContext(request))

def json_scheme_tree(request,scheme_id,admin_url):
    scheme = Scheme.objects.get(id=scheme_id)
    return HttpResponse(    scheme.json_tree(admin_url=True), 
                            content_type="application/json")

def tag_list(request):
    context = {}
    context['tags'] = Label.objects.all()
    return render_to_response('tag_list.html',context,RequestContext(request))
 
