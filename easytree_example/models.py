from django.db import models
from easytree.models import BaseEasyTree
from easytree.managers import EasyTreeManager
from django.conf import settings

class ExampleNode(BaseEasyTree):

    title = models.CharField(
        max_length=60
    )
    
    objects = EasyTreeManager()
    
    class Meta:
        ordering=('tree_id', 'lft')
    
    def display(self):
        return '<span class="display_indent">%s</span> %s' % (u'&gt;&gt;&gt; ' * ((self.depth or 1) -1), self.title)
    display.allow_tags = True
    
    def __unicode__(self):
        return '%s %s' % (u'>>> ' * ((self.depth or 1) -1), self.title)
        
class SubClassedExampleNode(ExampleNode):
    
    language = models.CharField(max_length=2, choices=settings.LANGUAGES)
    
