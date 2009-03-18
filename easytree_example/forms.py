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

        if getattr(self.instance, 'node_order_by', None):
            relative_positions_choices = ('sorted-sibling', 'sorted-child')
        else:
            relative_positions_choices = [k for k in pos_map.keys() if k not in ('sorted-sibling', 'sorted-child')]
                
        self.fields['relative_position'] = forms.ChoiceField(choices=[(k, v) for k, v in pos_map.items() if k in relative_positions_choices])
        
    relative_position = forms.ChoiceField()
    create_as_root_node = forms.BooleanField(required=False, help_text='Check this box if you want this to be a new root node.')
    relative_to = forms.ModelChoiceField(queryset=ExampleNode.objects.all(), required=False)
    
    class Meta:
        model = ExampleNode
        
    def clean_relative_to(self):
        
        relative_to = self.cleaned_data.get('relative_to')
        create_as_root_node = self.cleaned_data.get('create_as_root_node')
        relative_position = self.cleaned_data.get('relative_position')
        
        if not self.instance.pk:
            if not relative_to:
                if not create_as_root_node:
                    raise forms.ValidationError, "Pick a related node and position or create this as a new root node."
                else:
                    try:
                        ExampleNode.easytree.move_opts.validate_root(None, relative_to, pos=relative_position)
                    except Exception, e:
                        raise forms.ValidationError, e.message
            else:
                if relative_position in ('last-child', 'first-child', 'sorted-child'):
                    try:
                        ExampleNode.easytree.move_opts.validate_child(None, relative_to, pos=relative_position)
                    except Exception, e:
                        raise forms.ValidationError, e.message
                else:
                    try:
                        ExampleNode.easytree.move_opts.validate_sibling(None, relative_to, pos=relative_position)
                    except Exception, e:
                        raise forms.ValidationError, e.message
        else:
            try:
                ExampleNode.easytree.move_opts.validate_move(self.instance, relative_to, pos=relative_position)
            except Exception, e:
                raise forms.ValidationError, e.message        
        
        return relative_to
        
    def save(self, **kwargs):
        instance = super(ExampleNodeModelForm, self).save(commit=False)
        relative_to = self.cleaned_data.get('relative_to', None)
        relative_position = self.cleaned_data.get('relative_position')
        if relative_to:
            instance.easytree_relative_position = relative_position
            instance.easytree_relative_to = relative_to
        if kwargs.get('commit', False):
            instance.save() 
        return instance