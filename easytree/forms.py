from django import forms
from django.utils.translation import ugettext_lazy as _
from easytree import utils
from easytree.exceptions import EasyTreeException

pos_map = {
    'first-sibling': _('First sibling'),
    'left': _('Previous sibling'),
    'right': _('Next sibling'),
    'last-sibling': _('Last sibling'),
    'sorted-sibling': _('Sorted sibling'),
    'first-child': _('First child'),
    'last-child': _('Last child'),
    'sorted-child': _('Sorted child')
}

class EasyTreeModelChoiceField(forms.ModelChoiceField):
    
    def label_from_instance(self, obj):
        return u'%s %s' % (
            u'>>>' * ((obj.depth or 1) -1),
            super(EasyTreeModelChoiceField, self).label_from_instance(obj)
        )

class BaseEasyTreeForm(forms.ModelForm):
    
    toplevel_model_cache = None
    
    def get_toplevel_model(self):
        if not self.toplevel_model_cache:
            self.toplevel_model_cache = utils.get_toplevel_model(self._meta.model)
        return self.toplevel_model_cache
        
    toplevel_model = property(get_toplevel_model)
    
    def __init__(self, *args, **kwargs):
        
        super(BaseEasyTreeForm, self).__init__(*args, **kwargs)
        
        raw_relative_to = getattr(self.instance._easytree_meta, 'raw_relative_to', False)
        choice_field_kwargs = {
            'queryset': self.toplevel_model.objects.order_by('tree_id', 'lft'),
            'required': False,
            'label': _("Relative to %(modelname)s") % {'modelname': self.toplevel_model._meta.verbose_name}
        }
        if raw_relative_to:
            choice_field_kwargs['widget'] = forms.TextInput

        self.fields['relative_to'] = EasyTreeModelChoiceField(**choice_field_kwargs)
        
        max_depth = getattr(self.instance._easytree_meta, 'max_depth', 0)
        if max_depth == 1:
            relative_positions_choices = ('left', 'right', 'first-sibling', 'last-sibling')
        elif getattr(self.instance, 'node_order_by', None):
            relative_positions_choices = ('sorted-sibling', 'sorted-child')
        else:
            relative_positions_choices = [k for k in pos_map.keys() if k not in ('sorted-sibling', 'sorted-child')]
                
        self.fields['relative_position'] = forms.ChoiceField(
            required=False,
            choices=[('','-------')] + [(k, v) for k, v in pos_map.items() if k in relative_positions_choices],
            label=_("Relative position")
        )

    def clean(self):
        
        cleaned_data = self.cleaned_data
        
        model = self.toplevel_model
        
        relative_to = cleaned_data.get('relative_to')
        relative_position = cleaned_data.get('relative_position')
        
        if not self.instance.pk:
            
            if not relative_to:
                try:
                    model.objects.validate_root(None, relative_to, pos=relative_position, cleaned_data=cleaned_data)
                except EasyTreeException, e:
                    raise forms.ValidationError, e.message
            else:
                if relative_position in ('last-child', 'first-child', 'sorted-child'):
                    
                    try:
                        model.objects.validate_child(None, relative_to, pos=relative_position, cleaned_data=cleaned_data)
                    except EasyTreeException, e:
                        raise forms.ValidationError, e.message
                        
                else:
                    
                    try:
                        model.objects.validate_sibling(None, relative_to, pos=relative_position, cleaned_data=cleaned_data)
                    except EasyTreeException, e:
                        raise forms.ValidationError, e.message
                        
        else:
            if relative_to:
                try:
                    model.objects.validate_move(self.instance, relative_to, pos=relative_position, cleaned_data=cleaned_data)
                except EasyTreeException, e:
                    raise forms.ValidationError, e.message        
        
        cleaned_data['relative_to'] = relative_to
        
        return cleaned_data
        
    def save(self, **kwargs):
        instance = super(BaseEasyTreeForm, self).save(commit=False)
        relative_to = self.cleaned_data.get('relative_to', None)
        relative_position = self.cleaned_data.get('relative_position')
        if relative_to:
            instance.easytree_relative_position = relative_position
            instance.easytree_relative_to = relative_to
        if kwargs.get('commit', False):
            instance.save() 
        return instance
