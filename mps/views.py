from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from forms import SearchForm

from haystack.query import SearchQuerySet
from haystack.views import search_view_factory
import haystack.forms

from django.contrib.auth.models import Group

import os

from mps.settings import MEDIA_ROOT

from resources.models import Definition
from django.views.generic.base import TemplateView


def main(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            return search(request)

    else:
        form = SearchForm(initial={'app': 'Global'})

    c = RequestContext(request)

    c.update({
        'form': form,
    })

    return render_to_response('index.html', c)


def loggedin(request):
    c = RequestContext(request)
    c.update({'full_name': request.user.username})
    return render_to_response('loggedin.html', c)


def search(request):
    app = request.POST.get('app', '')
    search_term = request.POST.get('search_term', '')

    bioactivities = {
        'compound': request.POST.get('compound', ''),
        'target': request.POST.get('target', ''),
        'name': request.POST.get('name', ''),
        'pubchem': request.POST.get('pubchem', ''),
        'exclude_targetless': request.POST.get('exclude_targetless', ''),
        'exclude_organismless': request.POST.get('exclude_organismless', ''),
        'exclude_questionable': request.POST.get('exclude_questionable', ''),
    }

    # If there is not a specified app, just return to the home page
    if not app:
        return HttpResponseRedirect('/')

    if app == 'Global':
        return HttpResponseRedirect('/search?q={}'.format(search_term))

    elif app == 'Bioactivities':
        search_term = [(term + '=' + bioactivities.get(term)) for term in bioactivities if bioactivities.get(term)]
        search_term = '&'.join(search_term)
        return HttpResponseRedirect('/bioactivities/?{}'.format(search_term))

    # If, for whatever reason, invalid data is entered, just return to the home page
    else:
        return HttpResponseRedirect('/')

# class CustomSearch(SearchView):
#
#     results_per_page = 1000
#
#     def get_results(self):
#         """
#         NORMALLY Fetches the results via the form.
#         Returns an empty list if there's no query to search with.
#         """
#         if self.query:
#             return SearchQuerySet().autocomplete(text=self.query)
#         else:
#             return []
#
#     def extra_context(self):
#         spelling = self.results.spelling_suggestion(self.query)
#         return {'suggestion': spelling,}


# A generic use of the search_view_factory
def custom_search(request):
    # Filter on group: either get all with no group or those with a group the user has
    sqs = SearchQuerySet().exclude(group__in=Group.objects.all())

    if request.user.groups.all():
        sqs = sqs | SearchQuerySet().filter(group__in=request.user.groups.all())

    view = search_view_factory(
        template='search/search.html',
        searchqueryset=sqs,
        form_class=haystack.forms.ModelSearchForm,
        results_per_page=1000,
    )
    return view(request)


def mps_help(request):
    c = RequestContext(request)
    # Add version for templates
    c['version'] = len(os.listdir(MEDIA_ROOT + '/excel_templates/'))
    # Get glossary
    c['glossary'] = Definition.objects.exclude(definition='')

    return render_to_response('help.html', c)


# TODO Consider defining this in URLS or either bringing the rest here
class UnderConstruction(TemplateView):
    template_name = 'under_construction.html'
