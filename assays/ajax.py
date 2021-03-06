# coding=utf-8
import ujson as json
# Ask if folks mind the pvalues getting truncated, non-U-json fixes this
import json as default_json
import math
# from collections import defaultdict
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseServerError,
    JsonResponse
)
from django.apps import apps
from .models import (
    AssayStudy,
    AssayMatrixItem,
    AssayMatrix,
    AssayStudyAssay,
    AssayDataPoint,
    AssayDataFileUpload,
    # ????
    AssayChipReadout,
    AssayChipSetup,
    AssayRun,
    AssayChipReadoutAssay,
    AssayPlateReadoutAssay,
    # NO!
    # AssaySetupCompound,
    AssayGroupCompound,
    AssayStudySet,
    AssayCategory,
    AssayTarget,
    AssayReference,
    SpeciesParameters,
    DEFAULT_SETUP_CRITERIA,
    DEFAULT_SETTING_CRITERIA,
    DEFAULT_COMPOUND_CRITERIA,
    DEFAULT_CELL_CRITERIA,
    attr_getter,
    tuple_attrgetter,
    get_split_times,
    AssayPlateReaderMap,
    AssayPlateReaderMapItem,
    AssayPlateReaderMapItemValue,
    AssayPlateReaderMapDataFile,
    assay_plate_reader_map_info_shape_col_dict,
    assay_plate_reader_map_info_shape_row_dict,
    assay_plate_reader_map_info_plate_size_choices_list,
    PhysicalUnits,
    AssayOmicDataFileUpload,
    AssayOmicDataPoint,
    AssayOmicAnalysisTarget,
    AssayGroup,
    AssaySampleLocation,
)
from microdevices.models import (
    MicrophysiologyCenter,
    Microdevice,
    OrganModel,
    OrganModelProtocol,
    OrganModelProtocolCell,
    OrganModelProtocolSetting,
    OrganModelLocation,
)
from compounds.models import (
    Compound
)

# from mps.settings import TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX
from .forms import (
    AssayStudyDataUploadForm,
    ReadyForSignOffForm,
    AssayPlateReaderMapDataFileAddForm,
)

from .utils import (
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
    two_sample_power_analysis,
    one_sample_power_analysis,
    create_power_analysis_group_table,
    pk_clearance_results,
    calculate_pk_parameters,
    review_plate_reader_data_file_format,
    get_the_plate_layout_info_for_assay_plate_map,
    review_plate_reader_data_file_return_file_list,
    plate_reader_data_file_process_data,
    omic_data_file_process_data,
    this_file_same_as_another_in_this_study,
    get_model_location_dictionary,
    sandrasGeneralFormatNumberFunction
)

import csv
from io import StringIO
from django.shortcuts import get_object_or_404
from mps.templatetags.custom_filters import ADMIN_SUFFIX, is_group_editor

from django.contrib.auth.models import User
from mps.settings import DEFAULT_FROM_EMAIL

from django.template.loader import render_to_string

from mps.mixins import user_is_valid_study_viewer

# from django.utils import timezone

from django.db.models import Avg, Max, Min
from django.db import connection

import numpy as np
from scipy.stats.mstats import gmean
from scipy.stats import iqr

from bs4 import BeautifulSoup
import requests
import re
import os
import copy

from django.utils import timezone

from mps.utils import *

import logging
logger = logging.getLogger(__name__)

# Calling main is and always will be indicative of an error condition.
# ajax.py is strictly for AJAX requests

# Ajax requests are sent to ajax(request) and funneled into the correct
# handler function using a simulated Python switch routing function

# TODO OPTIMIZE DATABASE HITS
# Global variable for what to call control values (avoid magic strings)
CONTROL_LABEL = '-Control-'

# Note manipulations for sorting
def atof(text):
    try:
        retval = float(text)
    except ValueError:
        retval = text
    return retval


def alphanum_key(text):
    return [
        atof(c.replace(INTERVAL_1_SIGIL, '!').replace(INTERVAL_2_SIGIL, '"').replace(SHAPE_SIGIL, '"').replace('\n', '')) for c in re.split(r'[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)', text)
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
        dropdown.append({'value': value, 'text': str(finding)})

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
        dropdown.append({'value': value, 'text': str(finding)})

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
        protocol_file = protocol[0].protocol_file
        file_name = '/'.join(protocol_file.name.split('/')[1:])
        # href = '/media/' + protocol_file.name
        href = '/media/{}'.format(protocol_file.name)
        data.update({
            'file_name': file_name,
            'href': href
        })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


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


def fetch_device_dimensions_from_organ_model(request):
    organ_model_id = request.POST.get('organ_model_id', None)

    data = {
        'number_of_rows': 1,
        'number_of_columns': 1
    }

    organ_model = OrganModel.objects.filter(id=organ_model_id)

    if organ_model:
        device = organ_model[0].device
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
            subject = 'Sign Off Requested for {0}'.format(str(study))

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
            'study__group__center_groups',

            # Is going through the matrix item too expensive here?
            'matrix_item__group__assaygroupcompound_set__compound_instance__compound',
            'matrix_item__group__assaygroupcompound_set__compound_instance__supplier',
            'matrix_item__group__assaygroupcompound_set__concentration_unit',
            'matrix_item__group__assaygroupcompound_set__addition_location',
            'matrix_item__group__assaygroupcell_set__cell_sample__cell_type__organ',
            'matrix_item__group__assaygroupcell_set__cell_sample__cell_subtype',
            'matrix_item__group__assaygroupcell_set__cell_sample__supplier',
            'matrix_item__group__assaygroupcell_set__addition_location',
            'matrix_item__group__assaygroupcell_set__density_unit',
            'matrix_item__group__assaygroupsetting_set__setting',
            'matrix_item__group__assaygroupsetting_set__unit',
            'matrix_item__group__assaygroupsetting_set__addition_location',

            # Old!
            # 'matrix_item__assaysetupsetting_set__setting',
            # 'matrix_item__assaysetupcell_set__cell_sample',
            # 'matrix_item__assaysetupcell_set__density_unit',
            # 'matrix_item__assaysetupcell_set__cell_sample__cell_type__organ',
            # 'matrix_item__assaysetupcompound_set__compound_instance__compound',
            # 'matrix_item__assaysetupcompound_set__concentration_unit',
            # We ought to rely on the group's device and organ model, to be sure?
            # 'matrix_item__device',
            # 'matrix_item__organ_model',

            # Replace with group device and organ_model
            'matrix_item__group__organ_model__device',

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
        study_id = str(data_point.study)

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

        # OLD
        # device = data_point.matrix_item.device.name

        # if data_point.matrix_item.organ_model:
        #     organ_model = data_point.matrix_item.organ_model.name
        # else:
        #     organ_model = '-No MPS Model-'

        # Revised for Group schema
        # Device acquisition may be foolish
        device = data_point.matrix_item.group.organ_model.device.name
        organ_model = data_point.matrix_item.group.organ_model.name

        # TODO TODO TODO: Ought we include the version? It wasn't previously requested

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
        # settings = data_point.matrix_item.stringify_settings()
        # cells = data_point.matrix_item.stringify_cells()
        # compounds = data_point.matrix_item.stringify_compounds()

        # Revised
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
        data[index] = [str(item) for item in current_list]

    string_io = StringIO()
    csv_writer = csv.writer(string_io, dialect=csv.excel)

    # Add the UTF-8 BOM
    data[0][0] = '\ufeff' + data[0][0]

    # Write the lines
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
            data_file_upload_name = str(data_file_upload)
            data_file_upload_url = data_file_upload.file_location

        else:
            data_file_upload_name = ''
            data_file_upload_url = ''

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
        normalize_units=False,
        group_sample_location=True
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

        if not group_sample_location:
            sample_location = ''

        # chip_id = raw.assay_chip_id.chip_setup.assay_chip_id

        time = raw.time / 1440.0

        # replaced = raw.replaced
        excluded = raw.excluded

        # No dynamic quality here
        if value is not None and (include_all or not excluded):
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

    for target, units in list(initial_control_data.items()):
        for unit, tags in list(units.items()):
            for tag, sample_locations in list(tags.items()):
                for sample_location, time_values in list(sample_locations.items()):
                    for time, points in list(time_values.items()):
                        # TODO TODO TODO More than a little crude: PLEASE REVISE THESE NESTED LOOPS SO THAT THEY ARE MORE ROBUST
                        study_values = {}

                        for point in points:
                            if truncate_negative and point.value < 0:
                                study_values.setdefault(point.study_id, []).append(0)
                            elif normalize_units:
                                study_values.setdefault(point.study_id, []).append(point.value * point.study_assay.unit.scale_factor)
                            else:
                                study_values.setdefault(point.study_id, []).append(point.value)

                        for study_id, values in list(study_values.items()):
                            if len(values) > 1:
                                # If geometric mean
                                if mean_type == 'geometric':
                                    # Geometric mean will sometimes fail (due to zero values and so on)
                                    average = gmean(values)
                                    if np.isnan(average):
                                        return {
                                            'errors': 'Geometric mean could not be calculated (probably due to negative values), please use an arithmetic mean instead.'
                                        }
                                # Median
                                elif mean_type == 'median':
                                    average = np.median(values)
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
# NOTE: The compound_post_filters are only present in charting because they are only needed when making compound legends
def get_item_groups(study, criteria, groups=None, matrix_items=None, compound_profile=False, matrix_item_compound_post_filters=None):
    treatment_groups = {}
    setup_to_treatment_group = {}
    header_keys = []

    # In theory, we could generate the tuple for each item
    # It would be more efficient to generate the group comparison tuples separately, however
    # An interesting, albeit maybe not all that terrible, consequence is that we will stitch together the groups quick dictionary and the matrix_items
    # The Group cannot acquire the Matrix, after all
    group_treatment_groups = {}
    group_id_to_setup_tuple = {}

    setups = groups.prefetch_related(
        # Needed if we are going to get device from group in lieu of item
        # 'organ_model__device',
        # Prefetch to acquire names quickly
        'organ_model',
        'organ_model_protocol',
        'assaygroupsetting_set__setting',
        'assaygroupsetting_set__addition_location',
        'assaygroupsetting_set__unit',
        'assaygroupcell_set__cell_sample__cell_subtype',
        'assaygroupcell_set__cell_sample__cell_type__organ',
        'assaygroupcell_set__density_unit',
        'assaygroupcell_set__addition_location',
        'assaygroupcompound_set__compound_instance__compound',
        'assaygroupcompound_set__compound_instance__supplier',
        'assaygroupcompound_set__concentration_unit',
        'assaygroupcompound_set__addition_location',
        # SOMEWHAT FOOLISH
        'study__group__center_groups',
    )

    # Again, a bit foolish
    matrix_items = matrix_items.prefetch_related(
        'matrix__study',
        'device',
    )

    if not criteria:
        criteria = {
            'setup': DEFAULT_SETUP_CRITERIA,
            'setting': DEFAULT_SETTING_CRITERIA,
            'compound': DEFAULT_COMPOUND_CRITERIA,
            'cell': DEFAULT_CELL_CRITERIA,
            # CONTRIVED
            'item': []
        }

    # TODO TODO TODO REVISE THESE MAGIC KEYS
    if criteria.get('item', ''):
        # Could get this from group in theory
        if 'device_id' in criteria.get('item'):
            header_keys.append('Device')
    if criteria.get('setup', ''):
        # Could get device here
        # if 'organ_model__device_id' in criteria.get('setup'):
        #     header_keys.append('Device')
        if 'organ_model_id' in criteria.get('setup'):
            header_keys.append('MPS Model')
        if 'organ_model_protocol_id' in criteria.get('setup'):
            header_keys.append('MPS Model Version')
        if 'study.group_id' in criteria.get('setup'):
            header_keys.append('MPS User Group')
        if 'study_id' in criteria.get('setup'):
            header_keys.append('Study')
    # Item has redundant fields
    # Interestingly, only the Item has a device for the moment
    # BE SURE THE TWO DO NOT BECOME DIVORCED
    if criteria.get('item', ''):
        # This one is non-negotiable, we can't have matrix come from a group
        if 'matrix_id' in criteria.get('item'):
            header_keys.append('Matrix')
        # Could get this from group in theory
        # if 'device_id' in criteria.get('item'):
        #     header_keys.append('Device')
    if criteria.get('compound', ''):
        header_keys.append('Compounds')
    if criteria.get('cell', ''):
        header_keys.append('Cells')
    if criteria.get('setting', ''):
        header_keys.append('Settings')

    header_keys.append('Items with Same Treatment')

    setup_attribute_getter = tuple_attrgetter(*criteria.get('setup', ['']))
    item_attribute_getter = tuple_attrgetter(*criteria.get('item', ['']))

    for setup in setups:
        treatment_group_tuple = []

        if criteria.get('setup', ''):
            treatment_group_tuple.append(setup_attribute_getter(setup))
        else:
            treatment_group_tuple.append(())

        if criteria.get('setting', ''):
            treatment_group_tuple.append(setup.devolved_settings(criteria.get('setting')))
        else:
            treatment_group_tuple.append(())

        if criteria.get('compound', ''):
            treatment_group_tuple.append(setup.devolved_compounds(criteria.get('compound')))
        else:
            treatment_group_tuple.append(())

        if criteria.get('cell', ''):
            treatment_group_tuple.append(setup.devolved_cells(criteria.get('cell')))
        else:
            treatment_group_tuple.append(())

        treatment_group_tuple = tuple(treatment_group_tuple)

        current_representative = group_treatment_groups.get(treatment_group_tuple, None)

        if current_representative is None:
            current_representative = setup.quick_dic(compound_profile=compound_profile,
            matrix_item_compound_post_filters=matrix_item_compound_post_filters, criteria=criteria)
            group_treatment_groups.update({
                treatment_group_tuple: current_representative
            })

        group_id_to_setup_tuple.update({
            setup.id: treatment_group_tuple
        })

        # current_representative.get('Items with Same Treatment').append(
            # TODO TODO TODO
            # setup.get_hyperlinked_name()
        # )

        # BAD: INEFFICIENT
        # for matrix_item in setup.assaymatrixitem_set.all():
        #     current_representative.get('Items with Same Treatment').append(
        #         matrix_item.get_hyperlinked_name()
        #     )
        #     current_representative.get('item_ids').append(
        #         matrix_item.id
        #     )
        #     current_representative.setdefault('names for items', []).append(
        #         matrix_item.name
        #     )
        #     # NOTE: Not a great idea
        #     setup_to_treatment_group.update({matrix_item.id: current_representative})

    for matrix_item in matrix_items:
        current_group_setup_tuple = group_id_to_setup_tuple.get(matrix_item.group_id)
        current_group_quick_dic = group_treatment_groups.get(current_group_setup_tuple)

        # Somewhat contrived
        if criteria.get('item', ''):
            item_treatment_group_tuple = item_attribute_getter(matrix_item)
        else:
            item_treatment_group_tuple = ()

        # CONCATENATING TUPLES *SHOULD* MAKE A NEW TUPLE
        treatment_group_tuple = current_group_setup_tuple + item_treatment_group_tuple

        current_representative = treatment_groups.get(treatment_group_tuple, None)

        if current_representative is None:
            current_representative = matrix_item.quick_dic(
                current_group_quick_dic
            )
            treatment_groups.update({
                treatment_group_tuple: current_representative
            })

        current_representative.get('Items with Same Treatment').append(
            matrix_item.get_hyperlinked_name()
        )
        current_representative.get('item_ids').append(
            matrix_item.id
        )
        current_representative.setdefault('names for items', []).append(
            matrix_item.name
        )

        # NOTE: Not a great idea
        setup_to_treatment_group.update({matrix_item.id: current_representative})

    # Attempt to sort reasonably
    # TODO SHOULD STUDY BE PLACED HERE?
    sorted_treatment_groups = sorted(
        list(treatment_groups.values()), key=lambda x: (
            x.get('Compounds'),
            x.get('MPS Model'),
            x.get('MPS Model Version'),
            x.get('Cells'),
            x.get('Settings'),
            x.get('Matrix'),
            x.get('Study'),
            x.get('MPS User Group'),
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


# TODO TODO TODO MAKE SURE STUDY NO LONGER REQUIRED
# TODO TODO TODO  CLEAN UP
# TODO WHY ARE THERE SO MANY PARAMS??
# TODO I JUST HAD A GREAT IDEA: ADD MORE PARAMS!!!
def get_data_points_for_charting(
        raw_data,
        key,
        mean_type,
        interval_type,
        number_for_interval,
        percent_control,
        include_all,
        truncate_negative,
        dynamic_excluded,
        criteria=None,
        post_filter=None,
        # MISNOMER
        study=None,
        groups=None,
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
    intermediate_data = {}

    initial_data = {}

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
            normalize_units=normalize_units,
            group_sample_location=group_sample_location
        )

        if controls.get('errors', ''):
            return controls

    # Append the additional_data as necessary
    # Why is this done? It is an expedient way to avoid duplicating data
    if additional_data:
        raw_data.extend(additional_data)

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
        'group', {}
    ).get('assaygroupcompound__compound_instance__compound_id__in', {})

    if post_filter:
        # WARNING THIS MAKES A NUMBER OF ASSUMPTIONS
        matrix_item_compound_post_filters = {
            '__'.join(current_filter.replace('assaygroupcompound__', '').split('__')[:-1]): [
                x for x in post_filter.get('group', {}).get(current_filter, [])
            ] for current_filter in post_filter.get('group', {}) if current_filter.startswith('assaygroupcompound__')
        }

    compound_profile = key == 'dose' or key == 'compound'

    # CLUMSY
    if not groups:
        groups = AssayGroup.objects.filter(study_id__in=study)

    # Organization is assay -> unit -> compound/tag -> field -> time -> value
    treatment_group_representatives, setup_to_treatment_group, header_keys = get_item_groups(
        study,
        criteria,
        groups=groups,
        matrix_items=matrix_items,
        compound_profile=compound_profile,
        # MISNOMER
        matrix_item_compound_post_filters=matrix_item_compound_post_filters
    )

    final_data = {
        'sorted_assays': [],
        'assays': [],
        'heatmap': {
            'matrices': {},
            'values': {}
        },
        'header_keys': header_keys,
        'assay_ids': {}
    }

    assay_ids = final_data.get('assay_ids')

    # Process number_for_interval
    try:
        number_for_interval = float(number_for_interval)
    # EVIL
    except:
        # Default to 1
        number_for_interval = 1

    for raw in raw_data:
        value = raw.value

        study_assay = raw.study_assay
        target = study_assay.target.name
        unit = study_assay.unit.unit
        method = study_assay.method.name

        if group_method:
            target = '{} [{}]'.format(target, method)
            assay_ids.update({
                '{}\n{}'.format(target, unit): {
                    'target': study_assay.target_id,
                    'unit': study_assay.unit_id,
                    'method': study_assay.method_id
                }
            })
        else:
            assay_ids.update({
                '{}\n{}'.format(target, unit): {
                    'target': study_assay.target_id,
                    'unit': study_assay.unit_id
                }
            })

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
        if value is not None and not replaced and (include_all or not dynamic_excluded.get(str(raw.id), excluded)):
            # Get tag for data point
            # If by compound
            if key == 'group':
                # tag = get_list_of_present_compounds(related_compounds_map, raw, ' & ')
                tag = 'Group {}'.format(setup_to_treatment_group.get(matrix_item_id).get('index') + 1)
            elif key == 'compound':
                tag = []

                is_control = True

                current_compound_profile = setup_to_treatment_group.get(matrix_item_id).get('compound_profile')

                for compound in current_compound_profile:
                    # TERRIBLE CONDITIONAL
                    if (compound.get('valid_compound') and
                        compound.get('addition_time') <= raw_time
                        # NO LONGER CONSIDER DURATION
#                        compound.get('addition_time') <= raw_time and
#                        compound.get('addition_time') + compound.get('duration') >= raw_time
                    ):
                        # THIS VALUE IS ALREADY SCALED
                        concentration = compound.get('concentration')
                        tag.append(
                            # May need this to have float minutes, unsure
                            '{} {} {}'.format(
                                compound.get('name'),
                                concentration,
                                compound.get('base_unit')
                            )
                        )

                    is_control = False

                if tag:
                    tag = ' & '.join(tag)
                elif is_control and (post_filter is None or '0' in post_filter_compounds):
                    tag = '-No Compound-'
                else:
                    continue
            elif key == 'dose':
                tag = []
                concentration = 0

                is_control = True

                current_compound_profile = setup_to_treatment_group.get(matrix_item_id).get('compound_profile')

                for compound in current_compound_profile:
                    # TERRIBLE CONDITIONAL
                    if (compound.get('valid_compound') and
                        compound.get('addition_time') <= raw_time
                        # NO LONGER CONSIDER DURATION
#                        compound.get('addition_time') <= raw_time and
#                        compound.get('addition_time') + compound.get('duration') >= raw_time
                    ):
                        # THIS VALUE IS ALREADY SCALED: SEE get_compound_profile
                        concentration += compound.get('concentration')
                        tag.append(
                            # May need this to have float minutes, unsure
                            '{} at D{}H{}M{}'.format(
                                compound.get('name'),
                                int(raw_time / 24 / 60),
                                int(raw_time / 60 % 24),
                                int(raw_time % 60)
                            )
                        )

                    is_control = False

                # CONTRIVED: Set time to concentration AND time
                time = (concentration, time)
                if tag:
                    tag = ' & '.join(tag)
                elif is_control and (post_filter is None or '0' in post_filter_compounds):
                    tag = '-No Compound- at D{}H{}M{}'.format(
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

            if not group_sample_location:
                sample_location = ''

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
    for target, units in list(initial_data.items()):
        for unit, tags in list(units.items()):
            for tag, sample_locations in list(tags.items()):
                for sample_location, time_points in list(sample_locations.items()):
                    for time, points in list(time_points.items()):
                        # TODO TODO TODO More than a little crude: PLEASE REVISE THESE NESTED LOOPS SO THAT THEY ARE MORE ROBUST
                        study_values = {}

                        for point in points:
                            if truncate_negative and point.value < 0:
                                study_values.setdefault(point.study_id, []).append(0)
                            else:
                                study_values.setdefault(point.study_id, []).append(point.value)

                        for study_id, values in list(study_values.items()):
                            if len(values) > 1:
                                # If geometric mean
                                if mean_type == 'geometric':
                                    # Geometric mean will sometimes fail (due to zero values and so on)
                                    average = gmean(values)
                                    if np.isnan(average):
                                        return {'errors': 'Geometric mean could not be calculated (probably due to negative values), please use an arithmetic mean instead.'}
                                # Median
                                elif mean_type == 'median':
                                    average = np.median(values)
                                # If arithmetic mean
                                else:
                                    average = np.mean(values)
                            else:
                                average = values[0]

                            # If standard deviation
                            # NOTE: ONLY STANDARD DEVIATION IS AFFECTED BY number_for_interval
                            if interval_type == 'std':
                                interval = np.std(values) * number_for_interval
                            # IQR
                            elif interval_type == 'iqr':
                                # NOTE THAT THIS IS NOT MULTIPLIED BY number_for_interval
                                interval = iqr(values)
                            # Standard error if not std
                            else:
                                interval = np.std(values) / len(values) ** 0.5

                            average_interval_study_id = (
                                average,
                                interval,
                                study_id
                            )

                            averaged_data.setdefault(
                                target, {}
                            ).setdefault(
                                unit, {}
                            ).setdefault(
                                tag, {}
                            ).setdefault(
                                sample_location, {}
                            ).setdefault(
                                time, []
                            ).append(average_interval_study_id)

    accommodate_sample_location = group_sample_location and len(all_sample_locations) > 1

    for target, units in list(averaged_data.items()):
        for unit, tags in list(units.items()):
            # row_indices = {}
            accommodate_units = len(units) > 1

            if not percent_control:
                # Not converted to percent control
                # Newline is used as a delimiter
                # assay_label = target + '\n' + unit
                assay_label = '{}\n{}'.format(target, unit)
            else:
                # Convert to percent control
                if accommodate_units:
                    current_unit = '%Control from {}'.format(unit)
                else:
                    current_unit = '%Control'
                # Newline is used as a delimiter
                # assay_label = target + '\n' + current_unit
                assay_label = '{}\n{}'.format(target, current_unit)

            current_table = intermediate_data.setdefault(assay_label, [['Time']])
            # row_indices = {}
            current_data = {}
            x_header = []
            y_header = {}
            final_data.get('sorted_assays').append(assay_label)

            for tag, sample_locations in list(tags.items()):
                # TODO: A little naive
                if use_key_discrimination and key_discrimination.get(tag[1], ''):
                    tag = '{} || {}'.format(tag[1], tag[0])
                elif use_key_discrimination:
                    tag = tag[1]

                accommodate_intervals = False
                include_current = False

                for sample_location, time_values in list(sample_locations.items()):
                    if accommodate_sample_location:
                        current_key = '{} || {}'.format(tag, sample_location)
                        accommodate_intervals = False
                        include_current = False

                    else:
                        current_key = tag

                    # all_keys.update({current_key: True})

                    all_values = {}
                    all_intervals = {}

                    for time_concentration, current_values in time_values.items():
                        for value_interval_study_id in current_values:
                            value = value_interval_study_id[0]
                            interval = value_interval_study_id[1]
                            study_id = value_interval_study_id[2]

                            # UGLY NOT DRY
                            # Contrived combination of time and concentration only for dose-response
                            if key == 'dose':
                                concentration = time_concentration[0]
                                time = time_concentration[1]

                                if not percent_control:
                                    all_values.setdefault(concentration, []).append(value)
                                    all_intervals.update({concentration: interval})

                                elif controls.get((study_id, target, unit, sample_location, time), False):
                                    control_value = controls.get((study_id, target, unit, sample_location, time))

                                    # We can not divide by zero
                                    if control_value == 0:
                                        return {
                                            'errors': 'Could not calculate percent control because some control values are zero (divide by zero error).'
                                        }

                                    adjusted_value = (value / control_value) * 100
                                    adjusted_interval = (interval / control_value) * 100

                                    all_values.setdefault(concentration, []).append(adjusted_value)
                                    all_intervals.update({concentration: adjusted_interval})

                            else:
                                time = time_concentration

                                if not percent_control:
                                    all_values.setdefault(time, []).append(value)
                                    all_intervals.update({time: interval})

                                elif controls.get((study_id, target, unit, sample_location, time), False):
                                    control_value = controls.get((study_id, target, unit, sample_location, time))

                                    # We can not divide by zero
                                    if control_value == 0:
                                        return {'errors': 'Could not calculate percent control because some control values are zero (divide by zero error).'}

                                    adjusted_value = (value / control_value) * 100
                                    adjusted_interval = (interval / control_value) * 100

                                    all_values.setdefault(time, []).append(adjusted_value)
                                    all_intervals.update({time: adjusted_interval})

                    for time, values in all_values.items():
                        if len(values) > 1:
                            # If geometric mean
                            if mean_type == 'geometric':
                                # Geometric mean will sometimes fail (due to zero values and so on)
                                average = gmean(values)
                                if np.isnan(average):
                                    return {'errors': 'Geometric mean could not be calculated (probably due to negative values), please use an arithmetic mean instead.'}
                            # Median
                            elif mean_type == 'median':
                                average = np.median(values)
                            # If arithmetic mean
                            else:
                                average = np.mean(values)

                            # If standard deviation
                            # NOTE: ONLY STANDARD DEVIATION IS AFFECTED BY number_for_interval
                            if interval_type == 'std':
                                interval = np.std(values) * number_for_interval
                            # IQR
                            elif interval_type == 'iqr':
                                # NOTE THAT THIS IS NOT MULTIPLIED BY number_for_interval
                                interval = iqr(values)
                            # Standard error if not std
                            else:
                                interval = np.std(values) / len(values) ** 0.5

                        else:
                            average = values[0]
                            interval = all_intervals[time]

                        current_data.setdefault(current_key, {}).update({time: average})
                        if interval != 0:
                            accommodate_intervals = True
                            current_data.setdefault(current_key+INTERVAL_1_SIGIL, {}).update({time: average - interval})
                            current_data.setdefault(current_key+INTERVAL_2_SIGIL, {}).update({time: average + interval})
                        y_header.update({time: True})
                        include_current = True

                    key_present = current_key in x_header

                    if include_current and not key_present:
                        x_header.append(current_key)

                    # Only include intervals if necessary
                    if accommodate_intervals and include_current and not key_present:
                        x_header.extend([
                            '{}{}'.format(current_key, INTERVAL_1_SIGIL),
                            '{}{}'.format(current_key, INTERVAL_2_SIGIL)
                        ])
                    else:
                        if '{}{}'.format(current_key, INTERVAL_1_SIGIL) in current_data:
                            del current_data['{}{}'.format(current_key, INTERVAL_1_SIGIL)]
                            del current_data['{}{}'.format(current_key, INTERVAL_2_SIGIL)]

            x_header.sort(key=alphanum_key)
            current_table[0].extend(x_header)

            x_header = {x_header[index]: index + 1 for index in range(len(x_header))}

            y_header = list(y_header.keys())
            y_header.sort(key=float)

            for y in y_header:
                current_table.append([y] + [None] * (len(x_header)))

            y_header = {float(y_header[index]): index + 1 for index in range(len(y_header))}

            for x, data_point in list(current_data.items()):
                for y, value in list(data_point.items()):
                    current_table[y_header.get(y)][x_header.get(x)] = value

    final_data.get('sorted_assays').sort(key=lambda s: s.upper())
    final_data['assays'] = [[] for x in range(len(final_data.get('sorted_assays')))]

    for assay, assay_data in list(intermediate_data.items()):
        final_data.get('assays')[final_data.get('sorted_assays').index(assay)] = assay_data

    final_data.update({
        'treatment_groups': treatment_group_representatives
    })

    return final_data


def fetch_data_points(request):
    pre_filter = {}

    post_filter = json.loads(request.POST.get('post_filter', '{}'))
    full_post_filter = json.loads(request.POST.get('full_post_filter', '{}'))

    if request.POST.get('matrix_item', ''):
        matrix_items = AssayMatrixItem.objects.filter(pk=int(request.POST.get('matrix_item')))
        matrix_item = matrix_items[0]
        study = matrix_item.study

        groups = AssayGroup.objects.filter(id=matrix_item.group_id)

        pre_filter.update({
            'matrix_item_id__in': matrix_items
        })
    elif request.POST.get('matrix', ''):
        matrix_item = None
        matrix = AssayMatrix.objects.get(pk=int(request.POST.get('matrix', None)))
        matrix_items = AssayMatrixItem.objects.filter(matrix_id=int(request.POST.get('matrix')))
        study = matrix.study

        groups = AssayGroup.objects.filter(id__in=matrix_items.values_list('group_id', flat=True))

        pre_filter.update({
            'matrix_item_id__in': matrix_items
        })
    elif request.POST.get('study', ''):
        matrix_item = None
        study = AssayStudy.objects.get(pk=int(request.POST.get('study', None)))
        matrix_items = AssayMatrixItem.objects.filter(study_id=study.id)

        groups = AssayGroup.objects.filter(
            study_id=study.id
        )

        pre_filter.update({
            'matrix_item_id__in': matrix_items
        })
    elif request.POST.get('group', ''):
        matrix_item = None
        group = AssayGroup.objects.get(pk=int(request.POST.get('group', None)))
        matrix_items = AssayMatrixItem.objects.filter(group_id=int(request.POST.get('group')))
        study = group.study

        # Contrived
        groups = AssayGroup.objects.filter(
            id=group.id
        )

        pre_filter.update({
            'matrix_item_id__in': matrix_items
        })
    elif request.POST.get('file', ''):
        matrix_item = None
        current_file = AssayDataFileUpload.objects.get(pk=int(request.POST.get('file', None)))
        # TERRIBLE TERRIBLE TERRIBLE
        matrix_items = AssayMatrixItem.objects.filter(assaydatapoint__data_file_upload_id=int(request.POST.get('file'))).distinct()
        study = current_file.study

        groups = AssayGroup.objects.filter(id__in=matrix_items.values_list('group_id', flat=True))

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
        study_id=study.id
    )

    # TODO: BAD, CONTRIVED
    # groups = AssayGroup.objects.filter(
    #     study_id=study.id
    # )

    # UGLY NOT DRY
    if not post_filter:
        assays = assays.prefetch_related(
            'target',
            'method'
        )

        post_filter = acquire_post_filter(studies, assays, groups, matrix_items, data_points)
    else:
        studies, assays, groups, matrix_items, data_points = apply_post_filter(
            full_post_filter, post_filter, studies, assays, groups, matrix_items, data_points
        )

    data = get_data_points_for_charting(
        data_points,
        request.POST.get('key', ''),
        request.POST.get('mean_type', ''),
        request.POST.get('interval_type', ''),
        request.POST.get('number_for_interval', ''),
        request.POST.get('percent_control', ''),
        request.POST.get('include_all', ''),
        request.POST.get('truncate_negative', ''),
        json.loads(request.POST.get('dynamic_excluded', '{}')),
        study=studies,
        groups=groups,
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
    number_for_interval = request.POST.get('number_for_interval', '')

    this_study = AssayStudy.objects.get(pk=int(study))

    # Very odd, but expedient
    studies = AssayStudy.objects.filter(id=this_study.id)
    # Likewise: please revise get_data_points_for_charting
    groups = AssayGroup.objects.filter(study_id=this_study.id)
    matrix_items = AssayMatrixItem.objects.filter(study_id=this_study.id)

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
            number_for_interval,
            percent_control,
            include_all,
            truncate_negative,
            dynamic_quality,
            study=studies,
            groups=groups,
            matrix_items=matrix_items,
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
    # Contrived!
    studies = AssayStudy.objects.filter(id=study.id)
    data = {}

    post_filter = json.loads(request.POST.get('post_filter', '{}'))
    full_post_filter = json.loads(request.POST.get('full_post_filter', '{}'))
    criteria = json.loads(request.POST.get('criteria', '{}'))

    item_id_filter = json.loads(request.POST.get('item_ids', '[]'))
    target_id_filter = request.POST.get('target_id', '')
    unit_id_filter = request.POST.get('unit_id', '')
    sample_location_id_filter = request.POST.get('sample_location_id', '')
    method_id_filter = request.POST.get('method_id', '')

    # If chip data
    matrix_items = AssayMatrixItem.objects.filter(
        study_id=study.id
    )

    if item_id_filter and any(item_id_filter):
        item_id_filter = [int(x) for x in item_id_filter]
        matrix_items = matrix_items.filter(id__in=item_id_filter)

    assays = AssayStudyAssay.objects.filter(study_id=study.id)

    if target_id_filter:
        assays = assays.filter(
            target_id=int(target_id_filter),
            unit__base_unit_id=int(unit_id_filter)
        ) | assays.filter(
            target_id=int(target_id_filter),
            unit_id=int(unit_id_filter)
        )

    if method_id_filter:
        assays = assays.filter(method_id=method_id_filter)

    # TODO: BAD, CONTRIVED
    # This is fine because we need everything for the study anyway
    groups = AssayGroup.objects.filter(
        study_id=study.id
    )

    # If there are item filters, they must have a upstream effect on groups
    if item_id_filter and any(item_id_filter):
        groups = groups.filter(assaymatrixitem__id__in=matrix_items).distinct()

    data_points = AssayDataPoint.objects.filter(
        study_id=study.id
    ).prefetch_related(
    # TODO optimize prefetch!
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

    # CRUDE
    # In theory, these things could be accomplished by modifying the post_filter?
    # Must apply matrix item filter
    if item_id_filter and any(item_id_filter):
        data_points = data_points.filter(matrix_item_id__in=matrix_items)
    if target_id_filter or method_id_filter:
        data_points = data_points.filter(study_assay_id__in=assays)
    if sample_location_id_filter:
        data_points = data_points.filter(sample_location_id=sample_location_id_filter)

    if not post_filter:
        assays = assays.prefetch_related(
            'target',
            'method'
        )

        post_filter = acquire_post_filter(studies, assays, groups, matrix_items, data_points)

        # SEE KLUDGE ABOVE
        # THIS IS FOR JUMPING TO A STUDY FROM INTERSTUDY REPRO
        # THE IDEA IS THAT IT IS SUPPOSED TO TRIM TO THE "RELEVENT" DATA
        # Obviously, one needs to make sure it is not superfluously run
        # if item_id_filter or target_id_filter:
        #     # CONTRIVANCE
        #     full_post_filter = copy.deepcopy(post_filter)

        #     studies, assays, groups, matrix_items, data_points = apply_post_filter(
        #         full_post_filter, post_filter, studies, assays, groups, matrix_items, data_points
        #     )
        #     # DUMB BUT EXPEDIENT
        #     # TODO REVISE
        #     # WHY DO I DO THIS? BECAUSE APPLYING FILTER DESTROYS PARTS OF THE POST FILTER
        #     # post_filter = acquire_post_filter(studies, assays, groups, matrix_items, data_points)
        #     # Deep copy the deep copy
        #     post_filter = copy.deepcopy(full_post_filter)
    else:
        studies, assays, groups, matrix_items, data_points = apply_post_filter(
            full_post_filter, post_filter, studies, assays, groups, matrix_items, data_points
        )

    # Boolean
    # include_all = self.request.GET.get('include_all', False)
    # chip_data = get_data_as_list_of_lists(matrix_items, include_header=True, include_all=False, data_points=data_points)

    # OLD
    # repro_data = get_repro_data(chip_data)
    # Organization is assay -> unit -> compound/tag -> field -> time -> value
    treatment_group_representatives, setup_to_treatment_group, treatment_header_keys = get_item_groups(
        None,
        criteria,
        groups=groups,
        matrix_items=matrix_items,
    )

    repro_data = []

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
            '{}'.format(len(data_point_treatment_groups) + 1)
        )
        point.data_group = current_group
        if current_group not in treatment_group_table:
            if point.study_assay.unit.base_unit_id:
                treatment_group_table.update({
                    current_group: [str(x) for x in list(
                        data_point_attribute_getter_base_values(point)
                    ) + [setup_to_treatment_group.get(item_id).get('index')]]
                })
            else:
                treatment_group_table.update({
                    current_group: [str(x) for x in list(
                        data_point_attribute_getter_current_values(point)
                    ) + [setup_to_treatment_group.get(item_id).get('index')]]
                })

        data_group_to_studies.setdefault(
            current_group, {}
        ).update({
            '<a href="{}" target="_blank">{} ({})</a>'.format(point.study.get_absolute_url(), point.study.name, point.study.group.name): point.study.name
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

    repro_data.append([
        'Study ID',
        # Contrived name
        'Chip ID',
        'Time',
        'Value',
        # NAME THIS SOMETHING ELSE
        'Treatment Group'
    ])

    for point in data_points:
        repro_data.append([
            point.study.name,
            point.matrix_item.name,
            point.time,
            point.standard_value,
            point.data_group
        ])

    # TODO REVISE
    intra_data_table = get_repro_data(
        len(treatment_group_table),
        repro_data
    )

    # TODO REVISE
    if intra_data_table.get('errors', ''):
        return intra_data_table

    gas_list = intra_data_table['reproducibility_results_table']['data']
    data['gas_list'] = gas_list

    mad_list = {}
    cv_list = {}
    chip_list = {}
    comp_list = {}
    for x in range(len(intra_data_table) - 1):
        # mad_list
        mad_list[x + 1] = {'columns': intra_data_table[x]['mad_score_matrix']['columns']}
        for y in range(len(intra_data_table[x]['mad_score_matrix']['index'])):
            intra_data_table[x]['mad_score_matrix']['data'][y].insert(0, intra_data_table[x]['mad_score_matrix']['index'][y])
        mad_list[x + 1]['data'] = intra_data_table[x]['mad_score_matrix']['data']
        # cv_list
        if intra_data_table[x].get('comp_ICC_Value'):
            cv_list[x + 1] = [['Time', 'CV (%)']]
            for y in range(len(intra_data_table[x]['CV_array']['index'])):
                intra_data_table[x]['CV_array']['data'][y].insert(0, intra_data_table[x]['CV_array']['index'][y])
            for entry in intra_data_table[x]['CV_array']['data']:
                cv_list[x + 1].append(entry)
        # chip_list
        intra_data_table[x]['cv_chart']['columns'].insert(0, "Time (days)")
        chip_list[x + 1] = [intra_data_table[x]['cv_chart']['columns']]
        for y in range(len(intra_data_table[x]['cv_chart']['index'])):
            intra_data_table[x]['cv_chart']['data'][y].insert(0, intra_data_table[x]['cv_chart']['index'][y])
        for z in range(len(intra_data_table[x]['cv_chart']['data'])):
            chip_list[x + 1].append(intra_data_table[x]['cv_chart']['data'][z])
        # comp_list
        if intra_data_table[x].get('comp_ICC_Value'):
            comp_list[x + 1] = []
            for y in range(len(intra_data_table[x]['comp_ICC_Value']['Chip ID'])):
                comp_list[x + 1].insert(y, [])
                comp_list[x + 1][y].append(intra_data_table[x]['comp_ICC_Value']['Chip ID'][y])
                comp_list[x + 1][y].append(intra_data_table[x]['comp_ICC_Value']['ICC Absolute Agreement'][y])
                comp_list[x + 1][y].append(intra_data_table[x]['comp_ICC_Value']['Missing Data Points'][y])

    data['mad_list'] = mad_list

    data['cv_list'] = cv_list

    data['chip_list'] = chip_list

    data['comp_list'] = comp_list

    # Get pie chart data
    excellent_counter = acceptable_counter = poor_counter = 0

    for x in range(0, len(data['gas_list'])):
        if not data['gas_list'][x][7]:
            continue
        if data['gas_list'][x][7][0] == 'E':
            excellent_counter += 1
        elif data['gas_list'][x][7][0] == 'A':
            acceptable_counter += 1
        elif data['gas_list'][x][7][0] == 'P':
            poor_counter += 1

    data['pie'] = [excellent_counter, acceptable_counter, poor_counter]

    data['data_groups'] = treatment_group_table

    final_data_group_to_sample_locations = {}
    for data_group, current_sample_location in list(data_group_to_sample_locations.items()):
        final_data_group_to_sample_locations[data_group] = sorted(current_sample_location)

    final_data_group_to_organ_models = {}
    for data_group, current_organ_model in list(data_group_to_organ_models.items()):
        final_data_group_to_organ_models[data_group] = sorted(current_organ_model)

    data['data_group_to_sample_locations'] = final_data_group_to_sample_locations
    data['data_group_to_organ_models'] = final_data_group_to_organ_models

    data['header_keys'] = {
        'treatment': treatment_header_keys,
        'data': data_header_keys
    }

    data['treatment_groups'] = treatment_group_representatives

    data['post_filter'] = post_filter

    return HttpResponse(json.dumps(data),
                        content_type='application/json')


# NAIVE: REQUIRES REVISION
def fetch_pre_submission_filters(request):
    current_filters = json.loads(request.POST.get('filters', '{}'))

    accessible_studies = get_user_accessible_studies(request.user)

    if current_filters.get('studies', None) is not None:
        accessible_studies = accessible_studies.filter(
            pbpk_steady_state=True
        ) | accessible_studies.filter(
            pbpk_bolus=True
        )

    # Notice EXCLUSION of items without organ models
    accessible_groups = AssayGroup.objects.filter(
        study__in=accessible_studies
    ).prefetch_related(
        'organ_model__organ'
    )

    # Please note exclusion of null organ model here
    organ_models = sorted(list(set([
        (
            group.organ_model_id,
            '{} ({})'.format(
                group.organ_model.name,
                group.organ_model.organ,
            )
        ) for group in accessible_groups
    ])), key=lambda x: x[1])

    organ_model_ids = {organ_model[0]: True for organ_model in organ_models}

    groups = {}
    targets = {}
    compounds = {}
    studies = {}
    data = {}

    number_of_points = 0
    # TODO TODO TODO
    number_of_studies = 0
    number_of_centers = 0
    if current_filters.get('organ_models', []):
        new_organ_model_ids = [int(id) for id in current_filters.get('organ_models', []) if int(id) in organ_model_ids]

        # In case changes in filters eliminate all organ models
        if new_organ_model_ids:
            organ_model_ids = new_organ_model_ids
    else:
        organ_model_ids = []

    accessible_groups = accessible_groups.filter(
        organ_model_id__in=organ_model_ids
    )

    accessible_studies = accessible_studies.filter(
        id__in=list(accessible_groups.values_list('study_id', flat=True))
    )

    # TERRIBLE NAME
    # CONFUSING: SHOULD BE STUDY_GROUP OR SOMETHING?!
    groups = sorted(list(set([
        (study.group_id, study.group.name) for study in
        accessible_studies
    ])), key=lambda x: x[1])

    group_ids = {group[0]: True for group in groups}

    if current_filters.get('groups', []):
        group_ids = [int(id) for id in current_filters.get('groups', []) if int(id) in group_ids]
    else:
        group_ids = []

    accessible_studies = accessible_studies.filter(
        # In retrospect, somewhat frustrating double-meaning of "group"
        group_id__in=group_ids,
    )

    accessible_groups = accessible_groups.filter(
        study__in=accessible_studies
    )

    accessible_matrix_items = AssayMatrixItem.objects.filter(
        group__in=accessible_groups
    )

    if current_filters.get('studies', None) is None:
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

    accessible_compounds = AssayGroupCompound.objects.filter(
        group__in=accessible_groups
    ).prefetch_related(
        'compound_instance__compound'
    )

    compounds = sorted(list(set([
        (compound.compound_instance.compound_id, compound.compound_instance.compound.name) for compound in
        accessible_compounds
    ])), key=lambda x: x[1])

    # Check to see whether to include no compounds
    include_no_compounds = accessible_groups.filter(
        assaygroupcompound__isnull=True
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

        # TODO Only take Compounds that correspond to a Target, and ignore No Compound
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
        accessible_groups = accessible_groups.filter(
            assaygroupcompound__compound_instance__compound_id__in=compound_ids
        ) | accessible_groups.filter(
            assaygroupcompound__isnull=True
        )
    else:
        accessible_groups = accessible_groups.filter(
            assaygroupcompound__compound_instance__compound_id__in=compound_ids
        )

    # Acquisition of studies (odd FOR PBPK ONLY)
    if current_filters.get('studies', None) is not None:
        relevant_study_ids = list(set(list(accessible_groups.values_list('study_id', flat=True))))

        accessible_studies = accessible_studies.filter(
            id__in=relevant_study_ids
        )

        studies = sorted(list(set([
            (study.id, str(study)) for study in
            accessible_studies
        ])), key=lambda x: x[1])

        study_ids = {study[0]: True for study in studies}

        if current_filters.get('studies', []):
            study_ids = [int(id) for id in current_filters.get('studies', []) if int(id) in study_ids]
        else:
            study_ids = []

        accessible_groups = accessible_groups.filter(
            study_id__in=study_ids
        )

    accessible_matrix_items = accessible_matrix_items.filter(
        group__in=accessible_groups
    )

    if current_filters.get('studies', None) is not None:
        number_of_points = AssayDataPoint.objects.filter(
            matrix_item__in=accessible_matrix_items,
            replaced=False,
            excluded=False,
            value__isnull=False
        ).count()

        data = {
            'filters': {
                'groups': groups,
                'organ_models': organ_models,
                'compounds': compounds,
                'studies': studies,
            },
            'number_of_points': number_of_points
        }
    else:
        number_of_points = AssayDataPoint.objects.filter(
            matrix_item_id__in=accessible_matrix_items,
            study_assay_id__in=accessible_study_assays,
            replaced=False,
            excluded=False,
            value__isnull=False
        ).count()

        data = {
            'filters': {
                'groups': groups,
                'organ_models': organ_models,
                'targets': targets,
                'compounds': compounds,
            },
            'number_of_points': number_of_points
        }

    return HttpResponse(
        json.dumps(data),
        content_type='application/json'
    )


# TODO RATHER VERBOSE
# TODO: MAKE SURE GROUP STUFF WORKS CORRECTLY
# Would have been a good idea to have methods for each model defining this
def acquire_post_filter(studies, assays, groups, matrix_items, data_points):
    # Table -> Filter -> value -> [name, in_use]
    post_filter = {}

    studies = studies.prefetch_related(
        'group__center_groups'
    )

    # Used downstream for variable displays
    studies_count = studies.count()

    for study in studies:
        current = post_filter.setdefault(
            'study', {}
        )

        current.setdefault(
            'id__in', {}
        ).update({
            study.id: '{} ({})'.format(study.name, study.group.name)
        })

        current.setdefault(
            'group_id__in', {}
        ).update({
            study.group_id: '{} ({})'.format(study.group.name, study.group.center_groups.first().name)
        })

    assays = assays.prefetch_related(
        'target',
        'method',
        # SLOPPY
        'unit__base_unit'
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

        # Tricky! Not actually in filter list...
        current.setdefault(
            'unit_id__in', {}
        ).update({
            assay.unit.id: assay.unit.unit
        })
        # EVEN TRICKIER
        if assay.unit.base_unit_id:
            current.setdefault(
                'unit_id__in', {}
            ).update({
                assay.unit.base_unit_id: assay.unit.base_unit.unit
            })

    # Contrived: Add no compounds
    post_filter.setdefault('group', {}).setdefault(
        'assaygroupcompound__compound_instance__compound_id__in', {}
    ).update({
        0: NO_COMPOUNDS_STRING
    })

    # Contrived: Add no cells
    post_filter.setdefault('group', {}).setdefault(
        'assaygroupcell__cell_sample_id__in', {}
    ).update({
        0: '-No Cells-'
    })

    # Contrived: Add no settings
    post_filter.setdefault('group', {}).setdefault(
        'assaygroupsetting__setting_id__in', {}
    ).update({
        0: '-No Settings-'
    })

    # Groups here
    groups = groups.prefetch_related(
        'assaygroupcompound_set__compound_instance__compound',
        'assaygroupcompound_set__compound_instance__supplier',
        'assaygroupcompound_set__concentration_unit',
        'assaygroupcompound_set__addition_location',
        'assaygroupcell_set__cell_sample__cell_type__organ',
        'assaygroupcell_set__cell_sample__cell_subtype',
        'assaygroupcell_set__cell_sample__supplier',
        'assaygroupcell_set__addition_location',
        'assaygroupcell_set__density_unit',
        'assaygroupsetting_set__setting',
        'assaygroupsetting_set__unit',
        'assaygroupsetting_set__addition_location',
    )

    for group in groups:
        current = post_filter.setdefault('group', {})

        # We really ought not manually add these
        current.setdefault(
            'organ_model_id__in', {}
        ).update({
            group.organ_model_id: group.organ_model.name
        })

        # Maybe this is better in items?
        # Rather ugly, to be honest (not even workable with a "getter")
        # current.setdefault(
        #     'organ_model__device_id__in', {}
        # ).update({
        #     group.organ_model__device_id: group.organ_model__device.name
        # })

        # THE TRICKY PART OF THIS IS THAT NOT ALL GROUPS HAVE PROTOCOLS
        # Worse still, the definition of a protocol is likely in flux
        if group.organ_model_protocol:
            current.setdefault(
                'organ_model_protocol_id__in', {}
            ).update({
                group.organ_model_protocol_id: group.organ_model_protocol.name
            })
        else:
            current.setdefault(
                'organ_model_protocol_id__in', {}
            ).update({
                # AVOID MAGIC STRINGS, PLEASE
                0: '-No MPS Model Version-'
            })

        # Begin iteration of components
        for compound in group.assaygroupcompound_set.all():
            current.setdefault(
                'assaygroupcompound__compound_instance__compound_id__in', {}
            ).update({
                compound.compound_instance.compound_id : compound.compound_instance.compound.name
            })

            current.setdefault(
                'assaygroupcompound__compound_instance__supplier_id__in', {}
            ).update({
                compound.compound_instance.supplier_id: compound.compound_instance.supplier.name
            })

            current.setdefault(
                'assaygroupcompound__compound_instance__lot__in', {}
            ).update({
                compound.compound_instance.lot: compound.compound_instance.lot
            })

            # SPECIAL EXCEPTION, CONCENTRATION AND UNITS ARE COMBINED
            current.setdefault(
                'assaygroupcompound__concentration__in', {}
            ).update({
                compound.concentration: compound.concentration
            })
            current.setdefault(
                'assaygroupcompound__concentration_unit_id__in', {}
            ).update({
                compound.concentration_unit_id: compound.concentration_unit_id
            })

            current.setdefault(
                'assaygroupcompound__concentration__concentration_unit_id__in', {}
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
                'assaygroupcompound__addition_time__in', {}
            ).update({
                compound.addition_time: compound.get_addition_time_string()
            })

            current.setdefault(
                'assaygroupcompound__duration__in', {}
            ).update({
                compound.duration: compound.get_duration_string()
            })

            current.setdefault(
                'assaygroupcompound__addition_location_id__in', {}
            ).update({
                compound.addition_location_id: compound.addition_location.name
            })

        for cell in group.assaygroupcell_set.all():
            current.setdefault(
                'assaygroupcell__cell_sample_id__in', {}
            ).update({
                cell.cell_sample_id: str(cell.cell_sample)
            })

            current.setdefault(
                'assaygroupcell__cell_sample__cell_type_id__in', {}
            ).update({
                cell.cell_sample.cell_type_id: cell.cell_sample.cell_type.cell_type
            })

            current.setdefault(
                'assaygroupcell__cell_sample__cell_subtype_id__in', {}
            ).update({
                cell.cell_sample.cell_subtype_id: cell.cell_sample.cell_subtype.cell_subtype
            })

            current.setdefault(
                'assaygroupcell__biosensor_id__in', {}
            ).update({
                cell.biosensor_id: cell.biosensor.name
            })

            current.setdefault(
                'assaygroupcell__passage__in', {}
            ).update({
                cell.passage: cell.passage
            })

            # SPECIAL EXCEPTION, DENSITY AND UNITS ARE COMBINED
            current.setdefault(
                'assaygroupcell__density__in', {}
            ).update({
                cell.density: cell.density
            })
            current.setdefault(
                'assaygroupcell__density_unit_id__in', {}
            ).update({
                cell.density_unit_id: cell.density_unit_id
            })

            # THIS NEEDS TO BE REMOVED BEFORE ACTUAL FILTERS ARE APPLIED
            current.setdefault(
                'assaygroupcell__density__density_unit_id__in', {}
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
                'assaygroupcell__addition_location_id__in', {}
            ).update({
                cell.addition_location_id: cell.addition_location.name
            })

            # NOTE NO ADDITION TIME FOR CELLS AT THE MOMENT

        for setting in group.assaygroupsetting_set.all():
            current.setdefault(
                'assaygroupsetting__setting_id__in', {}
            ).update({
                setting.setting_id: setting.setting.name
            })

            # SPECIAL EXCEPTION, VALUE AND UNITS ARE COMBINED
            current.setdefault(
                'assaygroupsetting__value__in', {}
            ).update({
                setting.value: setting.value
            })
            current.setdefault(
                'assaygroupsetting__unit_id__in', {}
            ).update({
                setting.unit_id: setting.unit_id
            })

            current.setdefault(
                'assaygroupsetting__value__unit_id__in', {}
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
                'assaygroupsetting__addition_time__in', {}
            ).update({
                setting.addition_time: setting.get_addition_time_string()
            })

            current.setdefault(
                'assaygroupsetting__duration__in', {}
            ).update({
                setting.duration: setting.get_duration_string()
            })

            current.setdefault(
                'assaygroupsetting__addition_location_id__in', {}
            ).update({
                setting.addition_location_id: setting.addition_location.name
            })

    matrix_items = matrix_items.prefetch_related(
        # Interesting and unfortunate prefetch
        # Don't want to cause an N+1
        'study',
        'matrix',
        'device',
    )

    for matrix_item in matrix_items:
        current = post_filter.setdefault('matrix_item', {})

        # Only show the study name if necessary
        if studies_count > 1:
            current.setdefault(
                'id__in', {}
            ).update({
                matrix_item.id: '{} ({})'.format(matrix_item.name, matrix_item.study.name)
            })
        else:
            current.setdefault(
                'id__in', {}
            ).update({
                matrix_item.id: '{}'.format(matrix_item.name)
            })

        # Surely a more elegant way to do this
        # If is a plate and there are more than one study, specify the study it is from
        if matrix_item.matrix.representation == 'plate' and studies_count > 1:
            current.setdefault(
                'matrix_id__in', {}
            ).update({
                matrix_item.matrix_id: '{} ({})'.format(matrix_item.matrix.name, matrix_item.study.name)
            })
        # If it is a plate and there is just one study
        elif matrix_item.matrix.representation == 'plate':
            current.setdefault(
                'matrix_id__in', {}
            ).update({
                matrix_item.matrix_id: '{}'.format(matrix_item.matrix.name)
            })
        # If it is a chip set
        else:
            current.setdefault(
                'matrix_id__in', {}
            ).update({
                matrix_item.matrix_id: 'Chips for {}'.format(matrix_item.study.name)
            })

        current.setdefault(
            'device_id__in', {}
        ).update({
            matrix_item.device_id: matrix_item.device.name
        })

        # REMOVED
        # if matrix_item.organ_model_id:
        #     current.setdefault(
        #         'organ_model_id__in', {}
        #     ).update({
        #         matrix_item.organ_model_id: matrix_item.organ_model.name
        #     })

        # for compound in matrix_item.assaysetupcompound_set.all():
        #     current.setdefault(
        #         'assaysetupcompound__compound_instance__compound_id__in', {}
        #     ).update({
        #         compound.compound_instance.compound_id : compound.compound_instance.compound.name
        #     })

        #     current.setdefault(
        #         'assaysetupcompound__compound_instance__supplier_id__in', {}
        #     ).update({
        #         compound.compound_instance.supplier_id: compound.compound_instance.supplier.name
        #     })

        #     current.setdefault(
        #         'assaysetupcompound__compound_instance__lot__in', {}
        #     ).update({
        #         compound.compound_instance.lot: compound.compound_instance.lot
        #     })

        #     # SPECIAL EXCEPTION, CONCENTRATION AND UNITS ARE COMBINED
        #     current.setdefault(
        #         'assaysetupcompound__concentration__in', {}
        #     ).update({
        #         compound.concentration: compound.concentration
        #     })
        #     current.setdefault(
        #         'assaysetupcompound__concentration_unit_id__in', {}
        #     ).update({
        #         compound.concentration_unit_id: compound.concentration_unit_id
        #     })

        #     current.setdefault(
        #         'assaysetupcompound__concentration__concentration_unit_id__in', {}
        #     ).update({
        #         '{}{}{}'.format(
        #             compound.concentration,
        #             COMBINED_VALUE_DELIMITER,
        #             compound.concentration_unit_id
        #         ): '{}{}{}'.format(
        #             compound.concentration,
        #             COMBINED_VALUE_DELIMITER,
        #             compound.concentration_unit
        #         )
        #     })

        #     current.setdefault(
        #         'assaysetupcompound__addition_time__in', {}
        #     ).update({
        #         compound.addition_time: compound.get_addition_time_string()
        #     })

        #     current.setdefault(
        #         'assaysetupcompound__duration__in', {}
        #     ).update({
        #         compound.duration: compound.get_duration_string()
        #     })

        #     current.setdefault(
        #         'assaysetupcompound__addition_location_id__in', {}
        #     ).update({
        #         compound.addition_location_id: compound.addition_location.name
        #     })

        # for cell in matrix_item.assaysetupcell_set.all():
        #     current.setdefault(
        #         'assaysetupcell__cell_sample_id__in', {}
        #     ).update({
        #         cell.cell_sample_id: str(cell.cell_sample)
        #     })

        #     current.setdefault(
        #         'assaysetupcell__cell_sample__cell_type_id__in', {}
        #     ).update({
        #         cell.cell_sample.cell_type_id: cell.cell_sample.cell_type.cell_type
        #     })

        #     current.setdefault(
        #         'assaysetupcell__cell_sample__cell_subtype_id__in', {}
        #     ).update({
        #         cell.cell_sample.cell_subtype_id: cell.cell_sample.cell_subtype.cell_subtype
        #     })

        #     current.setdefault(
        #         'assaysetupcell__biosensor_id__in', {}
        #     ).update({
        #         cell.biosensor_id: cell.biosensor.name
        #     })

        #     current.setdefault(
        #         'assaysetupcell__passage__in', {}
        #     ).update({
        #         cell.passage: cell.passage
        #     })

        #     # SPECIAL EXCEPTION, DENSITY AND UNITS ARE COMBINED
        #     current.setdefault(
        #         'assaysetupcell__density__in', {}
        #     ).update({
        #         cell.density: cell.density
        #     })
        #     current.setdefault(
        #         'assaysetupcell__density_unit_id__in', {}
        #     ).update({
        #         cell.density_unit_id: cell.density_unit_id
        #     })

        #     # THIS NEEDS TO BE REMOVED BEFORE ACTUAL FILTERS ARE APPLIED
        #     current.setdefault(
        #         'assaysetupcell__density__density_unit_id__in', {}
        #     ).update({
        #         '{}{}{}'.format(
        #             cell.density,
        #             COMBINED_VALUE_DELIMITER,
        #             cell.density_unit_id
        #         ): '{}{}{}'.format(
        #             cell.density,
        #             COMBINED_VALUE_DELIMITER,
        #             cell.density_unit
        #         )
        #     })

        #     current.setdefault(
        #         'assaysetupcell__addition_location_id__in', {}
        #     ).update({
        #         cell.addition_location_id: cell.addition_location.name
        #     })

        #     # NOTE NO ADDITION TIME FOR CELLS AT THE MOMENT

        # for setting in matrix_item.assaysetupsetting_set.all():
        #     current.setdefault(
        #         'assaysetupsetting__setting_id__in', {}
        #     ).update({
        #         setting.setting_id: setting.setting.name
        #     })

        #     # SPECIAL EXCEPTION, VALUE AND UNITS ARE COMBINED
        #     current.setdefault(
        #         'assaysetupsetting__value__in', {}
        #     ).update({
        #         setting.value: setting.value
        #     })
        #     current.setdefault(
        #         'assaysetupsetting__unit_id__in', {}
        #     ).update({
        #         setting.unit_id: setting.unit_id
        #     })

        #     current.setdefault(
        #         'assaysetupsetting__value__unit_id__in', {}
        #     ).update({
        #         '{}{}{}'.format(
        #             setting.value,
        #             COMBINED_VALUE_DELIMITER,
        #             setting.unit_id
        #         ): '{}{}{}'.format(
        #             setting.value,
        #             COMBINED_VALUE_DELIMITER,
        #             setting.unit
        #         )
        #     })

        #     current.setdefault(
        #         'assaysetupsetting__addition_time__in', {}
        #     ).update({
        #         setting.addition_time: setting.get_addition_time_string()
        #     })

        #     current.setdefault(
        #         'assaysetupsetting__duration__in', {}
        #     ).update({
        #         setting.duration: setting.get_duration_string()
        #     })

        #     current.setdefault(
        #         'assaysetupsetting__addition_location_id__in', {}
        #     ).update({
        #         setting.addition_location_id: setting.addition_location.name
        #     })

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

        current.setdefault(
            'time__in', {}
        ).update({
            data_point.time: data_point.get_time_string()
        })

    # STUPID, EXPEDIENT
    post_filter = json.loads(json.dumps(post_filter))

    return post_filter


def check_if_filters_diverge(full_post_filter, post_filter, parent_key, keys_to_check=None):
    # Superfluous variable, just for clarity
    divergence = False

    if keys_to_check:
        for key in keys_to_check:
            if len(post_filter.get(parent_key, {}).get(key, [])) != len(full_post_filter.get(parent_key, {}).get(key, [])):
                divergence = True
                return divergence
    else:
        for key in full_post_filter.get(parent_key, []):
            if len(post_filter.get(parent_key, {}).get(key, [])) != len(full_post_filter.get(parent_key, {}).get(key, [])):
                divergence = True
                return divergence

    return divergence


def apply_post_filter(full_post_filter, post_filter, studies, assays, groups, matrix_items, data_points):
    # Not very elegant...
    study_post_filters = {
        current_filter: [
            x for x in post_filter.get('study', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('study', {})
    }

    study_divergence = check_if_filters_diverge(full_post_filter, post_filter, 'study')

    if study_divergence:
        studies = studies.filter(
            **study_post_filters
        )
        groups = groups.filter(
            study_id__in=studies
        )

    assay_post_filters = {
        current_filter: [
            x for x in post_filter.get('assay', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('assay', {})
    }

    assay_divergence = check_if_filters_diverge(full_post_filter, post_filter, 'assay')

    # We might as well chain the filters
    # This way we don't need really awful conditionals
    if assay_divergence:
        assays = assays.filter(
            **assay_post_filters
        )
    if study_divergence:
        assays = assays.filter(
            study_id__in=studies
        )

    # TEST FOR GROUP DIVERGENCES *BEFORE* CHANGING THEM
    compound_divergence = check_if_filters_diverge(full_post_filter, post_filter, 'group', [key for key in post_filter.get('group', {}).keys() if key.startswith('assaygroupcompound__')])

    cell_divergence = check_if_filters_diverge(full_post_filter, post_filter, 'group', [key for key in post_filter.get('group', {}).keys() if key.startswith('assaygroupcell__')])

    setting_divergence = check_if_filters_diverge(full_post_filter, post_filter, 'group', [key for key in post_filter.get('group', {}).keys() if key.startswith('assaygroupsetting__')])

    group_divergence = check_if_filters_diverge(full_post_filter, post_filter, 'group', [key for key in post_filter.get('group', {}).keys() if not key.startswith('assaygroup')])

    # Special exceptions for combined filters
    combined_compounds_data = post_filter.setdefault('group', {}).setdefault(
        'assaygroupcompound__concentration__concentration_unit_id__in', {}
    )

    compound_concentration_filter = {}
    compound_unit_filter = {}
    compound_concentration_filters = []
    compound_unit_filters = []

    for concentration_unit_id in list(combined_compounds_data.keys()):
        concentration_unit_id = concentration_unit_id.split(COMBINED_VALUE_DELIMITER)
        concentration = concentration_unit_id[0]
        unit = concentration_unit_id[1]
        compound_concentration_filter.update({
            concentration: True
        })
        compound_unit_filter.update({
            unit: True
        })
        compound_concentration_filters.append(
            concentration
        )
        compound_unit_filters.append(
            unit
        )

    post_filter.get('group', {}).update({
        'assaygroupcompound__concentration__in': compound_concentration_filter,
        'assaygroupcompound__concentration_unit_id__in': compound_unit_filter
    })

    del post_filter['group']['assaygroupcompound__concentration__concentration_unit_id__in']

    combined_cells_data = post_filter.setdefault('group', {}).setdefault(
        'assaygroupcell__density__density_unit_id__in', {}
    )

    cell_density_filter = {}
    cell_unit_filter = {}
    cell_density_filters = []
    cell_unit_filters = []

    for density_unit_id in list(combined_cells_data.keys()):
        density_unit_id = density_unit_id.split(COMBINED_VALUE_DELIMITER)
        density = density_unit_id[0]
        unit = density_unit_id[1]
        cell_density_filter.update({
            density: True
        })
        cell_unit_filter.update({
            unit: True
        })
        cell_density_filters.append(
            density
        )
        cell_unit_filters.append(
            unit
        )

    post_filter.get('group', {}).update({
        'assaygroupcell__density__in': cell_density_filter,
        'assaygroupcell__density_unit_id__in': cell_unit_filter
    })

    del post_filter['group']['assaygroupcell__density__density_unit_id__in']

    combined_settings_data = post_filter.setdefault('group', {}).setdefault(
        'assaygroupsetting__value__unit_id__in', {}
    )

    setting_value_filter = {}
    setting_unit_filter = {}
    setting_value_filters = []
    setting_unit_filters = []

    for value_unit_id in list(combined_settings_data.keys()):
        value_unit_id = value_unit_id.split(COMBINED_VALUE_DELIMITER)
        value = value_unit_id[0]
        unit = value_unit_id[1]
        setting_value_filter.update({
            value: True
        })
        setting_unit_filter.update({
            unit: True
        })
        setting_value_filters.append(
            value
        )
        setting_unit_filters.append(
            unit
        )

    post_filter.get('group', {}).update({
        'assaygroupsetting__value__in': setting_value_filter,
        'assaygroupsetting__unit_id__in': setting_unit_filter
    })

    del post_filter['group']['assaygroupsetting__value__unit_id__in']

    # Groups somewhat contrived to deal with null compounds
    group_post_filters = {
        current_filter: [
            x for x in post_filter.get('group', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('group', {}) if not current_filter.startswith('assaygroup')
    }

    group_compound_post_filters = {
        current_filter: [
            x for x in post_filter.get('group', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('group', {}) if current_filter.startswith('assaygroupcompound__')
    }

    group_cell_post_filters = {
        current_filter: [
            x for x in post_filter.get('group', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('group', {}) if current_filter.startswith('assaygroupcell__')
    }

    group_setting_post_filters = {
        current_filter: [
            x for x in post_filter.get('group', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('group', {}) if current_filter.startswith('assaygroupsetting__')
    }

    if group_divergence:
        # We remove the organ_model_protocol_id first because it can have nulls
        # IT IS POSSIBLE: To instead have a contrive "-No MPS Model Version-" entry, but this could cause further complications
        # This was made under the assumption that all fields would be non-NULL, which unfortunately was not the case
        organ_model_protocol_id_filter = post_filter.get('group', {}).get('organ_model_protocol_id__in', {})
        # Contrived, somewhat inappropriate
        del group_post_filters['organ_model_protocol_id__in']

        groups = groups.filter(
            **group_post_filters
        )

        # SPECIAL EXCEPTION FOR MPS MODEL VERSION
        # SHOULD BE HANDLED MORE ELEGANTLY
        if organ_model_protocol_id_filter.get('0'):
            groups = groups.filter(organ_model_protocol_id__in=organ_model_protocol_id_filter) | groups.filter(organ_model_protocol__isnull=True)
        else:
            groups = groups.filter(organ_model_protocol_id__in=organ_model_protocol_id_filter)

    # COMBINED FIELDS IF NECESSARY
    # TODO TODO TODO
    # INEFFICIENT REVISE
    # ODD AND CONTRIVED: VIOLATES RO3
    # Compounds
    if compound_divergence:
        group_divergence = True

        compound_total = None
        if compound_concentration_filters:
            compound_total = AssayGroup.objects.none()
            for index in range(len(compound_concentration_filters)):
                compound_total = compound_total | groups.filter(
                    assaygroupcompound__concentration=compound_concentration_filters[index],
                    assaygroupcompound__concentration_unit_id=compound_unit_filters[index]
                )

        if post_filter.get('group', {}).get('assaygroupcompound__compound_instance__compound_id__in', {}).get(
                '0', None
        ):
            if compound_total is not None:
                groups = compound_total.filter(
                    **group_compound_post_filters
                ) | groups.filter(assaygroupcompound__isnull=True)
            else:
                groups = groups.filter(
                    **group_compound_post_filters
                ) | groups.filter(assaygroupcompound__isnull=True)
        else:
            if compound_total is not None:
                groups = compound_total

            groups = groups.filter(
                **group_compound_post_filters
            )

    if cell_divergence:
        group_divergence = True

        cell_total = None
        if cell_density_filters:
            cell_total = AssayGroup.objects.none()
            for index in range(len(cell_density_filters)):
                cell_total = cell_total | groups.filter(
                    assaygroupcell__density=cell_density_filters[index],
                    assaygroupcell__density_unit_id=cell_unit_filters[index]
                )

        if post_filter.get('group', {}).get('assaygroupcell__cell_sample_id__in', {}).get('0', None):
            if cell_total is not None:
                groups = cell_total.filter(
                    **group_cell_post_filters
                ) | groups.filter(assaygroupcell__isnull=True)

            else:
                groups = groups.filter(
                    **group_cell_post_filters
                ) | groups.filter(assaygroupcell__isnull=True)
        else:
            if cell_total is not None:
                groups = cell_total

            groups = groups.filter(
                **group_cell_post_filters
            )

    if setting_divergence:
        group_divergence = True

        setting_total = None
        if setting_value_filters:
            setting_total = AssayGroup.objects.none()
            for index in range(len(setting_value_filters)):
                setting_total = setting_total | groups.filter(
                    assaygroupsetting__value=setting_value_filters[index],
                    assaygroupsetting__unit_id=setting_unit_filters[index]
                )

        if post_filter.get('group', {}).get('assaygroupsetting__setting_id__in', {}).get('0', None):
            if setting_total is not None:
                groups = setting_total.filter(
                    **group_setting_post_filters
                ) | groups.filter(assaygroupsetting__isnull=True)
            else:
                groups = groups.filter(
                    **group_setting_post_filters
                ) | groups.filter(assaygroupsetting__isnull=True)
        else:
            if setting_total is not None:
                groups = setting_total

            groups = groups.filter(
                **group_setting_post_filters
            )

    groups = groups.distinct()

    # Correct matrix item start
    matrix_item_post_filters = {
        current_filter: [
            x for x in post_filter.get('matrix_item', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('matrix_item', {}) if not current_filter.startswith('assaysetup')
    }

    matrix_item_divergence = check_if_filters_diverge(full_post_filter, post_filter, 'matrix_item')

    if study_divergence or group_divergence:
        matrix_item_divergence = True
        matrix_items = matrix_items.filter(group_id__in=groups)

    if matrix_item_divergence:
        matrix_items = matrix_items.filter(
            **matrix_item_post_filters
        )

    data_point_post_filters = {
        current_filter: [
            x for x in post_filter.get('data_point', {}).get(current_filter, [])
        ] for current_filter in post_filter.get('data_point', {})
    }

    data_point_divergence = check_if_filters_diverge(full_post_filter, post_filter, 'data_point')

    # data_points = data_points.filter(
    #     study_id__in=studies,
    #     study_assay_id__in=assays,
    #     matrix_item_id__in=matrix_items,
    # ).filter(
    #     **data_point_post_filters
    # )

    if data_point_divergence:
        data_points = data_points.filter(
            **data_point_post_filters
        )
    if study_divergence:
        data_points = data_points.filter(
            study_id__in=studies,
        )
    if assay_divergence:
        data_points = data_points.filter(
            study_assay_id__in=assays,
        )
    if matrix_item_divergence or group_divergence:
        data_points = data_points.filter(
            matrix_item_id__in=matrix_items,
        )

    return studies, assays, groups, matrix_items, data_points


def fetch_data_points_from_filters(request):
    intention = request.POST.get('intention', 'charting')

    post_filter = json.loads(request.POST.get('post_filter', '{}'))
    full_post_filter = json.loads(request.POST.get('full_post_filter', '{}'))

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
        )

        # TODO: NEEDS TO BE REVIEWED
        groups = AssayGroup.objects.filter(
            study_id__in=accessible_studies,
        )

        if current_filters.get('organ_models', []):
            organ_model_ids = [int(id) for id in current_filters.get('organ_models', []) if id]

            groups = groups.filter(
                organ_model_id__in=organ_model_ids
            )
        # Default to empty
        else:
            groups = AssayGroup.objects.none()

        accessible_studies = accessible_studies.filter(
            id__in=list(groups.values_list('study_id', flat=True))
        )

        matrix_items.prefetch_related(
            'assaydatapoint_set__study_assay__target'
        )

        if current_filters.get('groups', []):
            group_ids = [int(id) for id in current_filters.get('groups', []) if id]
            accessible_studies = accessible_studies.filter(group_id__in=group_ids)

            group = groups.filter(
                study_id__in=accessible_studies
            )
        else:
            groups = AssayGroup.objects.none()

        if current_filters.get('compounds', []):
            compound_ids = [int(id) for id in current_filters.get('compounds', []) if id]

            # See whether to include no compounds
            if '0' in current_filters.get('compounds', []):
                groups = groups.filter(
                    assaygroupcompound__compound_instance__compound_id__in=compound_ids
                ) | groups.filter(assaygroupcompound__isnull=True)
            else:
                groups = groups.filter(
                    assaygroupcompound__compound_instance__compound_id__in=compound_ids
                )

        else:
            groups = AssayGroup.objects.none()

        matrix_items = matrix_items.filter(group__in=groups, study__in=accessible_studies)

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

            post_filter = acquire_post_filter(studies, assays, groups, matrix_items, data_points)
        else:
            studies, assays, groups, matrix_items, data_points = apply_post_filter(
                full_post_filter, post_filter, studies, assays, groups, matrix_items, data_points
            )

        if intention == 'charting':
            data = get_data_points_for_charting(
                data_points,
                request.POST.get('key', ''),
                request.POST.get('mean_type', ''),
                request.POST.get('interval_type', ''),
                request.POST.get('number_for_interval', ''),
                request.POST.get('percent_control', ''),
                request.POST.get('include_all', ''),
                request.POST.get('truncate_negative', ''),
                json.loads(request.POST.get('dynamic_excluded', '{}')),
                study=studies,
                groups=groups,
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
                groups,
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


def fetch_data_points_from_study_set(request):
    intention = request.POST.get('intention', 'charting')

    post_filter = json.loads(request.POST.get('post_filter', '{}'))
    full_post_filter = json.loads(request.POST.get('full_post_filter', '{}'))

    study_set_id = int(request.POST.get('study_set_id', 0))

    current_study_set = AssayStudySet.objects.filter(id=study_set_id)

    if current_study_set:
        current_study_set = current_study_set[0]

        accessible_studies = get_user_accessible_studies(request.user)

        studies = accessible_studies.filter(id__in=current_study_set.studies.all())

        assays = current_study_set.assays.filter(study_id__in=studies)

        matrix_items = AssayMatrixItem.objects.filter(study_id__in=studies)

        # TODO: BAD, CONTRIVED
        # This is fine, we need everything for the set
        groups = AssayGroup.objects.filter(
            study_id__in=studies
        )

        # Not particularly DRY
        data_points = AssayDataPoint.objects.filter(
            matrix_item_id__in=matrix_items,
            study_assay_id__in=assays
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

            post_filter = acquire_post_filter(studies, assays, groups, matrix_items, data_points)
        else:
            studies, assays, groups, matrix_items, data_points = apply_post_filter(
                full_post_filter, post_filter, studies, assays, groups, matrix_items, data_points
            )

        if intention == 'charting':
            data = get_data_points_for_charting(
                data_points,
                request.POST.get('key', ''),
                request.POST.get('mean_type', ''),
                request.POST.get('interval_type', ''),
                request.POST.get('number_for_interval', ''),
                request.POST.get('percent_control', ''),
                request.POST.get('include_all', ''),
                request.POST.get('truncate_negative', ''),
                json.loads(request.POST.get('dynamic_excluded', '{}')),
                study=studies,
                groups=groups,
                matrix_item=None,
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
                groups,
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
        groups,
        inter_level,
        max_interpolation_size,
        initial_norm,
        criteria
    ):
    # Organization is assay -> unit -> compound/tag -> field -> time -> value
    treatment_group_representatives, setup_to_treatment_group, treatment_header_keys = get_item_groups(
        None,
        criteria,
        groups=groups,
        matrix_items=matrix_items,
    )

    matrix_item_id_to_tooltip_string = {
        matrix_item.id: '{} ({})'.format(matrix_item.name, matrix_item.matrix.name) for matrix_item in matrix_items
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
            '{}'.format(len(data_point_treatment_groups) + 1)
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
                    current_group: [str(x) for x in list(
                        data_point_attribute_getter_base_values(point)
                    ) + [setup_to_treatment_group.get(item_id).get('index')]]
                })
            else:
                treatment_group_table.update({
                    current_group: [str(x) for x in list(
                        data_point_attribute_getter_current_values(point)
                    ) + [setup_to_treatment_group.get(item_id).get('index')]]
                })

        data_group_to_studies.setdefault(
            current_group, {}
        ).update({
            '<a data-anchor="study" href="{}" target="_blank">{} ({})</a>'.format(point.study.get_absolute_url(), point.study.name, point.study.group.name): point.study.name
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
        # Contrived name
        'Chip ID',
        'Time',
        'Value',
        'MPS User Group',
        # NAME THIS SOMETHING ELSE
        # THIS IS A DATA GROUP, NOT A TREATMENT GROUP
        # TREATMENT GROUPS = ITEMS, DATA GROUP = DATA POINTS
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

    for this_set, chart_groups in list(initial_chart_data.items()):
        current_set = final_chart_data.setdefault(this_set, {})
        for chart_group, legends in list(chart_groups.items()):
            current_data = {}
            current_table = current_set.setdefault(chart_group, [['Time']])
            x_header = {}
            y_header = {}
            for legend, times in list(legends.items()):
                x_header.update({
                    legend: True,
                })

                if chart_group == 'average':
                    x_header.update({
                        legend: True,
                        # This is to deal with intervals
                        '{}{}'.format(legend, INTERVAL_1_SIGIL): True,
                        '{}{}'.format(legend, INTERVAL_2_SIGIL): True,
                    })
                else:
                    x_header.update({
                        legend: True,
                        # This is to deal with custom tooltips
                        '{}{}'.format(legend, TOOLTIP_SIGIL): True,
                    })

                for time, values in list(times.items()):
                    if chart_group == 'item':
                        for index, value_pair in enumerate(values):
                            value = value_pair[0]
                            matrix_item_id = value_pair[1]

                            current_data.setdefault(legend, {}).update({'{}~{}'.format(time, index): value})
                            current_data.setdefault('{}{}'.format(legend, TOOLTIP_SIGIL), {}).update(
                                {
                                    '{}~{}'.format(time, index): [time, legend, value, matrix_item_id]
                                }
                            )
                            y_header.update({'{}~{}'.format(time, index): True})
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
                            current_data.setdefault('{}{}'.format(legend, INTERVAL_1_SIGIL), {}).update({time: value - std})
                            current_data.setdefault('{}{}'.format(legend, INTERVAL_2_SIGIL), {}).update({time: value + std})
                        else:
                            current_data.setdefault(legend, {}).update({time: values[0]})
                        y_header.update({time: True})

            x_header_keys = list(x_header.keys())
            x_header_keys.sort(key=alphanum_key)
            current_table[0].extend(x_header_keys)

            # if chart_group == 'average':
            #     current_table[0].extend(x_header_keys)
            # else:
            #     current_table[0].extend([x.split('    ~@x')[0] for x in x_header_keys])

            x_header = {x_header_keys[index]: index + 1 for index in range(len(x_header_keys))}

            y_header = list(y_header.keys())
            y_header.sort(key=lambda x: float(str(x).split('~')[0]))
            # y_header.sort(key=float)

            for y in y_header:
                current_table.append([float(str(y).split('~')[0])] + [None] * (len(x_header)))
                # current_table.append([y] + [None] * (len(x_header)))

            y_header = {y_header[index]: index + 1 for index in range(len(y_header))}

            for x, data_point in list(current_data.items()):
                for y, value in list(data_point.items()):
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
        current_icc = float(row[6]) if row[6] else 0
        compare_icc = float(current_dic.get('best')[6]) if current_dic.get('best') and current_dic.get('best')[6] else 0

        if current_dic.get('best', '') and (current_icc > compare_icc or not compare_icc):
            current_dic.update({
                'best': row
            })
        # Subject to revision
        elif not current_dic.get('best', ''):
            current_dic.update({
                'best': row
            })

    for this_set, current_dic in list(results_rows_full.items()):
        current_best = current_dic.get('best')

        # If the current best has no ICC, try CV
        if not current_best[6]:
            for current_type, row in list(current_dic.items()):
                current_cv = float(row[5]) if row[5] else 999
                compare_cv = float(current_dic.get('best')[5]) if current_dic.get('best') and current_dic.get('best')[5] else 999

                if current_cv < compare_cv:
                    current_dic.update({
                        'best': row
                    })

    for this_set, current_dic in list(results_rows_full.items()):
        current_best = current_dic.get('best')

        if current_best[8]:
            if current_best[8][0] == 'E':
                excellent_counter += 1
            elif current_best[8][0] == 'A':
                acceptable_counter += 1
            elif current_best[8][0] == 'P':
                poor_counter += 1

        for current_type, row in list(current_dic.items()):
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

    for this_set, chart_groups in list(inter_chart_data.items()):
        current_set = final_chart_data.setdefault(this_set, {})
        for chart_group, legends in list(chart_groups.items()):
            current_data = {}
            current_table = current_set.setdefault(chart_group, [['Time']])
            x_header = {}
            y_header = {}
            for legend, times in list(legends.items()):
                # Get the median
                current_median = np.median([
                    np.median(x) for x in list(initial_chart_data.get(
                        this_set
                    ).get(
                        'average'
                    ).get(
                        legend
                    ).values())
                ])

                x_header.update({
                    legend: True,
                    # This is to deal with the style
                    '{}{}'.format(legend, SHAPE_SIGIL): True,
                    # This is to deal with intervals
                    '{}{}'.format(legend, INTERVAL_1_SIGIL): True,
                    '{}{}'.format(legend, INTERVAL_2_SIGIL): True,
                })
                for time, value_shape in list(times.items()):
                    value, shape = value_shape[0], value_shape[1]
                    if shape:
                        current_data.setdefault(legend, {}).update({time: value})
                        current_data.setdefault('{}{}'.format(legend, SHAPE_SIGIL), {}).update({time: shape})
                        y_header.update({time: True})
                    else:
                        values = initial_chart_data.get(
                            this_set
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
                            current_data.setdefault('{}{}'.format(legend, INTERVAL_1_SIGIL), {}).update({time: value - std})
                            current_data.setdefault('{}{}'.format(legend, INTERVAL_2_SIGIL), {}).update({time: value + std})
                            current_data.setdefault('{}{}'.format(legend, SHAPE_SIGIL), {}).update({time: shape})
                        else:
                            current_data.setdefault(legend, {}).update({time: values[0]})

                        y_header.update({time: True})

            x_header_keys = list(x_header.keys())
            x_header_keys.sort(key=alphanum_key)
            current_table[0].extend(x_header_keys)

            x_header = {x_header_keys[index]: index + 1 for index in range(len(x_header_keys))}

            y_header = list(y_header.keys())
            y_header.sort(key=float)

            for y in y_header:
                current_table.append([y] + [None] * (len(x_header)))

            y_header = {y_header[index]: index + 1 for index in range(len(y_header))}

            for x, data_point in list(current_data.items()):
                for y, value in list(data_point.items()):
                    current_table[y_header.get(y)][x_header.get(x)] = value

    final_data_group_to_studies = {}
    for data_group, current_studies in list(data_group_to_studies.items()):
        final_data_group_to_studies[data_group] = sorted(current_studies, key=current_studies.get)

    final_data_group_to_sample_locations = {}
    for data_group, current_sample_location in list(data_group_to_sample_locations.items()):
        final_data_group_to_sample_locations[data_group] = sorted(current_sample_location)

    final_data_group_to_organ_models = {}
    for data_group, current_organ_model in list(data_group_to_organ_models.items()):
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


def fetch_post_filter(request):
    pass


def get_organ_model_protocol_setup(organ_model_protocol_id):
    organ_model_protocol = get_object_or_404(OrganModelProtocol, pk=organ_model_protocol_id)

    data = {
        'cell': [],
        'setting': [],
        # 'compound': [],
    }

    excluded_keys = ['id', '_state', 'organ_model_protocol_id']

    setup_cells = data.get('cell')
    setup_settings = data.get('setting')
    # setup_compounds = data.get('compound')

    for cell in OrganModelProtocolCell.objects.filter(organ_model_protocol_id=organ_model_protocol_id):
        current_cell = {
            key: cell.__dict__.get(key) for key in cell.__dict__.keys() if key not in excluded_keys
        }
        setup_cells.append(current_cell)

    for setting in OrganModelProtocolSetting.objects.filter(organ_model_protocol_id=organ_model_protocol_id):
        current_setting = {
            key: setting.__dict__.get(key) for key in setting.__dict__.keys() if key not in excluded_keys
        }
        setup_settings.append(current_setting)

    # for compound in OrganModelProtocolCompound.objects.filter(id=organ_model_protocol_id):
    #     current_compound = compound.__dict__.pop('_state')
    #     setup_compounds.append(current_compound)

    return data


def fetch_organ_model_protocol_setup(request):
    organ_model_protocol_id = request.POST.get('organ_model_protocol_id', 0)

    data = get_organ_model_protocol_setup(organ_model_protocol_id)

    return HttpResponse(
        json.dumps(data),
        content_type='application/json'
    )


def fetch_organ_model_type(request):
    organ_model_id = request.POST.get('organ_model_id', 0)

    data = ''

    organ_model = OrganModel.objects.filter(id=organ_model_id)

    if organ_model:
        data = organ_model[0].device.device_type

    return HttpResponse(
        json.dumps(data),
        content_type='application/json'
    )


def fetch_matrix_setup(request):
    matrix_id = request.POST.get('matrix_id', 0)
    matrix = get_object_or_404(AssayMatrix, pk=matrix_id)
    organ_model_protocol_id = matrix.study.organ_model_protocol_id

    data = {}

    organ_model_protocol = get_organ_model_protocol_setup(organ_model_protocol_id)

    data.update({
        'current_setup': organ_model_protocol
    })

    return HttpResponse(
        json.dumps(data),
        content_type='application/json'
    )


def fetch_assay_associations(request):
    data = {
        'category_to_targets': {},
        'target_to_methods': {}
    }
    category_to_targets = data.get('category_to_targets')
    target_to_methods = data.get('target_to_methods')

    categories = AssayCategory.objects.all().prefetch_related('targets')

    # CONTRIVED FOR "ALL" CATEGORY
    current_dropdown = [{'value': "", 'text': '---------'}]

    for target in AssayTarget.objects.all():
        # match value to the desired subject ID
        value = str(target.id)
        # dropdown += '<option value="' + value + '">' + str(finding) + '</option>'
        current_dropdown.append({'value': value, 'text': str(target)})

    current_dropdown = sorted(current_dropdown, key=lambda k: k['text'])

    category_to_targets.update({
        '': current_dropdown
    })
    # END "ALL" CATEGORY

    for category in categories:
        current_dropdown = [{'value': "", 'text': '---------'}]

        for target in category.targets.all():
            # match value to the desired subject ID
            value = str(target.id)
            # dropdown += '<option value="' + value + '">' + str(finding) + '</option>'
            current_dropdown.append({'value': value, 'text': str(target)})

        current_dropdown = sorted(current_dropdown, key=lambda k: k['text'])

        category_to_targets.update({
            category.id: current_dropdown
        })

    targets = AssayTarget.objects.all().prefetch_related('methods')

    for target in targets:
        current_dropdown = [{'value': "", 'text': '---------'}]

        for method in target.methods.all():
            # match value to the desired subject ID
            value = str(method.id)
            # dropdown += '<option value="' + value + '">' + str(finding) + '</option>'
            current_dropdown.append({'value': value, 'text': str(method)})

        current_dropdown = sorted(current_dropdown, key=lambda k: k['text'])

        target_to_methods.update({
            target.id: current_dropdown
        })

    return HttpResponse(
        json.dumps(data),
        content_type='application/json'
    )


def valid_user_validation(request):
    """Makes sure the user is authenticated and is active"""
    return request.user.is_authenticated and request.user.is_active


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
    elif request.POST.get('group', ''):
        group = get_object_or_404(AssayGroup, pk=request.POST.get('group'))
        study = group.study
    elif request.POST.get('file', ''):
        current_file = get_object_or_404(AssayDataFileUpload, pk=request.POST.get('file'))
        study = current_file.study

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


def fetch_power_analysis_group_table(request):
    study = get_object_or_404(AssayStudy, pk=int(request.POST.get('study', '')))
    # Contrived!
    studies = AssayStudy.objects.filter(id=study.id)
    data = {}

    post_filter = json.loads(request.POST.get('post_filter', '{}'))
    full_post_filter = json.loads(request.POST.get('full_post_filter', '{}'))
    criteria = json.loads(request.POST.get('criteria', '{}'))
    # GET RID OF COMPOUND FOR SAKE OF POWER ANALYSIS' INITIAL TABLE
    compound_criteria = criteria.pop('compound')

    # If chip data
    matrix_items = AssayMatrixItem.objects.filter(
        study_id=study.id
    )

    assays = AssayStudyAssay.objects.filter(study_id=study.id)

    # TODO: BAD, CONTRIVED
    # Fine, we need everything for power analysis
    groups = AssayGroup.objects.filter(
        study_id=study.id
    )

    data_points = AssayDataPoint.objects.filter(
        study_id=study.id
    ).prefetch_related(
    # TODO optimize prefetch!
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

        post_filter = acquire_post_filter(studies, assays, groups, matrix_items, data_points)
    else:
        studies, assays, groups, matrix_items, data_points = apply_post_filter(
            full_post_filter, post_filter, studies, assays, groups, matrix_items, data_points
        )

    # OLD
    # repro_data = get_repro_data(chip_data)
    # Organization is assay -> unit -> compound/tag -> field -> time -> value
    treatment_group_representatives, setup_to_treatment_group, treatment_header_keys = get_item_groups(
        None,
        criteria,
        groups=groups,
        matrix_items=matrix_items,
    )

    data_point_treatment_groups = {}
    treatment_group_table = {}
    data_group_to_studies = {}
    data_group_to_sample_locations = {}
    data_group_to_organ_models = {}
    compound_table_data = {}
    compound_avg_val_data = {}

    power_analysis_input = []

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

    initial_chart_data = {}
    final_chart_data = {}

    pass_to_power_analysis_dict = {}

    matrix_id_to_stringified_compounds = {}
    for matrix_item in matrix_items:
        matrix_id_to_stringified_compounds[matrix_item.id] = matrix_item.stringify_compounds();

    for point in data_points:
        item_id = point.matrix_item_id
        data_point_tuple = data_point_attribute_getter_current(point)
        current_group = data_point_treatment_groups.setdefault(
            (
                data_point_tuple,
                setup_to_treatment_group.get(item_id).get('index')
            ),
            '{}'.format(len(data_point_treatment_groups) + 1)
        )
        point.data_group = current_group
        if current_group not in treatment_group_table:
            treatment_group_table.update({
                current_group: [str(x) for x in list(
                    data_point_attribute_getter_current_values(point)
                ) + [setup_to_treatment_group.get(item_id).get('index')]]
            })

        compound_table_key = current_group
        current_time = point.time
        if compound_table_key not in compound_table_data:
            compound_table_data[compound_table_key] = {}
        compound_table_current_compounds = matrix_id_to_stringified_compounds[point.matrix_item.id]
        if compound_table_current_compounds not in compound_table_data[compound_table_key]:
            compound_table_data[compound_table_key][compound_table_current_compounds] = {
                'chips': [],
                'time-points': [],
            }
        if point.matrix_item.name not in compound_table_data[compound_table_key][compound_table_current_compounds]['chips']:
            compound_table_data[compound_table_key][compound_table_current_compounds]['chips'].append(point.matrix_item.name)
        if current_time not in compound_table_data[compound_table_key][compound_table_current_compounds]['time-points']:
            compound_table_data[compound_table_key][compound_table_current_compounds]['time-points'].append(current_time)

        data_group_to_studies.setdefault(
            current_group, {}
        ).update({
            '<a href="{}" target="_blank">{} ({})</a>'.format(point.study.get_absolute_url(), point.study.name, point.study.group.name): point.study.name
        })

        data_group_to_sample_locations.setdefault(
            current_group, {}
        ).update({
            point.sample_location.name: True
        })

        if point.matrix_item.organ_model_id:
            data_group_to_organ_models.setdefault(
                current_group, {}
            ).update({
                point.matrix_item.organ_model.name: True
            })
        else:
            data_group_to_organ_models.setdefault(
                current_group, {}
            ).update({
                '-No Device-': True
            })

        power_analysis_input.append([
            point.data_group,
            current_time,
            matrix_id_to_stringified_compounds[point.matrix_item.id],
            point.matrix_item.name,
            point.value
        ])

        if current_group not in compound_avg_val_data:
            compound_avg_val_data[current_group] = {'times':[]}
        if compound_table_current_compounds not in compound_avg_val_data[current_group]:
            compound_avg_val_data[current_group][compound_table_current_compounds] = {}
        if current_time not in compound_avg_val_data[current_group]['times']:
            compound_avg_val_data[current_group]['times'].append(current_time)
        if current_time not in compound_avg_val_data[current_group][compound_table_current_compounds]:
            compound_avg_val_data[current_group][compound_table_current_compounds][current_time] = point.value

        # TODO BAD NOT DRY
        # CHARTING STUFF
        initial_chart_data.setdefault(
            point.data_group, {}
        ).setdefault(
            compound_table_current_compounds, {}
        ).setdefault(
            # NOTE CONVERT TO DAYS
            point.time / 1440.0, []
        ).append(point.value)

        pass_to_power_analysis_dict.setdefault(
            point.data_group, {}
        ).setdefault(
            compound_table_current_compounds, []
        ).append([
            point.data_group,
            point.time,
            compound_table_current_compounds,
            point.matrix_item.name,
            point.value
        ])

    # TODO BAD NOT DRY
    for chart_group, legends in list(initial_chart_data.items()):
        current_data = {}
        current_table = final_chart_data.setdefault(chart_group, [['Time']])
        x_header = {}
        y_header = {}
        for legend, times in list(legends.items()):
            x_header.update({
                legend: True,
            })

            x_header.update({
                legend: True,
                # This is to deal with intervals
                '{}{}'.format(legend, '     ~@i1'): True,
                '{}{}'.format(legend, '     ~@i2'): True,
            })

            for time, values in list(times.items()):
                if len(values) > 1:
                    # TODO TODO TODO ONLY ARITHMETIC MEAN RIGHT NOW
                    value = np.mean(values)
                    std = np.std(values)
                    current_data.setdefault(legend, {}).update({time: value})
                    current_data.setdefault('{}{}'.format(legend, '     ~@i1'), {}).update({time: value - std})
                    current_data.setdefault('{}{}'.format(legend, '     ~@i2'), {}).update({time: value + std})
                else:
                    current_data.setdefault(legend, {}).update({time: values[0]})
                y_header.update({time: True})

        x_header_keys = list(x_header.keys())
        x_header_keys.sort(key=alphanum_key)
        current_table[0].extend(x_header_keys)

        # if chart_group == 'average':
        #     current_table[0].extend(x_header_keys)
        # else:
        #     current_table[0].extend([x.split('    ~@x')[0] for x in x_header_keys])

        x_header = {x_header_keys[index]: index + 1 for index in range(len(x_header_keys))}

        y_header = list(y_header.keys())
        y_header.sort(key=lambda x: float(str(x).split('~')[0]))
        # y_header.sort(key=float)

        for y in y_header:
            current_table.append([float(str(y).split('~')[0])] + [None] * (len(x_header)))
            # current_table.append([y] + [None] * (len(x_header)))

        y_header = {y_header[index]: index + 1 for index in range(len(y_header))}

        for x, data_point in list(current_data.items()):
            for y, value in list(data_point.items()):
                current_table[y_header.get(y)][x_header.get(x)] = value

    for x in compound_table_data:
        temp = []
        for y in compound_table_data[x]:
            temp.append([y, len(compound_table_data[x][y]['chips']), len(compound_table_data[x][y]['time-points'])])
        compound_table_data[x] = temp

    data['compound_table_data'] = compound_table_data

    power_analysis_input.insert(0, [
        'Group',
        'Time',
        'Compound Treatment(s)',
        # Contrived name
        'Chip ID',
        'Value'
    ])

    power_analysis_group_table = create_power_analysis_group_table(len(treatment_group_table), power_analysis_input)

    data['power_analysis_group_table'] = power_analysis_group_table['data']

    data['data_groups'] = treatment_group_table

    final_data_group_to_sample_locations = {}
    for data_group, current_sample_location in list(data_group_to_sample_locations.items()):
        final_data_group_to_sample_locations[data_group] = sorted(current_sample_location)

    final_data_group_to_organ_models = {}
    for data_group, current_organ_model in list(data_group_to_organ_models.items()):
        final_data_group_to_organ_models[data_group] = sorted(current_organ_model)

    data['data_group_to_sample_locations'] = final_data_group_to_sample_locations
    data['data_group_to_organ_models'] = final_data_group_to_organ_models

    # data['header_keys'] = data_header_keys
    data['header_keys'] = {
        'treatment': treatment_header_keys,
        'data': data_header_keys
    }

    data['treatment_groups'] = treatment_group_representatives

    data['post_filter'] = post_filter

    data['final_chart_data'] = final_chart_data

    data['pass_to_power_analysis_dict'] = pass_to_power_analysis_dict

    return HttpResponse(json.dumps(data),
                        content_type='application/json')


def fetch_two_sample_power_analysis_results(request):
    power_analysis_input = json.loads(request.POST.get('full_data', ''))
    pam = request.POST.get('pam', '')
    sig = request.POST.get('sig', '')
    power_analysis_data = two_sample_power_analysis(power_analysis_input, pam, float(sig))

    data = {}
    for key, current_list in power_analysis_data.items():
        for current_sublist in current_list:
            for current_index, current_item in enumerate(current_sublist):
                if type(current_item) is not str and current_item is not None:
                    current_sublist[current_index] = float(current_item)

    data['power_analysis_data'] = power_analysis_data

    return HttpResponse(json.dumps(data), content_type='application/json')


def fetch_one_sample_power_analysis_results(request):
    power_analysis_input = json.loads(request.POST.get('full_data', ''))
    one_sample_compound = request.POST.get('one_sample_compound', '')
    sig = request.POST.get('sig', '')
    one_sample_tp = request.POST.get('one_sample_tp', '')
    os_diff = request.POST.get('os_diff', '')
    os_diff_percentage = request.POST.get('os_diff_percentage', '')
    os_sample_size = request.POST.get('os_sample_size', '')
    os_power = request.POST.get('os_power', '')
    power_analysis_data = one_sample_power_analysis(
                            power_analysis_input,
                            float(sig),
                            one_sample_compound,
                            float(one_sample_tp),
                            os_diff,
                            os_diff_percentage,
                            os_sample_size,
                            os_power
                        )

    data = {'power_analysis_data': power_analysis_data}

    return HttpResponse(json.dumps(data), content_type='application/json')


def get_pubmed_reference_data(request):
    """Returns a dictionary of PubMed data given a PubMed ID"""
    data = {}
    term = None
    if request.POST.get('term', ''):
        term = request.POST.get('term')
    # Get URL of target for scrape
    url = 'https://pubmed.ncbi.nlm.nih.gov/?term={}'.format(term)
    # Make the http request
    response = requests.get(url)
    # Get the webpage as text
    stuff = response.text
    # Make a BeatifulSoup object
    soup = BeautifulSoup(stuff, 'html5lib')

    # Get Title
    if soup.find_all('h1', {'class': 'heading-title'}):
        data['title'] = soup.select('.heading-title')[0].get_text().strip()

    # Get Authors
    if soup.find_all('span', {'class': 'authors-list-item'}):
        data['authors'] = ''.join([x.get_text() for x in soup.select('.authors-list-item')])

    # Get Abstract
    if soup.find_all('div', {'class': 'abstract-content'}):
        data['abstract'] = soup.select('.abstract-content > p')[0].get_text().strip()
    else:
        data['abstract'] = 'No abstract available.'

    # Get Publication
    if soup.find_all('button', {'class': 'journal-actions-trigger'}):
        data['publication'] = soup.select('.journal-actions-trigger')[0].get_text().strip()

    # Get Year
    if soup.find_all('span', {'class': 'cit'}):
        data['year'] = soup.select('.cit')[0].get_text().split(' ')[0]
        # data['year'] = soup.select(".cit > span")[0].get_text()[0:5]

    # Get PMID and DOI
    # if soup.find_all('dl', {'class': 'rprtid'}):
    #     pmid_doi_headers = soup.select('.rprtid dt')
    #     pmid_doi_stuff = soup.select('.rprtid dd')
    #     data['pubmed_id'] = ''
    #     data['doi'] = 'N/A'
    #     for x in range(len(pmid_doi_headers)):
    #         if pmid_doi_headers[x].get_text() == 'PMID:':
    #             data['pubmed_id'] = pmid_doi_stuff[x].get_text()
    #         elif pmid_doi_headers[x].get_text() == 'DOI:':
    #             data['doi'] = pmid_doi_stuff[x].get_text()
    # else:
    #     data['pubmed_id'] = ''
    #     data['doi'] = 'N/A'

    if soup.find_all('strong', {'class': 'current-id'}):
        data['pubmed_id'] = soup.select('.current-id')[0].get_text()
    else:
        data['pubmed_id'] = ''

    if soup.find_all('span', {'class': 'citation-doi'}):
        data['doi'] = soup.select('.citation-doi')[0].get_text().strip()[5:-1]
    else:
        data['doi'] = ''

    return HttpResponse(
        json.dumps(data),
        content_type='application/json'
    )

# Somewhat crude, but we need some way to perform filters etc. if we use this
# dropdown_processing = {
#     ''
# }


# Why here in Assays?
# def fetch_dropdown(request):
#     """Returns dropdown values in JSON to be processed by selectize"""
#     dropdown = [{'value': "", 'text': '---------'}]
#     data = {'dropdown': dropdown}
#
#     app = request.POST.get('app', '')
#     model = request.POST.get('model', '')
#
#     entries = apps.get_model(app_label=app, model_name=model).objects.all()
#
#     for entry in entries:
#         # match value to the desired subject ID
#         value = str(entry.id)
#         dropdown.append({'value': value, 'text': str(entry)})
#
#     return JsonResponse(data)


# Crude method to clone
def make_clone(request, object_to_clone, special_handling=None, attributes_to_change=None):
    object_to_clone.id = None
    object_to_clone.pk = None

    # Special handling for study involves changing the name and start date
    if special_handling == 'STUDY':
        # Add clone parent to description
        object_to_clone.description = 'Cloned from Study {}.\n{}'.format(
            str(object_to_clone),
            object_to_clone.description
        )

        object_to_clone.name = 'Clone-' + object_to_clone.name
        object_to_clone.start_date = timezone.now()

        # Exclude files like images and protocols
        # SUBJECT TO CHANGE:
        # MIGHT BE A GOOD IDEA TO PROGRAMMATICALLY ACQUIRE ALL FILE FIELDS
        object_to_clone.protocol = None
        object_to_clone.image = None

        # Get rid of repro_nums
        object_to_clone.repro_nums = ''

    if attributes_to_change:
        for attribute, value in attributes_to_change.items():
            if hasattr(object_to_clone, attribute):
                setattr(object_to_clone, attribute, value)

    if hasattr(object_to_clone, 'created_by'):
        setattr(object_to_clone, 'created_by', request.user)

    if hasattr(object_to_clone, 'modified_by'):
        setattr(object_to_clone, 'modified_by', request.user)

    object_to_clone.save()

    return object_to_clone.id


def clone_study(request):
    data = {}

    study_to_clone = get_object_or_404(AssayStudy, pk=request.POST.get('study'))

    if AssayStudy.objects.filter(name='Clone-'+study_to_clone.name).count():
        return HttpResponse(
            json.dumps(
                {
                    'errors': 'A clone of this study already exists.',
                    'new_study_id': AssayStudy.objects.filter(name='Clone-'+study_to_clone.name)[0].get_absolute_url()
                }
            ),
            content_type="application/json"
        )

    # Crude method to clone
    # NOTE, undo signed_off_by and restricted
    new_study_id = make_clone(request, study_to_clone, special_handling='STUDY', attributes_to_change={'signed_off_by_id': None, 'restricted': True})

    # Restore (crude)
    study_to_clone = get_object_or_404(AssayStudy, pk=request.POST.get('study'))

    # Clone study assays
    for assay in study_to_clone.assaystudyassay_set.all():
        clone_attributes = {
            'study_id': new_study_id
        }
        make_clone(request, assay, attributes_to_change=clone_attributes)

    # Clone the groups
    group_to_group = {}

    for group in study_to_clone.assaygroup_set.all():
        clone_attributes = {
            'study_id': new_study_id
        }
        original_group_id = group.id
        new_group_id = make_clone(request, group, attributes_to_change=clone_attributes)
        group_to_group.update({
            original_group_id: new_group_id
        })

    # Double loop is goofy
    for group in study_to_clone.assaygroup_set.all():
        clone_attributes = {
            'study_id': new_study_id,
            'group_id': group_to_group.get(group.id)
        }
        # Horrible nested loops, can take a very long time!
        for cell in group.assaygroupcell_set.all():
            make_clone(request, cell, attributes_to_change=clone_attributes)
        for compound in group.assaygroupcompound_set.all():
            make_clone(request, compound, attributes_to_change=clone_attributes)
        for setting in group.assaygroupsetting_set.all():
            make_clone(request, setting, attributes_to_change=clone_attributes)

    # Don't clone references or supporting data

    matrix_to_matrix = {}

    for matrix in study_to_clone.assaymatrix_set.all():
        clone_attributes = {
            'study_id': new_study_id
        }
        original_matrix_id = matrix.id
        new_matrix_id = make_clone(request, matrix, attributes_to_change=clone_attributes)
        matrix_to_matrix.update({
            original_matrix_id: new_matrix_id
        })

    matrix_item_to_matrix_item = {}

    # Contrivance: ordering
    for matrix_item in study_to_clone.assaymatrixitem_set.all().order_by('pk'):
        clone_attributes = {
            'study_id': new_study_id,
            'matrix_id': matrix_to_matrix.get(matrix_item.matrix_id),
            'group_id': group_to_group.get(matrix_item.group_id)
        }
        original_matrix_item_id = matrix_item.id
        new_matrix_item_id = make_clone(request, matrix_item, attributes_to_change=clone_attributes)
        matrix_item_to_matrix_item.update({
            original_matrix_item_id: new_matrix_item_id
        })

    # OLD SCHEMA: USELESS
    # Double loop is goofy
    # for matrix_item in study_to_clone.assaymatrixitem_set.all():
    #     clone_attributes = {
    #         'study_id': new_study_id,
    #         'matrix_item_id': matrix_item_to_matrix_item.get(matrix_item.id)
    #     }
    #     # Horrible nested loops, can take a very long time!
    #     for cell in matrix_item.assaysetupcell_set.all():
    #         make_clone(request, cell, attributes_to_change=clone_attributes)
    #     for compound in matrix_item.assaysetupcompound_set.all():
    #         make_clone(request, compound, attributes_to_change=clone_attributes)
    #     for setting in matrix_item.assaysetupsetting_set.all():
    #         make_clone(request, setting, attributes_to_change=clone_attributes)

    data.update({
        'new_study_id': AssayStudy.objects.get(id=new_study_id).get_absolute_url()
    })

    return HttpResponse(
        json.dumps(data),
        content_type="application/json"
    )


def fetch_pbpk_group_table(request):
    data = {}
    post_filter = json.loads(request.POST.get('post_filter', '{}'))
    full_post_filter = json.loads(request.POST.get('full_post_filter', '{}'))
    pre_filter = {}

    if request.POST.get('filters', ''):
        current_filters = json.loads(request.POST.get('filters', '{}'))
        accessible_studies = get_user_accessible_studies(request.user)

        if current_filters.get('studies', []):
            study_ids = [int(id) for id in current_filters.get('studies', []) if id]
            accessible_studies = accessible_studies.filter(
                id__in=study_ids
            )
        else:
            accessible_studies = AssayStudy.objects.none()

        # NOT DRY REVISE ASAP PLEASE
        # Notice exclusion of missing organ model
        groups = AssayGroup.objects.filter(
            study_id__in=accessible_studies
        ).prefetch_related(
            'organ_model',
        )

        if current_filters.get('organ_models', []):
            organ_model_ids = [int(id) for id in current_filters.get('organ_models', []) if id]

            groups = groups.filter(
                organ_model_id__in=organ_model_ids
            )
        # Default to empty
        else:
            groups = AssayGroup.objects.none()

        accessible_studies = accessible_studies.filter(
            id__in=list(groups.values_list('study_id', flat=True))
        )

        matrix_items = AssayMatrixItem.objects.filter(
            group__in=groups
        ).prefetch_related(
            # 'assaysetupcompound_set__compound_instance',
            # Need cells for discrimination later
            # 'assaygroupcompound_set__compound_instance',
            # 'assaygroupcell_set__cell_sample__cell_type__organ',
            'assaydatapoint_set__study_assay__target'
        )

        groups = groups.prefetch_related(
            'assaygroupcompound_set__compound_instance',
            'assaygroupcell_set__cell_sample__cell_type__organ',
        )

        if current_filters.get('groups', []):
            group_ids = [int(id) for id in current_filters.get('groups', []) if id]
            accessible_studies = accessible_studies.filter(group_id__in=group_ids)

            groups = groups.filter(
                study_id__in=accessible_studies
            )
        else:
            groups = AssayGroup.objects.none()

        compound_ids = []
        if current_filters.get('compounds', []):
            compound_ids = [int(id) for id in current_filters.get('compounds', []) if id]
            # TODO Only take Compounds that correspond to a Target, and ignore No Compound

            # See whether to include no compounds
            if '0' in current_filters.get('compounds', []):
                groups = groups.filter(
                    assaygroupcompound__compound_instance__compound_id__in=compound_ids
                ) | groups.filter(assaygroupcompound__isnull=True)
            else:
                groups = groups.filter(
                    assaygroupcompound__compound_instance__compound_id__in=compound_ids
                )

        else:
            groups = AssayGroup.objects.none()

        matrix_items = matrix_items.filter(
            group__in=groups
        )

        pre_filter.update({
            'matrix_item_id__in': matrix_items.filter(assaydatapoint__isnull=False).distinct()
        })

        studies = accessible_studies

        # For each compound in filter, get name, match to Target, get list of IDs
        pbpk_compounds = [comp.title() for comp in Compound.objects.filter(id__in=compound_ids).values_list('name', flat=True)]

        targets = AssayTarget.objects.filter(name__in=pbpk_compounds)

        # A little contrived
        # TODO These targets need to match the compound for PBPK
        assays = AssayStudyAssay.objects.filter(
            study_id__in=studies,
            target_id__in=targets
        )

        pre_filter.update({'study_assay_id__in': assays})

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

            post_filter = acquire_post_filter(studies, assays, groups, matrix_items, data_points)
        else:
            studies, assays, groups, matrix_items, data_points = apply_post_filter(
                full_post_filter, post_filter, studies, assays, groups, matrix_items, data_points
            )

        data = get_pbpk_info(
            data_points,
            matrix_items,
            groups,
        )

        data.update({'post_filter': post_filter})

        return HttpResponse(
            json.dumps(data),
            content_type="application/json"
        )
    else:
        return HttpResponseServerError()


def get_pbpk_info(data_points, matrix_items, groups):
    # Hardcoded for now:
    criteria = {
        # 'setup': ['study_id', 'organ_model_id', 'device_id'],
        'setup': ['study_id', 'organ_model_id'],
        'special': ['method', 'sample_location'],
        # Maybe we'll utilize concentration unit later
        # 'compound': ['compound_instance.compound_id', 'concentration', 'concentration_unit_id']
        'compound': ['compound_instance.compound_id', 'concentration']
    }
    # Organization is assay -> unit -> compound/tag -> field -> time -> value
    treatment_group_representatives, setup_to_treatment_group, treatment_header_keys = get_item_groups(
        None,
        criteria,
        groups=groups,
        matrix_items=matrix_items,
    )

    cell_group_representives, setup_to_cell_group, cell_header_keys = get_item_groups(
        None,
        {'cell': ['cell_sample_id']},
        groups=groups,
        matrix_items=matrix_items,
    )

    matrix_item_id_to_tooltip_string = {
        matrix_item.id: '{} ({})'.format(matrix_item.name, matrix_item.matrix.name) for matrix_item in matrix_items
    }

    # inter_data = []

    data_point_treatment_groups = {}
    treatment_group_table = {}
    # Probably don't need these for PBPK
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

    study_name_to_pk_params = {}

    for point in data_points:
        point.standard_value = point.value
        item_id = point.matrix_item_id
        # Hopefully/probably will able to have a base unit (micro Mole)
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
            '{}'.format(len(data_point_treatment_groups) + 1)
        )

        if current_group not in sets_intra_points:
            sets_intra_points[current_group] = []
        sets_intra_points[current_group].append([
            point.time,
            point.value,
            point.matrix_item_id
        ])

        point.data_group = current_group
        if current_group not in treatment_group_table:
            if point.study_assay.unit.base_unit_id:
                treatment_group_table.update({
                    current_group: [str(x) for x in list(
                        data_point_attribute_getter_base_values(point)
                    ) + [setup_to_treatment_group.get(item_id).get('index')]]
                })
            else:
                treatment_group_table.update({
                    current_group: [str(x) for x in list(
                        data_point_attribute_getter_current_values(point)
                    ) + [setup_to_treatment_group.get(item_id).get('index')]]
                })

        if point.study.id not in study_name_to_pk_params:
            study_name_to_pk_params[point.study.id] = {'PK Type': '', 'Relevant Cells': point.study.number_of_relevant_cells, 'Total Device Volume': point.study.total_device_volume, 'Flow Rate': point.study.flow_rate}
            if point.study.pbpk_steady_state:
                study_name_to_pk_params[point.study.id]['PK Type'] = 'Continuous Infusion'
            else:
                study_name_to_pk_params[point.study.id]['PK Type'] = 'Bolus'

        data_group_to_studies.setdefault(
            current_group, {}
        ).update({
            '<a data-anchor="study" href="{}" target="_blank">{} ({})</a>'.format(point.study.get_absolute_url(), point.study.name, point.study.group.name): point.study.name
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

    # Why is this here?
    # inter_data.append([
    #     'Study ID',
    #     # Contrived name
    #     'Chip ID',
    #     'Time',
    #     'Value',
    #     'MPS User Group',
    #     # NAME THIS SOMETHING ELSE
    #     # THIS IS A DATA GROUP, NOT A TREATMENT GROUP
    #     # TREATMENT GROUPS = ITEMS, DATA GROUP = DATA POINTS
    #     'Treatment Group'
    # ])

    # GET RAW DATAPOINTS AS LEGEND -> TIME -> LIST OF VALUES
    # AFTER THAN REPOSITION THEM FOR CHARTING AND AVERAGE ONE OF THE SETS (KEEP RAW THOUGH)
    initial_chart_data = {}
    final_chart_data = {}

    for point in data_points:
        # inter_data.append([
        #     point.study.name,
        #     point.matrix_item.name,
        #     point.time,
        #     # NOTE USE OF STANDARD VALUE RATHER THAN VALUE
        #     point.standard_value,
        #     point.study.group.name,
        #     point.data_group
        # ])

        # This should probably be cells later
        # legend = point.study.name

        legend = cell_group_representives[setup_to_cell_group.get(point.matrix_item_id).get('index')].get('Cells')

        initial_chart_data.setdefault(
            point.data_group, {}
        ).setdefault(
            legend, {}
        ).setdefault(
            # NOTE CONVERT TO HOURS
            point.time / 60.0, []
        ).append(point.standard_value)

    for this_set, legends in list(initial_chart_data.items()):
        current_data = {}
        current_table = final_chart_data.setdefault(this_set, [['Time']])
        x_header = {}
        y_header = {}
        for legend, times in list(legends.items()):
            x_header.update({
                legend: True,
                # This is to deal with intervals
                '{}{}'.format(legend, INTERVAL_1_SIGIL): True,
                '{}{}'.format(legend, INTERVAL_2_SIGIL): True,
            })

            for time, values in list(times.items()):
                if len(values) > 1:
                    # TODO TODO TODO ONLY ARITHMETIC MEAN RIGHT NOW
                    value = np.mean(values)
                    std = np.std(values)
                    current_data.setdefault(legend, {}).update({time: value})
                    current_data.setdefault('{}{}'.format(legend, INTERVAL_1_SIGIL), {}).update({time: value - std})
                    current_data.setdefault('{}{}'.format(legend, INTERVAL_2_SIGIL), {}).update({time: value + std})
                else:
                    current_data.setdefault(legend, {}).update({time: values[0]})
                y_header.update({time: True})

        x_header_keys = list(x_header.keys())
        x_header_keys.sort(key=alphanum_key)
        current_table[0].extend(x_header_keys)

        x_header = {x_header_keys[index]: index + 1 for index in range(len(x_header_keys))}

        y_header = list(y_header.keys())
        y_header.sort(key=lambda x: float(str(x).split('~')[0]))

        for y in y_header:
            current_table.append([float(str(y).split('~')[0])] + [None] * (len(x_header)))

        y_header = {y_header[index]: index + 1 for index in range(len(y_header))}

        for x, data_point in list(current_data.items()):
            for y, value in list(data_point.items()):
                current_table[y_header.get(y)][x_header.get(x)] = value

    data = {
        'chart_data': final_chart_data,
        'data_groups': treatment_group_table,
        'header_keys': {
            'treatment': treatment_header_keys,
            'data': data_header_keys
        },
        'treatment_groups': treatment_group_representatives,
        'study_name_to_pk_params': study_name_to_pk_params
    }

    return data


def fetch_species_parameters(request):
    # This will eventually need to consider input from the interface, but none of this has been specified at this point.
    # STOPGAP for now. Select off of stringified version where organ+species match in future?
    species_params = SpeciesParameters.objects.get(id=1)

    # Sloppy, get Usansky reference. Always needed? Just for liver? I have no idea.
    additional_reference = AssayReference.objects.get(pubmed_id="15833900")
    if (additional_reference):
        additional_reference_url = additional_reference.get_absolute_url()
    else:
        additional_reference = ''
        additional_reference_url = ''

    data = {
        'species': species_params.species.species_name,
        'organ': species_params.organ.organ_name,
        'reference': str(species_params.reference),
        'reference_url': str(species_params.reference.get_absolute_url()),
        'additional_reference': str(additional_reference),
        'additional_reference_url': str(additional_reference_url),
        'body_mass': species_params.body_mass,
        'total_organ_weight': species_params.total_organ_weight,
        'organ_tissue': species_params.organ_tissue,
        'plasma_volume': species_params.plasma_volume,
        'vp': species_params.vp,
        've': species_params.ve,
        'rei': species_params.rei,
        'vr': species_params.vr,
        'asr': species_params.absorptive_surface_area,
        'ki': species_params.ki
    }

    return HttpResponse(
        json.dumps(data),
        content_type="application/json"
    )


def fetch_compound_physicochemical_parameters(request):
    # This will eventually need to consider input from the interface, but none of this has been specified at this point.
    # STOPGAP for now. Select off of stringified version where organ+species match in future?
    pk_compound = request.POST.get('pk_compound', '')

    pk_compound = (" ").join(pk_compound.split(" ")[:-3])

    compound = Compound.objects.filter(name__iexact=pk_compound)[0]

    if compound.protein_binding:
        fu = 1.0-(float(re.findall(r"[-+]?\d*\.\d+|\d+", compound.protein_binding)[0])/100)
    else:
        fu = compound.protein_binding

    # if compound.bioavailability:
    #     bioavailability = float(re.findall(r"[-+]?\d*\.\d+|\d+", compound.bioavailability)[0])/100
    # else:
    #     bioavailability = compound.bioavailability

    data = {
        'compound': pk_compound,
        'mw': compound.molecular_weight,
        'logd': compound.logd,
        'acidic_pka': compound.acidic_pka,
        'basic_pka': compound.basic_pka,
        # 'bioavailability': bioavailability,
        'fu': fu
    }

    return HttpResponse(
        json.dumps(data),
        content_type="application/json"
    )


def fetch_pbpk_intrinsic_clearance_results(request):
    data = {}

    try:
        total_device_vol_ul = float(request.POST.get('total_device_vol_ul', ''))
    except ValueError:
        total_device_vol_ul = None
    try:
        total_cells_in_device = float(request.POST.get('total_cells_in_device', ''))
    except ValueError:
        total_cells_in_device = None
    try:
        flow_rate = float(request.POST.get('flow_rate', ''))
    except ValueError:
        flow_rate = None
    cell_name = request.POST.get('cell_name', '').replace(u'\xa0', u' ')
    raw_compound_pk_data = json.loads(request.POST.get('compound_pk_data', '[[]]'))

    final_compound_pk_data = []
    cell_index = raw_compound_pk_data[0].index(cell_name)
    try:
        no_cell_index = raw_compound_pk_data[0].index("-No Cell Samples-")
    except ValueError:
        no_cell_index = -1

    for line in raw_compound_pk_data[1:]:
        if line[cell_index] is not None:
            final_compound_pk_data.append([float(line[0]), cell_name, float(line[cell_index])])
            if no_cell_index > 0:
                final_compound_pk_data.append([float(line[0]), "-No Cell Samples-", float(line[no_cell_index])])

    clearance_results = pk_clearance_results(
        request.POST.get('pk_type', ''),
        request.POST.get('with_no_cell_data', '') == 'true',
        cell_name,
        float(request.POST.get('start_time', '')),
        float(request.POST.get('end_time', '')),
        total_device_vol_ul,
        total_cells_in_device,
        flow_rate,
        float(request.POST.get('cells_per_tissue_g', '')),
        float(request.POST.get('total_organ_weight_g', '')),
        float(request.POST.get('compound_conc', '')),
        final_compound_pk_data
    )

    # TODO TEMP
    data = clearance_results

    return HttpResponse(
        json.dumps(data),
        content_type="application/json"
    )


def fetch_pbpk_dosing_results(request):
    data = {}
    fetch_pbpk_error = ""

    usansky_sinko_volume_data = [
        ['Human', 'Volume (L)', 'Vw', 'Vn', 'Vph'],
        ['Heart', 0.329, 0.758, 0.0115, 0.0166],
        ['Kidney', 0.308, 0.783, 0.0207, 0.0162],
        ['Liver', 1.82, 0.751, 0.0348, 0.0252],
        ['Lung', 0.532, 0.811, 0.003, 0.009],
        ['Spleen', 0.182, 0.788, 0.0201, 0.0198],
        ['Muscle', 28.3, 0.76, 0.0238, 0.0072],
        ['Plasma', 2.968, 0.945, 0.0035, 0.00225]
    ]

    # Plasma Values
    dose_mg = ''
    dose_interval = ''
    if request.POST.get('dose_mg'):
        try:
            dose_mg = float(request.POST.get('dose_mg').strip())
        except ValueError:
            fetch_pbpk_error = 'Invalid input provided for Dose.'
    if request.POST.get('dose_interval'):
        try:
            dose_interval = float(request.POST.get('dose_interval').strip())
        except ValueError:
            fetch_pbpk_error = 'Invalid input provided for Dose Interval.'

    # Dosing Values
    desired_Cp = ''
    desired_dose_interval = ''
    estimated_fraction_absorbed = ''
    if request.POST.get('desired_Cp'):
        try:
            desired_Cp = float(request.POST.get('desired_Cp').strip())
        except ValueError:
            fetch_pbpk_error = 'Invalid input provided for Desired Cp.'
    if request.POST.get('desired_dose_interval'):
        try:
            desired_dose_interval = float(request.POST.get('desired_dose_interval').strip())
        except ValueError:
            fetch_pbpk_error = 'Invalid input provided for Desired Dose Interval.'
    if request.POST.get('estimated_fraction_absorbed'):
        try:
            estimated_fraction_absorbed = float(request.POST.get('estimated_fraction_absorbed').strip())
        except ValueError:
            fetch_pbpk_error = 'Invalid input provided for Fraction Absorbed.'

    if desired_dose_interval == 0 or dose_interval == 0:
        fetch_pbpk_error = 'Intervals cannot be 0.'

    if fetch_pbpk_error != "":
        return HttpResponse(
            json.dumps({'error': fetch_pbpk_error}),
            content_type="application/json"
        )

    dosing_results = calculate_pk_parameters(
        float(request.POST.get('cl_ml_min').strip()),
        usansky_sinko_volume_data,
        float(request.POST.get('body_mass').strip()),
        float(request.POST.get('MW').strip()),
        float(request.POST.get('logD').strip()),
        float(request.POST.get('pKa').strip()),
        float(request.POST.get('fu').strip()),
        float(request.POST.get('Vp').strip()),
        float(request.POST.get('VE').strip()),
        float(request.POST.get('REI').strip()),
        float(request.POST.get('VR').strip()),
        float(request.POST.get('ASR').strip()),
        float(request.POST.get('Ki').strip()),
        float(request.POST.get('Ka').strip()),
        float(request.POST.get('Fa').strip()),
        dose_mg,
        dose_interval,
        desired_Cp,
        desired_dose_interval,
        estimated_fraction_absorbed,
        round(float(request.POST.get('prediction_time_length'))),
        request.POST.get('missing_plasma_values') == "true",
        request.POST.get('missing_dosing_values') == "true",
        request.POST.get('acidic_basic') == "acidic"
    )

    # TODO TEMP
    data = dosing_results

    return HttpResponse(
        json.dumps(data),
        content_type="application/json"
    )


# sck - assay plate map - fetch information about plate layout by size
def fetch_information_for_plate_map_layout(request):
    """
    Assay Plate Map All - Getting the information on how to layout a plate map based on plate size (calls utility) and Assay Plate Map - Getting the information for matrix item setup to display in plate map when clicked.
    """

    study_id = request.POST.get('study', '0')
    plate_size = request.POST.get('plate_size', '0')
    yes_if_matrix_item_setup_already_run = request.POST.get('yes_if_matrix_item_setup_already_run', 'no')

    if not study_id:
        return HttpResponseServerError()

    if not plate_size:
        return HttpResponseServerError()

    # this function is in utils.py
    layout_info = get_the_plate_layout_info_for_assay_plate_map(plate_size)

    # return from utils.py => [col_labels, row_labels, row_contents]
    col_labels = layout_info[0]
    row_labels = layout_info[1]
    row_contents = layout_info[2]

    data = {}
    data_to_return = []

    data_fields = {
        'col_labels': col_labels,
        'row_labels': row_labels,
        'row_contents': row_contents,
    }
    data_to_return.append(data_fields)

    matrix_data_to_return = []

    if yes_if_matrix_item_setup_already_run == 'no':

        matrix_items = AssayMatrixItem.objects.filter(
            study_id=study_id
        # ).prefetch_related(
        #     'matrix',
        # ).order_by('matrix__name', 'name',
        )

        # for matrix_item in matrix_items:
        #     print(matrix_item)
        #     print(matrix_item.id)
        #     print(matrix_item.name)
        #     print(matrix_item.assaysetupcompound_set)
        #     print(matrix_item.assaysetupcell_set)
        #     print(matrix_item.assaysetupsetting_set)
        #     print(matrix_item.stringify_compounds())
        #     print(matrix_item.stringify_cells())
        #     print(matrix_item.stringify_settings())
        #     print(matrix_item.matrix.name)

        # search term - change if CHIP SETUP changes todo-sck here here I think this is the only place in plate map stuff
        for each in matrix_items:
            short_compound = ""
            short_cell = ""
            short_setting = ""

            my_compound = each.stringify_compounds().split('\n')
            my_cell = each.stringify_cells().split('\n')

            # print("my_compound ", my_compound)

            for idx, item in enumerate(my_compound):
                if idx % 2 == 0:
                    short_compound = short_compound + "  " + item
            for idx, item in enumerate(my_cell):
                if idx % 2 == 0:
                    short_cell = short_cell + "  " + item
            short_setting = each.stringify_settings()

            # print('short_compound ', short_compound)

            data_fields = {
                'matrix_item_id': each.id,
                'long_compound': each.stringify_compounds(),
                'long_cell': each.stringify_cells(),
                'long_setting': each.stringify_settings(),
                'compound': short_compound,
                'cell': short_cell,
                'setting': short_setting,
            }
            matrix_data_to_return.append(data_fields)

    # data.update({'mi_list': matrix_data_to_return, })
    # data.update({'packed_lists': data_to_return, })

    data.update({'mi_list': matrix_data_to_return,
                 'packed_lists': data_to_return, })

    return HttpResponse(json.dumps(data), content_type="application/json")


# sck - assay plate map - start a plate map from an existing study matrix
def fetch_assay_study_matrix_for_platemap(request):
    """
    Assay Plate Map Add - Start an assay plate map from an existing study matrix.
    """

    this_study = request.POST.get('study', '0')
    this_matrix = request.POST.get('matrix', '0')

    if not this_matrix:
        return HttpResponseServerError()

    data = {}
    data_to_return = []

    this_queryset = AssayMatrixItem.objects.filter(
        study_id=this_study
    ).filter(
        matrix_id=this_matrix
    ).prefetch_related(
        'matrix',
    ).order_by('matrix__name', 'row_index', 'column_index', 'name', )

    max_row_index = 0
    max_column_index = 0

    for each in this_queryset:
        if each.row_index > max_row_index:
            max_row_index = each.row_index
        if each.column_index > max_column_index:
            max_column_index = each.column_index

        data_fields = {
            'matrix_item_id': each.id,
            'matrix_item_text': each.name,
            'matrix_item_row_index': each.row_index,
            'matrix_item_column_index': each.column_index,
        }

        data_to_return.append(data_fields)

    number_of_rows = max_row_index + 1
    number_of_columns = max_column_index + 1

    # HANDY - must sort in place or get empty list back
    # copy list to new variable
    plate_sizes = assay_plate_reader_map_info_plate_size_choices_list
    # sort in place
    plate_sizes.sort()
    # print("list after sorting ", plate_sizes)

    # if not found, use the largest plate (last one in sorted list)
    my_size = plate_sizes[-1]
    # HARDCODED - set the default...
    my_column_size = 24
    for this_size in plate_sizes:
        row_size = assay_plate_reader_map_info_shape_row_dict.get(this_size)
        col_size = assay_plate_reader_map_info_shape_col_dict.get(this_size)
        if number_of_rows <= row_size and number_of_columns <= col_size:
            my_size = this_size
            my_column_size = col_size
            break

    # print(data_to_return)

    data.update({'mi_list': data_to_return,
                 'device_size': my_size,
                 'number_columns': my_column_size,
                 })

    return HttpResponse(json.dumps(data), content_type="application/json")


# sck - assay plate map - start a plate map from an existing study plate map
def fetch_assay_study_platemap_for_platemap(request):
    """
    Assay Plate Map Add - Start an assay plate map from an existing plate map.
    """

    this_study = request.POST.get('study', '0')
    this_platemap = request.POST.get('platemap', '0')

    # if not plate map was sent here, for some reason, or, if the platemap got corrupted and was non-numeric, exit
    if not this_platemap:
        return HttpResponseServerError()
    elif not this_platemap.isnumeric():
        return HttpResponseServerError()

    data = {}
    platemap_data_to_return = []
    data_to_return = []

    this_platemap_queryset = AssayPlateReaderMap.objects.filter(
        id=this_platemap
    ).prefetch_related(
        'standard_unit',
    )

    # should be just one
    for this_map in this_platemap_queryset:

        try:
            this_standard_unit_unit = this_map.standard_unit.unit
        except:
            this_standard_unit_unit = "-"
        try:
            this_standard_unit_id = this_map.standard_unit.id
        except:
            this_standard_unit_id = 0

        data_fields = {
            'name': this_map.name,
            'description': this_map.description,
            'device': this_map.device,
            'time_unit': this_map.time_unit,
            'volume_unit': this_map.volume_unit,
            'cell_count': this_map.cell_count,
            'study_assay_id': this_map.study_assay_id,
            # 'standard_unit': this_map.standard_unit.unit,
            'standard_unit': this_standard_unit_id,
            'platemap_id': this_platemap,
        }
        platemap_data_to_return.append(data_fields)

    # print("platemap_data_to_return")
    # print(platemap_data_to_return)

    this_queryset = AssayPlateReaderMapItem.objects.filter(
        study_id=this_study
    ).filter(
        assayplatereadermap_id=this_platemap
    ).prefetch_related(
        'assayplatereadermap',
        'matrix_item',
        'location',
    ).order_by('plate_index', 'pk', )

    for each in this_queryset:
        # print(each)
        # fields = each.__dict__
        # for field, value in each.items():
        #     print(field, value)
        try:
            item_matrix_item_text = each.matrix_item.name
        except:
            item_matrix_item_text = "-"
        try:
            item_location_text = each.location.name
        except:
            item_location_text = "-"

        data_fields = {
            # 'well_name': each.name,
            'well_use': each.well_use,
            'standard_value': each.standard_value,
            'matrix_item': each.matrix_item_id,
            'matrix_item_text': item_matrix_item_text,
            'location': each.location_id,
            'location_text': item_location_text,
            'dilution_factor': each.dilution_factor,
            'collection_volume': each.collection_volume,
            'collection_time': each.collection_time,
            'default_time': each.default_time
        }

        data_to_return.append(data_fields)

    # print("data_to_return")
    # print(data_to_return)

    data.update({'platemap_info': platemap_data_to_return,
                 'item_info': data_to_return, })

    # print("json.dumps(data)")
    # print(json.dumps(data))
    # print("past it")

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


# sck - Assay Plate Reader Upload Data File (for the LOAD already saved file form)
def fetch_review_plate_reader_data_file_only(request):
    this_file_id = request.POST.get('this_file_id', '0')
    file_delimiter = request.POST.get('file_delimiter', '0')

    # print(this_file_id )
    # print(file_delimiter)

    if not this_file_id:
        return HttpResponseServerError()

    this_queryset = AssayPlateReaderMapDataFile.objects.get(
        id=this_file_id
    )

    # using .read() used bytes, so changed to open()
    # my_file_object = this_queryset.plate_reader_file.read().decode('utf-8')
    # my_file_object = this_queryset.plate_reader_file.read()
    my_file_object = this_queryset.plate_reader_file.open()

    # this function is in utils.py
    file_info = review_plate_reader_data_file_return_file_list(my_file_object, file_delimiter)

    # print("file info")
    # print(file_info)

    data = {}
    data_file_list_to_return = []
    idx = 0
    # file_info is a list with a dictionary FOR EACH line in the file - start at 0
    for each in file_info[0]:
        # print(each)
        data_file_list = {
            'line': idx,
            'line_list': each,
        }
        # print(idx)
        # print(data_file_list)
        data_file_list_to_return.append(data_file_list)
        idx = idx + 1

    # print(data_file_list_to_return)

    data.update({'file_list': data_file_list_to_return, })
    return HttpResponse(json.dumps(data), content_type="application/json")


# sck - Assay Plate Reader Upload Data File (for the UPDATE file form)
def fetch_review_plate_reader_data_file_with_block_info(request):
    """
    Assay PLATE READER FILE UPDATE pull information when viewing or updating and existing plate map FILE (calls utility).
    """
    this_file_id = request.POST.get('this_file_id', '0')
    this_file_format_selected = request.POST.get('this_file_format_selected', '0')
    file_delimiter = request.POST.get('file_delimiter', '0')
    form_plate_size = request.POST.get('form_plate_size', '0')
    form_number_blocks = request.POST.get('form_number_blocks', '0')
    form_number_blank_columns = request.POST.get('form_number_blank_columns', '0')
    form_number_blank_rows = request.POST.get('form_number_blank_rows', '0')

    set_delimiter = request.POST.get('set_delimiter', '0')
    set_format = request.POST.get('set_format', '0')
    set_plate_size = request.POST.get('set_plate_size', '0')
    # these are legacy and should be deleted
    # number_plate_lines = request.POST.get('number_plate_lines', '0')
    # number_plate_columns = request.POST.get('number_plate_columns', '0')
    set_number_blocks = request.POST.get('set_number_blocks', '0')
    set_number_blank_columns = request.POST.get('set_number_blank_columns', '0')
    set_number_blank_rows = request.POST.get('set_number_blank_rows', '0')

    if not this_file_id:
        return HttpResponseServerError()

    set_dict = {}
    set_dict.update({'this_file_format_selected': this_file_format_selected})
    set_dict.update({'file_delimiter': file_delimiter})
    set_dict.update({'form_plate_size': form_plate_size})
    set_dict.update({'form_number_blocks': form_number_blocks})
    set_dict.update({'form_number_blank_columns': form_number_blank_columns})
    set_dict.update({'form_number_blank_rows': form_number_blank_rows})
    set_dict.update({'set_delimiter': set_delimiter})
    set_dict.update({'set_format': set_format})
    set_dict.update({'set_plate_size': set_plate_size})
    set_dict.update({'set_number_blocks': set_number_blocks})
    set_dict.update({'set_number_blank_columns': set_number_blank_columns})
    set_dict.update({'set_number_blank_rows': set_number_blank_rows})

    this_queryset = AssayPlateReaderMapDataFile.objects.get(
        id=this_file_id
    )

    # using .read() used bytes, so changed to open()
    # my_file_object = this_queryset.plate_reader_file.read().decode('utf-8')
    # my_file_object = this_queryset.plate_reader_file.read()
    my_file_object = this_queryset.plate_reader_file.open()

    # this function is in utils.py
    file_info = review_plate_reader_data_file_format(my_file_object, set_dict)

    data = {}
    data_to_return = []
    idx = 1
    # file_info is a list with a dictionary FOR EACH BLOCK (with the fields)
    for each in file_info[0]:
        # print(each)
        data_fields = {
            'data_block': idx,
            'data_block_metadata': each.get('data_block_metadata'),

            'line_start': each.get('line_start'),
            'line_end': each.get('line_end'),

            'delimited_start': each.get('delimited_start'),
            'delimited_end': each.get('delimited_end'),

            'block_delimiter': each.get('block_delimiter'),
            'plate_size': each.get('plate_size'),
            'plate_lines': each.get('plate_lines'),
            'plate_columns': each.get('plate_columns'),
            'number_blank_columns': each.get('number_blank_columns'),
            'number_blank_rows': each.get('number_blank_rows'),
            'calculated_number_of_blocks': each.get('calculated_number_of_blocks'),
        }
        data_to_return.append(data_fields)
        idx = idx + 1

    data_file_list_to_return = []
    idx = 0
    # file_info is a list with a dictionary FOR EACH line in the file - start at 0
    for each in file_info[1]:
        # print(each)
        data_file_list = {
            'line': idx,
            'line_list': each,
        }
        data_file_list_to_return.append(data_file_list)
        idx = idx + 1

    # print(data_file_list_to_return)

    data.update({'file_block_info': data_to_return,
                 'file_list': data_file_list_to_return, })
    return HttpResponse(json.dumps(data), content_type="application/json")


# sck - Assay Plate Reader Update Data File Blocks - Selected Plate Size
def fetch_plate_reader_data_block_plate_map_size(request):
    """
        Assay PLATE READER FILE UPDATE return plate size of selected plate map.
    """

    platemap_id_stringify = request.POST.get('platemap_id_stringify', '0')
    # print("platemap_id_stringify ", platemap_id_stringify)

    if not platemap_id_stringify:
        return HttpResponseServerError()

    # print(platemap_id_stringify)
    # print(type(platemap_id_stringify))
    # print(len(platemap_id_stringify))
    platemap_id_stringify1 = platemap_id_stringify[1:]
    platemap_id_stringify2 = platemap_id_stringify1[:-1]
    # print(platemap_id_stringify2)
    platemap_id_list = platemap_id_stringify2.split(",")
    # print(platemap_id_list)
    # print(len(platemap_id_list))

    data = {}
    data_to_return = []

    for this_platemap in platemap_id_list:
        # print("this_platemap ", this_platemap)
        # print(len(this_platemap))

        if this_platemap == '""':
            # print("if")
            map_device = ""
            map_time_unit = ""
            my_id = ""
            # print(my_id)
        else:
            # print('else')
            a = this_platemap[1:]
            b = a[:-1]
            my_id = int(b)
            # print(my_id)
            match_platemap = AssayPlateReaderMap.objects.filter(
                id=my_id
            )
            # is only one in queryset
            for each in match_platemap:
                map_device = each.device
                map_time_unit = each.time_unit

        map_device = map_device
        map_time_unit = map_time_unit

        data_fields = {
            'device': map_device,
            'time_unit': map_time_unit,
        }
        data_to_return.append(data_fields)

    data.update({'platemap_size_and_unit': data_to_return, })

    # print(data)

    return HttpResponse(json.dumps(data),
                        content_type="application/json")

# sck - assay plate map - Get raw value and time for display in existing plate map with file block attached.
def fetch_information_for_value_set_of_plate_map_for_data_block(request):
    """
    Assay Plate Map Update or View with Data File Block - Get raw value and time for display in existing plate map with file block attached.
    """

    this_data_file_block = request.POST.get('pk_data_block', '0')
    this_platemap = request.POST.get('pk_platemap', '0')
    the_num_colors = int(request.POST.get('num_colors', '0'))
    # print(this_data_file_block)
    # print(this_platemap)
    if not this_data_file_block:
        return HttpResponseServerError()
    elif not this_data_file_block.isnumeric():
        return HttpResponseServerError()

    # 20200522 changing schema since do not need to allow edit after plate map association
    # this_queryset = AssayPlateReaderMapItemValue.objects.filter(
    #     assayplatereadermapdatafileblock_id=this_data_file_block
    # ).filter(
    #     assayplatereadermap_id=this_platemap
    # ).order_by('plate_index', )

    # 20200522 update
    this_queryset = AssayPlateReaderMapItemValue.objects.filter(
        assayplatereadermapdatafileblock_id=this_data_file_block
    ).filter(
        assayplatereadermap_id=this_platemap
    ).prefetch_related(
        'assayplatereadermap',
    ).order_by(
        'assayplatereadermapitem__plate_index',
    )
    # print("this_queryset ", this_queryset)

    min_raw_value = this_queryset.aggregate(Min('raw_value')).get('raw_value__min')
    max_raw_value = this_queryset.aggregate(Max('raw_value')).get('raw_value__max')
    # print("min ", min_raw_value)
    # print("max ", max_raw_value)
    # print("color", the_num_colors)
    interval = (max_raw_value - min_raw_value) / (the_num_colors)
    # print("interval ", interval)

    bin_upper_limit_list = [0] * the_num_colors

    idx = 0
    while idx < the_num_colors:
        bin_upper_limit_list[idx] = min_raw_value + interval*idx
        # print(bin_upper_limit_list[idx])
        idx = idx + 1

    data = {}
    data_to_return = []

    for each in this_queryset:
        # print(each)
        # print("each.raw_value ", each.raw_value)
        if each.raw_value is None:
            bin_index = 0
        else:
            bin_index = sub_to_fetch_information_for_value_set_of_plate_map_for_data_block(bin_upper_limit_list, each.raw_value)
        # print("bin_index ", bin_index)
        data_fields = {
            'time': each.time,
            'raw_value': each.raw_value,
            'bin_index': bin_index,
        }
        # make sure to order by the plate_index
        data_to_return.append(data_fields)
        data.update({'block_data': data_to_return, })
    # print(data)
    return HttpResponse(json.dumps(data),
                        content_type="application/json")

def sub_to_fetch_information_for_value_set_of_plate_map_for_data_block(bin_upper_limit_list, raw_value):
    bin_index = 0
    idx = 0
    num_loops = len(bin_upper_limit_list)
    # print("num_loops ", num_loops)
    while idx < num_loops:
        # print("idx ", idx)
        # print("raw ", raw_value)
        # print("bin ", bin_upper_limit_list[idx])
        if raw_value <= bin_upper_limit_list[idx]:
            # print("less")
            # first time is it greater than or equal upper limit, record and return then break
            bin_index = idx
            break
        else:
            # print("else")
            bin_index = idx

        idx = idx + 1
    return bin_index

# sck - assay plate map - Get raw value and time for display in existing plate map with file block attached.
# 20200510 transitioning this to get the selection down in the forms.py
# eventually, can get rid of this, but do not do it until sure do not want to do this way
# but note that, might go back for performance reasons
def fetch_information_for_study_platemap_standard_file_blocks(request):
    """
    Assay Plate Map Calibrate - Get list of file blocks in this study with at least one standard on plate.
    """

    this_study = request.POST.get('study', '0')
    if not this_study:
        return HttpResponseServerError()


    as_value_formset_with_file_block_standard = AssayPlateReaderMapItemValue.objects.filter(
        study_id=this_study
    ).filter(
        assayplatereadermapdatafileblock__isnull=False
    ).prefetch_related(
        'assayplatereadermapdatafileblock',
        'assayplatereadermap',
        'assayplatereadermapitem',
    ).filter(
        assayplatereadermapitem__well_use='standard'
    ).order_by(
        'assayplatereadermapdatafileblock__id', 'well_use'
    )
    # here here make sure gets well_use after change schema

    # print(as_value_formset_with_file_block_standard)

    number_filed_combos_standard = len(as_value_formset_with_file_block_standard)
    data = {}

    data_to_return_fileblock_database_pk = []
    data_to_return_string = []
    data_to_return_platemap_pk = []

    prev_file = "none"
    prev_data_block_file_specific_pk = 0

    # print(as_value_formset_with_file_block_standard)

    # want the first option to be no standards, pass data through
    # ('no_processing', 'No Processing (send Raw Values)'
    # distinct_plate_map_with_select_standard_string.append(('-1', 'No Processing (send Raw Values)'))
    # distinct_plate_map_with_block_standard_pk.append(('-1', '-1'))

    # queryset should have one record for each value SET that HAS a file-block and at least one standard associated to it
    if number_filed_combos_standard > 0:
        i = 0
        for record in as_value_formset_with_file_block_standard:
            # print("i ", i)

            short_file_name = os.path.basename(str(record.assayplatereadermapdatafile.plate_reader_file))
            # this is the data block of the file (for file 0 to something...)
            data_block_file_specific_pk = record.assayplatereadermapdatafileblock.data_block

            if prev_file == short_file_name and prev_data_block_file_specific_pk == data_block_file_specific_pk:
                pass
            else:
                data_platemap_pk = record.assayplatereadermap_id
                data_platemap_name = record.assayplatereadermap.name
                data_block_metadata = record.assayplatereadermapdatafileblock.data_block_metadata
                data_block_database_pk = record.assayplatereadermapdatafileblock.id

                # make a choice tuple list for showing selections and a choice tuple list of containing the file pk and block pk for javascript
                pick_string = 'PLATEMAP: ' + data_platemap_name + '  FILE: ' + short_file_name + '  BLOCK: ' + data_block_metadata + ' (' + str(data_block_file_specific_pk) + ')'
                data_to_return_fileblock_database_pk.append({str(i): data_block_database_pk})
                data_to_return_string.append({str(i): pick_string})
                data_to_return_platemap_pk.append({str(i): data_platemap_pk})

            prev_file = short_file_name
            prev_data_block_file_specific_pk = data_block_file_specific_pk
            i = i + 1

    data.update({'block_data_fileblock_database_pk': data_to_return_fileblock_database_pk, 'block_data_string': data_to_return_string, 'block_data_platemap_pk': data_to_return_platemap_pk,})
    # print(data)
    return HttpResponse(json.dumps(data),
                        content_type="application/json")


# sck - Find the multiplier for the unit conversion in the plate map integration
def fetch_multiplier_for_data_processing_plate_map_integration(request):
    """
        Assay PLATE READER MAP DATA PROCESSING find the multiplier
    """

    target = request.POST.get('target', '0')
    method = request.POST.get('method', '0')
    reportin_unit = request.POST.get('unit', '0')
    standard_unit = request.POST.get('standard_unit', '0')
    volume_unit = request.POST.get('volume_unit', '0')
    well_volume = request.POST.get('well_volume', '0')
    cell_count = request.POST.get('cell_count', '0')
    molecular_weight = request.POST.get('molecular_weight', '0')
    time_unit = request.POST.get('time_unit', '0').lower()

    if not standard_unit:
        return HttpResponseServerError()

    try:
        cell_count = float(cell_count)
    except:
        cell_count = 0.0
    try:
        well_volume = float(well_volume)
    except:
        well_volume = 0.0
    try:
        molecular_weight = float(molecular_weight)
    except:
        molecular_weight = 0.0

    # there were added to show the steps of the multiplier because of the difficulty of explaining how it worked
    multiplier_value_short = 1
    multiplier_string_short = '1'

    multiplier_string1 = '1'
    multiplier_string2 = '1'
    multiplier_string3 = '1'
    multiplier_string4 = '1'
    multiplier_string5 = '1'
    multiplier_string6 = '1'
    multiplier_string7 = '1'
    multiplier_string8 = '1'
    multiplier_string9 = '1'
    rmultiplier_step_string = '1'
    rmultiplier_step = 1

    # limit option of mole units for all
    # print("**0A standard_unit: ", standard_unit)
    # print("**0A reportin_unit: ", reportin_unit)
    standard_unit = re.sub('M', 'mol/L', standard_unit)
    standard_unit = re.sub('N', 'nmol/L', standard_unit)
    standard_unit = re.sub('mols', 'mol', standard_unit)
    reportin_unit = re.sub('M', 'mol/L', reportin_unit)
    reportin_unit = re.sub('N', 'nmol/L', reportin_unit)
    reportin_unit = re.sub('mols', 'mol', reportin_unit)
    # print("**0B standard_unit: ", standard_unit)
    # print("**0B reportin_unit: ", reportin_unit)

    # set the defaults
    more_conversions_needed = "yes"
    multiplier = 1.0
    multiplier_string = reportin_unit + " = (" + standard_unit + ")"
    multiplier_string_display = ""
    data = {}
    data_to_return = []

    # do we just have a base unit conversion?
    long_list_of_things = sub_to_fetch_multiplier_for_data_processing_plate_map_integration(more_conversions_needed, standard_unit, reportin_unit)
    more_conversions_needed = long_list_of_things[0]
    rmultiplier = long_list_of_things[1]
    rmultiplier_string = long_list_of_things[2]
    rmultiplier_string_display = long_list_of_things[3]

    rmultiplier_step_string = long_list_of_things[6]

    # initial base unit conversion - first in the string, so not accumulating
    if rmultiplier_step_string == '-':
        multiplier_string1 = '1'
        multiplier_value_short = rmultiplier
        multiplier_string_short = "1 * "
    else:
        multiplier_string1 = rmultiplier_step_string
        multiplier_value_short = rmultiplier
        multiplier_string_short = str(sandrasGeneralFormatNumberFunction(rmultiplier)) + " * "

    # print("**0 first send: ", rmultiplier_string)
    # print("**0 first send: ", rmultiplier)
    # print("**0 standard_unit: ", standard_unit)

    if more_conversions_needed == "error" or more_conversions_needed == "done":
        multiplier = multiplier * rmultiplier
        multiplier_string = multiplier_string + rmultiplier_string
        multiplier_string_display = multiplier_string_display + rmultiplier_string_display
        more_conversions_needed = "STOP"
        # add the rest of the 1s to the string
        multiplier_string_short = multiplier_string_short + "1 * 1 * 1 * 1 * 1 * 1 * 1"

        # print("**1A first send: ", multiplier_string)
        # print("**1A first send: ", multiplier)
        # print("**1A standard_unit: ", standard_unit)

    elif more_conversions_needed == "yes":

        # print("**1B first send: ", multiplier_string)
        # print("**1B first send:  ", multiplier)
        # print("**1B standard_unit: ", standard_unit)

        # did not fail but need more conversion
        # try seeing if a mole to mass conversion is needed (only works one way - mole to mass)
        # print("re.search(r'mol', standard_base_unit_unit) ",re.search(r'mol', standard_base_unit_unit))

        mysubstring = ''
        mysubmultiplier = 1

        if re.search(r'pmol', standard_unit) and re.search(r'g', reportin_unit):
            standard_unit = re.sub('mol', 'g', standard_unit)
            multiplier = multiplier * (1/10**12) * molecular_weight
            multiplier_string = multiplier_string + "*(1g/10^12pg)*(" + str(molecular_weight) + "g/mol)"
            mysubmultiplier = (1/10**12) * molecular_weight
            mysubstring = "(1g/10^12pg)*(" + str(molecular_weight) + "g/mol)"
        elif re.search(r'nmol', standard_unit) and re.search(r'g', reportin_unit):
            standard_unit = re.sub('mol', 'g', standard_unit)
            multiplier = multiplier * (1/10**9) * molecular_weight
            multiplier_string = multiplier_string + "*(1g/10^9ng)*(" + str(molecular_weight) + "g/mol)"
            mysubmultiplier = (1/10**9) * molecular_weight
            mysubstring = "(1g/10^9ng)*(" + str(molecular_weight) + "g/mol)"
        elif re.search(r'µmol', standard_unit) and re.search(r'g', reportin_unit):
            standard_unit = re.sub('mol', 'g', standard_unit)
            multiplier = multiplier * (1/10**6) * molecular_weight
            multiplier_string = multiplier_string + "*(1g/10^6µg)*(" + str(molecular_weight) + "g/mol)"
            mysubmultiplier = (1/10**6) * molecular_weight
            mysubstring = "(1g/10^6µg)*(" + str(molecular_weight) + "g/mol)"
        elif re.search(r'mmol', standard_unit) and re.search(r'g', reportin_unit):
            standard_unit = re.sub('mol', 'g', standard_unit)
            multiplier = multiplier * (1/10**3) * molecular_weight
            multiplier_string = multiplier_string + "*(1g/10^3mg)*(" + str(molecular_weight) + "g/mol)"
            mysubmultiplier = (1/10**3) * molecular_weight
            mysubstring = "(1g/10^3mg)*(" + str(molecular_weight) + "g/mol)"
        elif re.search(r'mol', standard_unit) and re.search(r'g', reportin_unit):
            standard_unit = re.sub('mol', 'g', standard_unit)
            multiplier = multiplier * molecular_weight
            #multiplier_string = multiplier_string + " * (1g/1g) * (" + str(molecular_weight) + "g/mol)"
            multiplier_string = multiplier_string + "*(" + str(molecular_weight) + "g/mol)"
            mysubmultiplier = molecular_weight
            mysubstring = "(1g/1g) * (" + str(molecular_weight) + "g/mol)"

        # Molar to Mass
        if mysubstring == '':
            multiplier_string2 = '1'
            multiplier_value_short = multiplier_value_short
            multiplier_string_short = multiplier_string_short + "1 * "
        else:
            multiplier_string2 = str(sandrasGeneralFormatNumberFunction(mysubmultiplier)) + " = " + mysubstring
            multiplier_value_short = multiplier_value_short * mysubmultiplier
            multiplier_string_short = multiplier_string_short + str(sandrasGeneralFormatNumberFunction(mysubmultiplier)) + " * "

        # if there was a 'well', there will be a need to divide by the well volume, so that before checking next

        # print("1B.1** after mole to mass string: ", multiplier_string)
        # print("1B.1** after mole to mass value: ", multiplier)
        # print("1B.1** standard_unit: ", standard_unit)

        # did not fail but need more conversion
        # see if standard unit has a 'well' in it
        locationWellStart = -1
        locationWellEnd = -1
        try:
            locationWellStart = re.search(r'well', standard_unit).start()
            locationWellEnd = re.search(r'well', standard_unit).end()
        except:
            locationWellStart = -1
            locationWellEnd = -1

        # print("locationWellStart ", locationWellStart)
        # print("locationWellEnd ", locationWellEnd)

        mysubstring = ''
        mysubmultiplier = 1

        if locationWellStart >= 0:
            # print("stardard_unit[:locationWellStart] ", standard_unit[:locationWellStart])
            # print("stardard_unit[locationWellEnd:] ", standard_unit[locationWellEnd:])
            standard_unit = standard_unit[:locationWellStart].strip() + volume_unit + standard_unit[locationWellEnd:].strip()
            # print("standard_unit ", standard_unit)
            multiplier = multiplier / well_volume
            multiplier_string = multiplier_string + "*(well/" + str(well_volume) + " " + volume_unit + ")"
            # print("multiplier string ", multiplier_string)
            # print("standard_unit ", standard_unit)
            mysubstring = "well/" + str(well_volume) + " " + volume_unit
            # Well volume adjustment
            mysubmultiplier = 1 / well_volume
            multiplier_string3 = str(sandrasGeneralFormatNumberFunction(mysubmultiplier)) + " = " + mysubstring
            multiplier_value_short = multiplier_value_short * mysubmultiplier
            multiplier_string_short = multiplier_string_short + str(sandrasGeneralFormatNumberFunction(mysubmultiplier)) + " * "
        else:
            multiplier_string3 = '1'
            multiplier_value_short = multiplier_value_short
            multiplier_string_short = multiplier_string_short + "1 * "

        # now, check and see if, with the mol to g and the well to well volume if base unit will convert
        # are we down to just a base unit conversion?
        long_list_of_things = sub_to_fetch_multiplier_for_data_processing_plate_map_integration(more_conversions_needed, standard_unit, reportin_unit)
        more_conversions_needed = long_list_of_things[0]
        rmultiplier = long_list_of_things[1]
        rmultiplier_string = long_list_of_things[2]
        rmultiplier_string_display = long_list_of_things[3]
        rmultiplier_step_string = long_list_of_things[6]

        # Secondary base unit conversion
        if rmultiplier_step_string == '-':
            multiplier_string4 = '1'
            multiplier_value_short = multiplier_value_short * rmultiplier
            multiplier_string_short = multiplier_string_short + "1 * "
        else:
            multiplier_string4 = rmultiplier_step_string
            multiplier_value_short = multiplier_value_short * rmultiplier
            multiplier_string_short = multiplier_string_short + str(sandrasGeneralFormatNumberFunction(rmultiplier)) + " * "

        # print("1B.2** after mole to mass: ", multiplier_string)
        # print("1B.2** after mole to mass: ", multiplier)
        # print("1B.2** standard_unit: ", standard_unit)
        # print("1B.2** more_conversions_needed: ", more_conversions_needed)

    if more_conversions_needed == "error" or more_conversions_needed == "done":
        # either error or done
        multiplier = multiplier * rmultiplier
        multiplier_string = multiplier_string + rmultiplier_string
        multiplier_string_display = multiplier_string_display + " " + rmultiplier_string_display
        more_conversions_needed = "STOP"
        # add the rest of the 1s to the string
        multiplier_string_short = multiplier_string_short + "1 * 1 * 1 * 1 "

        # print("2A** after per mol to mass and /well: ", multiplier_string)
        # print("2A** after per mol to mass and /well: ", multiplier)
        # print("2A** standard_unit: ", standard_unit)

    elif more_conversions_needed == "yes":
        # print("2B** after per mol to mass and /well: ", multiplier_string)
        # print("2B** standard_unit: ", standard_unit)

        # did not fail but need more conversion
        # see if need to multiple by the efflux volume

        # if standard_unit has L and reporting unit doesn't have L
        # this is set up to multiple by the volume unit and divide by the time unit
        # print(re.search(r'L', standard_unit))
        # print(re.search(r'L', reportin_unit))
        # put into L

        mysubstring = ''
        mysubmultiplier = 1

        if re.search(r'L', standard_unit) and not re.search(r'L', reportin_unit):
            if re.search(r'/pL', standard_unit):
                standard_unit = re.sub('/pL', '', standard_unit)
                multiplier = multiplier * 10**12
                multiplier_string = multiplier_string + "*(efflux " + volume_unit + ")*(10^12pL/1L)"
                mysubmultiplier = 10**12
                mysubstring = volume_unit + " * (10^12pL/1L) "
            elif re.search(r'/nL', standard_unit):
                standard_unit = re.sub('/nL', '', standard_unit)
                multiplier = multiplier * 10**9
                multiplier_string = multiplier_string + "*(efflux " + volume_unit + ")*(10^9nL/1L)"
                mysubmultiplier = 10**9
                mysubstring = volume_unit + " * (10^9nL/1L) "
            elif re.search(r'/µL', standard_unit):
                standard_unit = re.sub('/µL', '', standard_unit)
                multiplier = multiplier * 10**6
                multiplier_string = multiplier_string + "*(efflux " + volume_unit + ")*(10^6µL/1L)"
                mysubmultiplier = 10**6
                mysubstring = volume_unit + " * (10^6µL/1L) "
            elif re.search(r'/mL', standard_unit):
                standard_unit = re.sub('/mL', '', standard_unit)
                multiplier = multiplier * 10**3
                multiplier_string = multiplier_string + "*(efflux " + volume_unit + ")*(10^3mL/1L)"
                mysubmultiplier = 10**3
                mysubstring = volume_unit + " * (10^3mL/1L) "
            elif re.search(r'/L', standard_unit):
                standard_unit = re.sub('/L', '', standard_unit)
                multiplier = multiplier
                # multiplier_string = multiplier_string + " *(efflux " + volume_unit + " * (1L/1L)"
                multiplier_string = multiplier_string + "*(efflux " + volume_unit + ")"
                mysubmultiplier = 1
                mysubstring = volume_unit + " * (1L/1L) "


            if re.search(r'pL', volume_unit):
                multiplier = multiplier / 10**12
                multiplier_string = multiplier_string + "*(1L/10^12pL)"
                mysubmultiplier = mysubmultiplier / 10**12
                mysubstring = mysubstring + "*(1L/1L) "
            elif re.search(r'nL', volume_unit):
                multiplier = multiplier / 10**9
                multiplier_string = multiplier_string + "*(1L/10^9nL)"
                mysubmultiplier = mysubmultiplier / 10**9
                mysubstring = mysubstring + "*(1L/10^9nL) "
            elif re.search(r'µL', volume_unit):
                multiplier = multiplier / 10**6
                multiplier_string = multiplier_string + "*(1L/10^6µL)"
                mysubmultiplier = mysubmultiplier / 10**6
                mysubstring = mysubstring + "*(1L/10^6µL)"
            elif re.search(r'mL', volume_unit):
                multiplier = multiplier / 10**3
                multiplier_string = multiplier_string + "*(1L/10^3mL)"
                mysubmultiplier = mysubmultiplier / 10**3
                mysubstring = mysubstring + "*(1L/10^3mL)"
            elif re.search(r'L', volume_unit):
                multiplier = multiplier
                # multiplier_string = multiplier_string + " * (1L/1L) "
                multiplier_string = multiplier_string
                mysubmultiplier = mysubmultiplier / 1
                mysubstring = mysubstring + "*(1L/1L) "

            # Well volume adjustment when efflux volume used
            if mysubstring == '':
                multiplier_string5 = '1'
                multiplier_value_short = multiplier_value_short
                multiplier_string_short = multiplier_string_short + "1 * "
            else:
                mysubmultiplier = mysubmultiplier
                multiplier_string5 = str(sandrasGeneralFormatNumberFunction(mysubmultiplier)) + " = " + mysubstring
                multiplier_value_short = multiplier_value_short * mysubmultiplier
                multiplier_string_short = multiplier_string_short + str(
                    sandrasGeneralFormatNumberFunction(mysubmultiplier)) + " * "

        # print("2B.1** after volume prep: ", multiplier_string)
        # print("2B.1** after volume prep: ", multiplier)
        # print("2B.1** standard_unit: ", standard_unit)

        mysubstring = ''
        mysubmultiplier = 1

        if re.search(r'y', reportin_unit) or re.search(r'h', reportin_unit) or re.search(r'min', reportin_unit):
            if re.search(r'y', reportin_unit):
                standard_unit = standard_unit + "/day"
                if time_unit == "day":
                    multiplier = multiplier * 1
                    # multiplier_string = multiplier_string + " * (1/efflux collection day) * (1day/1day)"
                    multiplier_string = multiplier_string + "*(1/efflux collection day)"
                    mysubmultiplier = 1
                    mysubstring = "(1/day)*(1day/1day)"
                elif time_unit == "hour":
                    multiplier = multiplier * 24
                    multiplier_string = multiplier_string + "*(1/efflux collection hour)*(24hour/1day)"
                    mysubmultiplier = 24
                    mysubstring = "(1/hour)*(24hour/1day)"
                else:
                    multiplier = multiplier * 1440
                    multiplier_string = multiplier_string + "*(1/efflux collection minute)*(1440minute/1day)"
                    mysubmultiplier = 1440
                    mysubstring = "(1/minute)*(1440minute/1day)"

            elif re.search(r'h', reportin_unit):
                standard_unit = standard_unit + "/hour"
                if time_unit == "day":
                    multiplier = multiplier * 1/24
                    multiplier_string = multiplier_string + "*(1/efflux collection day)*(1day/24hour)"
                    mysubmultiplier = 1/24
                    mysubstring = "(1/day)*(1day/24hour)"
                elif time_unit == "hour":
                    multiplier = multiplier * 1
                    # multiplier_string = multiplier_string + " * (1/efflux collection hour) * (1hour/1hour)"
                    multiplier_string = multiplier_string + "*(1/efflux collection hour)"
                    mysubmultiplier = 1
                    mysubstring = "(1/hour)*(1hour/1hour)"
                else:
                    multiplier = multiplier * 60
                    multiplier_string = multiplier_string + "*(1/efflux collection minute)*(60minute/1hour)"
                    mysubmultiplier = 60
                    mysubstring = "(1/minute)*(60minute/1hour)"

            elif re.search(r'min', reportin_unit):
                standard_unit = standard_unit + "/minute"
                if time_unit == "day":
                    multiplier = multiplier / 1440
                    multiplier_string = multiplier_string + "*(1/efflux collection day)*(1day/1440minute)"
                    mysubmultiplier = 1 / 1440
                    mysubstring = "(1/day)*(1day/1440minute)"
                elif time_unit == "hour":
                    multiplier = multiplier / 60
                    multiplier_string = multiplier_string + "*(1/efflux collection hour)*(1hour/60minute)"
                    mysubmultiplier = 1 / 60
                    mysubstring = "(1/hour)*(1hour/60minute)"
                else:
                    multiplier = multiplier * 1
                    # multiplier_string = multiplier_string + "*(1/efflux collection minute)*(1minute/1minute)"
                    multiplier_string = multiplier_string + "*(1/efflux collection minute)"
                    mysubmultiplier = 1
                    mysubstring = "(1/minute)*(1minute/1minute)"

            # Time adjustment for efflux time unit
            if mysubstring == '':
                multiplier_string6 = '1'
                multiplier_value_short = multiplier_value_short
                multiplier_string_short = multiplier_string_short + "1 * "
            else:
                mysubmultiplier = mysubmultiplier
                multiplier_string6 = str(sandrasGeneralFormatNumberFunction(mysubmultiplier)) + " = " + mysubstring
                multiplier_value_short = multiplier_value_short * mysubmultiplier
                multiplier_string_short = multiplier_string_short + str(
                    sandrasGeneralFormatNumberFunction(mysubmultiplier)) + " * "


        # print("2B.2** after time prep: ", multiplier_string)
        # print("2B.2** after time prep: ", multiplier)
        # print("2B.2** standard_unit: ", standard_unit)

        # >> > m = re.search("is", String)
        # >> > m.span()
        # (2, 4)
        # >> > m.start()
        # 2
        # >> > m.end()
        # 4

        # deal with the reporting unit containing /cells
        # 20201104 added the try/except for non cell units and/or non 10 units (else got error on server)
        try:
            locationCellsStart = re.search(r'cells', reportin_unit).start()
        except:
            locationCellsStart = -1
        try:
            locationCellsEnd = re.search(r'cells', reportin_unit).end()
        except:
            locationCellsEnd = -1
        try:
            location10hatStart = re.search(r'10\^', reportin_unit).start()
        except:
            location10hatStart = -1
        try:
            location10hatEnd = re.search(r'10\^', reportin_unit).end()
        except:
            location10hatEnd = -1

        # print("locationCellsStart ",locationCellsStart)
        # print("locationCellsEnd ",locationCellsEnd)
        # print("location10hatStart ",location10hatStart)
        # print("location10hatEnd ",location10hatEnd)
        # print("heading back: ", multiplier_string)


        if locationCellsStart >= 0 and location10hatStart >= 0:
            # reportin unit has cells and 10^ in it; making assumption that the standard unit does not and need conversion
            cellNumberExponent = reportin_unit[location10hatEnd:locationCellsStart].strip()
            cellString = reportin_unit[location10hatStart:].strip()

            # print("locationCellsStart ", locationCellsStart)
            # print("location10hatStart ",location10hatStart)
            # print("cellNumberExponent = reportin_unit[location10hatEnd:locationCellsStart].strip()  ", cellNumberExponent)
            # print("cellString = reportin_unit[location10hatStart:].strip() ", cellString)
            # locationCellsStart  12
            # location10hatStart  7
            # cellNumberExponent = reportin_unit[location10hatEnd:locationCellsStart].strip()   6
            # cellString = reportin_unit[location10hatStart:].strip()  10^6 cells

            mysubstring = ''
            mysubmultiplier = 1

            try:
                intcellNumberExponent = int(cellNumberExponent)
                multiplier = multiplier * (10 ** intcellNumberExponent) / cell_count
                multiplier_string = multiplier_string + "*(10^" + str(intcellNumberExponent) + ")/(" + str(cell_count) + "*10^" + str(intcellNumberExponent) + " cells)"
                mysubstring = "(10^" + str(intcellNumberExponent) + ")/(" + str(cell_count) + "*10^" + str(intcellNumberExponent) + " cells)"
                              # + " Note: 10^" + str(intcellNumberExponent) + " will remain in the denominator."
                mysubmultiplier = (10 ** intcellNumberExponent) / cell_count
            except:
                multiplier = 0.0
                multiplier_string = multiplier_string + " PROBLEM with Cell Number division."
                multiplier_string_display = multiplier_string_display + " [This is not a complete multiplier]"


            # Adjust for the number of cells when normalizing
            if mysubstring == '':
                multiplier_string7 = '1'
                multiplier_value_short = multiplier_value_short
                multiplier_string_short = multiplier_string_short + "1 * "
            else:
                mysubmultiplier = mysubmultiplier
                multiplier_string7 = str(sandrasGeneralFormatNumberFunction(mysubmultiplier)) + " = " + mysubstring
                multiplier_value_short = multiplier_value_short * mysubmultiplier
                multiplier_string_short = multiplier_string_short + str(
                    sandrasGeneralFormatNumberFunction(mysubmultiplier)) + " * "

            # there is an assumption here that the 'cells' was last in the string
            standard_unit = standard_unit + "/" + cellString
            # print("standard_unit ", standard_unit)

            # print("2B.3** after cells prep: ", multiplier_string)
            # print("2B.3** after cells prep: ", multiplier)
            # print("2B.3** standard_unit: ", standard_unit)

            # are we down to just a base unit conversion?
            long_list_of_things = sub_to_fetch_multiplier_for_data_processing_plate_map_integration(more_conversions_needed, standard_unit, reportin_unit)
            more_conversions_needed = long_list_of_things[0]
            rmultiplier = long_list_of_things[1]
            rmultiplier_string = long_list_of_things[2]
            rmultiplier_string_display = long_list_of_things[3]
            rmultiplier_step_string = long_list_of_things[6]

            # Tert base unit conversion
            if rmultiplier_step_string == '-':
                multiplier_string8 = '1'
                multiplier_value_short = multiplier_value_short * rmultiplier
                multiplier_string_short = multiplier_string_short + "1"
            else:
                multiplier_string8 = rmultiplier_step_string
                multiplier_value_short = multiplier_value_short * rmultiplier
                multiplier_string_short = multiplier_string_short + str(sandrasGeneralFormatNumberFunction(rmultiplier))

    if more_conversions_needed == "error" or more_conversions_needed == "done":
        # either error or done
        multiplier = multiplier * rmultiplier
        multiplier_string = multiplier_string + rmultiplier_string
        multiplier_string_display = multiplier_string_display + " " + rmultiplier_string_display
        more_conversions_needed = "STOP"
        # print("3A** after per cells: ", multiplier_string)
        # print("3A** after per cells: ", multiplier)
        # print("3A** standard_unit: ", standard_unit)
    elif more_conversions_needed == "yes":
        # print("3B1** after per mol to mass and /well: ", multiplier_string)
        # print("3B1** after per mol to mass and /well: ", multiplier)
        # print("3B1** standard_unit: ", standard_unit)
        multiplier = 0.0
        multiplier_string = multiplier_string + "  Did not have all the information needed to complete the conversion."
        multiplier_string_display = multiplier_string_display + " " + rmultiplier_string_display + " [This is not a complete multiplier]"
        # print("3B2** after per mol to mass and /well: ", multiplier_string)
        # print("3B2** after per mol to mass and /well: ", multiplier)
        # print("3B2** standard_unit: ", standard_unit)

    # print("right before return: ", multiplier_string)
    # print("standard_unit: ", standard_unit)
    # print("--------")
    # load the data for sending back
    data_fields = {
        'multiplier': str(multiplier),
        'multiplier_string': multiplier_string,
        'multiplier_string_display': multiplier_string_display,
        'multiplier_string_short': multiplier_string_short,
        'multiplier_value_short': str(sandrasGeneralFormatNumberFunction(multiplier_value_short)),
        'multiplier_string1': multiplier_string1,
        'multiplier_string2': multiplier_string2,
        'multiplier_string3': multiplier_string3,
        'multiplier_string4': multiplier_string4,
        'multiplier_string5': multiplier_string5,
        'multiplier_string6': multiplier_string6,
        'multiplier_string7': multiplier_string7,
        'multiplier_string8': multiplier_string8,
        'multiplier_string9': multiplier_string9,
    }
    data_to_return.append(data_fields)

    data.update({'multiplier_data': data_to_return, })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def sub_to_fetch_multiplier_for_data_processing_plate_map_integration(more_conversions_needed, standard_unit, reportin_unit):
    multiplier = 1
    multiplier_string = ""
    multiplier_string_display = ""
    standard_scale_factor = 0
    standard_base_unit_unit = "unk"
    reportin_scale_factor = 0
    reportin_base_unit_unit = "unk"
    multiplier_step_string = "-"

    # check to see if the standard_unit is now equal to the reporting_unit
    if reportin_unit == standard_unit:
        # nothing needed, send back done
        multiplier = 1.0
        multiplier_string = ""
        more_conversions_needed = "done"
    else:
        # do complete easiest case first, before mix in a lot of custom options
        standard_unit_queryset = PhysicalUnits.objects.filter(
            unit=standard_unit
        ).prefetch_related(
            'base_unit',
        )
        lenStandardBase = len(standard_unit_queryset)

        if lenStandardBase == 0:
            multiplier = 0.0
            multiplier_string = multiplier_string + " Missing Base Unit in MPS Database."
            multiplier_string_display = multiplier_string_display + " Could not find " + standard_unit + " in the database physical unit list. Add it and an associated base unit before continuing. "
            more_conversions_needed = "error"

        reportin_unit_queryset = PhysicalUnits.objects.filter(
            unit=reportin_unit
        ).prefetch_related(
            'base_unit',
        )
        lenReportinBase = len(reportin_unit_queryset)

        if lenReportinBase == 0:
            multiplier = 0.0
            multiplier_string = multiplier_string + " Missing Base Unit in MPS Database."
            multiplier_string_display = multiplier_string_display + " Could not find " + reportin_unit + " in the database physical unit list. Add it and an associated base unit before continuing. "
            more_conversions_needed = "error"

        if lenStandardBase > 0 and lenReportinBase > 0:
            # should only be one...
            for each in standard_unit_queryset:
                standard_scale_factor = each.scale_factor
                standard_base_unit_unit = each.base_unit.unit

            for each in reportin_unit_queryset:
                reportin_scale_factor = each.scale_factor
                reportin_base_unit_unit = each.base_unit.unit

            if standard_base_unit_unit == reportin_base_unit_unit:
                # units needed ONLY conversion through the base unit
                multiplier = standard_scale_factor * (1.0/reportin_scale_factor)
                multiplier_string = "( (scale factor base to standard: " + str(standard_scale_factor) + ")(base: " + standard_base_unit_unit + ")/(standard: "+standard_unit+") )" + "/( (scale factor base to reporting: " + str(reportin_scale_factor) + ")(base: " + reportin_base_unit_unit + ")/(reporting: "+reportin_unit+") )"
                more_conversions_needed = "done"

                multiplier_step_string = str(sandrasGeneralFormatNumberFunction(multiplier)) + " = " + "[ ( " + str(
                    standard_scale_factor) + " " + standard_base_unit_unit + ") / (" + standard_unit + ") ]" + " / [ (" + str(
                    reportin_scale_factor) + " " + reportin_base_unit_unit + ") / (" + reportin_unit + ") ]"

    # print("")
    # print("----SUB")
    # print("--multiplier ", multiplier)
    # print("--multiplier_string ", multiplier_string)
    # print("--standard_scale_factor ", standard_scale_factor)
    # print("--standard_base_unit_unit ", standard_base_unit_unit)
    # print("--reportin_scale_factor ", reportin_scale_factor)
    # print("--reportin_base_unit_unit ", reportin_base_unit_unit)
    # print("----SUB")
    # print("")

    return [more_conversions_needed,
            multiplier,
            multiplier_string,
            multiplier_string_display,
            standard_base_unit_unit,
            reportin_base_unit_unit,
            multiplier_step_string,
            ]

# sck - the main function for processing data - pass to a utils.py funciton
def fetch_data_processing_for_plate_map_integration(request):
    """
        Assay PLATE READER MAP DATA PROCESSING do the processing - used from ajax and from form save
    """

    called_from =                      request.POST.get('called_from', '0')
    study =                            request.POST.get('study', '0')
    pk_platemap =                      request.POST.get('pk_platemap', '0')
    pk_data_block =                    request.POST.get('pk_data_block', '0')
    plate_name =                       request.POST.get('plate_name', '0')
    form_calibration_curve =           request.POST.get('form_calibration_curve', '0')
    multiplier =                       request.POST.get('multiplier', '0')
    unit =                             request.POST.get('unit', '0')
    standard_unit =                    request.POST.get('standard_unit', '0')
    form_min_standard =                request.POST.get('form_min_standard', '-1')
    form_max_standard =                request.POST.get('form_max_standard', '-1')
    form_logistic4_A =                 request.POST.get('form_logistic4_A', '-1')
    form_logistic4_D =                 request.POST.get('form_logistic4_D', '-1')
    form_blank_handling =              request.POST.get('form_blank_handling', '0')
    radio_standard_option_use_or_not = request.POST.get('radio_standard_option_use_or_not', '0')
    radio_replicate_handling_average_or_not_0 = request.POST.get('radio_replicate_handling_average_or_not_0', '0')
    borrowed_block_pk =                request.POST.get('borrowed_block_pk', '0')
    borrowed_platemap_pk =             request.POST.get('borrowed_platemap_pk', '0')
    count_standards_current_plate =    request.POST.get('count_standards_current_plate', '0')
    target =                           request.POST.get('target', '0')
    method =                           request.POST.get('method', '0')
    time_unit =                        request.POST.get('time_unit', '0')
    volume_unit =                      request.POST.get('volume_unit', '0')
    user_notes =                       request.POST.get('user_notes', '0')
    user_omits =                       request.POST.get('user_omits', '0')
    plate_size =                       request.POST.get('plate_size', '0')

    if not standard_unit:
        return HttpResponseServerError()

    # make a dictionary to send to the utils.py
    set_dict = {
        'called_from'                     : called_from                             ,
        'study'                           : study                                   ,
        'pk_platemap'                     : pk_platemap                             ,
        'pk_data_block'                   : pk_data_block                           ,
        'plate_name'                      : plate_name                              ,
        'form_calibration_curve'          : form_calibration_curve                  ,
        'multiplier'                      : multiplier                              ,
        'unit'                            : unit                                    ,
        'standard_unit'                   : standard_unit                           ,
        'form_min_standard'               : form_min_standard                       ,
        'form_max_standard'               : form_max_standard                       ,
        'form_logistic4_A'                : form_logistic4_A                        ,
        'form_logistic4_D'                : form_logistic4_D                        ,
        'form_blank_handling'             : form_blank_handling                     ,
        'radio_standard_option_use_or_not': radio_standard_option_use_or_not        ,
        'radio_replicate_handling_average_or_not_0': radio_replicate_handling_average_or_not_0,
        'borrowed_block_pk'               : borrowed_block_pk                       ,
        'borrowed_platemap_pk'            : borrowed_platemap_pk                    ,
        'count_standards_current_plate'   : count_standards_current_plate           ,
        'target'                          : target                                  ,
        'method'                          : method                                  ,
        'time_unit'                       : time_unit                               ,
        'volume_unit'                     : volume_unit                             ,
        'user_notes': user_notes,
        'user_omits': user_omits,
        'plate_size': plate_size,
    }

    # print(set_dict)

    # this function is in utils.py
    data_mover = plate_reader_data_file_process_data(set_dict)
    data = {}
    data.update({
        'sendmessage':                        data_mover[0],
        'list_of_dicts_of_each_sample_row_each':   data_mover[1],
        'list_of_dicts_of_each_standard_row_points': data_mover[2],
        'list_of_dicts_of_each_standard_row_ave_points': data_mover[3],
        'list_of_dicts_of_each_standard_row_curve':  data_mover[4],
        'dict_of_parameter_labels':  data_mover[5],
        'dict_of_parameter_values':  data_mover[6],
        'dict_of_curve_info':        data_mover[7],
        'dict_of_standard_info':     data_mover[8],
        'list_of_dicts_of_each_sample_row_average': data_mover[9],
        })
    return HttpResponse(json.dumps(data), content_type="application/json")


# sck omic data find sample information if group already in the upload file
def fetch_omic_sample_info_from_upload_data_table(request):
    """
        Assay Omic Data File get the sample info if the group previously added to upload table
    """

    # if changing a group, need to get all the updated info
    # if an add page, need to call to clear out the location list
    # if update page, need to get the model location list

    # if called_from a load, have to do both (did them here to avoid race errors)
    called_from = request.POST.get('called_from', '0')
    # could be called from change, load-add, load-update
    groupIDc = int(request.POST.get('groupIDc', '0'))
    groupPkc = int(request.POST.get('groupPkc', '0'))
    groupID1 = int(request.POST.get('groupID1', '0'))
    groupPk1 = int(request.POST.get('groupPk1', '0'))
    groupId2 = int(request.POST.get('groupId2', '0'))
    groupPk2 = int(request.POST.get('groupPk2', '0'))

    # when called from is a change, we are only working with ONE, the groupIDc and groupPkc
    # note that the ID is the id of the changed group (could be first or second on the form)
    # or the IDs on the form (1 and 2 - for the load-add and load-update)

    # these will hold the change results or form group 1
    timemess1 = ""
    locmess1 = ""
    day1 = None
    hour1 = None
    minute1 = None
    loc_pk1 = None
    location_dict1 = {}
    # these are the group 2 form defaults
    timemess2 = ""
    locmess2 = ""
    day2 = None
    hour2 = None
    minute2 = None
    loc_pk2 = None
    location_dict2 = {}

    if called_from == 'change' and groupPkc > 0:
        sample_info = sub_fetch_omic_sample_info_from_upload_data_table(groupPkc)
        timemess1 = sample_info[0]
        locmess1 = sample_info[1]
        day1 = sample_info[2]
        hour1 = sample_info[3]
        minute1 = sample_info[4]
        loc_pk1 = sample_info[5]

        model_row = AssayGroup.objects.only('organ_model').get(pk=groupPkc).organ_model
        this_model_pk = model_row.id
        location_dict1 = sub_fetch_model_location_dictionary(this_model_pk)

    if called_from == 'load-update' and groupPk1 > 0:
        # loading an update page, get the correct list for group1
        model_row = AssayGroup.objects.only('organ_model').get(pk=groupPk1).organ_model
        this_model_pk = model_row.id
        location_dict1 = sub_fetch_model_location_dictionary(this_model_pk)

    if called_from == 'load-update' and groupPk2 > 0:
        # loading an update page, get the correct list for group2
        model_row = AssayGroup.objects.only('organ_model').get(pk=groupPk2).organ_model
        this_model_pk = model_row.id
        location_dict2 = sub_fetch_model_location_dictionary(this_model_pk)

    # print("l1 ",location_dict1)
    # print("l2 ", location_dict2)

    # if the mess is found, the replace will happen in the form field in the html file
    data = {}
    data.update({
        'timemess1': timemess1,
        'day1': day1,
        'hour1': hour1,
        'minute1': minute1,
        'locmess1': locmess1,
        'sample_location_pk1': loc_pk1,
        'location_dict1': location_dict1,
        'timemess2': timemess2,
        'day2': day2,
        'hour2': hour2,
        'minute2': minute2,
        'locmess2': locmess2,
        'sample_location_pk2': loc_pk2,
        'location_dict2': location_dict2,
    })

    # print(data)
    return HttpResponse(json.dumps(data), content_type="application/json")


def fetch_this_file_is_this_study(request):
    omic_data_file = request.POST.get('omic_data_file', '0')
    study_id = int(request.POST.get('study_id', '0'))
    data_file_pk = int(request.POST.get('data_file_pk', '0'))

    continue_message = this_file_same_as_another_in_this_study(omic_data_file, study_id, data_file_pk)
    true_to_continue = continue_message[0]
    message = continue_message[1]

    data = {}
    data.update({
        'true_to_continue': true_to_continue,
        'message': message,
    })
    return HttpResponse(json.dumps(data), content_type="application/json")


def sub_fetch_omic_sample_info_from_upload_data_table(this_pk):
    locmess = "no"
    loc_pk = None
    timemess = "no"
    times = None
    day = None
    hour = None
    minute = None

    # find time if a previous instance with this group has been saved
    # note that, must search when saved as EITHER a group 1 or a group 2
    queryset1 = AssayOmicDataFileUpload.objects.filter(
        group_1=this_pk
    ).aggregate(Max('time_1'))['time_1__max']
    queryset2 = AssayOmicDataFileUpload.objects.filter(
        group_2=this_pk
    ).aggregate(Max('time_2'))['time_2__max']

    if queryset1 is not None and queryset2 is not None:
        timemess = "found"
        if queryset1 > queryset2:
            times = get_split_times(queryset1)
        else:
            times = get_split_times(queryset2)
    elif queryset1 is not None:
        times = get_split_times(queryset1)
    elif queryset2 is not None:
        times = get_split_times(queryset2)

    if times is not None:
        day = times.get("day")
        hour = times.get("hour")
        minute = times.get("minute")

    # find location if this group has previously been saved with a group
    queryset1 = AssayOmicDataFileUpload.objects.filter(
        group_1=this_pk
    ).aggregate(Max('location_1'))['location_1__max']

    if queryset1 is not None:
        locmess = "found"
        loc_pk = queryset1
    else:
        queryset2 = AssayOmicDataFileUpload.objects.filter(
            group_2=this_pk
        ).aggregate(Max('location_2'))['location_2__max']

        if queryset2 is not None:
            locmess = "found"
            loc_pk = queryset2

    return [timemess, locmess, day, hour, minute, loc_pk]


def sub_fetch_model_location_dictionary(this_model_pk):
    location_dict = get_model_location_dictionary(this_model_pk)
    return [location_dict]


def fetch_omics_data_for_visualization(request):
    data = {'data': {}}

    study = request.POST.get('study_id', '{}')

    try:
        study = int(study)
    except TypeError:
        data = {'error': 'There was a problem acquiring the study ID.'}
        return HttpResponse(
            json.dumps(data),
            content_type='application/json'
        )

    datafiles = AssayOmicDataFileUpload.objects.filter(study_id=study)

    if datafiles.count() == 0:
        data = {'error': 'There is no omics data for this study.'}
        return HttpResponse(
            json.dumps(data),
            content_type='application/json'
        )

    # TODO - Put this in loop below
    data['file_id_to_name'] = {}
    data['table'] = {}

    # It shall be much easier to match data if we match *exactly* rather than looking at substrings
    # Ideally, we will use update to modify multiple dictionary entries at once
    data['header_to_groups'] = {}

    # Account for multiple files with the same groups
    # First, this is abysmally inefficient, there has to be a better way.
    # Second, how do you perform underscore access of FK fields whose parent's name already has underscores? (ex. group_1_name)
    group_combos = []
    for datafile in datafiles:
        if datafile.group_1 is not None and datafile.group_2 is not None:
            group_combos.append("{}+{}".format(datafile.group_1.id, datafile.group_2.id))

    for datafile in datafiles:
        if datafile.group_1 is not None and datafile.group_2 is not None and datafile.data_type == "log2fc":
            omics_token = "{}+{}".format(datafile.group_1.id, datafile.group_2.id)

            split_times_1 = get_split_times(datafile.time_1)
            split_times_2 = get_split_times(datafile.time_2)

            if group_combos.count(omics_token) > 1:
                if datafile.location_1 is not None and datafile.location_2 is not None:
                    joint_name = " vs ".join([
                        datafile.group_1.name + "(" + datafile.location_1.name + ") @ D:" + str(split_times_1['day']) + " H:" + str(split_times_1['hour']) + " M:" + str(split_times_1['minute']),
                        datafile.group_2.name + "(" + datafile.location_2.name + ") @ D:" + str(split_times_2['day']) + " H:" + str(split_times_2['hour']) + " M:" + str(split_times_2['minute'])
                    ])
                else:
                    joint_name = " vs ".join([
                        # .format is more legible than + concatenation
                        # Also, ideally we would have a method for displaying times
                        datafile.group_1.name + " @ D:" + str(split_times_1['day']) + " H:" + str(split_times_1['hour']) + " M:" + str(split_times_1['minute']),
                        datafile.group_2.name + " @ D:" + str(split_times_2['day']) + " H:" + str(split_times_2['hour']) + " M:" + str(split_times_2['minute'])
                    ])
            else:
                joint_name = " vs ".join([datafile.group_1.name, datafile.group_2.name])

            data['data'][joint_name] = {}
            data['file_id_to_name'][datafile.id] = joint_name
            data['table'][joint_name] = [datafile.description, datafile.id]

            # Crude
            data['header_to_groups'][joint_name] = [
                {
                    'name': datafile.group_1.name,
                    'time': 'D{} H{} M{}'.format(
                        split_times_1['day'],
                        split_times_1['hour'],
                        split_times_1['minute'],
                    ),
                    'sample_location': datafile.location_1.name,
                }, {
                    'name': datafile.group_2.name,
                    'time': 'D{} H{} M{}'.format(
                        split_times_2['day'],
                        split_times_2['hour'],
                        split_times_2['minute'],
                    ),
                    'sample_location': datafile.location_2.name,
                }
            ]

    datapoints = AssayOmicDataPoint.objects.filter(study=study).exclude(value__isnull=True)

    target_ids = {}

    for datapoint in datapoints:
        try:
            if datapoint.name not in data['data'][data['file_id_to_name'][datapoint.omic_data_file_id]]:
                data['data'][data['file_id_to_name'][datapoint.omic_data_file_id]][datapoint.name] = {}
            data['data'][data['file_id_to_name'][datapoint.omic_data_file_id]][datapoint.name][datapoint.analysis_target_id] = datapoint.value

            target_ids.update({
                datapoint.analysis_target_id: True
            })
        except KeyError:
            continue

    data['target_name_to_id'] = {target.name: target.id for target in AssayOmicAnalysisTarget.objects.filter(id__in=target_ids)}

    return HttpResponse(
        default_json.dumps(data),
        content_type='application/json'
    )


def fetch_omics_data_for_upload_preview_prep(request):

    save = False
    study_id = request.POST.get('study_id', '{}')
    # the data file pk does not exist yet for preview, and, it is not used for preview, use 1
    data_file_pk = request.POST.get('file_id', '{}')
    data_file = request.FILES.get('omic_data_file', '{}')
    file_extension = os.path.splitext(data_file.name)[1]
    calledme = 'clean'
    data_type = request.POST.get('data_type', '{}')
    analysis_method = request.POST.get('analysis_method', '{}')
    group_1 = request.POST.get('group_1', '{}')
    group_2 = request.POST.get('group_2', '{}')
    description = request.POST.get('description', '{}')

    data_dicts = omic_data_file_process_data(save, study_id, data_file_pk, data_file, file_extension, calledme, data_type, analysis_method)

    data = data_dicts

    return HttpResponse(
        default_json.dumps(data),
        content_type='application/json'
    )


def get_filtered_omics_data_as_csv(get_params):
    """Returns data points as a csv in the form of a string"""
    ids = AssayOmicDataFileUpload.objects.filter(
        id__in=get_params['visible_charts']
    )

    data_points = AssayOmicDataPoint.objects.prefetch_related(
        'omic_data_file',
        'analysis_target__target',
    ).filter(
        omic_data_file__id__in=ids,
    )

    consolidated_targets = {}
    unique_targets = []
    data = []

    for data_point in data_points:
        name = data_point.name
        target = data_point.analysis_target.name
        value = data_point.value
        if value is None:
            continue
        datafile = data_point.omic_data_file
        datafile_id = datafile.id
        if datafile_id not in consolidated_targets:
            consolidated_targets[datafile_id] = {}
        if name not in consolidated_targets[datafile_id]:
            # assay = str(datafile.study_assay)
            assay_target = datafile.study_assay.target.name
            assay_method = datafile.study_assay.method.name
            group_1 = datafile.group_1.name
            group_2 = datafile.group_2.name
            time_1 = datafile.time_1
            time_1_dict = get_split_times(time_1)
            time_2 = datafile.time_2
            time_2_dict = get_split_times(time_2)
            location_1 = datafile.location_1
            location_2 = datafile.location_2
            consolidated_targets[datafile_id][name] = {
                # "assay": assay,
                "target": assay_target,
                "method": assay_method,
                "group_1": group_1,
                "group_2": group_2,
                "time_1_days": time_1_dict['day'],
                "time_1_hours": time_1_dict['hour'],
                "time_1_minutes": time_1_dict['minute'],
                "time_2_days": time_2_dict['day'],
                "time_2_hours": time_2_dict['hour'],
                "time_2_minutes": time_2_dict['minute'],
                "location_1": location_1,
                "location_2": location_2
            }
        consolidated_targets[datafile_id][name][target] = value
        if target not in unique_targets:
            unique_targets.append(target)

    # Header Row
    data.append(
        [
            "Probe ID",
            "Gene Name",
            "Expression",
            "Assay Target",
            "Assay Method",
            "Group 1",
            "Location 1",
            "Time 1 (Days)",
            "Time 1 (Hours)",
            "Time 1 (Minutes)",
            "Group 2",
            "Location 2",
            "Time 2 (Days)",
            "Time 2 (Hours)",
            "Time 2 (Minutes)"
        ]
    )

    for target in unique_targets:
        data[0].append(target)

    expression_text = {
        'over_expressed': "Over Expressed",
        'under_expressed': "Under Expressed",
        'neither_expressed': "General"
    }

    # Add filtered data
    for omicfile in consolidated_targets:
        for name in consolidated_targets[omicfile]:
            if "pvalue" not in consolidated_targets[omicfile][name] or "log2FoldChange" not in consolidated_targets[omicfile][name]:
                continue
            expression = ''

            # PValue Filters
            if get_params["negative_log10_pvalue"]:
                if not ((-math.log10(consolidated_targets[omicfile][name]["pvalue"]) >= get_params["min_negative_log10_pvalue"]) and (-math.log10(consolidated_targets[omicfile][name]["pvalue"]) <= get_params["max_negative_log10_pvalue"])):
                    continue
            else:
                if not ((consolidated_targets[omicfile][name]["pvalue"] >= get_params["min_pvalue"]) and (consolidated_targets[omicfile][name]["pvalue"] <= get_params["max_pvalue"])):
                    continue

            # Log2FoldChange Filters
            if get_params["absolute_log2_foldchange"]:
                if not ((consolidated_targets[omicfile][name]["log2FoldChange"] >= -get_params["abs_log2_foldchange"]) and (consolidated_targets[omicfile][name]["log2FoldChange"] <= get_params["abs_log2_foldchange"])):
                    continue
            else:
                if not ((consolidated_targets[omicfile][name]["log2FoldChange"] >= get_params["min_log2_foldchange"]) and (consolidated_targets[omicfile][name]["log2FoldChange"] <= get_params["max_log2_foldchange"])):
                    continue

            # Determine Expression
            if (consolidated_targets[omicfile][name]["log2FoldChange"] >= get_params["threshold_log2_foldchange"]) and (consolidated_targets[omicfile][name]["pvalue"] <= get_params["threshold_pvalue"]):
                expression = 'over_expressed'
            elif (consolidated_targets[omicfile][name]["log2FoldChange"] <= -get_params["threshold_log2_foldchange"]) and (consolidated_targets[omicfile][name]["pvalue"] <= get_params["threshold_pvalue"]):
                expression = 'under_expressed'
            else:
                expression = 'neither_expressed'

            # Expression Filter
            if not get_params[expression]:
                continue
            else:
                expression = expression_text[expression]

            # Append any data that has made it this far
            to_append = [
                name,
                name.split("_")[0],
                expression,
                # consolidated_targets[omicfile][name]['assay'],
                consolidated_targets[omicfile][name]['target'],
                consolidated_targets[omicfile][name]['method'],
                consolidated_targets[omicfile][name]['group_1'],
                consolidated_targets[omicfile][name]['location_1'],
                consolidated_targets[omicfile][name]['time_1_days'],
                consolidated_targets[omicfile][name]['time_1_hours'],
                consolidated_targets[omicfile][name]['time_1_minutes'],
                consolidated_targets[omicfile][name]['group_2'],
                consolidated_targets[omicfile][name]['location_2'],
                consolidated_targets[omicfile][name]['time_2_days'],
                consolidated_targets[omicfile][name]['time_2_hours'],
                consolidated_targets[omicfile][name]['time_2_minutes']
            ]
            for target in unique_targets:
                if target in consolidated_targets[omicfile][name]:
                    to_append.append(consolidated_targets[omicfile][name][target])
                else:
                    to_append.append('')

            data.append(to_append)

    for index in range(len(data)):
        current_list = list(data[index])
        data[index] = [str(item) for item in current_list]

    string_io = StringIO()
    csv_writer = csv.writer(string_io, dialect=csv.excel)

    # Add the UTF-8 BOM
    data[0][0] = '\ufeff' + data[0][0]

    # Write the lines
    for one_line_of_data in data:
        csv_writer.writerow(one_line_of_data)

    return string_io.getvalue()


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
    'fetch_post_filter': {
        'call': fetch_post_filter
    },
    'fetch_power_analysis_group_table': {
        'call': fetch_power_analysis_group_table
    },
    'fetch_two_sample_power_analysis_results': {
        'call': fetch_two_sample_power_analysis_results
    },
    'fetch_one_sample_power_analysis_results': {
        'call': fetch_one_sample_power_analysis_results
    },
    'fetch_data_points_from_study_set': {
        'call': fetch_data_points_from_study_set
    },
    'get_pubmed_reference_data': {
        'call': get_pubmed_reference_data
    },
    'fetch_organ_model_protocol_setup': {
        'call': fetch_organ_model_protocol_setup
    },
    'fetch_organ_model_type': {
        'call': fetch_organ_model_type
    },
    'fetch_device_dimensions_from_organ_model': {
        'call': fetch_device_dimensions_from_organ_model
    },
    'fetch_matrix_setup': {
        'call': fetch_matrix_setup
    },
    'fetch_assay_associations': {
        'call': fetch_assay_associations
    },
    'clone_study': {
        'call': clone_study,
        'validation': study_editor_validation
    },
    'fetch_pbpk_group_table': {
        'call': fetch_pbpk_group_table
    },
    'fetch_species_parameters': {
        'call': fetch_species_parameters
    },
    'fetch_compound_physicochemical_parameters': {
        'call': fetch_compound_physicochemical_parameters
    },
    'fetch_pbpk_intrinsic_clearance_results': {
        'call': fetch_pbpk_intrinsic_clearance_results
    },
    'fetch_pbpk_dosing_results': {
        'call': fetch_pbpk_dosing_results
    },
    # 'fetch_dropdown': {
    #     'call': fetch_dropdown,
    #     'validation': valid_user_validation
    # }
    'fetch_assay_study_matrix_for_platemap': {
        'call': fetch_assay_study_matrix_for_platemap
    },
    'fetch_assay_study_platemap_for_platemap': {
        'call': fetch_assay_study_platemap_for_platemap
    },
    'fetch_information_for_plate_map_layout': {
        'call': fetch_information_for_plate_map_layout
    },
    'fetch_review_plate_reader_data_file_only': {
        'call': fetch_review_plate_reader_data_file_only
    },
    'fetch_review_plate_reader_data_file_with_block_info': {
        'call': fetch_review_plate_reader_data_file_with_block_info
    },
    'fetch_plate_reader_data_block_plate_map_size': {
        'call': fetch_plate_reader_data_block_plate_map_size
    },
    'fetch_information_for_value_set_of_plate_map_for_data_block': {
        'call': fetch_information_for_value_set_of_plate_map_for_data_block
    },
    'fetch_information_for_study_platemap_standard_file_blocks': {
        'call': fetch_information_for_study_platemap_standard_file_blocks
    },
    'fetch_multiplier_for_data_processing_plate_map_integration': {
        'call': fetch_multiplier_for_data_processing_plate_map_integration
    },
    'fetch_data_processing_for_plate_map_integration': {
        'call': fetch_data_processing_for_plate_map_integration
    },
    'fetch_omic_sample_info_from_upload_data_table': {
        'call': fetch_omic_sample_info_from_upload_data_table
    },
    'fetch_omics_data_for_visualization': {
        'call': fetch_omics_data_for_visualization
    },
    'fetch_omics_data_for_upload_preview_prep': {
        'call': fetch_omics_data_for_upload_preview_prep
    },
    'fetch_this_file_is_this_study': {
        'call': fetch_this_file_is_this_study
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
