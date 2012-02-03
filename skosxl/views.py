# # -*- coding:utf-8 -*-
from django.shortcuts import render_to_response, redirect
from skosxl.models import Label,Concept,LabelledItem
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list
from django.http import HttpResponse
import json

from skosxl.models import Scheme,Concept,SemRelation
# example
# from coop_local.models import Initiative


def tag_detail(request,slug):
    context = {}
    tag = Label.objects.get(slug=slug)
    context['object'] = tag
    # example
    # context['initiatives'] = Initiative.objects.filter(tags=tag)
    return render_to_response('tag_detail.html',context,RequestContext(request))


def get_childs(concept):
    childs = []
    #print '>>>>>',concept
    if SemRelation.objects.filter(origin_concept=concept,rel_type=1).exists():
        for narrower in SemRelation.objects.filter(origin_concept=concept,rel_type=1):
            #print narrower.target_concept
            jrep = {    'name':narrower.target_concept.pref_label,
                        'admin_url':'/admin/skosxl/concept/'+str(narrower.target_concept.id)+'/',
                        'children':get_childs(narrower.target_concept)}
            childs.append(jrep)
    return childs

    
def concept_tree(request,scheme_id):
    test_ctree = {
        'name' : 'root',
        'children' :[
            { 'name' :'child 1' },
            { 'name' :'child 2' },
            { 'name' :'child 3' },
        ]
    }    
    scheme = Scheme.objects.get(id=scheme_id)
    ctree = {'name' : scheme.pref_label, 'children' : []}
    for top_concept in Concept.objects.filter(scheme=scheme,top_concept=True):
        ctree['children'].append({  'name':top_concept.pref_label,
                                    'admin_url':'/admin/skosxl/concept/'+str(top_concept.id)+'/',
                                    'children':get_childs(top_concept)})
    return HttpResponse(json.dumps(ctree), mimetype="application/json")
    
def tag_list(request):
    context = {}
    context['tags'] = Label.objects.all()
    return render_to_response('tag_list.html',context,RequestContext(request))
    
