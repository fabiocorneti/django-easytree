from easytree.exceptions import InvalidMoveToDescendant, MissingNodeOrderBy, InvalidPosition
import logging

class MoveOptions(object):
    
    def __init__(self, manager):
        self.manager = manager
        self.model = self.manager.model
        
    def validate_root(self, target, related, pos=None, **kwargs):
        
        node_order_by = getattr(self.model, 'node_order_by', None)
        
        self.process_validators(target, related, related, pos=None, func='add_root', **kwargs)
            
    def validate_sibling(self, target, related, pos=None, **kwargs):
        
        node_order_by = getattr(self.model, 'node_order_by', None)
        
        if pos not in ('first-sibling', 'left', 'right', 'last-sibling', 'sorted-sibling'):
            raise InvalidPosition('Invalid relative position: %s' % (pos,))
        if node_order_by and pos != 'sorted-sibling':
            raise InvalidPosition('Must use %s in add_sibling when'
                                  ' node_order_by is enabled' % ('sorted-sibling',))
        if pos == 'sorted-sibling' and not node_order_by:
            raise MissingNodeOrderBy('Missing node_order_by attribute.')
        
        self.process_validators(target, related, related, pos=None, func='add_sibling', **kwargs)
        
    def validate_child(self, target, related, pos=None, **kwargs):
        
        node_order_by = getattr(self.model, 'node_order_by', None)
        
        if pos not in ('first-child', 'last-child', 'sorted-child'):
            raise InvalidPosition('Invalid relative position: %s' % (pos,))
        if node_order_by and pos != 'sorted-child':
            raise InvalidPosition('Must use %s in add_child when'
                                  ' node_order_by is enabled' % ('sorted-child',))
        if pos == 'sorted-child' and not node_order_by:
            raise MissingNodeOrderBy('Missing node_order_by attribute.')
            
        self.process_validators(target, related, related, pos=None, func='add_child', **kwargs)
        
    def validate_move(self, target, related, pos, **kwargs):
        
        node_order_by = getattr(self.model, 'node_order_by', None)

        if pos not in ('first-sibling', 'left', 'right', 'last-sibling', 'sorted-sibling',
                       'first-child', 'last-child', 'sorted-child'):
            raise InvalidPosition('Invalid relative position: %s' % (pos,))
        if node_order_by and pos not in ('sorted-child', 'sorted-sibling'):
            raise InvalidPosition('Must use %s or %s in move when'
                                  ' node_order_by is enabled' % ('sorted-sibling',
                                  'sorted-child'))
        if pos in ('sorted-child', 'sorted-sibling') and not node_order_by:
            raise MissingNodeOrderBy('Missing node_order_by attribute.')
            
        parent = None
        dest = related
        
        if pos in ('first-child', 'last-child', 'sorted-child'):
            # moving to a child
            if self.manager.is_leaf(dest):
                parent = dest
                pos = 'last-child'
            else:
                dest = self.manager.get_last_child_for(dest)
                pos = {'first-child': 'first-sibling',
                       'last-child': 'last-sibling',
                       'sorted-child': 'sorted-sibling'}[pos]
                       
        if self.manager.is_descendant_of(dest, target):
            raise InvalidMoveToDescendant("Can't move node to a descendant.")
        
        self.process_validators(target, dest, related, pos=None, func='move', **kwargs)
        
        return (pos, dest, parent)                
        
    def process_validators(self, target, related, realrelated, pos, func=None, **kwargs):
        for v in getattr(self.manager, 'validators', []):
            validator = v()
            validator_func = getattr(validator, 'validate_%s' % func)
            if validator_func:
                validator_func(target, related, realrelated, pos, **kwargs) 
                
    def fix_add_sibling_vars(self, target, related, pos):
        """
        prepare the pos variable for the add_sibling method
        """
        node_order_by = getattr(self.model, 'node_order_by', None)
        
        if pos is None:
            if node_order_by:
                pos = 'sorted-sibling'
            else:
                pos = 'last-sibling'
                
        self.validate_sibling(target, related, pos)

        return pos   
             
    def fix_move_vars(self, target, related, pos):
        """
        prepare the pos var for the move method
        """
        node_order_by = getattr(self.model, 'node_order_by', None)
        
        if pos is None:
            if node_order_by:
                pos = 'sorted-sibling'
            else:
                pos = 'last-sibling'
                
        return self.validate_move(target, related, pos)