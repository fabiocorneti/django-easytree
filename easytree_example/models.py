from django.db import models
from easytree.models import BaseEasyTree
from easytree.managers import EasyTreeManager

class ExampleNode(BaseEasyTree):

    title = models.CharField(
        max_length=60
    )
    
    objects = models.Manager()
    
    easytree = EasyTreeManager()
    
    class Meta:
        ordering=('lft',)
    
    def __unicode__(self):
        return '%s %s' % (u'>>>' * ((self.depth or 1) -1), self.title)
    
