from django.shortcuts import render
from django.http import HttpResponseRedirect

#sck added
from django.db.models import F, ExpressionWrapper, DateField, DateTimeField, Q, CharField, Value
from datetime import datetime, timedelta
import pytz
#from django.db.models.functions import Concat
from cellsamples.models import Organ
#from django.db.models import Count

from assays.models import AssayStudy, OrganModel, AssayMatrixItem, AssayStudyStakeholder
from .forms import SearchForm

from haystack.query import SearchQuerySet
from haystack.views import search_view_factory
import haystack.forms

from django.contrib.auth.models import Group

import os

from mps.settings import MEDIA_ROOT

from resources.models import Definition, ComingSoonEntry, WhatIsNewEntry, FeatureSourceXref
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

    # DO NOT BOTHER WITH WHAT IS NEW ON THE INDEX PAGE FOR NOW
    # about_six_months_ago = datetime.now().replace(tzinfo=pytz.UTC) - timedelta(days=180)

    context = {
        'form': form,
        # REMOVED FOR NOW
        # 'what_is_new': WhatIsNewEntry.objects.filter(
        #     modified_on__gt=about_six_months_ago
        # ).order_by(
        #     'modified_on'
        # )
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
    glossary = Definition.objects.exclude(definition='')

    xref = FeatureSourceXref.objects.all(
    ).order_by(
        'database_feature', 'data_source'
    ).prefetch_related(
        'data_source',
    )

    feature_source = {}
    list_of_sources = []
    f = ''
    i = 0

    # make a list of the data sources associated with each feature using the xref table
    # store in a dictionary of feature and list of data sources
    for each in xref:
        sn = str(each.data_source.help_order)

        # print('each.database_feature: ',each.database_feature)
        # print('sn: ', sn)

        # HANDY - get each field name in a queryset
        # for field in each._meta.get_fields():
        #     print(field)

        if i > 0 and i+1 < len(xref) and f == each.database_feature:
            # print('not first, not last, same feature')
            # write this data source to the list of data sources for this feature
            list_of_sources.append(sn)
        elif i > 0 and i+1 < len(xref) and f != each.database_feature:
            # print('not first, not last, feature changed')
            # write the previous feature and the list so far to the dictionary
            feature_source[f] = list_of_sources
            # reset the list to the current source
            list_of_sources = [sn]
        elif i > 0 and i + 1 == len(xref) and f == each.database_feature:
            # print('not first, IS last, same feature')
            # write this data source to the list of data sources for this feature
            list_of_sources.append(sn)
            # write the previous/this feature and the list so far to the dictionary
            feature_source[f] = list_of_sources
            list_of_sources = []
        elif i > 0 and i + 1 == len(xref) and f != each.database_feature:
            # print('not first, IS last, feature changed (last one is a different feature)')
            # write the previous feature and the list so far to the dictionary
            feature_source[f] = list_of_sources
            # write this data source to the list of data sources
            list_of_sources = [sn]
            # write the list (of one) to the dictionary of features
            feature_source[each.database_feature] = list_of_sources
        elif i == 0 and i+1 < len(xref):
            # print('the first, not last')
            # write this data source to the list of data sources for this feature
            list_of_sources.append(sn)
        else:
            # print('the first and only')
            # write this data source to the list of data sources
            list_of_sources = [sn]
            # write the list (of one) to the dictionary of features
            feature_source[each.database_feature] = list_of_sources
            list_of_sources = []

        # print('list_of_sources: ',list_of_sources)

        f = each.database_feature
        i = i + 1

    # print('feature_source: ', feature_source)

    # get a subset of the features for the feature table
    feature = glossary.filter(help_category='feature').order_by('help_order')

    # add a field to the feature queryset that has the list (stringified) of the data source(s) for each feature
    # HANDY - add field to queryset add a field to a queryset
    for each in feature:
        # print('---each.reference ', each.reference)
        # print('each.help_reference ', each.help_reference)

        this_feature = each
        this_list = feature_source.get(this_feature)
        try:
            this_list_string = ', '.join(map(str, this_list))
        except:
            this_list_string = ''
        each.source_list = this_list_string

    # for each in feature:
    #     print('each.source_list: ', each.source_list)

    # get other subsets for other tables on the help page
    source = glossary.filter(help_category='source').order_by('help_order')
    component_assay = glossary.filter(help_category='component-assay').order_by('help_order')
    component_model = glossary.filter(help_category='component-model').order_by('help_order')
    component_compound = glossary.filter(help_category='component-compound').order_by('help_order')
    component_cell = glossary.filter(help_category='component-cell').order_by('help_order')

    # limit the glossary to only those selected for display
    glossary = glossary.filter(glossary_display=True)

    data = {
        # 'version': len(os.listdir(MEDIA_ROOT + '/excel_templates/')),
        'glossary': glossary,
        'source': source,
        'feature': feature,
        'component_assay': component_assay,
        'component_model': component_model,
        'component_compound': component_compound,
        'component_cell': component_cell,
    }

    return render(request, 'help.html', data)


#added sck
# TODO NOT DRY
def mps_about(request):
    number_of_days = 120

    # Needed to make minimum timezone aware
    minimum_datetime = datetime.min.replace(tzinfo=pytz.UTC)
    datetime_now = datetime.now().replace(tzinfo=pytz.UTC)

    signed_off_restricted_studies = AssayStudy.objects.filter(
        restricted=True,
        # PLEASE NOTE: Locking a study will prevent this script from interacting with it
        locked=False
    ).exclude(
        signed_off_date__isnull=True
    ).exclude(
        signed_off_by_id=None
    )

    # Indicates whether there are required stakeholders that have not approved
    required_stakeholder_map = {}

    relevant_required_stakeholders_without_approval = AssayStudyStakeholder.objects.filter(
        sign_off_required=True,
        signed_off_by_id=None,
        study__id__in=signed_off_restricted_studies
    )

    for stakeholder in relevant_required_stakeholders_without_approval:
        required_stakeholder_map.update({
            stakeholder.study_id: True
        })

    # Contains as a datetime the lastest approval for a study
    latest_approval = {}

    approved_stakeholders = AssayStudyStakeholder.objects.filter(
        sign_off_required=True,
        study__id__in=signed_off_restricted_studies
    ).exclude(
        signed_off_date__isnull=True
    ).exclude(
        signed_off_by_id=None
    )

    for stakeholder in approved_stakeholders:
        # Compare to minimum if no date at the moment
        if stakeholder.signed_off_date > latest_approval.get(stakeholder.study_id, minimum_datetime):
            latest_approval.update({
                stakeholder.study_id: stakeholder.signed_off_date
            })

    soon_released = {}

    for study in signed_off_restricted_studies:
        # If there are no stakeholders, just use the sign off date
        if study.id not in latest_approval:
            # Days are approximated for a year
            scheduled_release_date = study.signed_off_date + timedelta(days=365.2425)
        else:
            # Days are approximated for a year
            scheduled_release_date = latest_approval.get(study.id) + timedelta(days=365.2425)

        stakeholders_without_approval = required_stakeholder_map.get(study.id, False)

        if not stakeholders_without_approval and scheduled_release_date <= datetime_now + timedelta(days=number_of_days):
            soon_released.update({
                study.id: scheduled_release_date
            })

    signed_off_restricted_studies = signed_off_restricted_studies.filter(id__in=soon_released.keys())

    get_queryset_with_organ_model_map(signed_off_restricted_studies)

    for study in signed_off_restricted_studies:
        study.scheduled_release_date = soon_released.get(study.id)

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

    # Get 25 studies that are public with the latest sign off
    recently_released_studies = AssayStudy.objects.filter(
        restricted=False
    ).exclude(
        signed_off_date__isnull=True
    ).order_by(
        '-modified_by',
        '-signed_off_date'
    )[:25]

    for study in recently_released_studies:
        study.released_on = study.signed_off_date + timedelta(days=365.2425)

    full_context = {
        'number_of_days': number_of_days,
        'about_studies': signed_off_restricted_studies,
        'about_models_distinct': reduce_distinct_to_list,
        'recently_released_studies': recently_released_studies,
        'coming_soon_entries': ComingSoonEntry.objects.all().order_by('-modified_on'),
        'what_is_new_entries': WhatIsNewEntry.objects.all().order_by('-modified_on')
    }

    return render(request, 'about.html', full_context)


# TODO Consider defining this in URLS or either bringing the rest here
class UnderConstruction(TemplateView):
    template_name = 'under_construction.html'
