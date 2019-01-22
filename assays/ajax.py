# coding=utf-8
import ujson as json
# from collections import defaultdict
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseServerError
)
from .models import (
    AssayStudy,
    AssayMatrixItem,
    AssayMatrix,
    AssayStudyAssay,
    AssayDataPoint,
    AssayChipReadout,
    AssayChipSetup,
    AssayRun,
    AssayChipReadoutAssay,
    AssayPlateReadoutAssay,
    AssaySetupCompound,
    DEFAULT_SETUP_CRITERIA,
    DEFAULT_SETTING_CRITERIA,
    DEFAULT_COMPOUND_CRITERIA,
    DEFAULT_CELL_CRITERIA,
    attr_getter,
    tuple_attrgetter,
    get_split_times,
)
from microdevices.models import (
    MicrophysiologyCenter,
    Microdevice,
    OrganModel,
    OrganModelProtocol
)

# from mps.settings import TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX
from .forms import (
    AssayStudyDataUploadForm,
    ReadyForSignOffForm
)

from .utils import (
    UnicodeWriter,
    # REPLACED_DATA_POINT_CODE,
    # MATRIX_ITEM_PREFETCH,
    DEFAULT_EXPORT_HEADER,
    get_repro_data,
    get_user_accessible_studies,
    get_inter_study_reproducibility_report,
    # GLOBAL STRINGS
    NO_COMPOUNDS_STRING,
    # NO_CELLS_STRING,
    # NO_SETTINGS_STRING,
    intra_status_for_inter,
)

from StringIO import StringIO
from django.shortcuts import get_object_or_404
from mps.templatetags.custom_filters import ADMIN_SUFFIX, is_group_editor

from django.contrib.auth.models import User
from mps.settings import DEFAULT_FROM_EMAIL

from django.template.loader import render_to_string

from mps.mixins import user_is_valid_study_viewer

# from django.utils import timezone

import numpy as np
from scipy.stats.mstats import gmean

import re

import logging
logger = logging.getLogger(__name__)

# Calling main is and always will be indicative of an error condition.
# ajax.py is strictly for AJAX requests

# Ajax requests are sent to ajax(request) and funneled into the correct
# handler function using a simulated Python switch routing function

# TODO OPTIMIZE DATABASE HITS
# Global variable for what to call control values (avoid magic strings)
CONTROL_LABEL = '-Control-'

# Variable to indicate that these should be split for special filters
COMBINED_VALUE_DELIMITER = '~@|'

# Note manipulations for sorting
# Somewhat contrived
# THESE SHOULD BE DEFINED, NOT LAMBDA FUNCTIONS
convert = lambda text: int(text) if text.isdigit() else text.lower()
alphanum_key = lambda key: [
    convert(
        c.replace('     ~@I1', '!').replace('     ~@I2', '"').replace('     ~@S', '"')
    ) for c in re.split('([0-9]+)', key)
]

alphanum_key_for_item_groups = lambda pair: re.split('([0-9]+)', pair[0])

# TODO REFACTOR Rather than passing the same thing over and over, we can make an object with attributes!
# def main(request):
#     """Default to server error"""
#     return HttpResponseServerError()


def fetch_center_id(request):
    """Returns center ID for dynamic run form

    Receives the following from POST:
    id -- the ID of the Microphysiology Center of interest
    """

    group = request.POST.get('id', '')

    if not group:
        logger.error('center not present in request to fetch_assay_info')
        return HttpResponseServerError()

    data = {}

    try:
        center_data = MicrophysiologyCenter.objects.filter(groups__id=group)[0]

        data.update({
            'center_id': center_data.center_id,
            'name': center_data.name,
        })
    # Evil exception
    except:
        data.update({
            'center_id': '',
            'name': '',
        })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


# Should these be refactored just to use fetch_dropdown instead?
def fetch_organ_models(request):
    """Gets a dropdown of organ models for Chip Setup

    Receives the following from POST:
    device -- the device to acquire organ models from
    """
    dropdown = [{'value': "", 'text': '---------'}]

    device = request.POST.get('device', '')

    findings = OrganModel.objects.filter(device_id=device).prefetch_related('device')

    for finding in findings:
        # match value to the desired subject ID
        value = str(finding.id)
        dropdown.append({'value': value, 'text': unicode(finding)})

    data = {}

    data.update({
        'dropdown': dropdown,
    })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def fetch_protocols(request):
    """Gets a dropdown of protocols for Chip Setup

    Receives the following from POST:
    organ_model -- the organ model to acquire protocols from
    """
    dropdown = [{'value': "", 'text': '---------'}]

    organ_model = request.POST.get('organ_model', '')

    # Order should be from newest to oldest
    findings = OrganModelProtocol.objects.filter(
        organ_model_id=organ_model
    ).prefetch_related(
        'organ_model'
    ).order_by('-version')

    # We no longer default to the first protocol to prevent unexpected behavior
    # Add the protocols
    for finding in findings:
        # match value to the desired subject ID
        value = str(finding.id)
        dropdown.append({'value': value, 'text': unicode(finding)})

    data = {}

    data.update({
        'dropdown': dropdown,
    })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def fetch_protocol(request):
    """Get the file location for a given protocol

    Receives the following from POST:
    protocol -- the ID of the protocol of interest
    """
    data = {}

    protocol_id = request.POST.get('protocol', '')

    protocol = OrganModelProtocol.objects.filter(pk=protocol_id)

    if protocol and protocol[0].organ_model.center and any(i in protocol[0].organ_model.center.groups.all() for i in request.user.groups.all()):
        protocol_file = protocol[0].file
        file_name = '/'.join(protocol_file.name.split('/')[1:])
        href = '/media/' + protocol_file.name
        data.update({
            'file_name': file_name,
            'href': href
        })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def fetch_dropdown(request):
    """Acquires options for whittling down number of dropdown

    Receives the following from POST:
    master -- master is what determines the subject's drop down choices
    subject -- subject is the model of interest as selected from the above dictionary
    next_model -- the next model to filter (if the subject is two FK away)
    next_filter -- second filter (if the subject is two FK away)
    """

    dropdown = '<option value="">---------</option>'

    # the model who's dropdown you want to whittle down
    all_models = {
        'AssayChipReadout': AssayChipReadout,
        'AssayChipSetup': AssayChipSetup,
        'AssayRun': AssayRun,
        'AssayChipReadoutAssay': AssayChipReadoutAssay,
        'AssayPlateReadoutAssay': AssayPlateReadoutAssay
    }

    # master is what determines the subject's drop down choices
    # master itself is a string for the filter that comes later
    master = request.POST.get('master', '')
    master_id = request.POST.get('master_id', '')

    # subject is the model of interest as selected from the above dictionary
    subject = all_models.get(request.POST.get('subject', ''))

    # filter is for additional filtering (for instance, if a subject is two FK away
    next_model = request.POST.get('next_model', '')
    next_filter = request.POST.get('next_filter', '')

    findings = subject.objects.filter(**{master: master_id})

    if next_model and next_filter:
        next_model = all_models.get(next_model)
        original = list(findings)
        findings = []

        for item in original:
            findings.extend(next_model.objects.filter(**{next_filter: item}))

    for finding in findings:
        # match value to the desired subject ID
        value = str(finding.id)
        dropdown += u'<option value="' + value + '">' + unicode(finding) + u'</option>'

    data = {}

    data.update({
        'dropdown': dropdown,
    })

    return HttpResponse(json.dumps(data),
                        content_type='application/json')


def fetch_device_dimensions(request):
    device_id = request.POST.get('device_id', None)

    data = {
        'number_of_rows': 1,
        'number_of_columns': 1
    }

    device = Microdevice.objects.filter(id=device_id)

    if device:
        device = device[0]
        data.update({
            'number_of_rows': device.number_of_rows,
            'number_of_columns': device.number_of_columns
        })

    return HttpResponse(json.dumps(data), content_type='application/json')


def send_ready_for_sign_off_email(request):
    data = {}

    if not AssayStudy.objects.filter(pk=int(request.POST.get('study', '')), signed_off_by=None):
        return HttpResponse(json.dumps({'errors': 'This study cannot be signed off on.'}),
                            content_type='application/json')

    study = get_object_or_404(AssayStudy, pk=int(request.POST.get('study', '')))

    message = request.POST.get('message', '').strip()[:2000]

    if not is_group_editor(request.user, study.group.name):
        return HttpResponse(json.dumps({'errors': 'You do not have permission to do this.'}), content_type='application/json')

    email_form = ReadyForSignOffForm(request.POST)

    if email_form.is_valid():
        required_group_name = study.group.name + ADMIN_SUFFIX
        users_to_be_alerted = User.objects.filter(groups__name=required_group_name, is_active=True)

        if users_to_be_alerted:
            # Magic strings are in poor taste, should use a template instead
            # I would use a template, but it gets picky about newlines (which as often added automatically)
            # I could strip the newlines, but alternatively I might as well just have it here
            subject = 'Sign Off Requested for {0}'.format(unicode(study))

            for user in users_to_be_alerted:
                content = render_to_string(
                    'assays/email/request_for_sign_off.txt',
                    {
                        'study': study,
                        'requester': request.user,
                        'user': user,
                        'message': message
                    }
                )

                # Actually send the email
                user.email_user(subject, content, DEFAULT_FROM_EMAIL)

                data.update({'message': message})
        else:
            data.update({
                'errors': 'No valid users were detected. You cannot send this email.'
            })
    else:
        data.update({
            'errors': 'The form was invalid.'
        })

    return HttpResponse(json.dumps(data), content_type='application/json')


# TODO TODO TODO
# This is a rather ugly function, naive
def get_data_as_list_of_lists(ids, data_points=None, both_assay_names=False, include_header=False, include_all=False):
    if not data_points:
        # TODO ORDER SUBJECT TO CHANGE
        data_points = AssayDataPoint.objects.prefetch_related(
            'study__group__microphysiologycenter_set',
            'matrix_item__assaysetupsetting_set__setting',
            'matrix_item__assaysetupcell_set__cell_sample',
            'matrix_item__assaysetupcell_set__density_unit',
            'matrix_item__assaysetupcell_set__cell_sample__cell_type__organ',
            'matrix_item__assaysetupcompound_set__compound_instance__compound',
            'matrix_item__assaysetupcompound_set__concentration_unit',
            'matrix_item__device',
            'matrix_item__organ_model',
            'matrix_item__matrix',
            'study_assay__target',
            'study_assay__method',
            'study_assay__unit',
            'sample_location',
            # 'data_file_upload',
            # Will use eventually, maybe
            'subtarget'
        ).filter(
            matrix_item_id__in=ids,
            replaced=False
        ).order_by(
            'matrix_item__name',
            'study_assay__target__name',
            'study_assay__method__name',
            'time',
            'sample_location__name',
            'excluded',
            'update_number'
        )

        # TODO OLD
        # related_compounds_map = get_related_compounds_map(readouts=ids)

    data = []

    if include_header:
        data.append(
            DEFAULT_EXPORT_HEADER
        )

    for data_point in data_points:
        # Definitely need to rename these fields/models...
        study_id = unicode(data_point.study)

        item_name = data_point.matrix_item.name

        matrix_name = data_point.matrix_item.matrix.name

        cross_reference = data_point.cross_reference

        assay_plate_id = data_point.assay_plate_id
        assay_well_id = data_point.assay_well_id

        # Add time here
        time_in_minutes = data_point.time
        times = get_split_times(time_in_minutes)

        target = data_point.study_assay.target.name
        method = data_point.study_assay.method.name
        sample_location = data_point.sample_location.name

        subtarget = data_point.subtarget.name

        device = data_point.matrix_item.device.name

        if data_point.matrix_item.organ_model:
            organ_model = data_point.matrix_item.organ_model.name
        else:
            organ_model = '-No MPS Model-'

        value = data_point.value

        if value is None:
            value = ''

        value_unit = data_point.study_assay.unit.unit

        replaced = data_point.replaced
        excluded = data_point.excluded

        if excluded:
            excluded = 'EXCLUDED'
        else:
            excluded = ''

        caution_flag = data_point.caution_flag
        replicate = data_point.replicate
        # TODO ADD OTHER STUFF
        notes = data_point.notes

        # Sets of data
        settings = data_point.matrix_item.stringify_settings()
        cells = data_point.matrix_item.stringify_cells()
        compounds = data_point.matrix_item.stringify_compounds()

        if not replaced and (include_all or not excluded):
            data.append(
                [
                    study_id,
                    item_name,
                    matrix_name,
                    cross_reference,
                    assay_plate_id,
                    assay_well_id,
                    times.get('day'),
                    times.get('hour'),
                    times.get('minute'),
                    device,
                    organ_model,
                    settings,
                    cells,
                    compounds,
                    target,
                    subtarget,
                    method,
                    sample_location,
                    value,
                    value_unit,
                    replicate,
                    caution_flag,
                    excluded,
                    notes
                ]
            )

    return data


def get_data_as_csv(ids, data_points=None, both_assay_names=False, include_header=False, include_all=False):
    """Returns data points as a csv in the form of a string"""
    data = get_data_as_list_of_lists(
        ids,
        data_points,
        both_assay_names,
        include_header,
        include_all
    )

    for index in range(len(data)):
        current_list = list(data[index])
        data[index] = [unicode(item) for item in current_list]

    string_io = StringIO()
    csv_writer = UnicodeWriter(string_io)
    for one_line_of_data in data:
        csv_writer.writerow(one_line_of_data)

    return string_io.getvalue()


# TODO TODO TODO
def get_data_as_json(ids, data_points=None):
    if not data_points:
        data_points = AssayDataPoint.objects.prefetch_related(
            'matrix_item',
            'study_assay__target',
            'study_assay__method',
            'study_assay__unit',
            'sample_location',
            'data_file_upload',
            # Will use eventually
            'subtarget'
        ).filter(
            matrix_item_id__in=ids,
            # Just remove replaced datapoints initially
            replaced=False
        ).order_by(
            # TODO
            'matrix_item__name',
            'study_assay__target__name',
            'study_assay__method__name',
            'time',
            'sample_location__name',
            'excluded',
            'update_number'
        )

    data = {}

    data_points_to_return = []
    sample_locations = {}
    study_assays = {}

    for data_point in data_points:
        name = data_point.matrix_item.name
        assay_plate_id = data_point.assay_plate_id
        assay_well_id = data_point.assay_well_id
        # Add time here
        time_in_minutes = data_point.time
        times = get_split_times(time_in_minutes)
        study_assay = data_point.study_assay
        sample_location = data_point.sample_location

        value = data_point.value

        if value is None:
            value = ''

        caution_flag = data_point.caution_flag
        # quality = data_point.quality
        excluded = data_point.excluded
        # TODO ADD OTHER STUFF
        notes = data_point.notes

        update_number = data_point.update_number
        replicate = data_point.replicate

        data_file_upload = data_point.data_file_upload

        if data_file_upload:
            data_file_upload_name = unicode(data_file_upload)
            data_file_upload_url = data_file_upload.file_location

        else:
            data_file_upload_name = u''
            data_file_upload_url = u''

        if sample_location.id not in sample_locations:
            sample_locations.update(
                {
                    sample_location.id: {
                        'name': sample_location.name,
                        'description': sample_location.description
                    }
                }
            )

        if study_assay.id not in study_assays:
            study_assays.update(
                {
                    study_assay.id: {
                        'target_name': study_assay.target.name,
                        'target_short_name': study_assay.target.short_name,
                        'method_name': study_assay.method.name,
                        'unit': study_assay.unit.unit,
                    }
                }
            )

        data_point_fields = {
            'id': data_point.id,
            'name': name,
            'assay_plate_id': assay_plate_id,
            'assay_well_id': assay_well_id,
            'time_in_minutes': time_in_minutes,
            'day': times.get('day'),
            'hour': times.get('hour'),
            'minute': times.get('minute'),
            'study_assay_id': study_assay.id,
            'sample_location_id': sample_location.id,
            'value': value,
            'caution_flag': caution_flag,
            'excluded': excluded,
            # TODO ADD OTHER STUFF
            'notes': notes.strip(),
            'update_number': update_number,
            'replicate': replicate.strip(),
            'data_file_upload_url': data_file_upload_url,
            'data_file_upload_name': data_file_upload_name
        }
        data_points_to_return.append(data_point_fields)

    data.update({
        'data_points': data_points_to_return,
        'sample_locations': sample_locations,
        'study_assays': study_assays
    })

    return data


# TODO TODO TODO MAKE SURE THIS WORKS WITH NEW FILTERING
def get_control_data(
        study,
        mean_type,
        include_all,
        truncate_negative,
        new_data_for_control=None,
        normalize_units=False
):
    """Gets control data for performing percent control calculations

    study - the study in question
    mean_type - what sort of mean to use
    include_all - whether to include all values
    truncate_negative - whether to treat negative values as zeroes
    new_data_for_control - new data that wouldn't be found in the database
    """
    initial_control_data = {}
    controls = {}

    data_points = list(AssayDataPoint.objects.filter(
        study_id__in=study,
        replaced=False
    ).prefetch_related(
        'study',
        'study_assay__target',
        'study_assay__method',
        'study_assay__unit__base_unit',
        'matrix_item',
        'sample_location'
    ))

    if new_data_for_control:
        data_points.extend(new_data_for_control)

    # A little too much copy-pasting here, not very DRY
    for raw in data_points:
        value = raw.value

        # TODO CHANGE TO USE FOLLOWING
        study_assay = raw.study_assay
        target = study_assay.target.name
        unit = study_assay.unit.unit

        if normalize_units and study_assay.unit.base_unit:
            unit = study_assay.unit.base_unit.unit

        # Not currently used
        method = study_assay.method.name

        sample_location = raw.sample_location.name

        # chip_id = raw.assay_chip_id.chip_setup.assay_chip_id

        time = raw.time / 1440.0

        # replaced = raw.replaced
        excluded = raw.excluded

        # No dynamic quality here
        if value is not None and (include_all or not excluded):
            if truncate_negative and value < 0:
                value = 0

            # TODO CONTROL DEFINITIONS WILL BECOME MORE COMPLICATED LATER
            # Check if the setup is marked a control chip
            if raw.matrix_item.test_type == 'control':
                initial_control_data.setdefault(
                    target, {}
                ).setdefault(
                    unit, {}
                ).setdefault(
                    CONTROL_LABEL, {}
                ).setdefault(
                    sample_location, {}
                ).setdefault(
                    time, []
                ).append(
                    raw
                )

    for target, units in initial_control_data.items():
        for unit, tags in units.items():
            for tag, sample_locations in tags.items():
                for sample_location, time_values in sample_locations.items():
                    for time, points in time_values.items():
                        # TODO TODO TODO More than a little crude: PLEASE REVISE THESE NESTED LOOPS SO THAT THEY ARE MORE ROBUST
                        study_values = {}

                        for point in points:
                            if normalize_units:
                                study_values.setdefault(point.study_id, []).append(point.value * point.study_assay.unit.scale_factor)
                            else:
                                study_values.setdefault(point.study_id, []).append(point.value)

                        for study_id, values in study_values.items():
                            if len(values) > 1:
                                # If geometric mean
                                if mean_type == 'geometric':
                                    # Geometric mean will sometimes fail (due to zero values and so on)
                                    average = gmean(values)
                                    if np.isnan(average):
                                        return {
                                            'errors': 'Geometric mean could not be calculated (probably due to negative values), please use an arithmetic mean instead.'
                                        }
                                # If arithmetic mean
                                else:
                                    average = np.average(values)
                            else:
                                average = values[0]

                            controls.update(
                                    {(study_id, target, unit, sample_location, time): average}
                            )

    return controls


# TODO WE MAY WANT THE DEFINITION OF A TREATMENT GROUP TO CHANGE, WHO KNOWS
def get_item_groups(study, criteria, matrix_items=None):
    treatment_groups = {}
    setup_to_treatment_group = {}
    header_keys = []

    # By pulling the setups for the study, I avoid problems with preview data
    if matrix_items is None:
        matrix_items = AssayMatrixItem.objects.filter(
            study=study
        )

    setups = matrix_items.prefetch_related(
        'organ_model',
        'assaysetupsetting_set__setting',
        'assaysetupsetting_set__addition_location',
        'assaysetupsetting_set__unit',
        'assaysetupcell_set__cell_sample__cell_subtype',
        'assaysetupcell_set__cell_sample__cell_type__organ',
        'assaysetupcell_set__density_unit',
        'assaysetupcell_set__addition_location',
        'assaysetupcompound_set__compound_instance__compound',
        'assaysetupcompound_set__concentration_unit',
        'assaysetupcompound_set__addition_location',
    )

    if not criteria:
        criteria = {
            'setup': DEFAULT_SETUP_CRITERIA,
            'setting': DEFAULT_SETTING_CRITERIA,
            'compound': DEFAULT_COMPOUND_CRITERIA,
            'cell': DEFAULT_CELL_CRITERIA
        }

    # TODO TODO TODO REVISE THESE MAGIC KEYS
    if criteria.get('setup', ''):
        if 'organ_model_id' in criteria.get('setup'):
            header_keys.append('MPS Model')
        if 'study_id' in criteria.get('setup'):
            header_keys.append('Study')
    if criteria.get('cell', ''):
        header_keys.append('Cells')
    if criteria.get('compound', ''):
        header_keys.append('Compounds')
    if criteria.get('setting', ''):
        header_keys.append('Settings')

    header_keys.append('Items with Same Treatment')

    setup_attribute_getter = tuple_attrgetter(*criteria.get('setup', ['']))

    for setup in setups:
        treatment_group_tuple = ()

        if criteria.get('setup', ''):
            treatment_group_tuple = setup_attribute_getter(setup)

        if criteria.get('setting', ''):
            treatment_group_tuple += setup.devolved_settings(criteria.get('setting'))

        if criteria.get('compound', ''):
            treatment_group_tuple += setup.devolved_compounds(criteria.get('compound'))

        if criteria.get('cell', ''):
            treatment_group_tuple += setup.devolved_cells(criteria.get('cell'))

        current_representative = treatment_groups.setdefault(treatment_group_tuple, setup.quick_dic(criteria))

        current_representative.get('Items with Same Treatment').append(
            setup.get_hyperlinked_name()
        )
        current_representative.setdefault('names for items', []).append(
            setup.name
        )
        setup_to_treatment_group.update({setup.id: current_representative})

    # Attempt to sort reasonably
    # TODO SHOULD STUDY BE PLACED HERE?
    sorted_treatment_groups = sorted(
        treatment_groups.values(), key=lambda x: (
            x.get('Compounds'),
            x.get('MPS Model'),
            x.get('Cells'),
            x.get('Settings'),
            x.get('Items with Same Treatment')[0]
        )
    )

    for index, representative in enumerate(sorted_treatment_groups):
        items = representative.get('Items with Same Treatment')
        item_names = representative.get('names for items')
        sorted_items = [x for _, x in sorted(zip(item_names, items), key=alphanum_key_for_item_groups)]
        # representative.get('Items with Same Treatment').sort()
        representative.update({
            'Items with Same Treatment': sorted_items
        })
        representative.update({
            'Items with Same Treatment': ', '.join(representative.get('Items with Same Treatment')),
            'index': index
        })

    return (sorted_treatment_groups, setup_to_treatment_group, header_keys)


# TODO PROTOTYPE ONLY
# def get_paired_id_and_name(field):
#     return '\n'.join((field.name, unicode(field.id)))
#
#
# def get_data_for_heatmap(raw_data):
#     data = {
#         'matrices': {},
#         'values': {}
#     }
#
#     # Nesting like this is a serious violation of style
#     for raw in raw_data:
#         data.get('values').setdefault(
#             get_paired_id_and_name(raw.matrix_item.matrix), {}
#         ).setdefault(
#             get_paired_id_and_name(raw.study_assay.target), {}
#         ).setdefault(
#             get_paired_id_and_name(raw.study_assay.method), {}
#         ).setdefault(
#             # Dumb exception
#             '\n'.join((raw.study_assay.unit.unit, unicode(raw.study_assay.unit.id))), {}
#         ).setdefault(
#             get_paired_id_and_name(raw.sample_location), {}
#         ).setdefault(
#             get_paired_id_and_name(raw.subtarget), {}
#         ).setdefault(
#             '\n'.join((raw.get_time_string(), unicode(raw.time))), {}
#         ).setdefault(
#             '_'.join([unicode(raw.matrix_item.row_index), unicode(raw.matrix_item.column_index)]), []
#         ).append(raw.value)
#
#         data.get('matrices').setdefault(
#             get_paired_id_and_name(raw.matrix_item.matrix), [[''] * raw.matrix_item.matrix.number_of_columns for _ in range(raw.matrix_item.matrix.number_of_rows)]
#         )[raw.matrix_item.row_index][raw.matrix_item.column_index] = raw.matrix_item.name
#
#     return data


# TODO TODO TODO MAKE SURE STUDY NO LONGER REQUIRED
def get_data_points_for_charting(
        raw_data,
        key,
        mean_type,
        interval_type,
        percent_control,
        include_all,
        truncate_negative,
        dynamic_excluded,
        criteria=None,
        post_filter=None,
        study=None,
        matrix_item=None,
        matrix_items=None,
        new_data=False,
        additional_data=None,
        normalize_units=False
):
    """Get all readout data for a study and return it in JSON format

    From POST:
    raw_data - the AssayChipRawData needed to create the JSON
    related_compounds_map - dic of setup pointing to compounds
    key - whether this data should be considered by device or by compound
    interval_type - the type of interval (std, ste, etc)
    percent_control - whether to use percent control (WIP)
    include_all - whether to include all values
    dynamic_excluded - dic of data points to exclude
    study - supplied only if needed to get percent control values (validating data sets and so on)
    matrix_item - supplied only when data is for an individual matrix_item
    new_data - indicates whether data in raw_data is new
    additional_data - data to merge with raw_data (used when displaying individual readouts for convenience)
    """
    # Organization is assay -> unit -> compound/tag -> field -> time -> value
    treatment_group_representatives, setup_to_treatment_group, header_keys = get_item_groups(
        study,
        criteria,
        matrix_items
    )

    final_data = {
        'sorted_assays': [],
        'assays': [],
        'heatmap': {
            'matrices': {},
            'values': {}
        },
        'header_keys': header_keys
    }

    intermediate_data = {}

    initial_data = {}

    controls = {}
    if percent_control:
        new_data_for_control = None
        if new_data:
            new_data_for_control = raw_data

        controls = get_control_data(
            study,
            # key,
            mean_type,
            include_all,
            truncate_negative,
            new_data_for_control=new_data_for_control,
            normalize_units=normalize_units
        )

        if controls.get('errors' , ''):
            return controls

    averaged_data = {}

    all_keys = {}
    key_discrimination = {}
    use_key_discrimination = key == 'device'

    all_sample_locations = {}

    # Accommodation of "special" grouping
    group_sample_location = True
    group_method = True
    group_time = True

    # CRUDE
    if criteria:
        group_sample_location = 'sample_location' in criteria.get('special', [])
        group_method = 'method' in criteria.get('special', [])
        group_time = 'time' in criteria.get('special', [])

    # Append the additional_data as necessary
    # Why is this done? It is an expedient way to avoid duplicating data
    if additional_data:
        raw_data.extend(additional_data)

    # Don't bother with heatmaps at the moment
    # if not matrix_item:
    #     if not matrix_items:
    #         heatmap_matrices = AssayMatrix.objects.filter(
    #             study_id=study,
    #             representation='plate'
    #         )
    #     else:
    #         heatmap_matrices = AssayMatrix.objects.filter(
    #             assaymatrixitem__in=matrix_items,
    #             representation='plate'
    #         )
    #
    #     heatmap_data = raw_data.filter(matrix_item__matrix_id__in=heatmap_matrices)
    #
    #     final_data.update({
    #         'heatmap': get_data_for_heatmap(heatmap_data)
    #     })
    #
    #     if key == 'device':
    #         raw_data = raw_data.exclude(matrix_item__matrix_id__in=heatmap_matrices)

    assays_of_interest = AssayStudyAssay.objects.filter(study_id__in=study)

    target_method_pairs = {}

    if group_method:
        group_method = False

        for assay in assays_of_interest:
            if target_method_pairs.get(assay.target_id, assay.method_id) != assay.method_id:
                group_method = True
                break

            target_method_pairs.update({assay.target_id: assay.method_id})

    # Make sure the post_filter is at least a dic
    if post_filter is None:
        post_filter = {}

    # TODO NOTE THAT THIS MAKES ASSUMPTION ABOUT THE STATE OF THE POST FILTER
    # That is to say, you may want to be positive that the "combined" fields are split out
    matrix_item_compound_post_filters = {}

    post_filter_compounds = post_filter.get(
        'matrix_item', {}
    ).get('assaysetupcompound__compound_instance__compound_id__in', {})

    if post_filter:
        # WARNING THIS MAKES A NUMBER OF ASSUMPTIONS
        matrix_item_compound_post_filters = {
            '__'.join(current_filter.replace('assaysetupcompound__', '').split('__')[:-1]): [
                x for x in post_filter.get('matrix_item', {}).get(current_filter, [])
            ] for current_filter in post_filter.get('matrix_item', {}) if current_filter.startswith('assaysetupcompound__')
        }

    for raw in raw_data:
        # Now uses full name
        # assay = raw.assay_id.assay_id.assay_short_name
        # Deprecated
        # assay = raw.assay_id.assay_id.assay_name
        # unit = raw.assay_id.readout_unit.unit
        # Deprecated
        # field = raw.field_id
        value = raw.value

        study_assay = raw.study_assay
        target = study_assay.target.name
        unit = study_assay.unit.unit

        # Not currently used
        method = study_assay.method.name

        if group_method:
            target = u'{} [{}]'.format(target, method)

        sample_location = raw.sample_location.name

        matrix_item_id = raw.matrix_item_id
        matrix_item_name = raw.matrix_item.name

        matrix_id = raw.matrix_item.matrix_id
        matrix_name = raw.matrix_item.matrix.name

        # Convert to days for now
        time = raw.time / 1440.0
        raw_time = raw.time

        replaced = raw.replaced
        excluded = raw.excluded

        # TODO Should probably just use dynamic_excluded instead of quality for this
        if value is not None and not replaced and (include_all or not dynamic_excluded.get(unicode(raw.id), excluded)):
            if truncate_negative and value < 0:
                value = 0
            # Get tag for data point
            # If by compound
            if key == 'group':
                # tag = get_list_of_present_compounds(related_compounds_map, raw, ' & ')
                tag = u'Group {}'.format(setup_to_treatment_group.get(matrix_item_id).get('index') + 1)
            elif key == 'compound':
                tag = []

                is_control = True

                for compound in raw.matrix_item.assaysetupcompound_set.all():
                    # Makes sure the compound doesn't violate filters
                    # This is because a compound can be excluded even if its parent matrix item isn't!
                    valid_compound = True

                    for filter, values in matrix_item_compound_post_filters.items():
                        if unicode(attr_getter(compound, filter.split('__'))) not in values:
                            valid_compound = False
                            break

                    # TERRIBLE CONDITIONAL
                    if (valid_compound and
                        compound.addition_time <= raw_time and
                        compound.addition_time + compound.duration >= raw_time
                    ):
                        concentration = compound.concentration * compound.concentration_unit.scale_factor
                        tag.append(
                            # May need this to have float minutes, unsure
                            u'{} {} {}'.format(
                                compound.compound_instance.compound.name,
                                concentration,
                                compound.concentration_unit.base_unit,
                            )
                        )

                    is_control = False

                if tag:
                    tag = u' & '.join(tag)
                elif is_control and (post_filter is None or u'0' in post_filter_compounds):
                    tag = u'-No Compound-'
                else:
                    continue
            elif key == 'dose':
                tag = []
                concentration = 0

                is_control = True

                for compound in raw.matrix_item.assaysetupcompound_set.all():
                    # Makes sure the compound doesn't violate filters
                    # This is because a compound can be excluded even if its parent matrix item isn't!
                    valid_compound = True

                    for filter, values in matrix_item_compound_post_filters.items():
                        if unicode(attr_getter(compound, filter.split('__'))) not in values:
                            valid_compound = False
                            break

                    # TERRIBLE CONDITIONAL
                    if (valid_compound and
                        compound.addition_time <= raw_time and
                        compound.addition_time + compound.duration >= raw_time
                    ):
                        concentration += compound.concentration * compound.concentration_unit.scale_factor
                        tag.append(
                            # May need this to have float minutes, unsure
                            u'{} at D{}H{}M{}'.format(
                                compound.compound_instance.compound.name,
                                int(raw_time / 24 / 60),
                                int(raw_time / 60 % 24),
                                int(raw_time % 60)
                            )
                        )

                    is_control = False

                # CONTRIVED: Set time to concentration AND time
                time = (concentration, time)
                if tag:
                    tag = u' & '.join(tag)
                elif is_control and (post_filter is None or u'0' in post_filter_compounds):
                    tag = u'-No Compound- at D{}H{}M{}'.format(
                        int(raw_time / 24 / 60),
                        int(raw_time / 60 % 24),
                        int(raw_time % 60)
                    )
                else:
                    continue
            # If by device
            else:
                tag = (matrix_item_id, matrix_item_name)

                if all_keys.setdefault(matrix_item_name, matrix_item_id) != matrix_item_id:
                    key_discrimination.update({matrix_item_name: True})

            # Set data in nested monstrosity that is initial_data
            initial_data.setdefault(
                target, {}
            ).setdefault(
                unit, {}
            ).setdefault(
                tag, {}
            ).setdefault(
                sample_location, {}
            ).setdefault(
                time, []
            ).append(raw)

            # Update all_sample_locations
            all_sample_locations.update({sample_location: True})

    # Nesting like this is a little sloppy, flat > nested
    for target, units in initial_data.items():
        for unit, tags in units.items():
            for tag, sample_locations in tags.items():
                for sample_location, time_points in sample_locations.items():
                    for time, points in time_points.items():
                        # TODO TODO TODO More than a little crude: PLEASE REVISE THESE NESTED LOOPS SO THAT THEY ARE MORE ROBUST
                        study_values = {}

                        for point in points:
                            study_values.setdefault(point.study_id, []).append(point.value)

                        for study_id, values in study_values.items():
                            if len(values) > 1:
                                # If geometric mean
                                if mean_type == 'geometric':
                                    # Geometric mean will sometimes fail (due to zero values and so on)
                                    average = gmean(values)
                                    if np.isnan(average):
                                        return {'errors': 'Geometric mean could not be calculated (probably due to negative values), please use an arithmetic mean instead.'}
                                # If arithmetic mean
                                else:
                                    average = np.average(values)
                            else:
                                average = values[0]

                            # If standard deviation
                            if interval_type == 'std':
                                interval = np.std(values)
                            # Standard error if not std
                            else:
                                interval = np.std(values) / len(values) ** 0.5

                            average_interval_study_id = (
                                average,
                                interval,
                                study_id
                            )

                            averaged_data.setdefault(target, {}).setdefault(unit, {}).setdefault(tag, {}).setdefault(sample_location, {}).update({
                                time: average_interval_study_id
                            })

    accommodate_sample_location = group_sample_location and len(all_sample_locations) > 1

    for target, units in averaged_data.items():
        for unit, tags in units.items():
            # row_indices = {}
            accommodate_units = len(units) > 1

            if not percent_control:
                # Not converted to percent control
                # Newline is used as a delimiter
                assay_label = target + u'\n' + unit
            else:
                # Convert to percent control
                if accommodate_units:
                    current_unit = u'%Control from {}'.format(unit)
                else:
                    current_unit = u'%Control'
                # Newline is used as a delimiter
                assay_label = target + u'\n' + current_unit

            current_table = intermediate_data.setdefault(assay_label, [['Time']])
            # row_indices = {}
            current_data = {}
            x_header = []
            y_header = {}
            final_data.get('sorted_assays').append(assay_label)

            for tag, sample_locations in tags.items():
                # TODO: A little naive
                if use_key_discrimination and key_discrimination.get(tag[1], ''):
                    tag = u'{} || {}'.format(tag[1], tag[0])
                elif use_key_discrimination:
                    tag = tag[1]

                accommodate_intervals = False
                include_current = False

                for sample_location, time_values in sample_locations.items():
                    if accommodate_sample_location:
                        current_key = u'{} || {}'.format(tag, sample_location)
                        accommodate_intervals = False
                        include_current = False

                    else:
                        current_key = tag

                    # all_keys.update({current_key: True})

                    for time, value_interval_study_id in time_values.items():
                        value = value_interval_study_id[0]
                        interval = value_interval_study_id[1]
                        study_id = value_interval_study_id[2]

                        if interval != 0:
                            accommodate_intervals = True

                        # UGLY NOT DRY
                        # Contrived combination of time and concentration only for dose-response
                        if key == 'dose':
                            concentration = time[0]
                            time = time[1]

                            if not percent_control:
                                current_data.setdefault(current_key, {}).update({concentration: value})
                                current_data.setdefault(u'{}{}'.format(current_key,  '     ~@i1'), {}).update({concentration: value - interval})
                                current_data.setdefault(u'{}{}'.format(current_key, '     ~@i2'), {}).update({concentration: value + interval})
                                y_header.update({concentration: True})
                                include_current = True

                            elif controls.get((study_id, target, unit, sample_location, time), False):
                                control_value = controls.get((study_id, target, unit, sample_location, time))

                                # We can not divide by zero
                                if control_value == 0:
                                    return {
                                        'errors': 'Could not calculate percent control because some control values are zero (divide by zero error).'}

                                adjusted_value = (value / control_value) * 100
                                adjusted_interval = (interval / control_value) * 100

                                current_data.setdefault(current_key, {}).update({concentration: adjusted_value})
                                current_data.setdefault(u'{}{}'.format(current_key , '     ~@i1'), {}).update(
                                    {concentration: adjusted_value - adjusted_interval})
                                current_data.setdefault(u'{}{}'.format(current_key, '     ~@i2'), {}).update(
                                    {concentration: adjusted_value + adjusted_interval})
                                y_header.update({concentration: True})
                                include_current = True
                        else:
                            if not percent_control:
                                current_data.setdefault(current_key, {}).update({time: value})
                                current_data.setdefault(current_key+'     ~@i1', {}).update({time: value - interval})
                                current_data.setdefault(current_key+'     ~@i2', {}).update({time: value + interval})
                                y_header.update({time: True})
                                include_current = True

                            elif controls.get((study_id, target, unit, sample_location, time), False):
                                control_value = controls.get((study_id, target, unit, sample_location, time))

                                # We can not divide by zero
                                if control_value == 0:
                                    return {'errors': 'Could not calculate percent control because some control values are zero (divide by zero error).'}

                                adjusted_value = (value / control_value) * 100
                                adjusted_interval = (interval / control_value) * 100

                                current_data.setdefault(current_key, {}).update({time: adjusted_value})
                                current_data.setdefault(current_key+'     ~@i1', {}).update({time: adjusted_value - adjusted_interval})
                                current_data.setdefault(current_key+'     ~@i2', {}).update({time: adjusted_value + adjusted_interval})
                                y_header.update({time: True})
                                include_current = True

                    key_present = current_key in x_header

                    if include_current and not key_present:
                        x_header.append(current_key)
                    # To include all
                    # x_header.append(current_key)
                    # x_header.extend([
                    #     current_key + '     ~@i1',
                    #     current_key + '     ~@i2'
                    # ])

                    # Only include intervals if necessary
                    if accommodate_intervals and include_current and not key_present:
                        x_header.extend([
                            u'{}{}'.format(current_key, '     ~@i1'),
                            u'{}{}'.format(current_key, '     ~@i2')
                        ])
                    else:
                        if u'{}{}'.format(current_key, '     ~@i1') in current_data:
                            del current_data[u'{}{}'.format(current_key, '     ~@i1')]
                            del current_data[u'{}{}'.format(current_key, '     ~@i2')]

            # for current_key in all_keys:
            #     if current_key not in x_header:
            #         x_header.extend([
            #             current_key,
            #             current_key + '     ~@i1',
            #             current_key + '     ~@i2'
            #         ])

            x_header.sort(key=alphanum_key)
            current_table[0].extend(x_header)

            x_header = {x_header[index]: index + 1 for index in range(len(x_header))}

            y_header = y_header.keys()
            y_header.sort(key=float)

            for y in y_header:
                current_table.append([y] + [None] * (len(x_header)))

            y_header = {float(y_header[index]): index + 1 for index in range(len(y_header))}

            for x, data_point in current_data.items():
                for y, value in data_point.items():
                    current_table[y_header.get(y)][x_header.get(x)] = value

    final_data.get('sorted_assays').sort(key=lambda s: s.upper())
    final_data['assays'] = [[] for x in range(len(final_data.get('sorted_assays')))]

    for assay, assay_data in intermediate_data.items():
        final_data.get('assays')[final_data.get('sorted_assays').index(assay)] = assay_data

    final_data.update({
        'treatment_groups': treatment_group_representatives
    })

    return final_data


def fetch_data_points(request):
    pre_filter = {}

    post_filter = json.loads(request.POST.get('post_filter', '{}'))

    if request.POST.get('matrix_item', ''):
        matrix_items = AssayMatrixItem.objects.filter(pk=int(request.POST.get('matrix_item')))
        matrix_item = matrix_items[0]
        study = matrix_item.study
        pre_filter.update({
            'matrix_item_id__in': matrix_items
        })
    elif request.POST.get('matrix', ''):
        matrix_item = None
        matrix = AssayMatrix.objects.get(pk=int(request.POST.get('matrix', None)))
        matrix_items = AssayMatrixItem.objects.filter(matrix_id=int(request.POST.get('matrix')))
        study = matrix.study
        pre_filter.update({
            'matrix_item_id__in': matrix_items
        })
    elif request.POST.get('study', ''):
        matrix_item = None
        study = AssayStudy.objects.get(pk=int(request.POST.get('study', None)))
        matrix_items = AssayMatrixItem.objects.filter(study=study)
        pre_filter.update({
            'matrix_item_id__in': matrix_items
        })
    else:
        return HttpResponseServerError()

    data_points = AssayDataPoint.objects.filter(
        **pre_filter
    ).prefetch_related(
        #TODO
        'study_assay__target',
        'study_assay__method',
        'study_assay__unit',
        'sample_location',
        'matrix_item__matrix',
        'subtarget'
    )

    # Very odd, but expedient
    studies = AssayStudy.objects.filter(id=study.id)

    # A little contrived
    assays = AssayStudyAssay.objects.filter(
        study=study
    )

    # UGLY NOT DRY
    if not post_filter:
        assays = assays.prefetch_related(
            'target',
            'method'
        )

        post_filter = acquire_post_filter(studies, assays, matrix_items, data_points)
    else:
        studies, assays, matrix_items, data_points = apply_post_filter(
            post_filter, studies, assays, matrix_items, data_points
        )

    data = get_data_points_for_charting(
        data_points,
        request.POST.get('key', ''),
        request.POST.get('mean_type', ''),
        request.POST.get('interval_type', ''),
        request.POST.get('percent_control', ''),
        request.POST.get('include_all', ''),
        request.POST.get('truncate_negative', ''),
        json.loads(request.POST.get('dynamic_excluded', '{}')),
        study=studies,
        matrix_item=matrix_item,
        matrix_items=matrix_items,
        criteria=json.loads(request.POST.get('criteria', '{}')),
        post_filter=post_filter
    )

    data.update({
        'post_filter': post_filter
    })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


# TODO REFACTOR
def fetch_item_data(request):
    """Returns the Data Points for an Item

    Receives the following from POST:
    id -- the ID of the Item of interest
    """

    matrix_item_id = request.POST.get('matrix_item', '')

    if not matrix_item_id:
        return HttpResponseServerError()

    data = get_data_as_json([matrix_item_id])

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def validate_data_file(request):
    """Validates a bulk file and returns either errors or a preview of the data entered

    Receives the following from POST:
    study -- the study to acquire readouts from
    key -- specifies whether to split readouts by compound or device
    percent_control -- specifies whether to convert to percent control
    include_all -- specifies whether to include all data (exclude invalid if null string)
    """
    study = request.POST.get('study', '')
    key = request.POST.get('key', '')
    mean_type = request.POST.get('mean_type', 'arithmetic')
    interval_type = request.POST.get('interval_type', 'ste')
    percent_control = request.POST.get('percent_control', '')
    include_all = request.POST.get('include_all', '')
    truncate_negative = request.POST.get('truncate_negative', '')
    dynamic_quality = json.loads(request.POST.get('dynamic_quality', '{}'))

    this_study = AssayStudy.objects.get(pk=int(study))

    # Very odd, but expedient
    studies = AssayStudy.objects.filter(id=this_study.id)

    form = AssayStudyDataUploadForm(request.POST, request.FILES, request=request, instance=this_study)

    if form.is_valid():
        form_data = form.cleaned_data

        preview_data = form_data.get('preview_data')
        new_data_points = preview_data.get('readout_data')

        # NOTE THE EMPTY DIC, RIGHT NOW BULK PREVIEW NEVER SHOWS COMPOUND JUST DEVICE
        readout_data = get_data_points_for_charting(
            new_data_points,
            key,
            mean_type,
            interval_type,
            percent_control,
            include_all,
            truncate_negative,
            dynamic_quality,
            study=studies,
            new_data=True,
            criteria=json.loads(request.POST.get('criteria', '{}'))
        )

        data = {
            'readout_data': readout_data,
            'number_of_conflicting_entries': preview_data.get('number_of_conflicting_entries', 0)
        }

        return HttpResponse(json.dumps(data),
                            content_type="application/json")

    else:
        errors = ''
        if form.errors.get('__all__'):
            errors += form.errors.get('__all__').as_text()
        data = {
            'errors': errors
        }
        return HttpResponse(json.dumps(data),
                            content_type='application/json')


def fetch_assay_study_reproducibility(request):
    study = get_object_or_404(AssayStudy, pk=int(request.POST.get('study', '')))
    data = {}

    # If chip data
    matrix_items = AssayMatrixItem.objects.filter(
        study_id=study.id
    )

    # Boolean
    # include_all = self.request.GET.get('include_all', False)
    chip_data = get_data_as_list_of_lists(matrix_items, include_header=True, include_all=False)

    repro_data = get_repro_data(chip_data)

    gas_list = repro_data['reproducibility_results_table']['data']
    data['gas_list'] = gas_list

    mad_list = {}
    cv_list = {}
    chip_list = {}
    comp_list = {}
    for x in range(len(repro_data) - 1):
        # mad_list
        mad_list[x + 1] = {'columns': repro_data[x]['mad_score_matrix']['columns']}
        for y in range(len(repro_data[x]['mad_score_matrix']['index'])):
            repro_data[x]['mad_score_matrix']['data'][y].insert(0, repro_data[x]['mad_score_matrix']['index'][y])
        mad_list[x + 1]['data'] = repro_data[x]['mad_score_matrix']['data']
        # cv_list
        if repro_data[x].get('comp_ICC_Value'):
            cv_list[x + 1] = [['Time', 'CV (%)']]
            for y in range(len(repro_data[x]['CV_array']['index'])):
                repro_data[x]['CV_array']['data'][y].insert(0, repro_data[x]['CV_array']['index'][y])
            for entry in repro_data[x]['CV_array']['data']:
                cv_list[x + 1].append(entry)
        # chip_list
        repro_data[x]['cv_chart']['columns'].insert(0, "Time (days)")
        chip_list[x + 1] = [repro_data[x]['cv_chart']['columns']]
        for y in range(len(repro_data[x]['cv_chart']['index'])):
            repro_data[x]['cv_chart']['data'][y].insert(0, repro_data[x]['cv_chart']['index'][y])
        for z in range(len(repro_data[x]['cv_chart']['data'])):
            chip_list[x + 1].append(repro_data[x]['cv_chart']['data'][z])
        # comp_list
        if repro_data[x].get('comp_ICC_Value'):
            comp_list[x + 1] = []
            for y in range(len(repro_data[x]['comp_ICC_Value']['Chip ID'])):
                comp_list[x + 1].insert(y, [])
                comp_list[x + 1][y].append(repro_data[x]['comp_ICC_Value']['Chip ID'][y])
                comp_list[x + 1][y].append(repro_data[x]['comp_ICC_Value']['ICC Absolute Agreement'][y])
                comp_list[x + 1][y].append(repro_data[x]['comp_ICC_Value']['Missing Data Points'][y])

    data['mad_list'] = mad_list

    data['cv_list'] = cv_list

    data['chip_list'] = chip_list

    data['comp_list'] = comp_list

    # Get pie chart data
    excellent_counter = acceptable_counter = poor_counter = 0

    for x in range(0, len(data['gas_list'])):
        if data['gas_list'][x][10][0] == 'E':
            excellent_counter += 1
        elif data['gas_list'][x][10][0] == 'A':
            acceptable_counter += 1
        elif data['gas_list'][x][10][0] == 'P':
            poor_counter += 1

    data['pie'] = [excellent_counter, acceptable_counter, poor_counter]

    return HttpResponse(json.dumps(data),
                        content_type='application/json')


# NAIVE: REQUIRES REVISION
def fetch_pre_submission_filters(request):
    current_filters = json.loads(request.POST.get('filters', '{}'))
    filters_present = False

    for key, value in current_filters.items():
        if value:
            filters_present = True
            break

    accessible_studies = get_user_accessible_studies(request.user)

    # Notice EXCLUSION of items without organ models
    accessible_matrix_items = AssayMatrixItem.objects.filter(
        study_id__in=accessible_studies
    ).exclude(
        organ_model_id=None
    ).prefetch_related(
        'organ_model'
    )

    # Please note exclusion of null organ model here
    organ_models = sorted(list(set([
        (matrix_item.organ_model_id, matrix_item.organ_model.name) for matrix_item in
        accessible_matrix_items.exclude(organ_model_id=None)
    ])), key=lambda x: x[1])

    organ_model_ids = {organ_model[0]: True for organ_model in organ_models}

    groups = {}
    targets = {}
    compounds = {}

    number_of_points = 0
    # TODO TODO TODO
    number_of_studies = 0
    number_of_centers = 0

    if filters_present:
        if current_filters.get('organ_models', []):
            new_organ_model_ids = [int(id) for id in current_filters.get('organ_models', []) if int(id) in organ_model_ids]

            # In case changes in filters eliminate all organ models
            if new_organ_model_ids:
                organ_model_ids = new_organ_model_ids
        else:
            organ_model_ids = []

        accessible_matrix_items = accessible_matrix_items.filter(
            organ_model_id__in=organ_model_ids
        )

        accessible_studies = accessible_studies.filter(
            id__in=list(accessible_matrix_items.values_list('study_id', flat=True))
        )

        groups = sorted(list(set([
            (study.group_id, study.group.name) for study in
            accessible_studies
        ])), key=lambda x: x[1])

        group_ids = {group[0]: True for group in groups}

        if current_filters.get('groups', []):
            group_ids = [int(id) for id in current_filters.get('groups', []) if int(id) in group_ids]
        else:
            group_ids = []

        accessible_studies = accessible_studies.filter(group_id__in=group_ids)

        accessible_matrix_items = accessible_matrix_items.filter(
            study_id__in=accessible_studies
        )

        accessible_study_assays = AssayStudyAssay.objects.filter(
            assaydatapoint__matrix_item_id__in=accessible_matrix_items
        ).prefetch_related(
            'target'
        )

        targets = sorted(list(set([
            (study_assay.target_id, study_assay.target.name) for study_assay in
            accessible_study_assays
        ])), key=lambda x: x[1])

        target_ids = {target[0]: True for target in targets}

        if current_filters.get('targets', []):
            new_target_ids = [int(id) for id in current_filters.get('targets', []) if int(id) in target_ids]

            # In case changes in filters eliminate all targets
            if new_target_ids:
                target_ids = new_target_ids

            accessible_study_assays = accessible_study_assays.filter(target_id__in=target_ids)

            accessible_matrix_items = accessible_matrix_items.filter(
                assaydatapoint__study_assay__in=accessible_study_assays
            ).distinct()
        else:
            # Default to None
            target_ids = []
            accessible_study_assays = AssayStudyAssay.objects.none()
            accessible_matrix_items = AssayMatrixItem.objects.none()

        accessible_compounds = AssaySetupCompound.objects.filter(
            matrix_item__in=accessible_matrix_items
        ).prefetch_related(
            'compound_instance__compound'
        )

        compounds = sorted(list(set([
            (compound.compound_instance.compound_id, compound.compound_instance.compound.name) for compound in
            accessible_compounds
        ])), key=lambda x: x[1])

        # Check to see whether to include no compounds
        include_no_compounds = accessible_matrix_items.filter(
            assaysetupcompound__isnull=True
        ).count()

        # Prepend contrived no compound
        if include_no_compounds:
            compounds.insert(0, (0, NO_COMPOUNDS_STRING))

        compound_ids = {compound[0]: True for compound in compounds}

        if current_filters.get('compounds', []):
            new_compound_ids = [int(id) for id in current_filters.get('compounds', []) if int(id) in compound_ids]

            # In case changes in filters eliminate all compounds
            if new_compound_ids:
                compound_ids = new_compound_ids

            # A little odd
            if '0' in current_filters.get('compounds', []):
                include_no_compounds = True
            else:
                include_no_compounds = False
        else:
            # Default to none
            compound_ids = []
            include_no_compounds = False

        # Compensate for no compounds
        if include_no_compounds:
            accessible_matrix_items = accessible_matrix_items.filter(
                assaysetupcompound__compound_instance__compound_id__in=compound_ids
            ) | accessible_matrix_items.filter(
                assaysetupcompound__isnull=True
            )
        else:
            accessible_matrix_items = accessible_matrix_items.filter(
                assaysetupcompound__compound_instance__compound_id__in=compound_ids
            )

        number_of_points = AssayDataPoint.objects.filter(
            matrix_item_id__in=accessible_matrix_items,
            study_assay_id__in=accessible_study_assays,
            replaced=False,
            excluded=False,
            value__isnull=False
        ).count()
    # Do not default to showing all data points
    # else:
    #     number_of_points = AssayDataPoint.objects.filter(
    #         study_id__in=accessible_studies,
    #         replaced=False,
    #         excluded=False,
    #         value__isnull=False
    #     ).count()

    data = {
        'filters': {
            'groups': groups,
            'organ_models': organ_models,
            'targets': targets,
            'compounds': compounds,
        },
        'number_of_points': number_of_points
    }

    return HttpResponse(json.dumps(data),
                        content_type='application/json')


# TODO RATHER VERBOSE
def acquire_post_filter(studies, assays, matrix_items, data_points):
    # Table -> Filter -> value -> [name, in_use]
    post_filter = {}

    for study in studies:
        current = post_filter.setdefault(
            'study', {}
        )

        current.setdefault(
            'id__in', {}
        ).update({
            study.id: u'{} ({})'.format(study.name, study.group.name)
        })

    assays = assays.prefetch_related(
        'target',
        'method'
    )

    for assay in assays:
        current = post_filter.setdefault('assay', {})

        current.setdefault(
            'target_id__in', {}
        ).update({
            assay.target.id: assay.target.name
        })

        current.setdefault(
            'method_id__in', {}
        ).update({
            assay.method.id: assay.method.name
        })

    # Contrived: Add no compounds
    post_filter.setdefault('matrix_item', {}).setdefault(
        'assaysetupcompound__compound_instance__compound_id__in', {}
    ).update({
        0: NO_COMPOUNDS_STRING
    })

    # Contrived: Add no cells
    post_filter.setdefault('matrix_item', {}).setdefault(
        'assaysetupcell__cell_sample_id__in', {}
    ).update({
        0: '-No Cells-'
    })

    # Contrived: Add no settings
    post_filter.setdefault('matrix_item', {}).setdefault(
        'assaysetupsetting__setting_id__in', {}
    ).update({
        0: '-No Settings-'
    })

    matrix_items = matrix_items.prefetch_related(
        'assaysetupcompound_set__compound_instance__compound',
        'assaysetupcompound_set__compound_instance__supplier',
        'assaysetupcompound_set__addition_location',
        'assaysetupcell_set__cell_sample__cell_type',
        'assaysetupcell_set__cell_sample__cell_subtype',
        'assaysetupcell_set__addition_location',
        'assaysetupcell_set__biosensor',
        'assaysetupsetting_set__setting',
        'assaysetupsetting_set__addition_location',
        'organ_model',
        'matrix',
        'study'
    )

    for matrix_item in matrix_items:
        current = post_filter.setdefault('matrix_item', {})

        current.setdefault(
            'id__in', {}
        ).update({
            matrix_item.id: u'{} ({})'.format(matrix_item.name, matrix_item.study.name)
        })

        current.setdefault(
            'matrix_id__in', {}
        ).update({
            matrix_item.matrix_id: u'{} ({})'.format(matrix_item.matrix.name, matrix_item.study.name)
        })

        if matrix_item.organ_model_id:
            current.setdefault(
                'organ_model_id__in', {}
            ).update({
                matrix_item.organ_model_id: matrix_item.organ_model.name
            })

        for compound in matrix_item.assaysetupcompound_set.all():
            current.setdefault(
                'assaysetupcompound__compound_instance__compound_id__in', {}
            ).update({
                compound.compound_instance.compound_id : compound.compound_instance.compound.name
            })

            current.setdefault(
                'assaysetupcompound__compound_instance__supplier_id__in', {}
            ).update({
                compound.compound_instance.supplier_id: compound.compound_instance.supplier.name
            })

            current.setdefault(
                'assaysetupcompound__compound_instance__lot__in', {}
            ).update({
                compound.compound_instance.lot: compound.compound_instance.lot
            })

            # SPECIAL EXCEPTION, CONCENTRATION AND UNITS ARE COMBINED
            current.setdefault(
                'assaysetupcompound__concentration__in', {}
            ).update({
                compound.concentration: compound.concentration
            })
            current.setdefault(
                'assaysetupcompound__concentration_unit_id__in', {}
            ).update({
                compound.concentration_unit_id: compound.concentration_unit_id
            })

            current.setdefault(
                'assaysetupcompound__concentration__concentration_unit_id__in', {}
            ).update({
                '{}{}{}'.format(
                    compound.concentration,
                    COMBINED_VALUE_DELIMITER,
                    compound.concentration_unit_id
                ): '{}{}{}'.format(
                    compound.concentration,
                    COMBINED_VALUE_DELIMITER,
                    compound.concentration_unit
                )
            })

            current.setdefault(
                'assaysetupcompound__addition_time__in', {}
            ).update({
                compound.addition_time: compound.get_addition_time_string()
            })

            current.setdefault(
                'assaysetupcompound__duration__in', {}
            ).update({
                compound.duration: compound.get_duration_string()
            })

            current.setdefault(
                'assaysetupcompound__addition_location_id__in', {}
            ).update({
                compound.addition_location_id: compound.addition_location.name
            })

        for cell in matrix_item.assaysetupcell_set.all():
            current.setdefault(
                'assaysetupcell__cell_sample_id__in', {}
            ).update({
                cell.cell_sample_id: unicode(cell.cell_sample)
            })

            current.setdefault(
                'assaysetupcell__cell_sample__cell_type_id__in', {}
            ).update({
                cell.cell_sample.cell_type_id: cell.cell_sample.cell_type.cell_type
            })

            current.setdefault(
                'assaysetupcell__cell_sample__cell_subtype_id__in', {}
            ).update({
                cell.cell_sample.cell_subtype_id: cell.cell_sample.cell_subtype.cell_subtype
            })

            current.setdefault(
                'assaysetupcell__biosensor_id__in', {}
            ).update({
                cell.biosensor_id: cell.biosensor.name
            })

            current.setdefault(
                'assaysetupcell__passage__in', {}
            ).update({
                cell.passage: cell.passage
            })

            # SPECIAL EXCEPTION, DENSITY AND UNITS ARE COMBINED
            current.setdefault(
                'assaysetupcell__density__in', {}
            ).update({
                cell.density: cell.density
            })
            current.setdefault(
                'assaysetupcell__density_unit_id__in', {}
            ).update({
                cell.density_unit_id: cell.density_unit_id
            })

            # THIS NEEDS TO BE REMOVED BEFORE ACTUAL FILTERS ARE APPLIED
            current.setdefault(
                'assaysetupcell__density__density_unit_id__in', {}
            ).update({
                '{}{}{}'.format(
                    cell.density,
                    COMBINED_VALUE_DELIMITER,
                    cell.density_unit_id
                ): '{}{}{}'.format(
                    cell.density,
                    COMBINED_VALUE_DELIMITER,
                    cell.density_unit
                )
            })

            current.setdefault(
                'assaysetupcell__addition_location_id__in', {}
            ).update({
                cell.addition_location_id: cell.addition_location.name
            })

            # NOTE NO ADDITION TIME FOR CELLS AT THE MOMENT

        for setting in matrix_item.assaysetupsetting_set.all():
            current.setdefault(
                'assaysetupsetting__setting_id__in', {}
            ).update({
                setting.setting_id: setting.setting.name
            })

            # SPECIAL EXCEPTION, VALUE AND UNITS ARE COMBINED
            current.setdefault(
                'assaysetupsetting__value__in', {}
            ).update({
                setting.value: setting.value
            })
            current.setdefault(
                'assaysetupsetting__unit_id__in', {}
            ).update({
                setting.unit_id: setting.unit_id
            })

            current.setdefault(
                'assaysetupsetting__value__unit_id__in', {}
            ).update({
                '{}{}{}'.format(
                    setting.value,
                    COMBINED_VALUE_DELIMITER,
                    setting.unit_id
                ): '{}{}{}'.format(
                    setting.value,
                    COMBINED_VALUE_DELIMITER,
                    setting.unit
                )
            })

            current.setdefault(
                'assaysetupsetting__addition_time__in', {}
            ).update({
                setting.addition_time: setting.get_addition_time_string()
            })

            current.setdefault(
                'assaysetupsetting__duration__in', {}
            ).update({
                setting.duration: setting.get_duration_string()
            })

            current.setdefault(
                'assaysetupsetting__addition_location_id__in', {}
            ).update({
                setting.addition_location_id: setting.addition_location.name
            })

    data_points = data_points.prefetch_related(
        'sample_location'
    )

    for data_point in data_points:
        current = post_filter.setdefault('data_point', {})

        current.setdefault(
            'sample_location_id__in', {}
        ).update({
            data_point.sample_location_id: data_point.sample_location.name
        })

        # Out for now
        # current.setdefault(
        #     'time__in', {}
        # ).update({
        #     data_point.time: data_point.time
        # })

    return post_filter


def apply_post_filter(post_filter, studies, assays, matrix_items, data_points):
    # Not very elegant...
    study_post_filters = {
        current_filter: [
            x for x in post_filter.get('study', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('study', {})
    }

    studies = studies.filter(
        **study_post_filters
    )

    assay_post_filters = {
        current_filter: [
            x for x in post_filter.get('assay', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('assay', {})
    }

    assays = assays.filter(
        study_id__in=studies
    ).filter(
        **assay_post_filters
    )

    # Special exceptions for combined filters
    combined_compounds_data = post_filter.setdefault('matrix_item', {}).setdefault(
        'assaysetupcompound__concentration__concentration_unit_id__in', {}
    )

    compound_concentration_filter = {}
    compound_unit_filter = {}

    for concentration_unit_id in combined_compounds_data.keys():
        concentration_unit_id = concentration_unit_id.split(COMBINED_VALUE_DELIMITER)
        concentration = concentration_unit_id[0]
        unit = concentration_unit_id[1]
        compound_concentration_filter.update({
            concentration: True
        })
        compound_unit_filter.update({
            unit: True
        })

    post_filter.get('matrix_item', {}).update({
        'assaysetupcompound__concentration__in': compound_concentration_filter,
        'assaysetupcompound__concentration_unit_id__in': compound_unit_filter
    })

    del post_filter['matrix_item']['assaysetupcompound__concentration__concentration_unit_id__in']

    combined_cells_data = post_filter.setdefault('matrix_item', {}).setdefault(
        'assaysetupcell__density__density_unit_id__in', {}
    )

    cell_density_filter = {}
    cell_unit_filter = {}

    for density_unit_id in combined_cells_data.keys():
        density_unit_id = density_unit_id.split(COMBINED_VALUE_DELIMITER)
        density = density_unit_id[0]
        unit = density_unit_id[1]
        cell_density_filter.update({
            density: True
        })
        cell_unit_filter.update({
            unit: True
        })

    post_filter.get('matrix_item', {}).update({
        'assaysetupcell__density__in': cell_density_filter,
        'assaysetupcell__density_unit_id__in': cell_unit_filter
    })

    del post_filter['matrix_item']['assaysetupcell__density__density_unit_id__in']

    combined_settings_data = post_filter.setdefault('matrix_item', {}).setdefault(
        'assaysetupsetting__value__unit_id__in', {}
    )

    setting_value_filter = {}
    setting_unit_filter = {}

    for value_unit_id in combined_settings_data.keys():
        value_unit_id = value_unit_id.split(COMBINED_VALUE_DELIMITER)
        value = value_unit_id[0]
        unit = value_unit_id[1]
        setting_value_filter.update({
            value: True
        })
        setting_unit_filter.update({
            unit: True
        })

    post_filter.get('matrix_item', {}).update({
        'assaysetupsetting__value__in': setting_value_filter,
        'assaysetupsetting__unit_id__in': setting_unit_filter
    })

    del post_filter['matrix_item']['assaysetupsetting__value__unit_id__in']

    # Matrix Items somewhat contrived to deal with null compounds
    matrix_item_post_filters = {
        current_filter: [
            x for x in post_filter.get('matrix_item', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('matrix_item', {}) if not current_filter.startswith('assaysetup')
    }

    matrix_item_compound_post_filters = {
        current_filter: [
            x for x in post_filter.get('matrix_item', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('matrix_item', {}) if current_filter.startswith('assaysetupcompound__')
    }

    matrix_item_cell_post_filters = {
        current_filter: [
            x for x in post_filter.get('matrix_item', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('matrix_item', {}) if current_filter.startswith('assaysetupcell__')
    }

    matrix_item_setting_post_filters = {
        current_filter: [
            x for x in post_filter.get('matrix_item', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('matrix_item', {}) if current_filter.startswith('assaysetupsetting__')
    }

    matrix_items = matrix_items.filter(study__in=studies)

    matrix_items = matrix_items.filter(
        **matrix_item_post_filters
    )

    # Compounds
    if post_filter.get('matrix_item', {}).get('assaysetupcompound__compound_instance__compound_id__in', {}).get(
            '0', None
    ):
        matrix_items = matrix_items.filter(
            **matrix_item_compound_post_filters
        ) | matrix_items.filter(assaysetupcompound__isnull=True)
    else:
        matrix_items = matrix_items.filter(
            **matrix_item_compound_post_filters
        )

    # Cells
    if post_filter.get('matrix_item', {}).get('assaysetupcell__cell_sample_id__in', {}).get('0', None):
        matrix_items = matrix_items.filter(
            **matrix_item_cell_post_filters
        ) | matrix_items.filter(assaysetupcell__isnull=True)
    else:
        matrix_items = matrix_items.filter(
            **matrix_item_cell_post_filters
        )

    # Setting
    if post_filter.get('matrix_item', {}).get('assaysetupsetting__setting_id__in', {}).get('0', None):
        matrix_items = matrix_items.filter(
            **matrix_item_setting_post_filters
        ) | matrix_items.filter(assaysetupsetting__isnull=True)
    else:
        matrix_items = matrix_items.filter(
            **matrix_item_setting_post_filters
        )

    matrix_items = matrix_items.distinct()

    data_point_post_filters = {
        current_filter: [
            x for x in post_filter.get('data_point', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('data_point', {})
    }

    data_points = data_points.filter(
        study_id__in=studies,
        study_assay_id__in=assays,
        matrix_item_id__in=matrix_items,
    ).filter(
        **data_point_post_filters
    )

    return studies, assays, matrix_items, data_points


def fetch_data_points_from_filters(request):
    intention = request.POST.get('intention', 'charting')

    post_filter = json.loads(request.POST.get('post_filter', '{}'))

    pre_filter = {}
    if request.POST.get('filters', ''):
        current_filters = json.loads(request.POST.get('filters', '{}'))
        accessible_studies = get_user_accessible_studies(request.user)

        # Notice exclusion of missing organ model
        matrix_items = AssayMatrixItem.objects.filter(
            study_id__in=accessible_studies
        ).exclude(
            organ_model_id=None
        ).prefetch_related(
            'organ_model',
            # 'assaysetupcompound_set__compound_instance',
            # 'assaydatapoint_set__study_assay__target'
        )

        if current_filters.get('organ_models', []):
            organ_model_ids = [int(id) for id in current_filters.get('organ_models', []) if id]

            matrix_items = matrix_items.filter(
                organ_model_id__in=organ_model_ids
            )
        # Default to empty
        else:
            matrix_items = AssayMatrixItem.objects.none()

        accessible_studies = accessible_studies.filter(
            id__in=list(matrix_items.values_list('study_id', flat=True))
        )

        matrix_items.prefetch_related(
            'assaysetupcompound_set__compound_instance',
            'assaydatapoint_set__study_assay__target'
        )

        if current_filters.get('groups', []):
            group_ids = [int(id) for id in current_filters.get('groups', []) if id]
            accessible_studies = accessible_studies.filter(group_id__in=group_ids)

            matrix_items = matrix_items.filter(
                study_id__in=accessible_studies
            )
        else:
            matrix_items = AssayMatrixItem.objects.none()

        if current_filters.get('compounds', []):
            compound_ids = [int(id) for id in current_filters.get('compounds', []) if id]

            # See whether to include no compounds
            if '0' in current_filters.get('compounds', []):
                matrix_items = matrix_items.filter(
                    assaysetupcompound__compound_instance__compound_id__in=compound_ids
                ) | matrix_items.filter(assaysetupcompound__isnull=True)
            else:
                matrix_items = matrix_items.filter(
                    assaysetupcompound__compound_instance__compound_id__in=compound_ids
                )

        else:
            matrix_items = AssayMatrixItem.objects.none()

        if current_filters.get('targets', []):
            target_ids = [int(id) for id in current_filters.get('targets', []) if id]

            matrix_items = matrix_items.filter(
                assaydatapoint__study_assay__target_id__in=target_ids
            ).distinct()

            pre_filter.update({
                'study_assay__target_id__in': target_ids
            })
        else:
            matrix_items = AssayMatrixItem.objects.none()
            target_ids = []

        pre_filter.update({
            'matrix_item_id__in': matrix_items.filter(assaydatapoint__isnull=False).distinct()
        })

        matrix_item = None
        studies = accessible_studies

        # A little contrived
        assays = AssayStudyAssay.objects.filter(
            study_id__in=studies,
            target_id__in=target_ids
        )

        # Not particularly DRY
        data_points = AssayDataPoint.objects.filter(
            **pre_filter
        ).prefetch_related(
            # TODO
            'study__group',
            'study_assay__target',
            'study_assay__method',
            'study_assay__unit__base_unit',
            'sample_location',
            'matrix_item__matrix',
            'matrix_item__organ_model',
            'subtarget'
        ).filter(
            replaced=False,
            excluded=False,
            value__isnull=False
        )

        if not post_filter:
            assays = assays.prefetch_related(
                'target',
                'method'
            )

            post_filter = acquire_post_filter(studies, assays, matrix_items, data_points)
        else:
            studies, assays, matrix_items, data_points = apply_post_filter(
                post_filter, studies, assays, matrix_items, data_points
            )

        if intention == 'charting':
            data = get_data_points_for_charting(
                data_points,
                request.POST.get('key', ''),
                request.POST.get('mean_type', ''),
                request.POST.get('interval_type', ''),
                request.POST.get('percent_control', ''),
                request.POST.get('include_all', ''),
                request.POST.get('truncate_negative', ''),
                json.loads(request.POST.get('dynamic_excluded', '{}')),
                study=studies,
                matrix_item=matrix_item,
                matrix_items=matrix_items,
                criteria=json.loads(request.POST.get('criteria', '{}')),
                post_filter=post_filter
            )

            data.update({'post_filter': post_filter})

            return HttpResponse(json.dumps(data),
                                content_type="application/json")
        elif intention == 'inter_repro':
            criteria = json.loads(request.POST.get('criteria', '{}'))
            inter_level = int(request.POST.get('inter_level', 1))
            max_interpolation_size = int(request.POST.get('max_interpolation_size', 2))
            initial_norm = int(request.POST.get('initial_norm', 0))

            data = get_inter_study_reproducibility(
                data_points,
                matrix_items,
                inter_level,
                max_interpolation_size,
                initial_norm,
                criteria
            )

            data.update({'post_filter': post_filter})

            return HttpResponse(json.dumps(data),
                                content_type="application/json")
        else:
            return HttpResponseServerError()
    else:
        return HttpResponseServerError()


def get_inter_study_reproducibility(
        data_points,
        matrix_items,
        inter_level,
        max_interpolation_size,
        initial_norm,
        criteria
    ):
    # Organization is assay -> unit -> compound/tag -> field -> time -> value
    treatment_group_representatives, setup_to_treatment_group, treatment_header_keys = get_item_groups(
        None,
        criteria,
        matrix_items
    )

    matrix_item_id_to_tooltip_string = {
        matrix_item.id: u'{} ({})'.format(matrix_item.name, matrix_item.matrix.name) for matrix_item in matrix_items
    }

    inter_data = []

    data_point_treatment_groups = {}
    treatment_group_table = {}
    data_group_to_studies = {}
    data_group_to_sample_locations = {}
    data_group_to_organ_models = {}

    # CONTRIVED FOR NOW
    data_header_keys = [
        'Target',
        # 'Method',
        'Value Unit',
        # 'Sample Location'
    ]

    base_tuple = (
        'study_assay.target_id',
        # 'study_assay.method_id',
        'study_assay.unit.base_unit_id',
        # 'sample_location_id'
    )

    current_tuple = (
        'study_assay.target_id',
        # 'study_assay.method_id',
        'study_assay.unit_id',
        # 'sample_location_id'
    )

    additional_keys = []

    sets_intra_points = {}

    # CRUDE
    if criteria:
        group_sample_location = 'sample_location' in criteria.get('special', [])
        group_method = 'method' in criteria.get('special', [])

        if group_method:
            data_header_keys.append('Method')
            additional_keys.append('study_assay.method_id')

        if group_sample_location:
            data_header_keys.append('Sample Location')
            additional_keys.append('sample_location_id')

    if additional_keys:
        base_tuple += tuple(additional_keys)
        current_tuple += tuple(additional_keys)

    # ASSUME _id termination
    base_value_tuple = tuple([x.replace('_id', '') for x in base_tuple])
    current_value_tuple = tuple([x.replace('_id', '') for x in current_tuple])

    # TODO TODO TODO TODO
    data_point_attribute_getter_base = tuple_attrgetter(*base_tuple)
    data_point_attribute_getter_current = tuple_attrgetter(*current_tuple)

    data_point_attribute_getter_base_values = tuple_attrgetter(*base_value_tuple)
    data_point_attribute_getter_current_values = tuple_attrgetter(*current_value_tuple)

    for point in data_points:
        point.standard_value = point.value
        item_id = point.matrix_item_id
        if point.study_assay.unit.base_unit_id:
            data_point_tuple = data_point_attribute_getter_base(point)
            point.standard_value *= point.study_assay.unit.scale_factor
        else:
            data_point_tuple = data_point_attribute_getter_current(point)
        current_group = data_point_treatment_groups.setdefault(
            (
                data_point_tuple,
                # setup_to_treatment_group.get(item_id).get('id')
                setup_to_treatment_group.get(item_id).get('index')
            ),
            # 'Group {}'.format(len(data_point_treatment_groups) + 1)
            u'{}'.format(len(data_point_treatment_groups) + 1)
        )

        # TODO Intra-in-Inter: Dictionary of format {group_num : {study1 : [point1, point2], study2 : [point1, point2]}}
        study_name = "{} ({})".format(point.study.name, point.study.group)

        if current_group not in sets_intra_points:
            sets_intra_points[current_group] = {}
        if study_name not in sets_intra_points[current_group]:
            sets_intra_points[current_group][study_name] = []
        sets_intra_points[current_group][study_name].append([
            point.time,
            point.value,
            point.matrix_item_id
        ])

        point.data_group = current_group
        if current_group not in treatment_group_table:
            if point.study_assay.unit.base_unit_id:
                treatment_group_table.update({
                    current_group: [unicode(x) for x in list(
                        data_point_attribute_getter_base_values(point)
                    ) + [setup_to_treatment_group.get(item_id).get('index')]]
                })
            else:
                treatment_group_table.update({
                    current_group: [unicode(x) for x in list(
                        data_point_attribute_getter_current_values(point)
                    ) + [setup_to_treatment_group.get(item_id).get('index')]]
                })

        data_group_to_studies.setdefault(
            current_group, {}
        ).update({
            u'<a href="{}" target="_blank">{} ({})</a>'.format(point.study.get_absolute_url(), point.study.name, point.study.group.name): point.study.name
        })

        data_group_to_sample_locations.setdefault(
            current_group, {}
        ).update({
            point.sample_location.name: True
        })

        data_group_to_organ_models.setdefault(
            current_group, {}
        ).update({
            point.matrix_item.organ_model.name: True
        })

    inter_data.append([
        'Study ID',
        'Chip ID',
        'Time',
        'Value',
        'MPS User Group',
        # NAME THIS SOMETHING ELSE
        'Treatment Group'
    ])

    # GET RAW DATAPOINTS AS LEGEND -> TIME -> LIST OF VALUES
    # AFTER THAN REPOSITION THEM FOR CHARTING AND AVERAGE ONE OF THE SETS (KEEP RAW THOUGH)
    initial_chart_data = {}
    final_chart_data = {}

    for point in data_points:
        inter_data.append([
            point.study.name,
            point.matrix_item.name,
            point.time,
            # NOTE USE OF STANDARD VALUE RATHER THAN VALUE
            point.standard_value,
            point.study.group.name,
            point.data_group
        ])

        if inter_level:
            legend = point.study.group.name
        else:
            legend = point.study.name

        initial_chart_data.setdefault(
            point.data_group, {}
        ).setdefault(
            'item', {}
        ).setdefault(
            legend, {}
        ).setdefault(
            # NOTE CONVERT TO DAYS
            point.time / 1440.0, []
        ).append((point.standard_value, matrix_item_id_to_tooltip_string.get(point.matrix_item_id)))

        initial_chart_data.setdefault(
            point.data_group, {}
        ).setdefault(
            'average', {}
        ).setdefault(
            legend, {}
        ).setdefault(
            # NOTE CONVERT TO DAYS
            point.time / 1440.0, []
        ).append(point.standard_value)

    for set, chart_groups in initial_chart_data.items():
        current_set = final_chart_data.setdefault(set, {})
        for chart_group, legends in chart_groups.items():
            current_data = {}
            current_table = current_set.setdefault(chart_group, [['Time']])
            x_header = {}
            y_header = {}
            for legend, times in legends.items():
                x_header.update({
                    legend: True,
                })

                if chart_group == 'average':
                    x_header.update({
                        legend: True,
                        # This is to deal with intervals
                        u'{}{}'.format(legend, '     ~@i1'): True,
                        u'{}{}'.format(legend, '     ~@i2'): True,
                    })
                else:
                    x_header.update({
                        legend: True,
                        # This is to deal with custom tooltips
                        u'{}{}'.format(legend, '     ~@t'): True,
                    })

                for time, values in times.items():
                    if chart_group == 'item':
                        for index, value_pair in enumerate(values):
                            value = value_pair[0]
                            matrix_item_id = value_pair[1]
                            current_data.setdefault(legend, {}).update({u'{}~{}'.format(time, index): value})
                            current_data.setdefault(u'{}{}'.format(legend, '     ~@t'), {}).update(
                                {
                                    u'{}~{}'.format(time, index): [time, legend, value, matrix_item_id]
                                }
                            )
                            y_header.update({u'{}~{}'.format(time, index): True})
                            # x_header.update({
                            #     '{}    ~@x{}'.format(legend, index): True
                            # })
                            # current_data.setdefault('{}    ~@x{}'.format(legend, index), {}).update({time: value})
                            # y_header.update({time: True})
                    else:
                        if len(values) > 1:
                            # TODO TODO TODO ONLY ARITHMETIC MEAN RIGHT NOW
                            value = np.mean(values)
                            std = np.std(values)
                            current_data.setdefault(legend, {}).update({time: value})
                            current_data.setdefault(u'{}{}'.format(legend, '     ~@i1'), {}).update({time: value - std})
                            current_data.setdefault(u'{}{}'.format(legend, '     ~@i2'), {}).update({time: value + std})
                        else:
                            current_data.setdefault(legend, {}).update({time: values[0]})
                        y_header.update({time: True})

            x_header_keys = x_header.keys()
            x_header_keys.sort(key=alphanum_key)
            current_table[0].extend(x_header_keys)

            # if chart_group == 'average':
            #     current_table[0].extend(x_header_keys)
            # else:
            #     current_table[0].extend([x.split('    ~@x')[0] for x in x_header_keys])

            x_header = {x_header_keys[index]: index + 1 for index in range(len(x_header_keys))}

            y_header = y_header.keys()
            y_header.sort(key=lambda x: float(unicode(x).split('~')[0]))
            # y_header.sort(key=float)

            for y in y_header:
                current_table.append([float(str(y).split('~')[0])] + [None] * (len(x_header)))
                # current_table.append([y] + [None] * (len(x_header)))

            y_header = {y_header[index]: index + 1 for index in range(len(y_header))}

            for x, data_point in current_data.items():
                for y, value in data_point.items():
                    current_table[y_header.get(y)][x_header.get(x)] = value

    # Reset chart data again
    # initial_chart_data = {}

    reproducibility_results_table, inter_data_table = get_inter_study_reproducibility_report(
        len(treatment_group_table),
        inter_data,
        inter_level,
        max_interpolation_size,
        initial_norm
    )

    if inter_data_table.get('errors', ''):
        return inter_data_table

    reproducibility_results_table = reproducibility_results_table.astype(object).replace(np.nan, '')
    # results_columns = [i for i in reproducibility_results_table.columns]
    # results_rows = results_columns + [[row[i] for i in range(1, len(row))] for row in reproducibility_results_table.itertuples()]
    results_rows = [
        [row[i] for i in range(1, len(row))] for row in reproducibility_results_table.itertuples()
    ]
    # Make into a suitable dictionary
    results_rows_full = {}
    results_rows_best = []
    excellent_counter = acceptable_counter = poor_counter = 0
    for row in results_rows:
        current_dic = results_rows_full.setdefault(
            row[0], {}
        )
        current_dic.update({
            row[1]: row
        })

        # Get numeric ICC
        current_icc = row[6] if row[6] else 0

        if current_dic.get('best', '') and (current_icc > current_dic.get('best')[6] or not current_dic.get('best')[6]):
            current_dic.update({
                'best': row
            })
        # Subject to revision
        elif not current_dic.get('best', ''):
            current_dic.update({
                'best': row
            })

    for set, current_dic in results_rows_full.items():
        current_best = current_dic.get('best')

        # If the current best has no ICC, try CV
        if not current_best[6]:
            for current_type, row in current_dic.items():
                current_cv = row[5] if row[5] else 999

                if current_cv < current_dic.get('best')[5]:
                    current_dic.update({
                        'best': row
                    })

    for set, current_dic in results_rows_full.items():
        current_best = current_dic.get('best')

        if current_best[8]:
            if current_best[8][0] == 'E':
                excellent_counter += 1
            elif current_best[8][0] == 'A':
                acceptable_counter += 1
            elif current_best[8][0] == 'P':
                poor_counter += 1

        for current_type, row in current_dic.items():
            # Format the ICC
            if row[6] and not type(row[6]) == str:
                row[6] = '{0:.4g}'.format(row[6])

            # Format Max CV while I am at it
            if row[5] and not type(row[5]) == str:
                row[5] = '{0:.4g}'.format(row[5])

        # Removed for now
        # Make sure it actually has points overlapping
        # if current_best[4]:
        #     results_rows_best.append(current_best)
        results_rows_best.append(current_best)

    inter_data_table = inter_data_table.astype(object).replace(np.nan, '')
    # inter_data_columns = [i for i in inter_data_table.columns]
    inter_data_rows = [[row[i] for i in range(1, len(row))] for row in inter_data_table.itertuples()]

    inter_chart_data = {}

    for row in inter_data_rows:
        # BE CAREFUL, INDICES MAY CHANGE
        shape = ''
        if row[3] != 'Original':
            shape = 'point {shape-type: star; size: 9;}'
        inter_chart_data.setdefault(
            row[5], {}
        ).setdefault(
            row[4], {}
        ).setdefault(
            row[1], {}
        ).setdefault(
            # NOTE CONVERT TO DAYS
            row[0] / 1440.0, (row[2], shape)
        )

    for set, chart_groups in inter_chart_data.items():
        current_set = final_chart_data.setdefault(set, {})
        for chart_group, legends in chart_groups.items():
            current_data = {}
            current_table = current_set.setdefault(chart_group, [['Time']])
            x_header = {}
            y_header = {}
            for legend, times in legends.items():
                # Get the median
                current_median = np.median([
                    np.median(x) for x in initial_chart_data.get(
                        set
                    ).get(
                        'average'
                    ).get(
                        legend
                    ).values()
                ])

                x_header.update({
                    legend: True,
                    # This is to deal with the style
                    u'{}{}'.format(legend, '     ~@s'): True,
                    # This is to deal with intervals
                    u'{}{}'.format(legend, '     ~@i1'): True,
                    u'{}{}'.format(legend, '     ~@i2'): True,
                })
                for time, value_shape in times.items():
                    value, shape = value_shape[0], value_shape[1]
                    if shape:
                        current_data.setdefault(legend, {}).update({time: value})
                        current_data.setdefault(u'{}{}'.format(legend, '     ~@s'), {}).update({time: shape})
                        y_header.update({time: True})
                    else:
                        values = initial_chart_data.get(
                            set
                        ).get(
                            'average'
                        ).get(
                            legend
                        ).get(
                            time
                        )

                        if initial_norm == 1 and current_median:
                            values = [current_value / current_median for current_value in values]

                        if len(values) > 1:
                            # TODO TODO TODO ONLY ARITHMETIC MEAN RIGHT NOW
                            value = np.mean(values)
                            std = np.std(values)
                            current_data.setdefault(legend, {}).update({time: value})
                            current_data.setdefault(u'{}{}'.format(legend, '     ~@i1'), {}).update({time: value - std})
                            current_data.setdefault(u'{}{}'.format(legend, '     ~@i2'), {}).update({time: value + std})
                            current_data.setdefault(u'{}{}'.format(legend, '     ~@s'), {}).update({time: shape})
                        else:
                            current_data.setdefault(legend, {}).update({time: values[0]})

                        y_header.update({time: True})

            x_header_keys = x_header.keys()
            x_header_keys.sort(key=alphanum_key)
            current_table[0].extend(x_header_keys)

            x_header = {x_header_keys[index]: index + 1 for index in range(len(x_header_keys))}

            y_header = y_header.keys()
            y_header.sort(key=float)

            for y in y_header:
                current_table.append([y] + [None] * (len(x_header)))

            y_header = {y_header[index]: index + 1 for index in range(len(y_header))}

            for x, data_point in current_data.items():
                for y, value in data_point.items():
                    current_table[y_header.get(y)][x_header.get(x)] = value

    final_data_group_to_studies = {}
    for data_group, current_studies in data_group_to_studies.items():
        final_data_group_to_studies[data_group] = sorted(current_studies, key=current_studies.get)

    final_data_group_to_sample_locations = {}
    for data_group, current_sample_location in data_group_to_sample_locations.items():
        final_data_group_to_sample_locations[data_group] = sorted(current_sample_location)

    final_data_group_to_organ_models = {}
    for data_group, current_organ_model in data_group_to_organ_models.items():
        final_data_group_to_organ_models[data_group] = sorted(current_organ_model)

    data = {
        'chart_data': final_chart_data,
        'repro_table_data_full': results_rows_full,
        'repro_table_data_best': results_rows_best,
        'data_groups': treatment_group_table,
        'header_keys': {
            'treatment': treatment_header_keys,
            'data': data_header_keys
        },
        'treatment_groups': treatment_group_representatives,
        'data_group_to_studies': final_data_group_to_studies,
        # BAD
        'data_group_to_sample_locations': final_data_group_to_sample_locations,
        'data_group_to_organ_models': final_data_group_to_organ_models,
        'pie': [excellent_counter, acceptable_counter, poor_counter],
        'sets_intra_points': sets_intra_points
    }

    return data


def intra_repro_in_inter(request):
    datapoints = json.loads(request.POST.get('datapoints', '{}'))
    statuses = []
    for x in datapoints:
        statuses.append(intra_status_for_inter(x))

    return HttpResponse(json.dumps(statuses),
                        content_type='application/json')


def study_viewer_validation(request):
    study = None
    if request.POST.get('study', ''):
        study = get_object_or_404(AssayStudy, pk=request.POST.get('study'))
    elif request.POST.get('matrix_item', ''):
        # GET STUDY FROM THE MATRIX ITEM
        matrix_item = get_object_or_404(AssayMatrixItem, pk=request.POST.get('matrix_item'))
        study = matrix_item.study
    elif request.POST.get('matrix', ''):
        # GET STUDY FROM THE MATRIX ITEM
        matrix = get_object_or_404(AssayMatrix, pk=request.POST.get('matrix'))
        study = matrix.study

    if study:
        return user_is_valid_study_viewer(request.user, study)
    else:
        return False


def study_editor_validation(request):
    study = None
    if request.POST.get('study', ''):
        study = get_object_or_404(AssayStudy, pk=request.POST.get('study'))
    elif request.POST.get('matrix_item', ''):
        # GET STUDY FROM THE MATRIX ITEM
        matrix_item = get_object_or_404(AssayMatrixItem, pk=request.POST.get('matrix_item'))
        study = matrix_item.study
    elif request.POST.get('matrix', ''):
        # GET STUDY FROM THE MATRIX ITEM
        matrix = get_object_or_404(AssayMatrix, pk=request.POST.get('matrix'))
        study = matrix.study

    if study:
        return is_group_editor(request.user, study.group.name)
    else:
        return False


# TODO TODO TODO
switch = {
    'fetch_center_id': {'call': fetch_center_id},
    'fetch_organ_models': {'call': fetch_organ_models},
    'fetch_protocols': {'call': fetch_protocols},
    'fetch_protocol': {'call': fetch_protocol},
    'send_ready_for_sign_off_email': {'call': send_ready_for_sign_off_email},
    'fetch_device_dimensions': {'call': fetch_device_dimensions},
    'fetch_data_points': {
        'call': fetch_data_points,
        'validation': study_viewer_validation
    },
    'fetch_item_data': {
        'call': fetch_item_data,
        'validation': study_viewer_validation
    },
    'fetch_assay_study_reproducibility': {
        'call': fetch_assay_study_reproducibility,
        'validation': study_viewer_validation
    },
    'validate_data_file': {
        'call': validate_data_file,
        'validation': study_editor_validation
    },
    'fetch_pre_submission_filters': {
        'call': fetch_pre_submission_filters
    },
    'fetch_data_points_from_filters': {
        'call': fetch_data_points_from_filters
    },
    'intra_repro_in_inter': {
        'call': intra_repro_in_inter
    },
}


def ajax(request):
    """Switch to correct function given POST call

    Receives the following from POST:
    call -- What function to redirect to
    """
    post_call = request.POST.get('call', '')

    # Abort if there is no valid call sent to us from Javascript
    if not post_call:
        logger.error('post_call not present in request to ajax')
        return HttpResponseServerError()

    # Route the request to the correct handler function
    # and pass request to the functions
    try:
        # select the function from the dictionary
        selection = switch[post_call]
    # If all else fails, handle the error message
    except KeyError:
        return HttpResponseServerError()

    else:
        procedure = selection.get('call')
        validation = selection.get('validation', None)
        if validation:
            valid = validation(request)

            if not valid:
                return HttpResponseForbidden()

        # execute the function
        return procedure(request)
