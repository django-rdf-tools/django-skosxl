# # -*- coding:utf-8 -*-
from django.shortcuts import render_to_response, redirect
from skosxl.models import Label,Concept
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
    
    for cfgname in ['rdf_io_mappings', 'urls_sissvoc'] :
        cm = import_module("".join(('skosxl.fixtures.',cfgname)), 'dataweb.fixtures')
        messages['ns'] = cm.load_base_namespaces(url_base=url_base)
        messages['rules'] = cm.load_urirules(url_base=url_base)
        messages['rdf_io'] = cm.load_rdf_mappings(url_base=url_base)
    return HttpResponse("loaded configurations:" + str(messages))  


def sparql_query(request):
    pp = pprint.PrettyPrinter( indent = 4 )
    #import pdb; pdb.set_trace()
    term = request.GET['q']
    concepts = []
    endpoints = (   
                    #('AGROVOC','http://202.73.13.50:55824/catalogs/performance/repositories/agrovoc'),
                    #('ISIDORE','http://www.rechercheisidore.fr/sparql?format=application/sparql-results+json'),
                    #('GEMET','http://cr.eionet.europa.eu/sparql'),
                    #('CPV','http://localhost:8080/openrdf-workbench/repositories/cpv'),
                    #('GEMET','http://localhost:8080/openrdf-sesame/repositories/gemet'), #openrdf
                    #('GEMET','http://localhost:8080/parliament/sparql'), 
                    ('GEMET','http://localhost:8080/sparql/'), #4store
                )
    for endpoint in endpoints :
        try:
            
            sparql = SPARQLWrapper(endpoint[1])
            query = u"""
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
PREFIX skosxl:<http://www.w3.org/2008/05/skos-xl#>
SELECT ?label ?uri WHERE {
    {?uri skos:prefLabel ?label .}
  UNION
    { ?uri skosxl:prefLabel ?label .}
  FILTER(regex(str(?label),""" + u'"'+term+u'"' + u""","i"))
  FILTER( lang(?label) = "fr" )
}
            """
            
            print query
            sparql.setQuery(query)          
            sparql.setReturnFormat(JSON)
            
            test = sparql.query()
            for triple in test:pp.pprint( triple )
            
            results = sparql.query().convert()
            for result in results["results"]["bindings"]:
                concepts.append({   'label':result["label"]["value"],
                                    'uri':result["uri"]["value"],
                                    'voc':endpoint[0]})
        except Exception,e :
            print "Caught:", e
    return HttpResponse(    json.dumps(concepts), 
                            content_type="application/json")


def scheme_detail(request,slug):
    context = {}
    scheme = Scheme.objects.get(slug=slug)
    context['object'] = scheme
    context['concepts'] = Concept.objects.filter(scheme=scheme)
    return render_to_response('scheme_detail.html',context,RequestContext(request))

def concept_detail(request,id):
    context = {}
    context['concept'] = Concept.objects.get(id=id)
    return render_to_response('concept_detail.html',context,RequestContext(request))


def tag_detail(request,slug):
    context = {}
    tag = Label.objects.get(slug=slug)
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
    
