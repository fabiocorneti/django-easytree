def get_toplevel_model(model):
    parent_models = model._meta.get_parent_list()
    if parent_models:
        toplevel_model = list(parent_models)[0]
    else:
        toplevel_model = model
    return toplevel_model