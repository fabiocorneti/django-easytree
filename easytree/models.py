from django.db import models
from django.db.models.base import ModelBase
import logging

class EasytreeOptions(object):

    node_order_by = []
    validators = []
    
    def __init__(self, opts):
        if opts:       
            for key, value in opts.__dict__.iteritems():
                setattr(self, key, value)

class EasyTreeModelBase(ModelBase):
    
    """
    BaseEasyTree metaclass
    This metaclass parses EasytreeOptions
    """
    def __new__(cls, name, bases, attrs):
        new = super(EasyTreeModelBase, cls).__new__(cls, name, bases, attrs)
        easytree_opts = attrs.pop('EasyTreeMeta', None)
        setattr(new, '_easytree_meta', EasytreeOptions(easytree_opts))
        return new

class BaseEasyTree(models.Model):
    
    __metaclass__ = EasyTreeModelBase
    
    lft = models.PositiveIntegerField(db_index=True)
    rgt = models.PositiveIntegerField(db_index=True)
    tree_id = models.PositiveIntegerField(db_index=True)
    depth = models.PositiveIntegerField(db_index=True)

    def make_materialized_path(self, field, sep, include_root):
        parents = self.__class__.objects.get_ancestors_for(self)
        return sep.join([getattr(parent, field) for parent in list(parents) + [self] \
            if not self.__class__.objects.is_root(parent) or include_root] )
        
    class Meta:
        abstract = True

    def delete(self):
        self.__class__.objects.filter(pk=self.pk).delete()
        super(BaseEasyTree, self).delete()            
        