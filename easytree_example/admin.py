from easytree_example.models import ExampleNode
from easytree_example.forms import ExampleNodeModelForm
from django.contrib import admin

class ExampleNodeAdmin(admin.ModelAdmin):
    
    form = ExampleNodeModelForm
    
    exclude = ('tree_id', 'depth', 'lft', 'rgt')

    list_display = ('display', 'lft', 'rgt', 'tree_id')

    ordering = ('lft',)

    list_filter = ('tree_id',)

    change_list_template = 'admin/easytree_change_list.html'

    def root_node_exists(self):
        
        try:
            root_node = ExampleNode.objects.get_root_nodes()[0]
        except IndexError:
            root_node = None
            
        return root_node

    def get_fieldsets(self, request, obj=None):
        
        if not obj:
            
            if not self.root_node_exists():
                return (
                    (None, {'fields': ('title', ), 'description': 'This node will become the first root node.' } ),
                )
            else:
                return (
                    (None, {'fields': ('title', ) }),
                    ('Position', {'fields': ('relative_to', 'relative_position'), 
                        'description': 'Select where in the tree you want this node located.'
                    } )
                )
        else:
            return (
                (None, {'fields': ('title', ) }),
                ('Move', {'fields': ('relative_to', 'relative_position'), 'description': 'Only fill these fields if you want to move this node.', 'classes': 'collapse'} )
            )
                

admin.site.register(ExampleNode, ExampleNodeAdmin)
