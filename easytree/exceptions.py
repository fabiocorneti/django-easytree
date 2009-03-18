class InvalidPosition(Exception):
    """
    Raised when passing an invalid pos value
    """

class InvalidMoveToDescendant(Exception):
    """
    Raised when attemping to move a node to one of it's descendants.
    """

class MissingNodeOrderBy(Exception):
    """
    Raised when an operation needs a missing
    :attr:`~treebeard.MP_Node.node_order_by` attribute
    """