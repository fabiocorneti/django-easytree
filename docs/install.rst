Install
=======

-------------------------
Installation instructions
-------------------------

1. Make sure that you have `Mercurial`__ installed, and that you can run its
   commands from a shell. (Enter ``hg help`` at a shell prompt to test
   this.)

__ http://www.selenic.com/mercurial/ 

2. Check out Django easytree from the mercurial repo like so:

   .. code-block:: bash

       hg clone http://bitbucket.org/fivethreeo/django-easytree

3. Next, make sure that the Python interpreter can load Django easytree's code. There
   are various ways of accomplishing this.  One of the most convenient, on
   Linux, Mac OSX or other Unix-like systems, is to use a symbolic link:
   
   .. code-block:: bash

       ln -s `pwd`/django-easytree/easytree SITE-PACKAGES-DIR/easytree

   (In the above line, change ``SITE-PACKAGES-DIR`` to match the location of
   your system's ``site-packages`` directory, as explained in the
   "Where are my ``site-packages`` stored?" section below.)

.. admonition:: Where are my ``site-packages`` stored?

    The location of the ``site-packages`` directory depends on the operating
    system, and the location in which Python was installed. To find out your
    system's ``site-packages`` location, execute the following:
    
    .. code-block:: bash

        python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"

    (Note that this should be run from a shell prompt, not a Python interactive
    prompt.)
    
-----    
Usage
-----

Add easytree to `INSTALLED_APPS`

`````````
In models
`````````

.. code-block:: python

    from easytree.models import BaseEasyTree
    from easytree.managers import EasyTreeManager
    
    class ExampleNode(BaseEasyTree):
       
        """ any other fields you want here """
    
        objects = EasyTreeManager()
    
        class Meta:
            ordering = ('tree_id', 'lft')
        
        class EasyTreeMeta:
            """ Defaults are set to this if EasyTreeMeta is not defined. """
            validators = []
            node_order_by = []

For EasyTreeMeta options see :ref:`easytree_meta_options`

.. _easytree_admin: 

````````````
In the admin
````````````

.. code-block:: python
    
    from yourapp.models import ExampleNode
    from easytree.admin import EasyTreeAdmin
    from django.contrib import admin
    
    class ExampleNodeAdmin(EasyTreeAdmin):
        pass
    
    admin.site.register(ExampleNode, ExampleNodeAdmin)
    
If you alter list_display in your admin class, remember to add 'display_as_node'.


------------------
Available settings
------------------

```````````````````
EASTYTREE_JQUERY_JS
```````````````````

Default: ``'http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js'`` (string)

``````````````````````
EASTYTREE_JQUERY_UI_JS
``````````````````````

Default: ``'http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.1/jquery-ui.min.js'`` (string)

```````````````````````
EASTYTREE_JQUERY_UI_CSS
```````````````````````

Default: ``'notset'`` (string)

Set this setting to the jquery ui themes css file if you want dragging and dialog styles in the admin.



