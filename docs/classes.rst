Classes
=======

.. automodule:: easytree

:mod:`easytree.models` --- Models
-----------------------------------

.. automodule:: easytree.models

   .. autoclass:: BaseEasyTree
      :show-inheritance:

      .. attribute:: lft
      .. attribute:: rgt
      .. attribute:: tree_id

:mod:`easytree.managers` --- Managers
-------------------------------------

.. automodule:: easytree.managers

   .. autoclass:: EasyTreeManager
      :show-inheritance:
      
      .. automethod:: add_root
      .. automethod:: add_child_to
      .. automethod:: add_sibling_to
      .. automethod:: get_tree
      .. automethod:: get_ancestors_for
      .. automethod:: get_children_for
      .. automethod:: get_descendants_for
      .. automethod:: get_descendant_count
      .. automethod:: get_parent_for
      .. automethod:: get_root
      .. automethod:: get_siblings_for
      .. automethod:: is_descendant_of
      .. automethod:: is_root
      .. automethod:: get_last_child_for
      .. automethod:: is_leaf
      .. automethod:: move
      .. automethod:: get_last_root_node
      .. automethod:: get_root_nodes

:mod:`easytree.exceptions` --- Exceptions
-----------------------------------------

.. automodule:: easytree.exceptions
    
    .. autoexception:: InvalidPosition

    .. autoexception:: InvalidMoveToDescendant

    .. autoexception:: MissingNodeOrderBy