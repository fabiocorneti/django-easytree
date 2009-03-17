from easytree_example.models import ExampleNode
from easytree_example.forms import ExampleNodeModelForm
from django.contrib import admin

class ExampleNodeAdmin(admin.ModelAdmin):
    
    form = ExampleNodeModelForm
    
    list_display = ('__unicode__', 'lft', 'rgt', 'tree_id')
    
    fieldsets = (
        (None, {'fields': ('title', 'relative_position', 'relative_to', 'create_as_root_node') } ),
    )

admin.site.register(ExampleNode, ExampleNodeAdmin)
