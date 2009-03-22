from django.contrib.admin.templatetags.admin_list import result_headers, items_for_result
from django.template import Library
register = Library()

def results(cl):
    if cl.formset:
        for res, form in zip(cl.result_list, cl.formset.forms):
            yield list(items_for_result(cl, res, form))
    else:
        for res in cl.model.objects.filter(pk__in=[o.pk for o in cl.result_list]).order_by('tree_id', 'lft'):
            yield {'object': res, 'items': list(items_for_result(cl, res, None))}

def result_list(cl):
    return {'cl': cl,
            'result_headers': list(result_headers(cl)),
            'results': list(results(cl))}
            
result_list = register.inclusion_tag("admin/easytree_change_list_results.html")(result_list)