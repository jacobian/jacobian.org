import dateutil.parser
from django import template

library = template.Library()

@library.filter
def to_date(value):
    return dateutil.parser.parse(value)

