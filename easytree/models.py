from django.db import models
import logging

class BaseEasyTree(models.Model):
    
    lft = models.PositiveIntegerField(db_index=True)
    rgt = models.PositiveIntegerField(db_index=True)
    tree_id = models.PositiveIntegerField(db_index=True)
    depth = models.PositiveIntegerField(db_index=True)
    
    class Meta:
        abstract = True

    def delete(self):
        self.__class__.objects.filter(pk=self.pk).delete()
        super(BaseEasyTree, self).delete()            
        