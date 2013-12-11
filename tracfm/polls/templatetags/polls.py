from django import template
import re
from datetime import datetime
from urllib import quote

register = template.Library()

"""
Simple tag let us define a regex for the active navigation tab
"""
@register.simple_tag(takes_context=True)
def url_exclude(context, exclude_poll=None, exclude_filter=None, exclude_sort=False):

    url = "?"
    if not exclude_sort and 'sort' in context:
        sort = context['sort']
        if not exclude_poll or get_poll_from_column(sort) != exclude_poll.id:
            url = "%s&sort=%s" % (url, quote(sort))

    if 'filter' in context:
        filters = context['filters']
        for filter in filters:

            # we are excluding the poll
            if exclude_poll and get_poll_from_filter(filter) == exclude_poll.id:
                continue

            # we are excluding by the filter
            if exclude_filter and filter.startswith(exclude_filter):
                continue

            url = "%s&filter=%s" % (url, quote(filter))

    if 'polls' in context:
        polls = context['polls']
        for poll in polls:
            if not exclude_poll or poll.id != exclude_poll.id:
                url = "%s&poll=%d" % (url, poll.id)


    return url

def get_poll_from_filter(filter):
    regex = "poll(\d+)_cat(\d+):(.*)"
    match = re.match(regex, filter, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def get_poll_from_column(column):
    regex = "-?poll(\d+)_cat(\d+)"
    match = re.match(regex, column, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None