class MoveOptions(object):
    
    def __init__(self, manager):
        self.manager = manager
        self.model = self.manager.model
    
    def validate_add_sibling_opts(self, target, related, pos, **kwargs):
        
        node_order_by = getattr(self.model, 'node_order_by', None)
        
        if pos not in ('first-sibling', 'left', 'right', 'last-sibling', 'sorted-sibling'):
            raise InvalidPosition('Invalid relative position: %s' % (pos,))
        if node_order_by and pos != 'sorted-sibling':
            raise InvalidPosition('Must use %s in add_sibling when'
                                  ' node_order_by is enabled' % ('sorted-sibling',))
        if pos == 'sorted-sibling' and not node_order_by:
            raise MissingNodeOrderBy('Missing node_order_by attribute.')
                
    def fix_add_sibling_opts(self, target, related, pos):
        """
        prepare the pos variable for the add_sibling method
        """
        node_order_by = getattr(self.model, 'node_order_by', None)
        
        if pos is None:
            if node_order_by:
                pos = 'sorted-sibling'
            else:
                pos = 'last-sibling'
                
        self.validate_add_sibling_opts(target, related, pos)

        return pos
        
    def validate_move_opts(self, target, related, pos, **kwargs):
        
        node_order_by = getattr(self.model, 'node_order_by', None)

        if pos not in ('first-sibling', 'left', 'right', 'last-sibling', 'sorted-sibling',
                       'first-child', 'last-child', 'sorted-child'):
            raise InvalidPosition('Invalid relative position: %s' % (pos,))
        if node_order_by and pos not in ('sorted-child', 'sorted-sibling'):
            raise InvalidPosition('Must use %s or %s in add_sibling when'
                                  ' node_order_by is enabled' % ('sorted-sibling',
                                  'sorted-child'))
        if pos in ('sorted-child', 'sorted-sibling') and not node_order_by:
            raise MissingNodeOrderBy('Missing node_order_by attribute.')
            
    def fix_move_opts(self, target, related, pos):
        """
        prepare the pos var for the move method
        """
        node_order_by = getattr(self.model, 'node_order_by', None)
        
        if pos is None:
            if node_order_by:
                pos = 'sorted-sibling'
            else:
                pos = 'last-sibling'
                
        self.validate_move_opts(target, related, pos)
        
        return pos