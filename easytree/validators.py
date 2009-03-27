from easytree.exceptions import SingleRootAllowed

class SingleRootAllowedValidator(object):
    
    error_msg = "Only one root is allowed in this tree"
    
    def root_node_exists(self, manager):    
        try:
            root_node = manager.get_root_nodes()[0]
        except IndexError:
            root_node = None
        return root_node
        
    def validate_add_root(self, manager, target, related, realrelated, pos, **kwargs):
        if self.root_node_exists(manager):
            raise SingleRootAllowed(self.error_msg)
                        
    def validate_add_sibling(self, manager, target, related, realrelated, pos, **kwargs):
        if manager.is_root(related):
            if self.root_node_exists(manager):
                raise SingleRootAllowed(self.error_msg)
                
    def validate_add_child(self, manager, target, related, realrelated, pos, **kwargs):
        pass
        
    def validate_move(self, manager, target, related, realrelated, pos, **kwargs):
        if manager.is_root(related):
            if pos not in ('first-child', 'last-child') and self.root_node_exists(manager):
                raise SingleRootAllowed(self.error_msg)
        

