# NOTE: Decided it was best to keep AJAX calls app-separated
import ujson as json
from django.http import HttpResponse, HttpResponseServerError
import re

# from django.contrib.auth.models import Group
#
# from haystack.query import SearchQuerySet

import logging
logger = logging.getLogger(__name__)

# Kind of a weird import, probably should have a utils file or something
from .views import get_search_queryset_with_permissions
import html


def main(request):
    """Default to Server Error"""
    return HttpResponseServerError()


def fetch_global_search_suggestions(request):
    """Return global search suggestions in JSON

    Receives the following from POST:
    text - The text the user has entered thus far into the search bar
    """
    data = []

    # Pattern for removing non-alphanumeric
    regex_pattern = re.compile('[\W_]+', re.UNICODE)

    # Get text from request
    # Only takes alphanumeric at the moment
    text = regex_pattern.sub(' ', request.POST.get('text', ''))

    # Filter on group: either get all with no group or those with a group the user has
    sqs = get_search_queryset_with_permissions(request)

    suggestions = sqs.autocomplete(text=text)
    # At the moment, I just take the first ten results
    for suggestion in suggestions[:10]:
        # data.append(suggestion.suggestion)
        data.append({
            'label': html.unescape(suggestion.text.split('\n')[0]),
            'value': html.unescape(suggestion.text.split('\n')[1])
        })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")

switch = {
    'fetch_global_search_suggestions': fetch_global_search_suggestions,
}


def ajax(request):
    """Switch to correct function given POST call

    Receives the following from POST:
    call -- What function to redirect to
    """
    post_call = request.POST.get('call', '')

    if not post_call:
        logger.error('post_call not present in request to ajax')
        return HttpResponseServerError

    # Abort if there is no valid call sent to us from Javascript
    if not post_call:
        return main(request)

    # Route the request to the correct handler function
    # and pass request to the functions
    try:
        # select the function from the dictionary
        procedure = switch[post_call]

    # If all else fails, handle the error message
    except KeyError:
        return main(request)

    else:
        # execute the function
        return procedure(request)
