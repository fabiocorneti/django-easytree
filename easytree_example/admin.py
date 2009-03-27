from easytree_example.models import ExampleNode, SubClassedExampleNode
from easytree.admin import EasyTreeAdmin
from django.contrib import admin

class ExampleNodeAdmin(EasyTreeAdmin):
    list_display = ('display', 'lft', 'rgt', 'tree_id', 'title')
    list_editable = ('title',)
    list_filter = ('tree_id',)
    
class SubClassedExampleNodeAdmin(EasyTreeAdmin):
    list_display = ('display', 'lft', 'rgt', 'tree_id', 'title')
    list_editable = ('title',)
    list_filter = ('tree_id',)
    
admin.site.register(ExampleNode, ExampleNodeAdmin)
admin.site.register(SubClassedExampleNode, SubClassedExampleNodeAdmin)
