from easytree_example.models import ExampleNode
from easytree_example.forms import ExampleNodeModelForm
from django.contrib import admin

class ExampleNodeAdmin(admin.ModelAdmin):
    
    form = ExampleNodeModelForm
    
    exclude = ('tree_id', 'depth', 'lft', 'rgt')

    list_display = ('__unicode__', 'lft', 'rgt', 'tree_id')
    
    def root_node_exists(self):
        
        try:
            root_node = ExampleNode.easytree.get_root_nodes()[0]
        except IndexError:
            root_node = None
            
        return root_node

    
    def get_fieldsets(self, request, obj=None):
        
        if not obj:
            
            if not self.root_node_exists():
                return (
                    (None, {'fields': ('title', 'relative_position', 'create_as_root_node') } ),
                )
            else:
                return (
                    (None, {'fields': ('title', ) }),
                    ('Position', {'fields': ('relative_position', 'relative_to', 'create_as_root_node'), 
                        'description': 'Select where in the tree you want this node located.'
                    } )
                )
        else:
            return (
                (None, {'fields': ('title', ) }),
                ('Move', {'fields': ('relative_position', 'relative_to'), 'description': 'Only fill theese fields if you want to move this node.', 'classes': 'collapse'} )
            )
                

admin.site.register(ExampleNode, ExampleNodeAdmin)
