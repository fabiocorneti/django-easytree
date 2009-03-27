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
    
    def __init__(cls, name, bases, attrs):
        parents = [b for b in bases if isinstance(b, EasyTreeModelBase)]
        if not parents:
            return
        easytree_opts = getattr(cls, 'EasyTreeMeta', None)
        opts = EasytreeOptions(easytree_opts)
        setattr(cls, '_easytree_meta', opts)

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
        