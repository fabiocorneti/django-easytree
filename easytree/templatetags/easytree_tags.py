from django.contrib.admin.templatetags.admin_list import result_headers, items_for_result
from django.template import Library
from django.conf import settings
import itertools, copy

register = Library()

def results(cl):
    
    objects = cl.model.objects.filter(pk__in=[o.pk for o in cl.result_list]).order_by('tree_id', 'lft')
        
    if cl.formset:
        pk_forms = dict([(form.instance.pk, form) for form in cl.formset.forms])
        forms = [pk_forms[obj.pk] for obj in objects]
        for res, form in zip(objects, forms):
            yield {'object': res, 'items': list(items_for_result(cl, res, form))}
    else:
        for res in objects:
            yield {'object': res, 'items': list(items_for_result(cl, res, None))}

def result_list(cl):
    return {'cl': cl,
            'result_headers': list(result_headers(cl)),
            'results': list(results(cl))}
            
result_list = register.inclusion_tag("admin/easytree_change_list_results.html")(result_list)

def previous_current_next(items):
    """
    From http://www.wordaligned.org/articles/zippy-triples-served-with-python

    Creates an iterator which returns (previous, current, next) triples,
    with ``None`` filling in when there is no previous or next
    available.
    """
    extend = itertools.chain([None], items, [None])
    previous, current, next = itertools.tee(extend, 3)
    try:
        current.next()
        next.next()
        next.next()
    except StopIteration:
        pass
    return itertools.izip(previous, current, next)

def tree_item_iterator(items):
    """
    Given a list of tree items, iterates over the list, generating
    two-tuples of the current tree item and a ``dict`` containing
    information about the tree structure around the item, with the
    following keys:

       ``'new_level'`
          ``True`` if the current item is the start of a new level in
          the tree, ``False`` otherwise.

       ``'closed_levels'``
          A list of levels which end after the current item. This will
          be an empty list if the next item is at the same level as the
          current item.

    """
    structure = {}
    first_level = False
    for previous, current, next in previous_current_next(items):
        
        current_level = getattr(current, 'depth')

        if previous:
            structure['new_level'] = (getattr(previous,
                                              'depth') < current_level)
        else:
            first_level = current_level
            structure['new_level'] = True

        if next:
            structure['closed_levels'] = range(current_level,
                                               getattr(next,
                                                       'depth'), -1)
        else:
            # All remaining levels need to be closed
            structure['closed_levels'] = range(current_level - first_level, -1, -1)

        # Return a deep copy of the structure dict so this function can
        # be used in situations where the iterator is consumed
        # immediately.
        yield current, copy.deepcopy(structure)

register.filter(tree_item_iterator)

def jquery_ui_media():
    if getattr(settings, 'EASYTREE_DISABLE_CHANGELIST_DD', False) == True:
        return ''
    else:
        return '''
    <script type="text/javascript" src="%s"></script>
    <script type="text/javascript" src="%s"></script>
    <link rel="stylesheet" type="text/css" href="%s" />''' % (
            getattr(settings, 'EASTYTREE_JQUERY_JS', 'http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js'),
            getattr(settings, 'EASTYTREE_JQUERY_UI_JS', 'http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.1/jquery-ui.min.js'),
            getattr(settings, 'EASTYTREE_JQUERY_UI_CSS', 'not_set')
        )
register.simple_tag(jquery_ui_media)

