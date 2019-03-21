# NOTE: Decided it was best to keep AJAX calls app-separated
import ujson as json
from django.http import HttpResponse, HttpResponseServerError
from .models import CellSubtype
import logging
logger = logging.getLogger(__name__)


def main(request):
    """Default to server error"""
    return HttpResponseServerError()


def get_cell_subtypes(request):
    """Acquires all available Cell Origins for the given cell type"""

    dropdown = '<option value="">---------</option>'

    cell_type = request.POST.get('cell_type', '')

    findings = CellSubtype.objects.filter(cell_type__isnull=True)

    if cell_type:
        findings = findings | CellSubtype.objects.filter(cell_type_id=cell_type)

    findings = findings.order_by('cell_type', 'cell_subtype')

    for finding in findings:
        # match value to the desired subject ID
        value = str(finding.id)
        dropdown += '<option value="' + value + '">' + str(finding) + '</option>'

    data = {}

    data.update({
        'dropdown': dropdown,
    })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")

switch = {
    'get_cell_subtypes': get_cell_subtypes,
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
