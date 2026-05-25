import frappe

no_cache = 1

def get_context(context):
    context.no_sidebar = True
    context.no_breadcrumbs = True
    context.no_header = True
    context.no_footer = True
    context.title = "API Security Monitor"
    return context
