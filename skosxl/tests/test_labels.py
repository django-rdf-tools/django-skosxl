from skosxl.models import *

from django.test import TestCase



class LabelHandlingTestCase(TestCase):
    """ Test cases label management """
    
    sc = None
    c1 = None
    
    def setUp(self):
        self.sc,created = Scheme.objects.get_or_create(uri='http://testme.org/scheme')
        self.c1,created = Concept.objects.get_or_create(scheme=self.sc, term='t')
        pass
        
        
    def test_pref_label_sync_up(self):
        l1 = Label.objects.create(concept=self.c1, label_text="A label", language=DEFAULT_LANG, label_type=LABEL_TYPES.prefLabel)
        l1.save()
        self.assertEqual ( self.c1.pref_label, "A label")
        l1.label_text="New label"
        l1.save()
        self.assertEqual ( self.c1.pref_label, "New label")   

    def test_pref_label_sync_down_create(self):
        self.c1.pref_label = 'New label'
        self.c1.save()
        l1=Label.objects.get(concept=self.c1,language=DEFAULT_LANG,label_type=LABEL_TYPES.prefLabel)
        self.assertEqual ( l1.label_text, "New label")
        
    def test_pref_label_sync_down_update(self):
        l1 = Label.objects.create(concept=self.c1, label_text="A label", language=DEFAULT_LANG, label_type=LABEL_TYPES.prefLabel)
        self.c1.pref_label = 'New label'
        self.c1.save()
        l1=Label.objects.get(concept=self.c1,language=DEFAULT_LANG,label_type=LABEL_TYPES.prefLabel)
        self.assertEqual ( l1.label_text, "New label")  
        