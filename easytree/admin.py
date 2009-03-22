from django.contrib import admin
from django.utils.functional import update_wrapper
from easytree import utils
from easytree.forms import extend_modelform

class EasyTreeAdmin(admin.ModelAdmin):

    exclude = ('tree_id', 'depth', 'lft', 'rgt')

    list_display = ('display', 'lft', 'rgt', 'tree_id')

    ordering = ('lft',)

    list_filter = ('tree_id',)

    change_list_template = 'admin/easytree_change_list.html'
    
    toplevel_model_cache = None
    
    def get_toplevel_model(self):
        if not self.toplevel_model_cache:
            self.toplevel_model_cache = utils.get_toplevel_model(self.model)
        return self.toplevel_model_cache    
    toplevel_model = property(get_toplevel_model)
    
    def root_node_exists(self):
        
        try:
            root_node = self.toplevel_model.objects.get_root_nodes()[0]
        except IndexError:
            root_node = None
            
        return root_node

    def get_form(self, request, obj=None, **kwargs):
        modelform = super(EasyTreeAdmin, self).get_form(request, obj=None, **kwargs)
        return extend_modelform(modelform)
        
    def get_fieldsets(self, request, obj=None):
        
        fieldsets = super(EasyTreeAdmin, self).get_fieldsets(request, obj=None)
        
        if not obj:
            
            if not self.root_node_exists():
                return fieldsets
            else:
                return list(fieldsets) + [
                    ('Position', {'fields': ('relative_to', 'relative_position'), 
                        'description': 'Select where in the tree you want this node located.'
                    }),
                ]
        else:
            return list(fieldsets) + [
                    ('Move', {'fields': ('relative_to', 'relative_position'), 'description': 'Only fill these fields if you want to move this node.', 'classes': 'collapse'} )
            ]
            
    def move_view(request):
        return HttpResponse('it works!')                
        
	def get_urls(self):
	    
	    admin_urls = super(EasyTreeAdmin, self).get_urls()
	    
        from django.conf.urls.defaults import patterns, url

        info = self.admin_site.name, self.model._meta.app_label, self.model._meta.module_name
        
        return patterns('',
            url(r'^move/$',
                self.admin_site.admin_view(self.move_view),
                name='%sadmin_%s_%s_move' % info),
        ) + admin_urls
        
