def get_toplevel_model(model):
    parent_models = model._meta.get_base_chain(model)
    if parent_models:
        toplevel_model = parent_models.reverse()[0]
    else:
        toplevel_model = model
    return toplevel_model