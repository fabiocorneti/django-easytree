from django.db import models
from django.db.models.signals import pre_save, post_save
from django.db import transaction, connection
from easytree import utils
from easytree.exceptions import InvalidMoveToDescendant, MissingNodeOrderBy, InvalidPosition
from easytree.signals import node_moved
from django.db.models import Q
import logging
import operator

def move_post_save(sender, instance, created, **kwargs):
    
    relative_to = getattr(instance, 'easytree_relative_to', None)
    relative_position = getattr(instance, 'easytree_relative_position', None) 
    
    if relative_to and not created:
        logging.debug(u'move_post_save: moved %s to %s | %s' % (unicode(instance), unicode(relative_to), (relative_position)) )
        sender.objects.move(instance, relative_to, pos=relative_position)
    
    # in case of saving models twice
    instance.easytree_relative_to = None
    instance.easytree_relative_position = None
    instance.easytree_current_parent = None
    
def calculate_lft_rght(sender, instance, **kwargs):
    
    relative_to = getattr(instance, 'easytree_relative_to', None)
    relative_position = getattr(instance, 'easytree_relative_position', None) 
    
    if not instance.pk:
        
        if relative_to:
            if relative_position in ('first-child', 'last-child', 'sorted-child'):
                logging.debug(u'calculate_lft_rght: added child to: %s | %s' % (unicode(relative_to), relative_position))
                sender.objects.add_child_to(relative_to, new_object=instance, pos=relative_position)
            else:
                logging.debug(u'calculate_lft_rght: added sibling to: %s | %s' % (unicode(relative_to), relative_position))
                sender.objects.add_sibling_to(relative_to, new_object=instance, pos=relative_position)
                      
        if not relative_to:
             logging.debug('calculate_lft_rght: added new root: %s | %s' % (unicode(instance), relative_position))
             sender.objects.add_root(new_object=instance)

class EasyTreeQuerySet(models.query.QuerySet):
    """
    Custom queryset for the tree node manager.

    Needed only for the customized delete method.
    """

    def delete(self, removed_ranges=None):
        """
        Custom delete method, will remove all descendant nodes to ensure a
        consistent tree (no orphans)

        :returns: ``None``
        """
        if removed_ranges is not None:
            # we already know the children, let's call the default django
            # delete method and let it handle the removal of the user's
            # foreign keys...
            super(EasyTreeQuerySet, self).delete()
            cursor = connection.cursor()

            # Now closing the gap (Celko's trees book, page 62)
            # We do this for every gap that was left in the tree when the nodes
            # were removed.  If many nodes were removed, we're going to update
            # the same nodes over and over again. This would be probably
            # cheaper precalculating the gapsize per intervals, or just do a
            # complete reordering of the tree (uses COUNT)...
            for tree_id, drop_lft, drop_rgt in sorted(removed_ranges, reverse=True):
                sql, params = self.model.objects._get_close_gap_sql(drop_lft, drop_rgt,
                                                            tree_id)
                cursor.execute(sql, params)
        else:
            # we'll have to manually run through all the nodes that are going
            # to be deleted and remove nodes from the list if an ancestor is
            # already getting removed, since that would be redundant
            removed = {}
            for node in self.order_by('tree_id', 'lft'):
                found = False
                for rid, rnode in removed.items():
                    if self.model.objects.is_descendant_of(node, rnode):
                        found = True
                        break
                if not found:
                    removed[node.id] = node
            logging.debug('removed: %s' % str(removed))
            # ok, got the minimal list of nodes to remove...
            # we must also remove their descendants
            toremove = []
            ranges = []
            for id, node in removed.items():
                toremove.append(
                  Q(lft__range=(node.lft, node.rgt))&Q(tree_id=node.tree_id))
                ranges.append((node.tree_id, node.lft, node.rgt))
            if toremove:
                self.model.objects.filter(
                    reduce(operator.or_, toremove)).delete(removed_ranges=ranges)
                    
class EasyTreeManager(models.Manager):
    
    def get_query_set(self):
        """
        Sets the custom queryset as the default.
        """
        return EasyTreeQuerySet(self.model)
        
    def __init__(self, *args, **kwargs):
        
        super(EasyTreeManager, self).__init__(*args, **kwargs)

        self.validators = kwargs.get('validators', [])
        
    def contribute_to_class(self, model, name):
        super(EasyTreeManager, self).contribute_to_class(model, name)
        pre_save.connect(calculate_lft_rght, sender=model)
        post_save.connect(move_post_save, sender=model)
        
    def get_first_model(self):
        return utils.get_toplevel_model(self.model)
        
    def get_descendant_count(self, target):
        """
        :returns: the number of descendants of a node.
        """
        return (target.rgt - target.lft - 1) / 2

    def get_ancestors_for(self, target):

        """
        :returns: A queryset containing the current node object's ancestors,
            starting by the root node and descending to the parent.
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

        See: :meth:`easytree.managers.EasyTreeManager.get_descendants_for`
        """
        cls = self.get_first_model()

        if self.is_leaf(target):
            return cls.objects.none()
        return self.get_tree(target).exclude(pk=target.id)

    def is_descendant_of(self, target, node):
        """
        :returns: ``True`` if the node if a descendant of another node given
            as an argument, else, returns ``False``

        See: :meth:`easytree.managers.EasyTreeManager.is_descendant_of`
        """
        return target.tree_id == node.tree_id and \
               target.lft > node.lft and \
               target.rgt < node.rgt
               
    def get_parent_for(self, target, update=False):
        """
        :returns: the parent node of the current node object.
            Caches the result in the object itself to help in loops.

        See: :meth:`easytree.managers.EasyTreeManager.get_parent_for`
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

        See: :meth:`easytree.managers.EasyTreeManager.get_siblings_for`
        """
        if target.lft == 1:
            return self.get_root_nodes()
        return self.get_children_for(self.get_parent_for(target, True))
        
    def get_first_sibling_for(self, target):
        """
        :returns: The leftmost node's sibling, can return the node itself if it
            was the leftmost sibling.

        Example::
         
           MyTreeModel.objects.get_first_sibling_for(instance)
        """
        return self.get_siblings_for(target)[0]
    
    def get_root_nodes(self):
        cls = self.get_first_model()
        """
        :returns: A queryset containing the root nodes in the tree.

        Example::

           MyTreeModel.objects.get_root_nodes()
        """
        return cls.objects.filter(lft=1)        
        
    def get_last_root_node(self):
        cls = self.get_first_model()

        """
        :returns: The last root node in the tree or ``None`` if it is empty

        Example::

           MyTreeModel.objects.get_last_root_node()

        """
        try:
            return self.get_root_nodes().reverse()[0]
        except IndexError:
            return None

    def get_tree(self, parent=None):
        """
        :returns: A *queryset* of nodes ordered as DFS, including the parent. If
                  no parent is given, all trees are returned.

        See: :meth:`easytree.managers.EasyTreeManager.get_tree`

        .. note::

            This metod returns a queryset.
        """
        cls = self.get_first_model()

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

        See: :meth:`easytree.managers.EasyTreeManager.get_depth_for`
        """
        return target.depth

    def get_root(self, target):
        """
        :returns: the root node for the current node object.

        See: :meth:`easytree.managers.EasyTreeManager.get_root`
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
        return self.get_root(target) == target

    def is_leaf(self, target):
        """
        :returns: True if the node is a leaf node (else, returns False)

        See: :meth:`easytree.managers.EasyTreeManager.is_leaf`
        """
        return target.rgt - target.lft == 1
        
    def get_children_for(self, target):
        """
        :returns: A queryset of all the node's children

        See: :meth:`easytree.managers.EasyTreeManager.get_children`
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
            
    def move(self, target, real_dest, pos=None):
        """
        Moves the current node and all it's descendants to a new position
        relative to another node.
        """
        
        stmts = []
        parent = None
        
        cls = self.get_first_model()
        dest = real_dest
        real_pos = pos
        
        pos, dest, parent = self.fix_move_vars(target, dest, pos)

        if target == dest and (
              (pos == 'left') or \
              (pos in ('right', 'last-sibling') and \
                dest == self.get_last_sibling(dest)) or \
              (pos == 'first-sibling' and \
                dest == self.get_first_sibling_for(dest))):
            # special cases, not actually moving the node so no need to UPDATE
            return

        if pos == 'sorted-sibling':
            siblings = list(self.get_sorted_pos_queryset_for(dest, \
                self.get_siblings_for(dest), target))
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
                dest_tree = self.get_siblings_for(dest).reverse()[0].tree_id + 1
            elif pos == 'first-sibling':
                dest_tree = 1
                sql, params = self._move_tree_right(1)
            elif pos == 'left':
                sql, params = self._move_tree_right(dest.tree_id)
        else:
            if pos == 'last-sibling':
                newpos = self.get_parent_for(dest).rgt
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
        
        logging.debug('%s %s' %  (dest_tree, fromobj.tree_id))
        if self.is_root(target) and self.is_root(dest): # close gap when moving root nodes
            sql, params = self._move_tree_left(fromobj.tree_id)
            cursor.execute(sql, params)
            
        transaction.commit_unless_managed()
        
        node_moved.send(
            sender=target.__class__,
            node_moved=cls.objects.get(pk=target.id), # make sure we get the updated nodes
            moved_to_node=cls.objects.get(pk=real_dest.pk),
            relative_position=real_pos
        )
            
    def add_sibling_to(self, target, pos=None, new_object=None):
        """
        Adds a new node as a sibling to the current node object.
        """
        cls = self.get_first_model()
        
        pos = self.fix_add_sibling_vars(new_object, target, pos)

        # creating a new object
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

            last_root = self.get_last_root_node()
            if pos == 'last-sibling' \
                  or (pos == 'right' and target == last_root):
                new_object.tree_id = last_root.tree_id + 1
            else:
                newpos = {'first-sibling': 1,
                          'left': target.tree_id,
                          'right': target.tree_id + 1}[pos]
                sql, params = self._move_tree_right(newpos)

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
            
        transaction.commit_unless_managed()        
        
    def add_child_to(self, target, new_object=None, pos=None):
        """
        Adds a child to the node.
        """
        cls = self.get_first_model()
        
        if not self.is_leaf(target):
            # there are child nodes, delegate insertion to add_sibling
            if self.model._easytree_meta.node_order_by:
                pos = 'sorted-sibling'
            else:
                pos = {'last-child': 'last-sibling', 'first-child': 'first-sibling'}[pos]
            last_child = self.get_last_child_for(target)
            
            last_child._cached_parent_obj = target
            return self.add_sibling_to(last_child, new_object=new_object, pos=pos)

        # we're adding the first child of this node
        sql, params = self._move_right(target.tree_id, target.rgt, False,
                                                 2)

        # creating a new object
        new_object.tree_id = target.tree_id
        new_object.depth = target.depth + 1
        new_object.lft = target.lft+1
        new_object.rgt = target.lft+2

        # this is just to update the cache
        target.rgt = target.rgt+2

        new_object._cached_parent_obj = target

        cursor = connection.cursor()
        cursor.execute(sql, params)
        transaction.commit_unless_managed()        
        
    def add_root(self, new_object=None):
        """
        Adds a root node to the tree.
        """
        cls = self.get_first_model()

        # do we have a root node already?
        last_root = self.get_last_root_node()

        if last_root and self.model._easytree_meta.node_order_by:
            # there are root nodes and node_order_by has been set
            # delegate sorted insertion to add_sibling
            return self.add_sibling_to(last_root, 'sorted-sibling', new_object=new_object)

        if last_root:
            # adding the new root node as the last one
            newtree_id = last_root.tree_id + 1
        else:
            # adding the first root node
            newtree_id = 1

        new_object
        new_object.depth = 1
        new_object.tree_id = newtree_id
        new_object.lft = 1
        new_object.rgt = 2
        
        transaction.commit_unless_managed()        
        
    def get_sorted_pos_queryset_for(self, target, siblings, newobj):
        """
        :returns: The position a new node will be inserted related to the
        current node, and also a queryset of the nodes that must be moved
        to the right. Called only for Node models with :attr:`node_order_by`

        This function was taken from django-mptt (BSD licensed) by Jonathan Buchanan:
        http://code.google.com/p/django-mptt/source/browse/trunk/mptt/signals.py?spec=svn100&r=100#12
        """

        fields, filters = [], []
        for field in self.model._easytree_meta.node_order_by:
            value = getattr(newobj, field)
            filters.append(Q(*
                [Q(**{f: v}) for f, v in fields] +
                [Q(**{'%s__gt' % field: value})]))
            fields.append((field, value))
        return siblings.filter(reduce(operator.or_, filters))
        
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
        
    def _move_tree_left(self, tree_id):
        cls = self.get_first_model()
        
        sql = 'UPDATE %(table)s ' \
              ' SET tree_id = tree_id-1 ' \
              ' WHERE tree_id >= %(tree_id)d' % {
                  'table': cls._meta.db_table,
                  'tree_id': tree_id
              }
        return sql, []
    
    """ Validation """
    
    def validate_root(self, target, related, pos=None, **kwargs):
        
        node_order_by = self.model._easytree_meta.node_order_by
        
        self.process_validators(target, related, related, pos=None, func='add_root', **kwargs)
            
    def validate_sibling(self, target, related, pos=None, **kwargs):
        
        node_order_by = self.model._easytree_meta.node_order_by
        
        if pos not in ('first-sibling', 'left', 'right', 'last-sibling', 'sorted-sibling'):
            raise InvalidPosition('Invalid relative position: %s' % (pos,))
        if node_order_by and pos != 'sorted-sibling':
            raise InvalidPosition('Must use %s in add_sibling when'
                                  ' node_order_by is enabled' % ('sorted-sibling',))
        if pos == 'sorted-sibling' and not node_order_by:
            raise MissingNodeOrderBy('Missing node_order_by attribute.')
        
        self.process_validators(target, related, related, pos=None, func='add_sibling', **kwargs)
        
    def validate_child(self, target, related, pos=None, **kwargs):
        
        node_order_by = self.model._easytree_meta.node_order_by
        
        if pos not in ('first-child', 'last-child', 'sorted-child'):
            raise InvalidPosition('Invalid relative position: %s' % (pos,))
        if node_order_by and pos != 'sorted-child':
            raise InvalidPosition('Must use %s in add_child when'
                                  ' node_order_by is enabled' % ('sorted-child',))
        if pos == 'sorted-child' and not node_order_by:
            raise MissingNodeOrderBy('Missing node_order_by attribute.')
            
        self.process_validators(target, related, related, pos=None, func='add_child', **kwargs)
        
    def validate_move(self, target, related, pos, **kwargs):
        
        node_order_by = self.model._easytree_meta.node_order_by

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
            if self.is_leaf(dest):
                parent = dest
                pos = 'last-child'
            else:
                dest = self.get_last_child_for(dest)
                pos = {'first-child': 'first-sibling',
                       'last-child': 'last-sibling',
                       'sorted-child': 'sorted-sibling'}[pos]
                       
            if dest == target:
                raise InvalidMoveToDescendant("Can't move node to a descendant.")
                           
        if self.is_descendant_of(dest, target):
            raise InvalidMoveToDescendant("Can't move node to a descendant.")

        self.process_validators(target, dest, related, pos=None, func='move', **kwargs)
        
        return (pos, dest, parent)                
        
    def process_validators(self, target, related, realrelated, pos, func=None, **kwargs):
        for validator in self.model._easytree_meta.validators:
            validator_func = getattr(validator, 'validate_%s' % func)
            if validator_func:
                validator_func(self, target, related, realrelated, pos, **kwargs) 
    
    """ Fix opts """
    
    def fix_add_sibling_vars(self, target, related, pos):
        """
        prepare the pos variable for the add_sibling method
        """
        node_order_by = self.model._easytree_meta.node_order_by
        
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
        node_order_by = self.model._easytree_meta.node_order_by
        
        if pos is None:
            if node_order_by:
                pos = 'sorted-sibling'
            else:
                pos = 'last-sibling'
                
        return self.validate_move(target, related, pos)
