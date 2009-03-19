from easytree_example.models import ExampleNode
from easytree_example.forms import ExampleNodeModelForm
from django.contrib import admin

class ExampleNodeAdmin(admin.ModelAdmin):
    
    form = ExampleNodeModelForm
    
    exclude = ('tree_id', 'depth', 'lft', 'rgt')

    list_display = ('__unicode__', 'lft', 'rgt', 'tree_id')
    
    def root_node_exists(self):
        
        try:
            root_node = ExampleNode.objects.get_root_nodes()[0]
        except IndexError:
            root_node = None
            
        return root_node

 

admin.site.register(ExampleNode, ExampleNodeAdmin)
