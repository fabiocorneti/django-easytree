.. _easytree_meta_options:

EasyTreeMeta options
====================

.. _easytree_meta_validators:

validators
----------

A list of EasyTree validators.

Example validator:

.. literalinclude:: ../easytree/validators.py
   :language: python
   
Each validator function is passed all kwrags from the manager fuctions validate_root, validate_sibling, validate_child and validate_move. See :ref:`Manager functions <manager_validation>`

node_order_by
-------------

Not implemented yet.

max_depth
---------

Max tree depth; implementation in progress.

raw_relative_to
---------------

If set to True, the relative_to widget for the model will be set to ``django.forms.TextInput`` .