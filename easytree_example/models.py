from django.db import models
from easytree.models import BaseEasyTree
from easytree.managers import EasyTreeManager
from easytree.signals import node_moved
from easytree.validators import SingleRootAllowedValidator

from django.conf import settings

class ExampleNode(BaseEasyTree):

    title = models.CharField(
        max_length=60
    )
    
    objects = EasyTreeManager()
    
    class Meta:
        ordering=('tree_id', 'lft')
    
    def __unicode__(self):
        return self.title
        
class SubClassedExampleNode(ExampleNode):

    objects = EasyTreeManager()

    language = models.CharField(max_length=2, choices=settings.LANGUAGES)
    
class SingleRootExampleNode(BaseEasyTree):
    
    title = models.CharField(
        max_length=60
    )
    
    objects = EasyTreeManager()
        
    def __unicode__(self):
        return self.title
        
    class EasyTreeMeta:
        validators = (SingleRootAllowedValidator(),)
    
    
def test_node_moved(sender, **kwargs):
    print kwargs

node_moved.connect(test_node_moved)