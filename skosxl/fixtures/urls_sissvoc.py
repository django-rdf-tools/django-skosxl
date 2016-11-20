
from rdf_io.models import Namespace, ObjectMapping,AttributeMapping 

from skosxl.models import Scheme



def load_base_namespaces():
    """
        load namespaces for the samples
    """
    pass
def load_urirules() :
    """
        Load uriredirect rules for these object types.
    """
    try:
        __import__('uriredirect')
        from uriredirect.models import *
        # configs to load 
        # note we could in future possibly hit the VoiD model for the resources and bind to all the declared APIs
        #
        defaultroot = "http://mapstory.org/def"
        api_bindings = { 'ft' : [ 
            { 'root' : defaultroot, 'apilabel' : "API - default redirects for register root", 'pattern' : None , 'term' : 'None', 'ldamethod' : 'skos/resource' } ,
            { 'root' : defaultroot, 'apilabel' : "API - default redirects for schemes", 'pattern' : '^(?P<subregister>[^/]+)$' ,  'term' : 'None' , 'ldamethod' : 'skos/resource' } ,
            { 'root' : defaultroot, 'apilabel' : "API - default redirects for concepts", 'pattern' : '^.*/(?P<term>[^\?]+)' , 'term' : '${term}', 'ldamethod' : 'skos/resource' } ],
            'featuretypes' : [ 
            { 'root' : defaultroot, 'apilabel' : "API - default redirects for register root", 'pattern' : None , 'term' : 'None' , 'ldamethod' : 'skos/resource' } ,
            { 'root' : defaultroot, 'apilabel' : "API - default redirects for subregisters", 'pattern' : '^(?P<term>[^/]+)$' , 'term' : 'None',  'ldamethod' : 'skos/resource' } ,
            { 'root' : defaultroot, 'apilabel' : "API - default redirects for register items", 'pattern' : '^.*/(?P<term>[^\?]+)' , 'term' : '${term}', 'ldamethod' : 'skos/resource' } ]
            }
        load_key = 'SKOS API rule: '    
        RewriteRule.objects.filter(description__startswith=load_key).delete()   
        for label in api_bindings.keys() :
            for api in api_bindings[label] :
                (reg,created) = UriRegister.objects.get_or_create(label=label, defaults = { 'url' : '/'.join((api['root'],label)) , 'can_be_resolved' : True} )
                (apirule,created) = RewriteRule.objects.get_or_create(label=' : '.join((api['apilabel'],label)) , defaults = {
                    'description' : ' : '.join((load_key ,api['apilabel'],label)),
                    'parent' : None ,
                    'register' : None ,
                    'service_location' : None ,
                    'service_params' : None ,
                    'pattern' : api['pattern'] ,
                    'use_lda' : True ,
                    'view_param' : '_view' ,
                    'view_pattern' : None } )
                if not created :
                    AcceptMapping.objects.filter(rewrite_rule=apirule).delete()
                    
                if api['pattern'] :
                    path = '/${path}'
                    path_base = '/${path_base}'
                    term=api['term']
                else:
                    path = ''
                    path_base = ''
                    term='None'
                    
                for ext in ('ttl','json','rdf','xml','html') :
                    mt = MediaType.objects.get(file_extension=ext)
                    (accept,created) = AcceptMapping.objects.get_or_create(rewrite_rule=apirule,media_type=mt, defaults = {
                        'redirect_to' : "".join(('${server}/', api['ldamethod'],'?uri=',defaultroot,'/',label,path,'&_format=',ext)) } )
                # sub rules for views
                viewlist = [ {'name': 'alternates', 'apipath': ''.join(('lid/resourcelist','?baseuri=',api['root'],'/',label,path_base,'&item=',term))},  ]
                if label == 'qbcomponents' :
                    viewlist = viewlist + [ {'name': 'qb', 'apipath': ''.join(('qbcomponent','?uri=',api['root'],'/',label,'/${path}'))}, ]
                elif label == 'profiles' :
                    viewlist = viewlist + [ {'name': 'profile', 'apipath': ''.join(('profile','?uri=',api['root'],'/',label,'/${path}'))}, ]
                for view in viewlist:
                    id = ' : '.join((label,api['apilabel'],"view",view['name']))
                    (api_vrule,created) = RewriteRule.objects.get_or_create(
                        label=id,
                        defaults = {
                        'description' : ' : '.join((load_key ,api['apilabel'],label,view['name'])) ,
                        'parent' : apirule ,
                        'register' : None ,
                        'service_location' : None ,
                        'service_params' : None ,
                        'pattern' : None ,
                        'use_lda' : True ,
                        'view_param' : '_view' ,
                        'view_pattern' : view['name'] } )
                    for ext in ('ttl','json','rdf','xml','html') :
                        mt = MediaType.objects.get(file_extension=ext)
                        (accept,created) = AcceptMapping.objects.get_or_create(rewrite_rule=api_vrule,media_type=mt, defaults = {
                        'redirect_to' : "".join(('${server}/', view['apipath'],'&_format=',ext)) } )
     
                # bind to API
                (rule,created) = RewriteRule.objects.get_or_create(label=' : '.join(("Register",label,api['apilabel'])) , defaults = {
                    'description' : ' : '.join((load_key ,'binding to register for ',api['apilabel'],label)) ,
                    'parent' : apirule ,
                    'register' : reg ,
                    'service_location' :  "http://192.168.56.151:8080/dna",
                    'service_params' : None ,
                    'pattern' : None ,
                    'use_lda' : True ,
                    'view_param' : '_view' ,
                    'view_pattern' : None } )

                
    except ImportError:
        return "Uriredirect module not available - not configured "
    except Exception as e:
        return "error configuring URI rules: %s" % e

def load_rdf_mappings():
    """
        load RDF mappings for SKOS XL Objects
    """
    pass 

