from django import template

register = template.Library()


@register.inclusion_tag("includes/blog_mixed_list.html", takes_context=True)
def blog_mixed_list(context, items):
    context.update({"items": items, "showdate": False})
    return context


@register.inclusion_tag("includes/blog_mixed_list.html", takes_context=True)
def blog_mixed_list_with_dates(context, items):
    context.update({"items": items, "showdate": True})
    return context


@register.simple_tag(takes_context=True)
def page_href(context, page):
    query_dict = context["request"].GET.copy()
    if page == 1 and "page" in query_dict:
        del query_dict["page"]
    query_dict["page"] = str(page)
    return "?" + query_dict.urlencode()


@register.simple_tag(takes_context=True)
def add_qsarg(context, name, value):
    query_dict = context["request"].GET.copy()
    if value not in query_dict.getlist(name):
        query_dict.appendlist(name, value)
    return "?" + query_dict.urlencode()


@register.simple_tag(takes_context=True)
def remove_qsarg(context, name, value):
    query_dict = context["request"].GET.copy()
    query_dict.setlist(name, [v for v in query_dict.getlist(name) if v != value])
    return "?" + query_dict.urlencode()
