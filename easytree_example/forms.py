from django import forms
from django.utils.translation import ugettext_lazy as _
from easytree_example.models import ExampleNode

pos_map = {
    'first-sibling': _('first sibling'),
    'left': _('left'),
    'right': _('right'),
    'last-sibling': _('last sibling'),
    'sorted-sibling': _('sorted sibling'),
    'first-child': _('first child'),
    'last-child': _('last child'),
    'sorted-child': _('sorted child')
}


class ExampleNodeModelForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(ExampleNodeModelForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            if getattr(self.instance, 'node_order_by', None):
                relative_positions_choices = ('sorted-sibling', 'sorted-child')
            else:
                relative_positions_choices = pos_map.keys()
        relative_positions_choices = ('sorted-sibling', 'sorted-child')

        self.fields['relative_position'] = forms.ChoiceField(choices=[(k, v) for k, v in pos_map.items() if k in relative_positions_choices])
        
    relative_position =  forms.ChoiceField()
    create_as_root_node = forms.BooleanField(required=False)
    relative_to = forms.ModelChoiceField(queryset=ExampleNode.objects.all(), required=False)
    
    class Meta:
        model = ExampleNode
        
    def clean_relative_to(self):
        
        parent = self.cleaned_data.get('relative_to')
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
        parent = self.cleaned_data.get('relative_to', None)
        if parent:
            instance.parent = parent
        if kwargs.get('commit', False):
            instance.save() 
        return instance