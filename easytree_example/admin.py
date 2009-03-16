from easytree_example.models import ExampleNode
from django.contrib import admin
from django import forms

class ExampleNodeModelForm(forms.ModelForm):
    
    create_as_root_node = forms.BooleanField(required=False)
    parent = forms.ModelChoiceField(queryset=ExampleNode.objects.all(), required=False)
    
    class Meta:
        model = ExampleNode
        
    def clean_parent(self):
        
        parent = self.cleaned_data.get('parent')
        create_as_root_node = self.cleaned_data.get('create_as_root_node')
        
        if not parent:
            try:
                parent = ExampleNode.easytree.get_root_nodes()[0]
            except IndexError:
                if not create_as_root_node:
                    raise forms.ValidationError, "No root node exists"
        
        return parent
        
    def save(self, **kwargs):
        instance = super(ExampleNodeModelForm, self).save(commit=False)
        parent = self.cleaned_data.get('parent', None)
        if parent:
            instance.parent = parent
        if kwargs.get('commit', False):
            instance.save() 
        return instance
        
class ExampleNodeAdmin(admin.ModelAdmin):
    
    form = ExampleNodeModelForm
    
    list_display = ('__unicode__', 'lft', 'rgt', 'tree_id')
    
    fieldsets = (
        (None, {'fields': ('title', 'parent', 'create_as_root_node') } ),
    )

admin.site.register(ExampleNode, ExampleNodeAdmin)
