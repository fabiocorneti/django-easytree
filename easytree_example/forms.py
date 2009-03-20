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
                
        self.fields['relative_position'] = forms.ChoiceField(
            required=False,
            choices=[(k, v) for k, v in pos_map.items() if k in relative_positions_choices]
        )
        
    relative_position = forms.ChoiceField(required=False)
    relative_to = forms.ModelChoiceField(queryset=ExampleNode.objects.order_by('tree_id', 'lft'), required=False)
    
    class Meta:
        model = ExampleNode
        
    def clean(self):
        cleaned_data = self.cleaned_data

        relative_to = cleaned_data.get('relative_to')
        relative_position = cleaned_data.get('relative_position')
        
        if not self.instance.pk:
            
            if not relative_to:
                
                try:
                    ExampleNode.objects.move_opts.validate_root(None, relative_to, pos=relative_position)
                except Exception, e:
                    raise forms.ValidationError, e.message
                    
            else:
                
                if relative_position in ('last-child', 'first-child', 'sorted-child'):
                    
                    try:
                        ExampleNode.objects.move_opts.validate_child(None, relative_to, pos=relative_position)
                    except Exception, e:
                        raise forms.ValidationError, e.message
                        
                else:
                    
                    try:
                        ExampleNode.objects.move_opts.validate_sibling(None, relative_to, pos=relative_position)
                    except Exception, e:
                        raise forms.ValidationError, e.message
                        
        else:
            if relative_to:
                try:
                    ExampleNode.objects.move_opts.validate_move(self.instance, relative_to, pos=relative_position)
                except Exception, e:
                    raise forms.ValidationError, e.message        
        
        cleaned_data['relative_to'] = relative_to
        
        return cleaned_data
        
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