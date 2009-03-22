from easytree_example.models import ExampleNode, SubClassedExampleNode
from easytree.admin import EasyTreeAdmin
from django.contrib import admin

class ExampleNodeAdmin(EasyTreeAdmin):
    pass
                
class SubClassedExampleNodeAdmin(EasyTreeAdmin):
    pass
                
admin.site.register(ExampleNode, ExampleNodeAdmin)
admin.site.register(SubClassedExampleNode, SubClassedExampleNodeAdmin)
