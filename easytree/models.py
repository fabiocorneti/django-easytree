from django.db import models
import logging

class BaseEasyTree(models.Model):
    
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
        