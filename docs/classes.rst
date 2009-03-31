Classes
=======

.. automodule:: easytree

:mod:`easytree.models` --- Models
-----------------------------------

.. automodule:: easytree.models

   .. autoclass:: EasyTreeOptions
      :show-inheritance:

      .. automethod:: __init__

   .. autoclass:: EasyTreeModelBase
      :show-inheritance:

      .. automethod:: __new__

   .. autoclass:: BaseEasyTree
      :show-inheritance:

      .. attribute:: lft
      .. attribute:: rgt
      .. attribute:: tree_id
      .. automethod:: make_materialized_path

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
      
      .. _manager_validation:
      
      .. automethod:: validate_root
      .. automethod:: validate_sibling
      .. automethod:: validate_child
      .. automethod:: validate_move
      

:mod:`easytree.exceptions` --- Exceptions
-----------------------------------------

.. automodule:: easytree.exceptions
    
    .. autoexception:: InvalidPosition

    .. autoexception:: InvalidMoveToDescendant

    .. autoexception:: MissingNodeOrderBy
    

:mod:`easytree.forms` --- Forms
-------------------------------

.. automodule:: easytree.forms

   .. autoclass:: EasyTreeModelChoiceField
      :show-inheritance:
      
   .. autoclass:: BaseEasyTreeForm
      :show-inheritance:
      
      
:mod:`easytree.admin` --- ModelAdmin
------------------------------------

.. automodule:: easytree.admin

   .. autoclass:: EasyTreeAdmin
      :show-inheritance:
      