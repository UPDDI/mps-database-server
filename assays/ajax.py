# coding=utf-8
import ujson as json
from collections import defaultdict
# TODO STOP USING WILDCARD IMPORTS
from django.http import *
# STOP USING WILDCARD IMPORTS
from .models import *
from microdevices.models import MicrophysiologyCenter, Microdevice

# from mps.settings import TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX
from .forms import (
    AssayChipReadoutForm,
    AssayPlateReadoutForm,
    AssayChipReadoutInlineFormset,
    AssayPlateReadoutInlineFormset
)

from .utils import (
    number_to_label,
    validate_file,
    DEFAULT_CSV_HEADER,
    CSV_HEADER_WITH_COMPOUNDS_AND_STUDY,
    CHIP_DATA_PREFETCH,
    UnicodeWriter,
    REPLACED_DATA_POINT_CODE,
    get_repro_data
)

import csv
from StringIO import StringIO
from django.shortcuts import get_object_or_404
from mps.templatetags.custom_filters import ADMIN_SUFFIX, is_group_editor

from django.contrib.auth.models import User
from mps.settings import DEFAULT_FROM_EMAIL

from django.template.loader import render_to_string

# from.utils import(
#     valid_chip_row,
#     stringify_excel_value,
#     unicode_csv_reader,
#     get_row_and_column,
#     process_readout_value,
#     get_sheet_type
# )
# import xlrd

# TODO FIX SPAGHETTI CODE
from .forms import ReadoutBulkUploadForm, ReadyForSignOffForm
from django.forms.models import inlineformset_factory

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


# TODO REFACTOR Rather than passing the same thing over and over, we can make an object with attributes!
def main(request):
    """Default to server error"""
    return HttpResponseServerError()


# TODO ADD BASE LAYOUT CONTENT TO ASSAY LAYOUT
def fetch_assay_layout_content(request):
    """Return compounds in a layout

    Receives the following from POST:
    id -- the id of the model of interest
    model -- the model of interest
    """

    current_id = request.POST.get('id', '')
    model = request.POST.get('model', '')

    if not model and current_id:
        logger.error('request_id not present in request to fetch_layout_format_labels')
        return HttpResponseServerError()

    if model == 'assay_layout':
        layout = AssayLayout.objects.get(id=current_id)

    elif model == 'assay_device_setup':
        layout = AssayPlateSetup.objects.get(id=current_id).assay_layout

    elif model == 'assay_device_readout':
        layout = AssayPlateReadout.objects.get(id=current_id).setup.assay_layout

    data = defaultdict(dict)

    # Fetch compounds
    compounds = AssayWellCompound.objects.filter(assay_layout=layout).prefetch_related(
        'assay_layout',
        'assay_compound_instance__compound_instance__compound',
        'assay_compound_instance__compound_instance__supplier',
        'assay_compound_instance__concentration_unit'
    ).order_by('compound__name')

    for compound in compounds:
        well = compound.row + '_' + compound.column
        if not 'compounds' in data[well]:
            data[well]['compounds'] = []
        receipt_date = ''
        if compound.assay_compound_instance.compound_instance.receipt_date:
            receipt_date = compound.assay_compound_instance.compound_instance.receipt_date.isoformat()
        data[well]['compounds'].append({
            'name': compound.assay_compound_instance.compound_instance.compound.name,
            'id': compound.assay_compound_instance.compound_instance.compound_id,
            'concentration': compound.assay_compound_instance.concentration,
            'concentration_unit_id': compound.assay_compound_instance.concentration_unit_id,
            'concentration_unit': compound.assay_compound_instance.concentration_unit.unit,
            'supplier': compound.assay_compound_instance.compound_instance.supplier.name,
            'lot': compound.assay_compound_instance.compound_instance.lot,
            'receipt_date': receipt_date,
            'addition_time': compound.assay_compound_instance.addition_time,
            'duration': compound.assay_compound_instance.duration
            # 'well': well
        })

    # Fetch timepoints
    timepoints = AssayWellTimepoint.objects.filter(assay_layout=layout).prefetch_related('assay_layout')

    for timepoint in timepoints:
        well = timepoint.row + '_' + timepoint.column
        data[well].update({'timepoint': timepoint.timepoint})

    # Fetch labels
    labels = AssayWellLabel.objects.filter(assay_layout=layout).prefetch_related('assay_layout')

    for label in labels:
        well = label.row + '_' + label.column
        data[well].update({'label': label.label})

    # Fetch types
    current_types = AssayWell.objects.filter(assay_layout=layout).prefetch_related('assay_layout', 'well_type')

    for current_type in current_types:
        well = current_type.row + '_' + current_type.column
        data[well].update({
            'type': current_type.well_type.well_type,
            'type_id': current_type.well_type_id,
            'color': current_type.well_type.background_color
        })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def fetch_readout(request):
    """Get the current plate readout data

    From POST:
    current_id - the current ID
    model - what model the ID is for
    """
    current_id = request.POST.get('id', '')
    model = request.POST.get('model', '')

    if not model and current_id:
        logger.error('request_id not present in request to fetch_layout_format_labels')
        return HttpResponseServerError()

    if model == 'assay_device_readout':
        current_readout_id = AssayPlateReadout.objects.get(id=current_id)

    elif model == 'assay_plate_test_results':
        current_readout_id = AssayPlateTestResult.objects.get(id=current_id).readout

    # data = defaultdict(list)
    data = []

    # TODO NOTE THAT THIS DOES NOT ORDER THE ROWS AND COLUMNS CORRECTLY
    # TODO PLEASE NOTE THIS IS A STOP GAP; CHANGE AFTER REVISING ROW AND COLUMN
    readouts = AssayReadout.objects.filter(
        assay_device_readout=current_readout_id
    ).prefetch_related(
        'assay_device_readout__setup__assay_run_id',
        'assay__assay_id',
        'assay__readout_unit'
    ).order_by(
        'assay',
        'row',
        'column',
        'elapsed_time',
        'update_number',
        'quality'
    )

    time_unit = AssayPlateReadout.objects.filter(id=current_readout_id.id)[0].timeunit.unit

    for readout in readouts:
        # TODO DRY DICTATES THAT I SHOULDN'T JUST COPY THIS TO UTILS
        notes = readout.notes
        if readout.update_number:
            notes = notes + '\nUpdate #' + unicode(readout.update_number)

        data.append({
            'plate_id': readout.assay_device_readout.setup.assay_plate_id,
            'row': readout.row,
            'column': readout.column,
            'value': readout.value,
            'assay': readout.assay.assay_id.assay_short_name,
            'time': readout.elapsed_time,
            # TODO SOMEWHAT FRIVOLOUS CONSIDER REVISING
            'time_unit': time_unit,
            'value_unit': readout.assay.readout_unit.unit,
            'feature': readout.assay.feature,
            'quality': readout.quality,
            'notes': notes,
            'update_number': readout.update_number
        })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def fetch_layout_format_labels(request):
    """Return layout format labels

    Receives the following from POST:
    id -- the id of the model of interest
    model -- the model of interest
    """

    current_id = request.POST.get('id', '')
    model = request.POST.get('model', '')

    if not model and current_id:
        logger.error('request_id not present in request to fetch_layout_format_labels')
        return HttpResponseServerError()

    if model == 'device':
        layout = Microdevice.objects.get(id=current_id)

    elif model == 'assay_layout':
        layout = AssayLayout.objects.get(id=current_id).device

    elif model == 'assay_device_setup':
        layout = AssayPlateSetup.objects.get(id=current_id).assay_layout.device

    elif model == 'assay_device_readout':
        layout = AssayPlateReadout.objects.get(id=current_id).setup.assay_layout.device

    data = {}

    # if layout.column_labels and layout.row_labels:
    #     column_labels = layout.column_labels.split()
    #     row_labels = layout.row_labels.split()
    # # Contrived way to deal with models without labels
    # else:
    #     column_labels = None
    #     row_labels = None

    column_labels = []
    row_labels = []

    if layout.number_of_columns:
        for x in range(layout.number_of_columns):
            column_labels.append(x + 1)

    if layout.number_of_rows:
        for x in range(layout.number_of_rows):
            row_labels.append(number_to_label(x + 1))

    data.update({
        'id': layout.id,
        'column_labels': column_labels,
        'row_labels': row_labels,
    })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def fetch_well_types(request):
    """Return well type ids and colors"""

    data = {}

    for well_type in AssayWellType.objects.all():
        data.update(
            {
                well_type.id: {
                    'name': well_type.well_type,
                    'color': well_type.background_color
                }
            }
        )

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


# Fetches and displays assay layout from plate readout
def fetch_plate_info(request):
    """Returns dynamic info for plate assays

    Receives the following from POST:
    id -- the ID of the Assay Plate Readout of interest
    """

    assay_id = request.POST.get('id', '')

    if not assay_id:
        logger.error('assay id not present in request to fetch_assay_info')
        return HttpResponseServerError()

    assay = AssayPlateReadout.objects.get(id=assay_id)

    data = {}

    data.update({
        'assay_layout_id': assay.assay_layout_id,
    })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


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
            'center_name': center_data.center_name,
        })

    except:
        data.update({
            'center_id': '',
            'center_name': '',
        })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def get_chip_readout_data_as_csv(chip_ids, chip_data=None, both_assay_names=False, include_header=False, include_all=False):
    """Returns readout data as a csv in the form of a string

    Params:
    chip_ids - Readout IDs to use to acquire chip data (if data not provided)
    chip_data - Readout raw data, optional, acquired with chip_ids if not provided
    both_assay_names - Indicates that both assay names should be returned (not currently used)
    """
    data = get_chip_readout_data_as_list_of_lists(
        chip_ids,
        chip_data,
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


def get_chip_readout_data_as_list_of_lists(chip_ids, chip_data=None, both_assay_names=False, include_header=False, include_all=False):
    """Returns readout data as a csv in the form of a string

    Params:
    chip_ids - Readout IDs to use to acquire chip data (if data not provided)
    chip_data - Readout raw data, optional, acquired with chip_ids if not provided
    both_assay_names - Indicates that both assay names should be returned (not currently used)
    """
    # related_compounds_map = {}

    if not chip_data:
        # TODO ORDER SUBJECT TO CHANGE
        chip_data = AssayChipRawData.objects.prefetch_related(
            'assay_chip_id__chip_setup__assay_run_id',
            'assay_instance__target',
            'assay_instance__method',
            'assay_instance__unit',
            'assay_chip_id__chip_setup__device',
            'assay_chip_id__chip_setup__organ_model',
            'assay_chip_id__chip_setup__assaycompoundinstance_set__compound_instance__compound',
            'assay_chip_id__chip_setup__assaycompoundinstance_set__concentration_unit',
            'assay_chip_id__chip_setup__assaychipcells_set__cell_sample__cell_type__organ',
            'assay_chip_id__chip_setup__assaychipcells_set__cell_sample__cell_subtype',
            'sample_location'
        ).filter(
            assay_chip_id__in=chip_ids
        ).order_by(
            'assay_chip_id__chip_setup__assay_chip_id',
            'assay_instance__target__name',
            'assay_instance__method__name',
            'time',
            'sample_location__name',
            'quality',
            'update_number'
        ).exclude(
            quality__contains=REPLACED_DATA_POINT_CODE
        )

        # related_compounds_map = get_related_compounds_map(readouts=chip_ids)

    data = []

    if include_header:
        data.append(
            CSV_HEADER_WITH_COMPOUNDS_AND_STUDY
        )

    for data_point in chip_data:
        # Definitely need to rename these fields/models...
        study_id = data_point.assay_chip_id.chip_setup.assay_run_id.assay_run_id

        chip_id = data_point.assay_chip_id.chip_setup.assay_chip_id

        cross_reference = data_point.cross_reference

        assay_plate_id = data_point.assay_plate_id
        assay_well_id = data_point.assay_well_id

        # Add time here
        time_in_minutes = data_point.time
        times = get_split_times(time_in_minutes)

        target = data_point.assay_instance.target.name
        method = data_point.assay_instance.method.name
        sample_location = data_point.sample_location.name

        device = data_point.assay_chip_id.chip_setup.device.device_name
        organ_model = data_point.assay_chip_id.chip_setup.organ_model

        cells = data_point.assay_chip_id.chip_setup.stringify_cells()

        # compound_treatment = get_list_of_present_compounds(related_compounds_map, data_point, ' | ')
        compound_treatment = data_point.assay_chip_id.chip_setup.stringify_compounds()

        value = data_point.value

        if value is None:
            value = ''

        value_unit = data_point.assay_instance.unit.unit
        quality = data_point.quality
        caution_flag = data_point.caution_flag
        replicate = data_point.replicate
        # TODO ADD OTHER STUFF
        notes = data_point.notes

        if organ_model:
            organ_model = organ_model.model_name

        if REPLACED_DATA_POINT_CODE not in quality and (include_all or not quality):
            data.append([
                study_id,
                chip_id,
                cross_reference,
                assay_plate_id,
                assay_well_id,
                times.get('day'),
                times.get('hour'),
                times.get('minute'),
                device,
                organ_model,
                cells,
                compound_treatment,
                target,
                method,
                sample_location,
                value,
                value_unit,
                replicate,
                caution_flag,
                quality,
                notes
            ])

    return data


def fetch_assay_run_reproducibility(request):
    study = get_object_or_404(AssayRun, pk=int(request.POST.get('study', '')))
    data = {}

    # If chip data
    chip_readouts = AssayChipReadout.objects.filter(
        chip_setup__assay_run_id_id=study
    )

    # Boolean
    # include_all = self.request.GET.get('include_all', False)
    chip_data = get_chip_readout_data_as_list_of_lists(chip_readouts, include_header=True, include_all=False)

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

    return HttpResponse(json.dumps(data),
                        content_type='application/json')


def get_chip_readout_data_as_json(chip_ids, chip_data=None):
    if not chip_data:
        chip_data = AssayChipRawData.objects.prefetch_related(
            *CHIP_DATA_PREFETCH
        ).filter(
            assay_chip_id__in=chip_ids
        ).order_by(
            'assay_chip_id__chip_setup__assay_chip_id',
            'assay_instance__target__name',
            'assay_instance__method__name',
            'time',
            'sample_location__name',
            'quality',
            'update_number'
        )

    data = {}

    data_points = []
    sample_locations = {}
    assay_instances = {}

    for data_point in chip_data:
        chip_id = data_point.assay_chip_id.chip_setup.assay_chip_id
        assay_plate_id = data_point.assay_plate_id
        assay_well_id = data_point.assay_well_id
        # Add time here
        time_in_minutes = data_point.time
        times = get_split_times(time_in_minutes)
        assay_instance = data_point.assay_instance
        sample_location = data_point.sample_location

        value = data_point.value

        if value is None:
            value = ''

        caution_flag = data_point.caution_flag
        quality = data_point.quality
        # TODO ADD OTHER STUFF
        notes = data_point.notes

        update_number = data_point.update_number
        replicate = data_point.replicate

        data_upload = data_point.data_upload

        if data_upload:
            data_upload_name = unicode(data_upload)
            data_upload_url = data_upload.file_location

        else:
            data_upload_name = u''
            data_upload_url = u''

        if sample_location.id not in sample_locations:
            sample_locations.update(
                {
                    sample_location.id: {
                        'name': sample_location.name,
                        'description': sample_location.description
                    }
                }
            )

        if assay_instance.id not in assay_instances:
            assay_instances.update(
                {
                    assay_instance.id: {
                        'target_name': assay_instance.target.name,
                        'target_short_name': assay_instance.target.short_name,
                        'method_name': assay_instance.method.name,
                        'unit': assay_instance.unit.unit,
                    }
                }
            )

        data_point_fields = {
            'chip_id': chip_id,
            'assay_plate_id': assay_plate_id,
            'assay_well_id': assay_well_id,
            'time_in_minutes': time_in_minutes,
            'day': times.get('day'),
            'hour': times.get('hour'),
            'minute': times.get('minute'),
            'assay_instance_id': assay_instance.id,
            'sample_location_id': sample_location.id,
            'value': value,
            'caution_flag': caution_flag,
            'quality': quality.strip(),
            # TODO ADD OTHER STUFF
            'notes': notes.strip(),
            'update_number': update_number,
            'replicate': replicate.strip(),
            'data_upload_url': data_upload_url,
            'data_upload_name': data_upload_name
        }
        data_points.append(data_point_fields)

    data.update({
        'data_points': data_points,
        'sample_locations': sample_locations,
        'assay_instances': assay_instances
    })
    return data


# TODO Needs refactor
def fetch_chip_readout(request):
    """Returns the Raw Chip Data stored for a Chip Readout

    Receives the following from POST:
    id -- the ID of the Chip Readout of interest
    """

    chip_id = request.POST.get('id', '')

    if not chip_id:
        logger.error('chip not present in request to fetch_chip_readout')
        return HttpResponseServerError()

    data = get_chip_readout_data_as_json([chip_id])

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def get_list_of_present_compounds(related_compounds_map, data_point, separator=' & '):
    """Returns a list of compounds present at a given time point

    Params:
    related_compounds_map - mapping for chip -> compounds
    data_point - the data point to find compounds for
    separator - string used to separate compounds
    """
    compounds = related_compounds_map.get(data_point.assay_chip_id.chip_setup_id, [])
    if compounds:
        compounds_to_add = []

        for compound in compounds:
            # Previously included only compounds within duration
            # if compound.addition_time <= time_minutes and compound.duration + compound.addition_time >= time_minutes:
            # Everything past addition time will be listed as effected

            # Revised yet again, now displays all treatments regradless of what was at the time point
            # if compound.addition_time <= data_point.time:

            compounds_to_add.append(
                compound.compound_instance.compound.name +
                ' ' + str(compound.concentration) + ' ' + compound.concentration_unit.unit
            )

        if not compounds_to_add:
            tag = CONTROL_LABEL
        else:
            tag = separator.join(compounds_to_add)
    else:
        tag = CONTROL_LABEL

    return tag


def get_control_data(
        study,
        related_compounds_map,
        key,
        mean_type,
        include_all,
        truncate_negative,
        new_data_for_control=None
):
    """Gets control data for performing percent control calculations

    study - the study in question
    related_compounds_map - the compounds in case the key is compound
    key - the key for the legend being used
    include_all - whether to include all values
    """
    initial_control_data = {}
    controls = {}

    data_points = list(AssayChipRawData.objects.filter(
        assay_chip_id__chip_setup__assay_run_id=study
    ).prefetch_related(
        *CHIP_DATA_PREFETCH
    ))

    if new_data_for_control:
        data_points.extend(new_data_for_control)

    # A little too much copy-pasting here, not very DRY
    for raw in data_points:
        value = raw.value

        # TODO CHANGE TO USE FOLLOWING
        assay_instance = raw.assay_instance
        target = assay_instance.target.name
        unit = assay_instance.unit.unit
        # Not currently used
        method = assay_instance.method.name

        sample_location = raw.sample_location.name

        # chip_id = raw.assay_chip_id.chip_setup.assay_chip_id

        time = raw.time / 1440.0

        quality = raw.quality

        # No dynamic quality here
        if value is not None and (include_all or not quality):
            if truncate_negative and value < 0:
                value = 0

            # Check if the setup is marked a control chip
            if raw.assay_chip_id.chip_setup.chip_test_type == 'control':
                initial_control_data.setdefault(
                    (target, method), {}
                ).setdefault(
                    unit, {}
                ).setdefault(
                    CONTROL_LABEL, {}
                ).setdefault(
                    sample_location, {}
                ).setdefault(
                    time, []
                ).append(
                    value
                )

    targets = [target_method[0] for target_method in initial_control_data.keys()]

    for target_method, units in initial_control_data.items():
        target = target_method[0]
        method = target_method[1]

        if targets.count(target) > 1:
            target = u'{} [{}]'.format(target, method)

        initial_control_data.update({
            target: units
        })

        del initial_control_data[target_method]

    for target, units in initial_control_data.items():
        for unit, tags in units.items():
            for tag, sample_locations in tags.items():
                for sample_location, time_values in sample_locations.items():
                    for time, values in time_values.items():
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
                                {(target, unit, sample_location, time): average}
                        )

    return controls


# TODO WE MAY WANT THE DEFINITION OF A TREATMENT GROUP TO CHANGE, WHO KNOWS
def get_treatment_groups(study):
    treatment_groups = {}
    # TODO PLEASE REMEMBER TO INCLUDE IDS OF SETUPS IN THIS
    treatment_group_representatives = []
    setup_to_treatment_group = {}

    # By pulling the setups for the study, I avoid problems with preview data
    setups = AssayChipSetup.objects.filter(
        assay_run_id=study
    ).prefetch_related(
        'assaychipcells_set',
        'assaycompoundinstance_set'
    )

    for setup in setups:
        treatment_group_tuple = (
            setup.device_id,
            setup.organ_model_id,
            setup.organ_model_protocol_id,
            setup.variance,
            setup.devolved_compounds(),
            setup.devolved_cells()
        )

        if treatment_group_tuple not in treatment_groups:
            current_representative = len(treatment_group_representatives)
            treatment_groups.update({
                treatment_group_tuple: current_representative
            })
            treatment_group_representatives.append(setup.quick_dic())
        else:
            current_representative = treatment_groups.get(treatment_group_tuple)

        treatment_group_representatives[current_representative].get('setups_with_same_group').append(
            setup.get_hyperlinked_name()
        )
        setup_to_treatment_group.update({setup.id: current_representative})

    for representative in treatment_group_representatives:
        representative.get('setups_with_same_group').sort()
        representative.update({
            'setups_with_same_group': ', '.join(representative.get('setups_with_same_group'))
        })

    return (treatment_group_representatives, setup_to_treatment_group)


def get_readout_data(
        raw_data,
        related_compounds_map,
        key,
        mean_type,
        interval_type,
        percent_control,
        include_all,
        truncate_negative,
        dynamic_quality,
        study=None,
        readout=None,
        new_data=False,
        additional_data=None
):
    """Get all readout data for a study and return it in JSON format

    From POST:
    raw_data - the AssayChipRawData needed to create the JSON
    related_compounds_map - dic of setup pointing to compounds
    key - whether this data should be considered by device or by compound
    interval_type - the type of interval (std, ste, etc)
    percent_control - whether to use percent control (WIP)
    include_all - whether to include all values
    dynamic_quality - dic of data points to exclude
    study - supplied only if needed to get percent control values (validating data sets and so on)
    readout - supplied only when data is for an individual readout
    new_data - indicates whether data in raw_data is new
    additional_data - data to merge with raw_data (used when displaying individual readouts for convenience)
    """

    # TODO ACCOUNT FOR CASE WHERE ASSAY HAS TWO DIFFERENT UNITS?
    # TODO MAY FORBID THIS CASE, MUST ASK FIRST
    # TODO ACCOUNT FOR CASE WHERE STUDY HAS MORE THAN ONE COMPOUND
    # Organization is assay -> unit -> compound/tag -> field -> time -> value
    # assays = {}

    treatment_group_representatives, setup_to_treatment_group = get_treatment_groups(study)
    # TODO CHANGE THIS POST TO SOMETHING MORE SEMANITC FROM JS
    # if key == 'compound':
    #     treatment_group_representatives, setup_to_treatment_group = get_treatment_groups(study)
    # else:
    #     treatment_group_representatives = []
    #     setup_to_treatment_group = {}

    final_data = {
        'sorted_assays': [],
        'assays': []
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
            related_compounds_map,
            key,
            mean_type,
            include_all,
            truncate_negative,
            new_data_for_control=new_data_for_control
        )

        if controls.get('errors' , ''):
            return controls

    averaged_data = {}

    all_sample_locations = {}
    all_keys = {}

    # Append the additional_data as necessary
    # Why is this done? It is an expedient way to avoid duplicating data
    if additional_data:
        raw_data.extend(additional_data)

    for raw in raw_data:
        # Now uses full name
        # assay = raw.assay_id.assay_id.assay_short_name
        # Deprecated
        # assay = raw.assay_id.assay_id.assay_name
        # unit = raw.assay_id.readout_unit.unit
        # Deprecated
        # field = raw.field_id
        value = raw.value

        # TODO CHANGE TO USE FOLLOWING
        assay_instance = raw.assay_instance
        target = assay_instance.target.name
        unit = assay_instance.unit.unit
        # Not currently used
        method = assay_instance.method.name

        sample_location = raw.sample_location.name
        all_sample_locations.update({sample_location: True})

        setup_id = raw.assay_chip_id.chip_setup_id
        chip_id = raw.assay_chip_id.chip_setup.assay_chip_id

        # BE SURE TO DO THIS IN JS
        quality_index = '~'.join([
            chip_id,
            str(raw.assay_plate_id),
            str(raw.assay_well_id),
            str(raw.assay_instance.id),
            str(raw.sample_location.id),
            str(raw.time).rstrip('0').rstrip('.'),
            raw.replicate,
            str(raw.update_number)
        ])

        # Convert all times to days for now
        # Get the conversion unit
        # scale = raw.assay_chip_id.timeunit.scale_factor
        # time = '{0:.2f}'.format((scale / 1440.0) * raw.time)
        # # Have time in minutes for comparing to addition_time and duration
        # time_minutes = scale * raw.time

        # time_minutes = raw.time
        # Time will always be in days
        # time = '{0:.2f}'.format(raw.time / 1440.0)
        time = raw.time / 1440.0

        quality = raw.quality

        # TODO Should probably just use dynamic_quality instead of quality for this
        if value is not None and REPLACED_DATA_POINT_CODE not in quality and (include_all or not dynamic_quality.get(quality_index, quality)):
            if truncate_negative and value < 0:
                value = 0
            # Get tag for data point
            # If by compound
            if key == 'group':
                # tag = get_list_of_present_compounds(related_compounds_map, raw, ' & ')
                tag = 'Group {}'.format(setup_to_treatment_group.get(setup_id) + 1)
            # If by device
            else:
                tag = chip_id

            # Set data in nested monstrosity that is initial_data
            initial_data.setdefault(
                (target, method), {}
            ).setdefault(
                unit, {}
            ).setdefault(
                tag, {}
            ).setdefault(
                sample_location, {}
            ).setdefault(
                time, []
            ).append(value)

    targets = [target_method[0] for target_method in initial_data.keys()]

    for target_method, units in initial_data.items():
        target = target_method[0]
        method = target_method[1]

        if targets.count(target) > 1:
            target = u'{} [{}]'.format(target, method)

        initial_data.update({
            target: units
        })

        del initial_data[target_method]

    # Nesting like this is a little sloppy, flat > nested
    for target, units in initial_data.items():
        for unit, tags in units.items():
            for tag, sample_locations in tags.items():
                for sample_location, time_values in sample_locations.items():
                    for time, values in time_values.items():
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

                        average_and_interval = (
                            average,
                            interval
                        )

                        averaged_data.setdefault(target, {}).setdefault(unit, {}).setdefault(tag, {}).setdefault(sample_location, {}).update({
                            time: average_and_interval
                        })

    initial_data = None

    accommodate_sample_location = len(all_sample_locations) > 1

    for target, units in averaged_data.items():
        for unit, tags in units.items():
            # row_indices = {}
            accommodate_units = len(units) > 1

            if not percent_control:
                # Not converted to percent control
                # Newline is used as a delimiter
                assay_label = target + '\n' + unit
            else:
                # Convert to percent control
                if accommodate_units:
                    current_unit = '%Control from ' + unit
                else:
                    current_unit = '%Control'
                # Newline is used as a delimiter
                assay_label = target + '\n' + current_unit

            current_table = intermediate_data.setdefault(assay_label, [['Time']])
            # row_indices = {}
            current_data = {}
            x_header = []
            y_header = {}
            final_data.get('sorted_assays').append(assay_label)

            for tag, sample_locations in tags.items():
                for sample_location, time_values in sample_locations.items():
                    accommodate_intervals = False
                    include_current = False

                    if accommodate_sample_location:
                        current_key = tag + ' ' + sample_location
                    else:
                        current_key = tag

                    all_keys.update({current_key: True})

                    for time, value_and_interval in time_values.items():
                        value = value_and_interval[0]
                        interval = value_and_interval[1]

                        if interval != 0:
                            accommodate_intervals = True

                        if not percent_control:
                            # assays.setdefault(assay_label, {}).setdefault(current_key, {}).setdefault('time', []).append(time)
                            # assays.setdefault(assay_label, {}).setdefault(current_key, {}).setdefault('values', []).append(value)
                            current_data.setdefault(current_key, {}).update({time: value})
                            current_data.setdefault(current_key+'_i1', {}).update({time: value - interval})
                            current_data.setdefault(current_key+'_i2', {}).update({time: value + interval})
                            y_header.update({time: True})
                            include_current = True

                        elif controls.get((target, unit, sample_location, time), False):
                            control_value = controls.get((target, unit, sample_location, time))

                            # We can not divide by zero
                            if control_value == 0:
                                return {'errors': 'Could not calculate percent control because some control values are zero (divide by zero error).'}

                            adjusted_value = (value / control_value) * 100
                            adjusted_interval = (interval / control_value) * 100

                            current_data.setdefault(current_key, {}).update({time: adjusted_value})
                            current_data.setdefault(current_key+'_i1', {}).update({time: adjusted_value - adjusted_interval})
                            current_data.setdefault(current_key+'_i2', {}).update({time: adjusted_value + adjusted_interval})
                            y_header.update({time: True})
                            include_current = True
                            # assays.setdefault(assay_label, {}).setdefault(current_key, {}).setdefault('time', []).append(time)
                            # Perform conversion
                            # assays.setdefault(assay_label, {}).setdefault(current_key, {}).setdefault('values', []).append((value / control_value) * 100)

                    if include_current:
                        x_header.append(current_key)
                    # To include all
                    # x_header.append(current_key)
                    # x_header.extend([
                    #     current_key + '_i1',
                    #     current_key + '_i2'
                    # ])

                    # Only include intervals if necessary
                    if accommodate_intervals and include_current:
                        x_header.extend([
                            current_key + '_i1',
                            current_key + '_i2'
                        ])
                    else:
                        if current_key+'_i1' in current_data:
                            del current_data[current_key+'_i1']
                            del current_data[current_key + '_i2']

            # for current_key in all_keys:
            #     if current_key not in x_header:
            #         x_header.extend([
            #             current_key,
            #             current_key + '_i1',
            #             current_key + '_i2'
            #         ])

            # Note manipulations for sorting
            # Somewhat contrived
            convert = lambda text: int(text) if text.isdigit() else text.lower()
            alphanum_key = lambda key: [
                convert(
                    c.replace('_I1', '!').replace('_I2', '"')
                ) for c in re.split('([0-9]+)', key)
            ]
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

    controls = None
    averaged_data = None

    final_data.get('sorted_assays').sort(key=lambda s: s.upper())
    final_data['assays'] = [[] for x in range(len(final_data.get('sorted_assays')))]

    for assay, assay_data in intermediate_data.items():
        final_data.get('assays')[final_data.get('sorted_assays').index(assay)] = assay_data

    final_data.update({
        'treatment_groups': treatment_group_representatives
    })

    return final_data


def get_related_compounds_map(readouts=None, study=None, data=None):
    """Returns a map of setup id -> compound

    Params:
    readouts - A queryset of readouts
    """
    related_compounds_map = {}

    if readouts:
        setups = readouts.values_list('chip_setup_id')
    elif data:
        setups = data.values_list('assay_chip_id__chip_setup__id')
    elif study:
        setups = AssayChipSetup.objects.filter(assay_run_id=study)
    else:
        setups = None

    related_compounds = AssayCompoundInstance.objects.filter(
        chip_setup=setups
    ).prefetch_related(
        'compound_instance__compound',
        'compound_instance__supplier',
        'concentration_unit',
        'chip_setup__assay_run_id'
    ).order_by('addition_time', 'compound_instance__compound__name')

    for compound in related_compounds:
        related_compounds_map.setdefault(compound.chip_setup_id, []).append(compound)

    return related_compounds_map


# TODO REQUIRES REVISION
# TODO NEED TO CONFIRM UNITS ARE THE SAME (ELSE CONVERSION)
def fetch_readouts(request):
    """Get all readouts for a given study for Study Summary

    Receives the following from POST:
    study -- the study to acquire readouts from
    key -- specifies whether to split readouts by compound or device
    percent_control -- specifies whether to convert to percent control
    include_all -- specifies whether to include all data (exclude invalid if null string)
    """
    # This business is a little excessive
    # Rather, we can refer to the POST as a dictionary and modify as necessary
    study = request.POST.get('study', '')
    readout = request.POST.get('readout', '')
    key = request.POST.get('key', '')
    mean_type = request.POST.get('mean_type', 'arithmetic')
    interval_type = request.POST.get('interval_type', 'ste')
    percent_control = request.POST.get('percent_control', '')
    include_all = request.POST.get('include_all', '')
    truncate_negative = request.POST.get('truncate_negative', '')
    dynamic_quality = json.loads(request.POST.get('dynamic_quality', '{}'))

    if readout:
        this_readout = AssayChipReadout.objects.get(pk=readout)
        this_study = this_readout.chip_setup.assay_run_id
        study = this_study
        readouts = AssayChipReadout.objects.filter(
            id=readout
        ).prefetch_related(
            'chip_setup__assay_run_id'
        )
    else:
        this_readout = None
        study = AssayRun.objects.get(pk=study)
        this_study = study
        readouts = AssayChipReadout.objects.filter(
            chip_setup__assay_run_id_id=study
        ).prefetch_related(
            'chip_setup__assay_run_id'
        )

    # Get chip readouts
    # if readout:
    #     readouts = AssayChipReadout.objects.filter(
    #         id=readout
    #     ).prefetch_related(
    #         'chip_setup__assay_run_id'
    #     )
    # else:
    #     readouts = AssayChipReadout.objects.filter(
    #         chip_setup__assay_run_id_id=study
    #     ).prefetch_related(
    #         'chip_setup__assay_run_id'
    #     )

    raw_data = AssayChipRawData.objects.filter(
        assay_chip_id=readouts
    ).prefetch_related(
        *CHIP_DATA_PREFETCH
    )

    related_compounds_map = {}

    if key == 'group':
        related_compounds_map = get_related_compounds_map(study=study)

    data = get_readout_data(
        raw_data,
        related_compounds_map,
        key,
        mean_type,
        interval_type,
        percent_control,
        include_all,
        truncate_negative,
        dynamic_quality,
        study=this_study,
        readout=this_readout
    )

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


# Should these be refactored just to use fetch_dropdown instead?
def fetch_organ_models(request):
    """Gets a dropdown of organ models for Chip Setup

    Receives the following from POST:
    device -- the device to acquire organ models from
    """
    dropdown = u'<option value="">---------</option>'

    device = request.POST.get('device', '')

    findings = OrganModel.objects.filter(device_id=device).prefetch_related('device')

    for finding in findings:
        # match value to the desired subject ID
        value = str(finding.id)
        dropdown += u'<option value="' + value + '">' + unicode(finding) + '</option>'

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
    dropdown = u'<option value="">---------</option>'

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
        dropdown += u'<option value="' + value + '">' + unicode(finding) + '</option>'

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
        dropdown += '<option value="' + value + '">' + str(finding) + '</option>'

    data = {}

    data.update({
        'dropdown': dropdown,
    })

    return HttpResponse(json.dumps(data),
                        content_type='application/json')


# USE THE POST DATA TO BUILD A BULKUPLOAD FORM
# DO NOT EXPLICITLY CALL VALIDATION
def validate_bulk_file(request):
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
    # overwrite_option = request.POST.get('overwrite_option', '')
    # bulk_file = request.FILES.get('bulk_file', None)
    dynamic_quality = json.loads(request.POST.get('dynamic_quality', '{}'))

    this_study = AssayRun.objects.get(pk=int(study))

    form = ReadoutBulkUploadForm(request.POST, request.FILES, request=request, instance=this_study)

    if form.is_valid():
        form_data = form.cleaned_data

        preview_data = form_data.get('preview_data')

        # Only chip preview right now
        chip_raw_data = preview_data.get('chip_preview', {}).get('readout_data', [])

        related_compounds_map = {}

        if key == 'group':
            related_compounds_map = get_related_compounds_map(study=this_study)

        # NOTE THE EMPTY DIC, RIGHT NOW BULK PREVIEW NEVER SHOWS COMPOUND JUST DEVICE
        readout_data = get_readout_data(
            chip_raw_data,
            related_compounds_map,
            key,
            mean_type,
            interval_type,
            percent_control,
            include_all,
            truncate_negative,
            dynamic_quality,
            study=this_study,
            new_data=True
        )

        data = {
            'readout_data': readout_data,
            'number_of_conflicting_entries': preview_data.get('chip_preview', {}).get('number_of_conflicting_entries', 0)
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

# TODO DUPLICATED THUS VIOLATING DRY
ACRAFormSet = inlineformset_factory(
    AssayChipReadout,
    AssayChipReadoutAssay,
    formset=AssayChipReadoutInlineFormset,
    extra=1,
    exclude=[],
)


# USE THE POST DATA TO BUILD A BULKUPLOAD FORM
# DO NOT EXPLICITLY CALL VALIDATION
def validate_individual_chip_file(request):
    """Validates a bulk file and returns either errors or a preview of the data entered

    Receives the following from POST:
    study -- the study to acquire readouts from
    key -- specifies whether to split readouts by compound or device
    percent_control -- specifies whether to convert to percent control
    include_all -- specifies whether to include all data (exclude invalid if null string)
    """
    study_id = request.POST.get('study', '')
    key = request.POST.get('key', '')
    mean_type = request.POST.get('mean_type', 'arithmetic')
    interval_type = request.POST.get('interval_type', 'ste')
    percent_control = request.POST.get('percent_control', '')
    include_all = request.POST.get('include_all', '')
    truncate_negative = request.POST.get('truncate_negative', '')
    readout_id = request.POST.get('readout', '')
    include_table = request.POST.get('include_table', '')
    # overwrite_option = request.POST.get('overwrite_option', '')
    # bulk_file = request.FILES.get('bulk_file', None)
    dynamic_quality = json.loads(request.POST.get('dynamic_quality', '{}'))

    readout = None
    if readout_id:
        readout = AssayChipReadout.objects.filter(pk=readout_id)
        if readout:
            readout = readout[0]
            setup_id = readout.chip_setup.id
            study = readout.chip_setup.assay_run_id
        else:
            setup_id = None
            study = AssayRun.objects.get(pk=int(study_id))
    else:
        setup_id = None
        study = AssayRun.objects.get(pk=int(study_id))

    if readout:
        form = AssayChipReadoutForm(study, setup_id, request.POST, request.FILES, request=request, instance=readout)
    else:
        form = AssayChipReadoutForm(study, setup_id, request.POST, request.FILES, request=request)
    # formset = ACRAFormSet(request.POST, request.FILES, instance=form.instance)

    # if formset.is_valid():
    if form.is_valid():
        form_data = form.cleaned_data

        preview_data = form_data.get('preview_data')

        # Only chip preview right now
        chip_raw_data = preview_data.get('chip_preview', {}).get('readout_data', [])

        # Now done in get_readout_data
        # Get the other raw data for this readout
        # full_raw_data = list(
        #     AssayChipRawData.objects.filter(
        #         assay_chip_id=readout
        #     ).prefetch_related(
        #         *CHIP_DATA_PREFETCH
        #     )
        # )
        # # Append the new data
        # full_raw_data.extend(chip_raw_data)

        additional_data = list(
            AssayChipRawData.objects.filter(
                assay_chip_id=readout
            ).prefetch_related(
                *CHIP_DATA_PREFETCH
            )
        )

        table = ''
        if include_table:
            table = get_chip_readout_data_as_json([readout_id], chip_data=chip_raw_data)

        related_compounds_map = {}

        if key == 'group':
            related_compounds_map = get_related_compounds_map(study=study)

        charts = get_readout_data(
            chip_raw_data,
            related_compounds_map,
            key,
            mean_type,
            interval_type,
            percent_control,
            include_all,
            truncate_negative,
            dynamic_quality,
            study=study,
            readout=readout,
            new_data=True,
            additional_data=additional_data
        )

        data = {
            'table': table,
            'charts': charts,
            'number_of_conflicting_entries': preview_data.get('chip_preview', {}).get('number_of_conflicting_entries', 0)
        }

        return HttpResponse(json.dumps(data),
                            content_type="application/json")

    else:
        errors = ''
        # if formset.non_form_errors():
        #     errors += formset.non_form_errors().as_text()
        if form.errors:
            errors += form.errors.as_text()
        data = {
            'errors': errors
        }
        return HttpResponse(json.dumps(data),
                            content_type='application/json')

APRAFormSet = inlineformset_factory(
    AssayPlateReadout,
    AssayPlateReadoutAssay,
    formset=AssayPlateReadoutInlineFormset,
    extra=1,
    exclude=[],
)


def validate_individual_plate_file(request):
    """Validates an individual plate and returns either errors or a preview of the data entered

    Receives the following from POST:
    study -- the study to acquire readouts from
    key -- specifies whether to split readouts by compound or device
    percent_control -- specifies whether to convert to percent control
    include_all -- specifies whether to include all data (exclude invalid if null string)
    """
    study_id = request.POST.get('study', '')
    readout_id = request.POST.get('readout', '')
    # overwrite_option = request.POST.get('overwrite_option', '')
    # bulk_file = request.FILES.get('bulk_file', None)

    readout = None
    if readout_id:
        readout = AssayPlateReadout.objects.filter(pk=readout_id)
        if readout:
            readout = readout[0]
            setup_id = readout.setup.id
            study = readout.setup.assay_run_id
        else:
            setup_id = None
            study = AssayRun.objects.get(pk=int(study_id))
    else:
        setup_id = None
        study = AssayRun.objects.get(pk=int(study_id))

    if readout:
        form = AssayPlateReadoutForm(study, setup_id, request.POST, instance=readout)
    else:
        form = AssayPlateReadoutForm(study, setup_id, request.POST)

    formset = APRAFormSet(request.POST, request.FILES, instance=form.instance)

    if formset.is_valid():
        # Validate form
        # form.is_valid()
        form_data = formset.forms[0].cleaned_data

        preview_data = form_data.get('preview_data')

        data = preview_data.get('plate_preview')

        return HttpResponse(json.dumps(data),
                            content_type="application/json")

    else:
        errors = ''
        if formset.__dict__.get('_non_form_errors', ''):
            errors += formset.__dict__.get('_non_form_errors', '').as_text()
        if form.errors:
            errors += form.errors.as_text()
        data = {
            'errors': errors
        }
        return HttpResponse(json.dumps(data),
                            content_type='application/json')


def fetch_quality_indicators(request):
    """Returns quality indicators as JSON for populating dropdowns"""

    # The JSON data to return; initialize with an entry for None
    # data = [{
    #     'id': '',
    #     'code': '',
    #     'name': '',
    #     'description': 'No quality indicator selected'
    # }]
    data = []

    for quality_indicator in AssayQualityIndicator.objects.all().order_by('code'):
        data.append({
            'id': quality_indicator.id,
            'code': quality_indicator.code,
            'name': quality_indicator.name,
            'description': quality_indicator.description
        })

    return HttpResponse(json.dumps(data), content_type='application/json')


def send_ready_for_sign_off_email(request):
    data = {}

    if not AssayRun.objects.filter(pk=int(request.POST.get('study_id', ''))):
        return HttpResponse(json.dumps({'errors': 'This study cannot be signed off on.'}),
                            content_type='application/json')

    study = get_object_or_404(AssayRun, pk=int(request.POST.get('study_id', '')))

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

switch = {
    'fetch_assay_layout_content': fetch_assay_layout_content,
    'fetch_readout': fetch_readout,
    'fetch_layout_format_labels': fetch_layout_format_labels,
    'fetch_well_types': fetch_well_types,
    'fetch_plate_info': fetch_plate_info,
    'fetch_center_id': fetch_center_id,
    'fetch_chip_readout': fetch_chip_readout,
    'fetch_readouts': fetch_readouts,
    'fetch_dropdown': fetch_dropdown,
    'fetch_organ_models': fetch_organ_models,
    'fetch_protocols': fetch_protocols,
    'fetch_protocol': fetch_protocol,
    'validate_bulk_file': validate_bulk_file,
    'validate_individual_chip_file': validate_individual_chip_file,
    'validate_individual_plate_file': validate_individual_plate_file,
    'fetch_quality_indicators': fetch_quality_indicators,
    'send_ready_for_sign_off_email': send_ready_for_sign_off_email,
    'fetch_assay_run_reproducibility': fetch_assay_run_reproducibility
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
