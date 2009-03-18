
class EasyTreeException(Exception):
        
    def __init__(self, message):
        self.message = message
        
class InvalidPosition(EasyTreeException):
    pass

class InvalidMoveToDescendant(EasyTreeException):
    """
    Raised when attemping to move a node to one of it's descendants.
    """

class MissingNodeOrderBy(EasyTreeException):
    """
    Raised when an operation needs a missing
    :attr:`~treebeard.MP_Node.node_order_by` attribute
    """