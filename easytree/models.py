from django.db import models
from django.db.models.base import ModelBase
import logging

class EasyTreeOptions(object):

    """
    Options class for EasyTreeModelBase.
    """
    
    node_order_by = []
    validators = []
    max_depth = 0

    def __init__(self, opts):
        if opts:       
            for key, value in opts.__dict__.iteritems():
                setattr(self, key, value)

class EasyTreeModelBase(ModelBase):
    
    """
    BaseEasyTree metaclass.
    
    This metaclass parses EasyTreeOptions.
    """
    
    def __new__(cls, name, bases, attrs):
        new = super(EasyTreeModelBase, cls).__new__(cls, name, bases, attrs)
        easytree_opts = attrs.pop('EasyTreeMeta', None)
        setattr(new, '_easytree_meta', EasyTreeOptions(easytree_opts))
        return new

class BaseEasyTree(models.Model):
    
    """
    Abstract base class for trees
    """
    
    __metaclass__ = EasyTreeModelBase
    
    lft = models.PositiveIntegerField(db_index=True)
    rgt = models.PositiveIntegerField(db_index=True)
    tree_id = models.PositiveIntegerField(db_index=True)
    depth = models.PositiveIntegerField(db_index=True)
        
    def make_materialized_path(self, field, sep, include_root):
        """
        Helper to make a materialized path to this node.
        """
        parents = self.__class__.objects.get_ancestors_for(self)
        return sep.join([getattr(parent, field) for parent in list(parents) + [self] \
            if not self.__class__.objects.is_root(parent) or include_root] )
    
    def tree(self):
        """ Returns a queryset of this node and all decendants """
        return self.__class__.objects.get_tree(parent=self)
    
    def descendants(self):
        """ Returns all decendants of this node """
        return self.__class__.objects.get_descendants_for(self)
    
    def children(self):
        """ Returns the children of this node """
        return self.__class__.objects.get_children_for(self)
    
    def siblings(self):
        """
        Returns the siblings of this node, including this node.
        """
        return self.__class__.objects.get_siblings_for(self)
        
    def ancestors(self):
        """ Returns all ancestors of this node """
        return self.__class__.objects.get_ancestors_for(self)
    
    def is_root(self):
        """ Returns True if this is a root node """
        return self.__class__.objects.is_root(self)
    
    def is_leaf(self):
        """ Returns True if this is a leaf node """
        return self.__class__.objects.is_leaf(self)
    
    class Meta:
        abstract = True

    def delete(self):
        self.__class__.objects.filter(pk=self.pk).delete()
        super(BaseEasyTree, self).delete()            
        