from django.contrib import admin
from django.utils import simplejson
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse
from easytree import utils
from easytree.forms import BaseEasyTreeForm
from easytree.exceptions import EasyTreeException
from django.db import transaction, connection

class EasyTreeAdmin(admin.ModelAdmin):

    exclude = ('tree_id', 'depth', 'lft', 'rgt')

    list_display = ('display_as_node',)

    ordering = ('lft',)

    change_list_template = 'admin/easytree_change_list.html'
    
    form = BaseEasyTreeForm
    
    toplevel_model_cache = None
    
    def display_as_node(self, obj):
        
        return  u'%s %s' % (
            u'>>>' * ((obj.depth or 1) -1),
            unicode(obj)
        )
        
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
    
    def get_fieldsets(self, request, obj=None):
        
        fieldsets = super(EasyTreeAdmin, self).get_fieldsets(request, obj=None)
        
        return self.add_tree_fieldsets(fieldsets, request, obj=obj)
        
    def add_tree_fieldsets(self, fieldsets, request, obj=None):
        
        if not obj:
            
            if not self.root_node_exists():
                return fieldsets
            else:
                return list(fieldsets) + [
                    ('Position', {'fields': ('relative_to', 'relative_position'), 
                        'description': _('Select where in the tree you want this node located.')
                    }),
                ]
        else:
            return list(fieldsets) + [
                    ('Move', {'fields': ('relative_to', 'relative_position'), 'description': _('Only fill these fields if you want to move this node.'), 'classes': 'collapse'} )
            ]
        
    def move_view(self, request):
        
        error = None
        
        try:
            node_to_move = self.toplevel_model.objects.get(pk=request.POST['node_to_move'])
            relative_to_node = self.toplevel_model.objects.get(pk=request.POST['relative_to_node'])
            relative_position = request.POST['relative_position']
        except KeyError:
            error = _('Invalid GET parameters')
        except self.toplevel_model.DoesNotExist:
            error = _('No such model instance')
            
        try:
            self.toplevel_model.objects.move(node_to_move, relative_to_node, pos=relative_position)
        except EasyTreeException, e:
            error = e.message
        
        json_data = {}
        if not error:
            json_data = {'success': True}
        else:
            json_data = {'success': False, 'error': error}
        
        return HttpResponse(simplejson.dumps(json_data), mimetype='text/javascript')                
        
    def get_urls(self):
        
        admin_urls = super(EasyTreeAdmin, self).get_urls()
        
        from django.conf.urls.defaults import patterns, url

        info = self.model._meta.app_label, self.model._meta.module_name
        
        return patterns('',
            url(r'^move/$',
                self.admin_site.admin_view(self.move_view),
                name='%s_%s_move' % info),
        ) + admin_urls
        
    def changelist_view(self, request, extra_context=None):
        
        from django.core.urlresolvers import reverse
        extra_context = extra_context or {}
        
        info = self.model._meta.app_label, self.model._meta.module_name
        extra_context['move_url'] = reverse('admin:%s_%s_move' % info)
        
        return super(EasyTreeAdmin, self).changelist_view(request, extra_context=extra_context)
