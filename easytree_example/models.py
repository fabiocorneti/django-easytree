from django.db import models

class Example(models.Model):

    title = models.CharField(
        max_length=60
    )
    
    def __unicode__(self):
        return self.title
        
class SubClassedExample(Example):
    extra = models.PositiveIntegerField()
