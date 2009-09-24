from django.conf import settings
from django.db import models
from easytree.models import BaseEasyTree
from easytree.managers import EasyTreeManager
from easytree.signals import node_moved

class TestNode(BaseEasyTree):

    title = models.CharField(max_length=60)
    
    objects = EasyTreeManager()
    
    class Meta:
        ordering=('tree_id', 'lft')

    def __unicode__(self):
        return self.title
