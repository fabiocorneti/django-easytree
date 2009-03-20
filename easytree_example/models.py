from django.db import models
from easytree.models import BaseEasyTree
from easytree.managers import EasyTreeManager

class ExampleNode(BaseEasyTree):

    title = models.CharField(
        max_length=60
    )
    
    objects = EasyTreeManager()
    
    class Meta:
        ordering=('tree_id', 'lft')
    
    def __unicode__(self):
        return '<span class="display_indent">%s</span> %s' % (u'&gt;&gt;&gt;' * ((self.depth or 1) -1), self.title)
    __unicode__.allow_tags = True
    
