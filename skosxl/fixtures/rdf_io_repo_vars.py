# Sets config vars for an inferencing chain for SKOS and RDF4J
from __future__ import unicode_literals

from django.conf import settings
import django.db.models.deletion
import django_extensions.db.fields
import rdf_io.models


from rdf_io.models import ConfigVar 
from django.contrib.contenttypes.models import ContentType
from skosxl.models import Scheme

def loaddata(url_base):
    config,created = ConfigVar.objects.update_or_create(var='INFERREPO',defaults={'value':'skos_inferencer'})
    config,created = ConfigVar.objects.update_or_create(var='DEFAULTREPO',defaults={'value':'ogc-na-2'})
    config,created = ConfigVar.objects.update_or_create(var='RDFSERVER',defaults={'value':'http://localhost:8080'})
    config,created = ConfigVar.objects.update_or_create(var='INFERSERVER',defaults={'value':'http://localhost:8080'})
    return ( {'configs': '3 vars set'} )
