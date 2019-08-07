from django.shortcuts import render
from django.http import HttpResponseRedirect

#sck added
from django.utils import timezone
#from django.db.models.functions import (ExtractYear, ExtractMonth, ExtractDay)
from django.db.models import F, ExpressionWrapper, DateField, DateTimeField, Q
from datetime import date, timedelta
#from django.db.models.functions import Concat
from cellsamples.models import Organ
#from django.db.models import Count

from assays.models import AssayStudy, OrganModel, AssayMatrixItem
from .forms import SearchForm

from haystack.query import SearchQuerySet
from haystack.views import search_view_factory
import haystack.forms

from django.contrib.auth.models import Group

import os

from mps.settings import MEDIA_ROOT

from resources.models import Definition
from django.views.generic.base import TemplateView

from microdevices.models import MicrophysiologyCenter
from mps.templatetags.custom_filters import ADMIN_SUFFIX, VIEWER_SUFFIX
import html

# Spaghetti code
from assays.views import get_queryset_with_organ_model_map


def main(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            return search(request)

    else:
        form = SearchForm(initial={'app': 'Global'})

    context = {
        'form': form,
    }

    return render(request, 'index.html', context)


def loggedin(request):
    return render(request, 'loggedin.html')


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


def get_search_queryset_with_permissions(request):
    sqs = SearchQuerySet().exclude(permissions='==PERMISSION START==')

    groups_with_center = MicrophysiologyCenter.objects.all().values_list('groups', flat=True)
    groups_with_center_full = {group.name: True for group in Group.objects.filter(id__in=groups_with_center)}

    if request.user.groups.all().count():
        user_groups = {
            group.name.replace(ADMIN_SUFFIX, '').replace(VIEWER_SUFFIX, ''): True for group in request.user.groups.all()
            if group.name.replace(ADMIN_SUFFIX, '').replace(VIEWER_SUFFIX, '') in groups_with_center_full
        }

        for group in list(user_groups.keys()):
            sqs = sqs | SearchQuerySet().filter(permissions=group)

    return sqs


# A generic use of the search_view_factory
def custom_search(request):
    # Filter on group: either get all with no group or those with a group the user has
    request.GET = request.GET.copy()
    request.GET.update({
        # EXCEEDINGLY CRUDE
        'q': html.escape(
            request.GET.get('q', '')
        ).replace('&#x27;', '&#39;')
    })
    sqs = get_search_queryset_with_permissions(request)

    view = search_view_factory(
        template='search/search.html',
        searchqueryset=sqs,
        form_class=haystack.forms.ModelSearchForm,
        results_per_page=1000,
    )

    return view(request)


def mps_help(request):
    c = {
        ###'version': len(os.listdir(MEDIA_ROOT + '/excel_templates/')),
        'glossary': Definition.objects.exclude(definition='')
    }

    return render(request, 'help.html', c)


#added sck
def mps_about(request):
    number_of_days = 30
    a_months_ago = date.today() - timedelta(days=365) + timedelta(days=number_of_days)
    #cellsamples_organ.organ_name
    #microdevices_organmodel.name
    #microdevices_microphysiologycenter.name

    soon_released = AssayStudy.objects.filter(
        restricted=True,
        locked=False,
        signed_off_date__lt=a_months_ago
    ).exclude(
        group_id__in=[21, 47, 109]
    ).exclude(
        signed_off_date__isnull=True
    ).annotate(
        scheduled_release_date=ExpressionWrapper(
            F('signed_off_date') + timedelta(days=365.2425),
            output_field=DateTimeField()
        ),
    )

    get_queryset_with_organ_model_map(soon_released)

    all_organ_models = OrganModel.objects.exclude(
        name__in=['Demo-Organ']
    ).prefetch_related('organ', 'center')

    distinct_by_name_and_center = {}

    for organ_model in all_organ_models:
        distinct_by_name_and_center[
            (organ_model.organ.organ_name, organ_model.center.name)
        ] = distinct_by_name_and_center.setdefault(
            (organ_model.organ.organ_name, organ_model.center.name), 0
        ) + 1

    reduce_distinct_to_list = []

    for current_tuple, count in distinct_by_name_and_center.items():
        reduce_distinct_to_list.append([current_tuple[0], current_tuple[1], count])

    d = {
        'number_of_days': number_of_days,
        'about_studies': soon_released,

        #This way before added the model to the study table
        # 'about_studies': AssayStudy.objects.filter(
        #     restricted=True,
        #     locked=False,
        #     signed_off_date__lt=a_months_ago
        # ).exclude(
        #     group_id__in=[21, 47, 109]
        # ).exclude(
        #     signed_off_date__isnull=True
        # ).annotate(
        #     scheduled_release_date=ExpressionWrapper(
        #         F('signed_off_date') + timedelta(days=365.2425),
        #         output_field=DateTimeField()),
        #     ),

        'about_models_distinct': reduce_distinct_to_list,
        #This way if do not want the distinct and want the model names
        #'about_models': all_organ_models,
    }

    return render(request, 'about.html', d)


# TODO Consider defining this in URLS or either bringing the rest here
class UnderConstruction(TemplateView):
    template_name = 'under_construction.html'
