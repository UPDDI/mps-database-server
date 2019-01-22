# coding=utf-8

from django.http import HttpResponse, HttpResponseServerError
from .models import CompoundAdverseEvent, OpenFDACompound, AdverseEvent
import ujson as json
# TODO TODO TODO REVISE IN PYTHON 3
import cgi


def main(request):
    """Default to Server Error"""
    return HttpResponseServerError()


def fetch_adverse_events_data(request):
    ae_data = list(CompoundAdverseEvent.objects.prefetch_related(
        'compound__compound',
        'event__organ'
    ).all().values(
        'compound_id',
        'compound__compound__name',
        'compound__compound_id',
        # Probably should be, you know, NAME
        'event__event',
        'frequency',
        'compound__estimated_usage',
        # WHY ISN'T THIS JUST NAME??
        'event__organ__organ_name',
        # Add logp
        'compound__compound__logp',
        'compound__compound__alogp',
        'compound__black_box',
        # SUBJECT TO CHANGE
        'compound__compound__tctc',
        'compound__compound__mps',
        'compound__compound__epa'
    ))

    data = []

    # A serializer would probably better serve us here...
    for ae in ae_data:
        project = u''

        if ae.get('compound__compound__tctc'):
            project += u'TCTC'

        if ae.get('compound__compound__epa'):
            project += u'EPA'

        if ae.get('compound__compound__mps'):
            project += u'MPS'

        if not project:
            project = u'Unassigned'

        organ_name = u''

        if ae.get('event__organ__organ_name'):
            organ_name = ae.get('event__organ__organ_name')

        black_box_warning = False

        if ae.get('compound__black_box'):
            black_box_warning = True

        normalized_reports = u''
        estimated_usage = u''

        if ae.get('compound__estimated_usage'):
            normalized_reports = u'{:,.2f}'.format(
                float(ae.get('frequency')) / ae.get('compound__estimated_usage') * 10000
            )
            estimated_usage = u'{:,}'.format(ae.get('compound__estimated_usage'))

        data.append(
            {
                'view': ae.get('compound_id'),
                'compound': {
                    'id': ae.get('compound__compound_id'),
                    'name': cgi.escape(ae.get('compound__compound__name'))
                },
                'event': {
                    'lower': cgi.escape(ae.get('event__event').lower()),
                    'name': cgi.escape(ae.get('event__event'))
                },
                'number_of_reports': u'{:,}'.format(
                    ae.get('frequency')
                ),
                'normalized_reports': normalized_reports,
                'estimated_usage': estimated_usage,
                'organ': organ_name,
                'black_box_warning': black_box_warning,
                'project': project,
                'logp': ae.get('compound__compound__logp'),
                'alogp': ae.get('compound__compound__alogp')
            }
        )

    all_data = {
        'data': data
    }

    return HttpResponse(
        json.dumps(all_data),
        content_type="application/json"
    )


def fetch_aggregate_ae_by_compound(request):
    compounds = OpenFDACompound.objects.all().prefetch_related(
        'compound'
    )

    compound_frequency = {}
    ae_to_compound = {}

    for adverse_event in CompoundAdverseEvent.objects.all().prefetch_related('event', 'compound__compound'):
        compound_frequency.setdefault(adverse_event.compound_id, []).append(adverse_event.frequency)
        ae_to_compound.setdefault(adverse_event.event.event, {}).update({
            adverse_event.compound.compound.name: True
        })

    data = []

    for compound in compounds:
        estimated_usage = u''

        if compound.estimated_usage:
            estimated_usage = u'{:,}'.format(compound.estimated_usage)

        checkbox = u'<input class="checkbox big-checkbox compound" type="checkbox" value="{}">'.format(compound.compound.name)

        data.append({
            # 'checkbox': cgi.escape(compound.compound.name),
            'checkbox': cgi.escape(checkbox),
            'compound': compound.compound.name,
            'estimated_usage': estimated_usage,
            'frequency': u'{:,}'.format(sum(compound_frequency.get(compound.id, [0])))
        })

    all_data = {
        'data': data,
        'ae_to_compound': ae_to_compound
    }

    return HttpResponse(
        json.dumps(all_data),
        content_type="application/json"
    )


def fetch_aggregate_ae_by_event(request):
    adverse_events = AdverseEvent.objects.all().prefetch_related(
        'organ'
    )

    adverse_event_frequency = {}

    for adverse_event in CompoundAdverseEvent.objects.all():
        adverse_event_frequency.setdefault(adverse_event.event_id, []).append(adverse_event.frequency)

    data = []

    for adverse_event in adverse_events:
        frequency = sum(adverse_event_frequency.get(adverse_event.id, [0]))
        organ_name = u''

        if adverse_event.organ:
            organ_name = adverse_event.organ.organ_name

        checkbox = u'<input class="checkbox big-checkbox adverse-event" type="checkbox" value="{}">'.format(adverse_event.event)

        if frequency:
            data.append({
                # 'checkbox': cgi.escape(adverse_event.event),
                'checkbox': cgi.escape(checkbox),
                'event': adverse_event.event,
                'organ': organ_name,
                'frequency': u'{:,}'.format(frequency)
            })

    all_data = {
        'data': data
    }

    return HttpResponse(
        json.dumps(all_data),
        content_type="application/json"
    )

switch = {
    'fetch_adverse_events_data': fetch_adverse_events_data,
    'fetch_aggregate_ae_by_event': fetch_aggregate_ae_by_event,
    'fetch_aggregate_ae_by_compound': fetch_aggregate_ae_by_compound
}


# Should probably consolidate these (DRY)
def ajax(request):
    """Switch to correct function given POST call

    Receives the following from POST:
    call -- What function to redirect to
    """
    post_call = request.POST.get('call', '')

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
