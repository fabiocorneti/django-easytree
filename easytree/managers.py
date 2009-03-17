from django.db import models
from django.db.models.signals import pre_save, post_save
from django.db import connection
from easytree.moveoptions import MoveOptions
import logging

def move_post_save(sender, instance, **kwargs):
    new_parent = getattr(instance, 'parent', None)
    current_parent = getattr(instance, 'current_parent', None)
    if new_parent and current_parent:
        logging.debug('move_post_save: moved %s form %s to %s' % (str(instance), str(current_parent), str(new_parent)) )
        sender.easytree.move(instance, new_parent, pos='first-child')

def calculate_lft_rght(sender, instance, **kwargs):
    new_parent = getattr(instance, 'parent', None)
    current_parent = sender.easytree.get_parent_for(instance)
    instance.current_parent = current_parent
    if new_parent and not current_parent:
         logging.debug('calculate_lft_rght: added child to: %s' % str(new_parent))
         sender.easytree.add_child_to(new_parent, new_object=instance, pos='first-sibling')
    if not new_parent and not current_parent:
         logging.debug('calculate_lft_rght: added new root: %s' % str(instance))
         sender.easytree.add_root(new_object=instance)
        
class EasyTreeManager(models.Manager):
    
    def __init__(self, *args, **kwargs):
        
        super(EasyTreeManager, self).__init__(*args, **kwargs)

        move_opts_class = kwargs.get('move_opts_class', MoveOptions)
        self.move_opts = move_opts_class(self)
        
    
    def contribute_to_class(self, model, name):
        super(EasyTreeManager, self).contribute_to_class(model, name)
        if model == self.get_first_model():
            pre_save.connect(calculate_lft_rght, sender=model)
            post_save.connect(move_post_save, sender=model)
        
    def get_first_model(self):
        return self.model
        
    def get_descendant_count(self, target):
        """
        :returns: the number of descendants of a node.

        See: :meth:`treebeard.Node.get_descendant_count`
        """
        return (target.rgt - target.lft - 1) / 2

    def get_ancestors_for(self, target):

        """
        :returns: A queryset containing the current node object's ancestors,
            starting by the root node and descending to the parent.

        See: :meth:`treebeard.Node.get_ancestors`
        """
        cls = self.get_first_model()
        
        if self.is_root(target):
            return cls.objects.none()
        if not target.rgt:
            return cls.objects.none()
        return cls.objects.filter(
            tree_id=target.tree_id,
            lft__lt=target.lft,
            rgt__gt=target.rgt)
            
    def get_descendants_for(self, target):
        """
        :returns: A queryset of all the node's descendants as DFS, doesn't
            include the node itself

        See: :meth:`treebeard.Node.get_descendants`
        """
        cls = self.get_first_model()

        if self.is_leaf(target):
            return cls.objects.none()
        return self.get_tree(target).exclude(pk=target.id)

    def is_descendant(self, target, node):
        """
        :returns: ``True`` if the node if a descendant of another node given
            as an argument, else, returns ``False``

        See: :meth:`treebeard.Node.is_descendant_of_of`
        """
        return target.tree_id == node.tree_id and \
               target.lft > node.lft and \
               target.rgt < node.rgt
               
    def get_parent_for(self, target, update=False):
        """
        :returns: the parent node of the current node object.
            Caches the result in the object itself to help in loops.

        See: :meth:`treebeard.Node.get_parent`
        """
        if self.is_root(target):
            return None
        try:
            if update:
                del target._cached_parent_obj
            else:
                return target._cached_parent_obj
        except AttributeError:
            pass
        # parent = our most direct ancestor
        try: 
            target._cached_parent_obj = self.get_ancestors_for(target).reverse()[0]
        except IndexError:
            return None
        return target._cached_parent_obj
                
    def get_siblings_for(self, target):
        """
        :returns: A queryset of all the node's siblings, including the node
            itself.

        See: :meth:`treebeard.Node.get_siblings`
        """
        if target.lft == 1:
            return self.get_root_nodes()
        return self.get_children_for(self.get_parent_for(target, True))
        
    def get_root_nodes(self):
        cls = self.get_first_model()
        """
        :returns: A queryset containing the root nodes in the tree.

        Example::

           MyTreeModel.easytree.get_root_nodes()
        """
        return cls.objects.filter(lft=1)        
        
    def get_last_root_node(self):
        cls = self.get_first_model()

        """
        :returns: The last root node in the tree or ``None`` if it is empty

        Example::

           MyTreeModel.easytree.get_last_root_node()

        """
        try:
            return self.get_root_nodes().reverse()[0]
        except IndexError:
            return None
            
    def _get_close_gap_sql(self, drop_lft, drop_rgt, tree_id):
        cls = self.get_first_model()
        
        sql = 'UPDATE %(table)s ' \
              ' SET lft = CASE ' \
              '           WHEN lft > %(drop_lft)d ' \
              '           THEN lft - %(gapsize)d ' \
              '           ELSE lft END, ' \
              '     rgt = CASE ' \
              '           WHEN rgt > %(drop_lft)d ' \
              '           THEN rgt - %(gapsize)d ' \
              '           ELSE rgt END ' \
              ' WHERE (lft > %(drop_lft)d ' \
              '     OR rgt > %(drop_lft)d) AND '\
              '     tree_id=%(tree_id)d' % {
                  'table': cls._meta.db_table,
                  'gapsize': drop_rgt - drop_lft + 1,
                  'drop_lft': drop_lft,
                  'tree_id': tree_id
              }
        return sql, []
        
    def move(self, target, dest, pos=None):
        """
        Moves the current node and all it's descendants to a new position
        relative to another node.

        See: :meth:`treebeard.Node.move`
        """

        pos = self.move_opts.fix_move_opts(target, dest, pos)
        cls = self.get_first_model()

        stmts = []
        parent = None

        if pos in ('first-child', 'last-child', 'sorted-child'):
            # moving to a child
            if self.is_leaf(dest):
                parent = dest
                pos = 'last-child'
            else:
                dest = self.get_last_child_for(dest)
                pos = {'first-child': 'first-sibling',
                       'last-child': 'last-sibling',
                       'sorted-child': 'sorted-sibling'}[pos]

        if self.is_descendant_of(dest, target):
            raise InvalidMoveToDescendant("Can't move node to a descendant.")

        if target == dest and (
              (pos == 'left') or \
              (pos in ('right', 'last-sibling') and \
                dest == self.get_last_sibling(dest)) or \
              (pos == 'first-sibling' and \
                dest == self.get_first_sibling(dest))):
            # special cases, not actually moving the node so no need to UPDATE
            return

        if pos == 'sorted-sibling':
            siblings = list(self.get_sorted_pos_queryset_for(dest, \
                self.get_siblings_for(dest, self), target))
            if siblings:
                pos = 'left'
                dest = siblings[0]
            else:
                pos = 'last-sibling'
        if pos in ('left', 'right', 'first-sibling'):
            siblings = list(self.get_siblings_for(dest))

            if pos == 'right':
                if dest == siblings[-1]:
                    pos = 'last-sibling'
                else:
                    pos = 'left'
                    found = False
                    for node in siblings:
                        if found:
                            dest = node
                            break
                        elif node == dest:
                            found = True
            if pos == 'left':
                if dest == siblings[0]:
                    pos = 'first-sibling'
            if pos == 'first-sibling':
                dest = siblings[0]
        
        # ok let's move this
        cursor = connection.cursor()
        move_right = self._move_right
        gap = target.rgt - target.lft + 1
        sql = None
        dest_tree = dest.tree_id

        # first make a hole
        if pos == 'last-child':
            newpos = parent.rgt
            sql, params = move_right(dest.tree_id, newpos, False, gap)
        elif self.is_root(dest):
            newpos = 1
            if pos == 'last-sibling':
                dest_tree = get_siblings_for(dest).reverse()[0].tree_id + 1
            elif pos == 'first-sibling':
                dest_tree = 1
                sql, params = self._move_tree_right(1)
            elif pos == 'left':
                sql, params = self._move_tree_right(dest.tree_id)
        else:
            if pos == 'last-sibling':
                newpos = self.get_parent(dest).rgt
                sql, params = move_right(dest.tree_id, newpos, False, gap)
            elif pos == 'first-sibling':
                newpos = dest.lft
                sql, params = move_right(dest.tree_id, newpos-1, False, gap)
            elif pos == 'left':
                newpos = dest.lft
                sql, params = move_right(dest.tree_id, newpos, True, gap)

        if sql:
            cursor.execute(sql, params)

        # we reload 'self' because lft/rgt may have changed

        fromobj = cls.objects.get(pk=target.id)

        depthdiff = dest.depth - fromobj.depth
        if parent:
            depthdiff += 1

        # move the tree to the hole
        sql = "UPDATE %(table)s " \
              " SET tree_id = %(dest_tree)d, " \
              "     lft = lft + %(jump)d , " \
              "     rgt = rgt + %(jump)d , " \
              "     depth = depth + %(depthdiff)d " \
              " WHERE tree_id = %(from_tree)d AND " \
              "     lft BETWEEN %(fromlft)d AND %(fromrgt)d" % {
                  'table': cls._meta.db_table,
                  'from_tree': fromobj.tree_id,
                  'dest_tree': dest_tree,
                  'jump': newpos - fromobj.lft,
                  'depthdiff': depthdiff,
                  'fromlft': fromobj.lft,
                  'fromrgt': fromobj.rgt
              }
        cursor.execute(sql, [])

        # close the gap
        sql, params = self._get_close_gap_sql(fromobj.lft,
            fromobj.rgt, fromobj.tree_id)
        cursor.execute(sql, params)
            
    def _move_right(self, tree_id, rgt, lftmove=False, incdec=2):
        cls = self.get_first_model()

        if lftmove:
            lftop = '>='
        else:
            lftop = '>'
        sql = 'UPDATE %(table)s ' \
              ' SET lft = CASE WHEN lft %(lftop)s %(parent_rgt)d ' \
              '                THEN lft %(incdec)+d ' \
              '                ELSE lft END, ' \
              '     rgt = CASE WHEN rgt >= %(parent_rgt)d ' \
              '                THEN rgt %(incdec)+d ' \
              '                ELSE rgt END ' \
              ' WHERE rgt >= %(parent_rgt)d AND ' \
              '       tree_id = %(tree_id)s' % {
                  'table': cls._meta.db_table,
                  'parent_rgt': rgt,
                  'tree_id': tree_id,
                  'lftop': lftop,
                  'incdec': incdec}
        return sql, []

    def _move_tree_right(self, tree_id):
        cls = self.get_first_model()
        
        sql = 'UPDATE %(table)s ' \
              ' SET tree_id = tree_id+1 ' \
              ' WHERE tree_id >= %(tree_id)d' % {
                  'table': cls._meta.db_table,
                  'tree_id': tree_id
              }
        return sql, []

    def add_sibling_to(self, target, pos=None, new_object=None, **kwargs):
        """
        Adds a new node as a sibling to the current node object.

        See: :meth:`treebeard.Node.add_sibling`
        """
        cls = self.get_first_model()
        
        pos = self.move_opts.fix_add_sibling_opts(new_object, target, pos)

        # creating a new object
        new_object = new_object or cls(**kwargs)
        new_object.depth = target.depth

        sql = None

        if self.is_root(target):
            new_object.lft = 1
            new_object.rgt = 2
            if pos == 'sorted-sibling':
                siblings = list(self.get_sorted_pos_queryset_for(target, \
                    self.get_siblings(target), new_object))
                if siblings:
                    pos = 'left'
                    target = siblings[0]
                else:
                    pos = 'last-sibling'

            last_root = cls.get_last_root_node()
            if pos == 'last-sibling' \
                  or (pos == 'right' and target == last_root):
                new_object.tree_id = last_root.tree_id + 1
            else:
                newpos = {'first-sibling': 1,
                          'left': target.tree_id,
                          'right': target.tree_id + 1}[pos]
                sql, params = self._move_tree_right(target, newpos)

                new_object.tree_id = newpos
        else:
            new_object.tree_id = target.tree_id

            if pos == 'sorted-sibling':
                siblings = list(self.get_sorted_pos_queryset_for(target,
                    self.get_siblings_for(target), new_object))
                if siblings:
                    pos = 'left'
                    target = siblings[0]
                else:
                    pos = 'last-sibling'

            if pos in ('left', 'right', 'first-sibling'):
                siblings = list(self.get_siblings_for(target))

                if pos == 'right':
                    if target == siblings[-1]:
                        pos = 'last-sibling'
                    else:
                        pos = 'left'
                        found = False
                        for node in siblings:
                            if found:
                                target = node
                                break
                            elif node == target:
                                found = True
                if pos == 'left':
                    if target == siblings[0]:
                        pos = 'first-sibling'
                if pos == 'first-sibling':
                    target = siblings[0]

            move_right = self._move_right

            if pos == 'last-sibling':
                newpos = self.get_parent_for(target).rgt
                sql, params = move_right(target.tree_id, newpos, False, 2)
            elif pos == 'first-sibling':
                newpos = target.lft
                sql, params = move_right(target.tree_id, newpos-1, False, 2)
            elif pos == 'left':
                newpos = target.lft
                sql, params = move_right(target.tree_id, newpos, True, 2)

            new_object.lft = newpos
            new_object.rgt = newpos + 1

        # saving the instance before returning it
        if sql:
            cursor = connection.cursor()
            cursor.execute(sql, params)
        
    def add_child_to(self, target, new_object=None, **kwargs):
        """
        Adds a child to the node.

        See: :meth:`treebeard.Node.add_child`
        """
        cls = self.get_first_model()
        
        if not self.is_leaf(target):
            # there are child nodes, delegate insertion to add_sibling
            if getattr(target, 'node_order_by', None):
                kwargs['pos'] = 'sorted-sibling'
            else:
                kwargs['pos'] = 'last-sibling'
            last_child = self.get_last_child_for(target)
            tmp = cls.objects.get(pk=target.id)
            last_child._cached_parent_obj = target
            return self.add_sibling_to(last_child, new_object=new_object, **kwargs)

        # we're adding the first child of this node
        sql, params = self._move_right(target.tree_id, target.rgt, False,
                                                 2)

        # creating a new object
        newobj = new_object or cls(**kwargs)
        newobj.tree_id = target.tree_id
        newobj.depth = target.depth + 1
        newobj.lft = target.lft+1
        newobj.rgt = target.lft+2

        # this is just to update the cache
        target.rgt = target.rgt+2

        newobj._cached_parent_obj = target

        cursor = connection.cursor()
        cursor.execute(sql, params)
                    
    def add_root(self, new_object=None, **kwargs):
        """
        Adds a root node to the tree.

        See: :meth:`treebeard.Node.add_root`
        """
        cls = self.get_first_model()

        # do we have a root node already?
        last_root = self.get_last_root_node()

        if last_root and getattr(last_root, 'node_order_by', None):
            # there are root nodes and node_order_by has been set
            # delegate sorted insertion to add_sibling
            return self.add_sibling_to(last_root, 'sorted-sibling', new_object=new_object, **kwargs)

        if last_root:
            # adding the new root node as the last one
            newtree_id = last_root.tree_id + 1
        else:
            # adding the first root node
            newtree_id = 1

        new_object = new_object or cls(**kwargs)
        new_object.depth = 1
        new_object.tree_id = newtree_id
        new_object.lft = 1
        new_object.rgt = 2

    def get_tree(self, parent=None):
        """
        :returns: A *queryset* of nodes ordered as DFS, including the parent. If
                  no parent is given, all trees are returned.

        See: :meth:`treebeard.Node.get_tree`

        .. note::

            This metod returns a queryset.
        """
        cls = self.model

        if parent is None:
            # return the entire tree
            return cls.objects.all()
        if self.is_leaf(parent):
            return cls.objects.filter(pk=parent.id)
        return cls.objects.filter(
            tree_id=parent.tree_id,
            lft__range=(parent.lft, parent.rgt-1))
            
    def get_depth_for(self, target):
        """
        :returns: the depth (level) of the node

        See: :meth:`treebeard.Node.get_depth`
        """
        return target.depth


    def get_root(self, target):
        """
        :returns: the root node for the current node object.

        See: :meth:`treebeard.Node.get_root`
        """
        cls = self.get_first_model()
        try:
            if target.lft == 1:
                return target
            return cls.objects.get(tree_id=target.tree_id, lft=1)
        except cls.DoesNotExist:
            return None
            
    def is_root(self, target):
        """
        :returns: True if the node is a root node (else, returns False)

        Example::

           node.is_root()
        """
        return self.get_root(target) == self

    def is_leaf(self, target):
        """
        :returns: True if the node is a leaf node (else, returns False)

        See: :meth:`treebeard.Node.is_leaf`
        """
        return target.rgt - target.lft == 1
        
    def get_children_for(self, target):
        """
        :returns: A queryset of all the node's children

        See: :meth:`treebeard.Node.get_children`
        """
        return self.get_descendants_for(target).filter(depth=target.depth+1)
        
    def get_last_child_for(self, target):
        """
        :returns: The rightmost node's child, or None if it has no children.

        Example::

           node.get_last_child()
        """
        try:
            return self.get_children_for(target).reverse()[0]
        except IndexError:
            return None
            

        
    def get_sorted_pos_queryset_for(self, target, siblings, newobj):
        """
        :returns: The position a new node will be inserted related to the
        current node, and also a queryset of the nodes that must be moved
        to the right. Called only for Node models with :attr:`node_order_by`

        This function was taken from django-mptt (BSD licensed) by Jonathan Buchanan:
        http://code.google.com/p/django-mptt/source/browse/trunk/mptt/signals.py?spec=svn100&r=100#12
        """

        fields, filters = [], []
        for field in target.node_order_by:
            value = getattr(newobj, field)
            filters.append(Q(*
                [Q(**{f: v}) for f, v in fields] +
                [Q(**{'%s__gt' % field: value})]))
            fields.append((field, value))
        return siblings.filter(reduce(operator.or_, filters))
        try:
            newpos = target._get_lastpos_in_path(siblings.all()[0].path)
        except IndexError:
            newpos, siblings = None, []
        return newpos, siblings