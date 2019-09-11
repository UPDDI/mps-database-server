from django import forms
# TODO REVISE
from .models import (
    # PhysicalUnits,
    AssaySampleLocation,
    TIME_CONVERSIONS,
    AssayDataPoint,
    AssayDataFileUpload,
    AssaySubtarget,
    AssayMatrixItem,
    AssayStudyAssay,
    # AssayImage,
    # AssayImageSetting
    AssayStudy,
    AssayStudyStakeholder
)

from mps.templatetags.custom_filters import VIEWER_SUFFIX, ADMIN_SUFFIX

from django.db import connection, transaction
import xlrd

from django.conf import settings
import string
import codecs
import io

import pandas as pd
import numpy as np
import scipy.interpolate as sp
import scipy.stats as stats
from scipy.interpolate import CubicSpline
from scipy import integrate
from sympy import gamma
import rpy2.robjects as robjects
from rpy2.robjects import FloatVector

import csv
import codecs

from chardet.universaldetector import UniversalDetector

# TODO PLEASE REVIEW TO MAKE SURE CONSISTENT
COLUMN_HEADERS = (
    'CHIP ID',
    'CROSS REFERENCE',
    'ASSAY PLATE ID',
    'ASSAY WELL ID',
    'DAY',
    'HOUR',
    'MINUTE',
    'TARGET/ANALYTE',
    'SUBTARGET',
    'METHOD/KIT',
    'SAMPLE LOCATION',
    'VALUE',
    'VALUE UNIT',
    # SUBJECT TO CHANGE
    'REPLICATE',
    'CAUTION FLAG',
    'EXCLUDE',
    'NOTES'
)
REQUIRED_COLUMN_HEADERS = (
    'CHIP ID',
    'ASSAY PLATE ID',
    'ASSAY WELL ID',
    'DAY',
    'HOUR',
    'MINUTE',
    'TARGET/ANALYTE',
    'METHOD/KIT',
    'SAMPLE LOCATION',
    'VALUE',
    'VALUE UNIT',
    # 'EXCLUDE',
    # 'NOTES',
    # 'REPLICATE'
)
# SUBJECT TO CHANGE
DEFAULT_CSV_HEADER = (
    'Chip ID',
    'Cross Reference',
    'Assay Plate ID',
    'Assay Well ID',
    'Day',
    'Hour',
    'Minute',
    'Target/Analyte',
    'Subtarget',
    'Method/Kit',
    'Sample Location',
    'Value',
    'Value Unit',
    'Replicate',
    'Caution Flag',
    'Exclude',
    'Notes'
)
CSV_HEADER_WITH_COMPOUNDS_AND_STUDY = (
    'Study ID',
    'Chip ID',
    'Cross Reference',
    'Assay Plate ID',
    'Assay Well ID',
    'Day',
    'Hour',
    'Minute',
    'Device',
    'MPS Model',
    'Cells',
    'Compound Treatment(s)',
    'Target/Analyte',
    'Method/Kit',
    'Sample Location',
    'Value',
    'Value Unit',
    'Replicate',
    'Caution Flag',
    'Exclude',
    'Notes'
)

DEFAULT_EXPORT_HEADER = (
    'Study ID',
    'Chip ID',
    'Matrix ID',
    'Cross Reference',
    'Assay Plate ID',
    'Assay Well ID',
    'Day',
    'Hour',
    'Minute',
    'Device',
    'MPS Model',
    'Settings',
    'Cells',
    'Compound Treatment(s)',
    'Target/Analyte',
    'Subtarget',
    'Method/Kit',
    'Sample Location',
    'Value',
    'Value Unit',
    'Replicate',
    'Caution Flag',
    'Exclude',
    'Notes'
)

# I should have more tuples for containing prefetch arguments
CHIP_DATA_PREFETCH = (
    'assay_id__assay_id',
    'assay_id__readout_unit',
    'assay_id__reader_id',
    'assay_instance__target',
    'assay_instance__unit',
    'assay_instance__method',
    'assay_instance__study',
    'sample_location',
    'assay_chip_id__chip_setup',
    'assay_chip_id__chip_setup__device',
    'assay_chip_id__chip_setup__organ_model',
    'data_upload'
)

# SUBJECT TO CHANGE
MATRIX_ITEM_PREFETCH = (
    'study',
    'matrix',
    'device',
    # Subject to change
    'failure_reason'
)

# SUBJECT TO CHANGE
MATRIX_PREFETCH = (
    'device',
)

# STRINGS FOR WHEN NONE OF THE ENTITY IN QUESTION
NO_COMPOUNDS_STRING = '-No Compounds-'
NO_CELLS_STRING = '-No Cells-'
NO_SETTINGS_STRING = '-No Extra Settings-'


def charset_detect(in_file, chunk_size=4096):
    """Use chardet library to detect what encoding is being used"""
    in_file.seek(0)
    chardet_detector = UniversalDetector()
    chardet_detector.reset()
    while 1:
        chunk = in_file.read(chunk_size)
        if not chunk:
            break
        chardet_detector.feed(chunk)
        if chardet_detector.done:
            break
    chardet_detector.close()
    in_file.seek(0)
    return chardet_detector.result


def unicode_csv_reader(in_file, dialect=csv.excel, **kwargs):
    """Returns the contents of a csv in unicode"""
    chardet_results = charset_detect(in_file)
    encoding = chardet_results.get('encoding')
    csv_reader = csv.reader(codecs.iterdecode(in_file, encoding), dialect=dialect, **kwargs)
    rows = []

    for row in csv_reader:
        rows.append([str(cell) for cell in row])

    return rows


def get_user_accessible_studies(user):
    """This function acquires a queryset of all studies the user has access to

    Params:
    user - Django user instance
    """
    queryset = AssayStudy.objects.filter(
        # EXCLUDE ARCHIVED
        archived=False
    ).prefetch_related(
        'group'
    )

    user_group_names = [
        group.name.replace(VIEWER_SUFFIX, '').replace(ADMIN_SUFFIX, '') for group in user.groups.all()
    ]

    data_group_filter = {}
    access_group_filter = {}
    collaborator_group_filter = {}
    unrestricted_filter = {}
    unsigned_off_filter = {}
    stakeholder_group_filter = {}
    missing_stakeholder_filter = {}

    stakeholder_group_whitelist = list(set(
        AssayStudyStakeholder.objects.filter(
            group__name__in=user_group_names
        ).values_list('study_id', flat=True)
    ))

    missing_stakeholder_blacklist = list(set(
        AssayStudyStakeholder.objects.filter(
            signed_off_by_id=None,
            sign_off_required=True
        ).values_list('study_id', flat=True)
    ))

    data_group_filter.update({
        'group__name__in': user_group_names
    })
    collaborator_group_filter.update({
        'collaborator_groups__name__in': user_group_names,
    })
    access_group_filter.update({
        'access_groups__name__in': user_group_names,
    })
    unrestricted_filter.update({
        'restricted': False
    })
    unsigned_off_filter.update({
        'signed_off_by': None
    })
    stakeholder_group_filter.update({
        'id__in': stakeholder_group_whitelist
    })
    missing_stakeholder_filter.update({
        'id__in': missing_stakeholder_blacklist
    })

    # Show if:
    # 1: Study has group matching user_group_names
    # 2: Study has Collaborator group matching user_group_names
    # 3: Study has Stakeholder group matching user_group_name AND is signed off on
    # 4: Study has access group matching user_group_names AND is signed off on AND all Stakeholders have signed off
    # 5: Study is unrestricted AND is signed off on AND all Stakeholders have signed off
    combined = queryset.filter(**data_group_filter) | \
               queryset.filter(**collaborator_group_filter) | \
               queryset.filter(**stakeholder_group_filter).exclude(**unsigned_off_filter) | \
               queryset.filter(**access_group_filter).exclude(**unsigned_off_filter).exclude(
                   **missing_stakeholder_filter) | \
               queryset.filter(**unrestricted_filter).exclude(**unsigned_off_filter).exclude(
                   **missing_stakeholder_filter)

    # May be overzealous to prefetch here
    combined = combined.distinct().prefetch_related(
        'created_by',
        'modified_by',
        'signed_off_by',
        # CRUDE AND BAD
        # 'group__microphysiologycenter_set'
    )

    return combined


def label_to_number(label):
    """Returns a numeric index from an alphabetical index"""
    num = 0
    for char in label:
        if char in string.ascii_letters:
            num = num * 26 + (ord(char.upper()) - ord('A')) + 1
    return num


def number_to_label(num):
    """Returns a alphabetical label from a numeric index"""
    if num < 1:
        return ''
    remainder = num % 26
    quotient = num / 26
    if remainder:
        out = chr(64 + remainder).upper()
    else:
        out = 'Z'
        quotient -= 1
    if quotient:
        return number_to_label(quotient) + out
    else:
        return out


# Now uses unicode instead of string
def stringify_excel_value(value):
    """Given an excel value, return a unicode cast of it

    This also converts floats to integers when possible
    """
    # If the value is just a string literal, return it
    if type(value) == str or type(value) == str:
        return str(value)
    else:
        try:
            # If the value can be an integer, make it into one
            if int(value) == float(value):
                return str(int(value))
            else:
                return str(float(value))
        except:
            return str(value)


def get_csv_media_location(file_name):
    """Returns the location given a full path

    Params:
    file_name -- name of the file to write
    """
    split_name = file_name.split('/')
    csv_onward = '/'.join(split_name[-4:])
    return csv_onward

# TODO CSV_ROOT might be better off in the settings
CSV_ROOT = settings.MEDIA_ROOT.replace('mps/../', '', 1) + '/csv/'


class AssayFileProcessor:
    """Processes Assay MIFC files"""
    def __init__(self, current_file, study, user, current_data_file_upload=None, save=False):
        self.current_file = current_file
        self.user = user
        if save:
            self.data_file_upload = AssayDataFileUpload(
                file_location=current_file.url,
                created_by=user,
                modified_by=user,
                study=study
            )
        else:
            self.data_file_upload = AssayDataFileUpload()
        self.study = study
        self.save = save
        # NO REAL REASON FOR THIS TO BE A DIC RATHER THAN ATTRIBUTES
        self.preview_data = {
            'readout_data': [],
            'number_of_conflicting_entries': 0,
            'number_of_total_duplicates': 0
        }
        self.errors = []

    def valid_data_row(self, row, header_indices):
        """Confirm that a row is 'valid'"""
        valid_row = False

        for required_column in REQUIRED_COLUMN_HEADERS:
            # if len(row) < header_indices.get(required_column) or not row[header_indices.get(required_column)]:
            if len(row) < header_indices.get(required_column):
                valid_row = False
                break
            elif row[header_indices.get(required_column)]:
                valid_row = True

        return valid_row

    def get_and_validate_header(self, data_list, number_of_rows_to_check=3):
        """Takes the first three rows of a file and returns the indices in a dic and the row index of the header"""
        valid_header = False
        index = 0
        header_indices = None
        while len(data_list) > index and index < number_of_rows_to_check and not valid_header:
            header = data_list[index]
            header_indices = {
                column_header.upper(): index for index, column_header in enumerate(header) if
                column_header.upper() in COLUMN_HEADERS
            }

            valid_header = True

            for column_header in REQUIRED_COLUMN_HEADERS:
                if column_header not in header_indices:
                    index += 1
                    valid_header = False

        if valid_header:
            data_to_return = {
                'header_starting_index': index,
                'header_indices': header_indices
            }
            return data_to_return

        else:
            return False

    def process_data(self, data_list, sheet=''):
        """Validates CSV Uploads for Chip Readouts"""
        # A query list to execute to save chip data
        query_list = []
        # A list of readout data for preview
        readout_data = []
        number_of_total_duplicates = 0

        # Dictionary of all Study Assays with respective PKs
        assay_data = {}
        study_assays = AssayStudyAssay.objects.filter(
            study_id=self.study.id
        ).prefetch_related(
            'target',
            'method',
            'unit',
            # 'study'
        )
        # Note that the names are in uppercase
        for assay in study_assays:
            assay_data.update({
                (assay.target.name.upper(), assay.method.name.upper(), assay.unit.unit): assay,
                (assay.target.short_name.upper(), assay.method.name.upper(), assay.unit.unit): assay,
            })

        # Get matrix item name
        matrix_items = {
            matrix_item.name: matrix_item for matrix_item in AssayMatrixItem.objects.filter(study_id=self.study.id)
        }

        # Get sample locations
        sample_locations = {
            sample_location.name.upper(): sample_location for sample_location in AssaySampleLocation.objects.all()
        }

        # Get all subtargets
        subtargets = {
            subtarget.name.upper(): subtarget for subtarget in AssaySubtarget.objects.all()
        }

        default_subtarget = subtargets.get('NONE')

        # TODO THIS CALL WILL CHANGE IN FUTURE VERSIONS
        old_data = AssayDataPoint.objects.filter(
            study_id=self.study.id,
            replaced=False
        ).prefetch_related(
            'subtarget'
        )

        old_replaced_data = AssayDataPoint.objects.filter(
            study_id=self.study.id,
            replaced=True
        ).prefetch_related(
            'subtarget'
        )

        current_data = {}

        possible_conflicting_data = {}
        conflicting_entries = []

        # Fill check for conflicting
        # TODO THIS WILL NEED TO BE UPDATED
        # TODO IS THIS OPTIMAL WAY TO CHECK CONFLICTING?
        for entry in old_data:
            possible_conflicting_data.setdefault(
                (
                    entry.matrix_item_id,
                    entry.assay_plate_id,
                    entry.assay_well_id,
                    entry.study_assay_id,
                    entry.sample_location_id,
                    entry.time,
                    entry.replicate,
                    # Uses name to deal with subtargets that don't exist yet
                    entry.subtarget.name,
                ), []
            ).append(entry)

        # KIND OF CONFUSING, BUT IT IS EXPEDIENT TO PRETEND REPLACED DATA IS CURRENT DATA FOR UPDATE NUMBER
        for entry in old_replaced_data:
            current_data.setdefault(
                (
                    entry.matrix_item_id,
                    entry.assay_plate_id,
                    entry.assay_well_id,
                    entry.study_assay_id,
                    entry.sample_location_id,
                    entry.time,
                    entry.replicate,
                    # Uses name to deal with subtargets that don't exist yet
                    entry.subtarget.name,
                ), []
            ).append(1)

        # Get the headers to know where to get data
        header_data = self.get_and_validate_header(data_list, 3)
        starting_index = header_data.get('header_starting_index') + 1
        header_indices = header_data.get('header_indices')

        if sheet:
            sheet = sheet + ': '

        # Read headers going onward
        for line in data_list[starting_index:]:
            # Some lines may not be long enough (have sufficient commas), ignore such lines
            # Some lines may be empty or incomplete, ignore these as well
            # TODO TODO TODO
            # if not self.valid_data_row(line, header_indices):
            #     continue

            if not any(line[:18]):
                continue

            matrix_item_name = line[header_indices.get('CHIP ID')]

            assay_plate_id = line[header_indices.get('ASSAY PLATE ID')]
            assay_well_id = line[header_indices.get('ASSAY WELL ID')]

            # Currently required, may be optional later
            day = line[header_indices.get('DAY')]
            hour = line[header_indices.get('HOUR')]
            minute = line[header_indices.get('MINUTE')]

            times = {
                'day': day,
                'hour': hour,
                'minute': minute
            }
            # Elapsed time in minutes
            # Acquired later
            time = 0

            # Note that the names are in uppercase
            target_name = line[header_indices.get('TARGET/ANALYTE')].strip()
            method_name = line[header_indices.get('METHOD/KIT')].strip()
            sample_location_name = line[header_indices.get('SAMPLE LOCATION')].strip()

            value = line[header_indices.get('VALUE')]
            value_unit_name = line[header_indices.get('VALUE UNIT')].strip()

            # Check for subtarget name, add one if necessary
            if header_indices.get('SUBTARGET'):
                subtarget_name = line[header_indices.get('SUBTARGET')].strip()
            else:
                subtarget_name = ''

            subtarget = subtargets.get(subtarget_name.upper(), None)

            if not subtarget_name:
                subtarget = default_subtarget

            if subtarget_name and not subtarget:
                # TODO TODO TODO TODO MAKE NEW SUBTARGET
                subtarget = AssaySubtarget(name=subtarget_name)

                if self.save:
                    subtarget.save()

                subtargets.update({
                    subtarget_name.upper(): subtarget
                })

            # Throw error if no Sample Location
            if not sample_location_name:
                self.errors.append(
                    sheet + 'Please make sure all rows have a Sample Location. Additionally, check to see if all related data have the SAME Sample Location.'
                )

            sample_location = sample_locations.get(sample_location_name.upper())
            sample_location_id = None
            if not sample_location:
                self.errors.append(
                    str(sheet + 'The Sample Location "{0}" was not recognized.').format(sample_location_name)
                )
            else:
                sample_location_id = sample_location.id

            # TODO THE TRIMS HERE SHOULD BE BASED ON THE MODELS RATHER THAN MAGIC NUMBERS
            # Get notes, if possible
            notes = ''
            if header_indices.get('NOTES', '') and header_indices.get('NOTES') < len(line):
                notes = line[header_indices.get('NOTES')].strip()[:255]

            cross_reference = ''
            if header_indices.get('CROSS REFERENCE', '') and header_indices.get('CROSS REFERENCE') < len(line):
                cross_reference = line[header_indices.get('CROSS REFERENCE')].strip()[:255]

            # Excluded sees if ANYTHING is in EXCLUDE
            excluded = False
            if header_indices.get('EXCLUDE', '') and header_indices.get('EXCLUDE') < len(line):
                # PLEASE NOTE: Will only ever add 'X' now
                # quality = line[header_indices.get('QC STATUS')].strip()[:20]
                if line[header_indices.get('EXCLUDE')].strip():
                    excluded = True

            caution_flag = ''
            if header_indices.get('CAUTION FLAG', '') and header_indices.get('CAUTION FLAG') < len(line):
                caution_flag = line[header_indices.get('CAUTION FLAG')].strip()[:20]

            # Get replicate if possible
            # DEFAULT IS SUBJECT TO CHANGE PLEASE BE AWARE
            replicate = ''
            if header_indices.get('REPLICATE', '') and header_indices.get('REPLICATE') < len(line):
                replicate = line[header_indices.get('REPLICATE')].strip()[:255]

            # TODO TODO TODO TODO
            matrix_item = matrix_items.get(matrix_item_name, None)
            matrix_item_id = None
            if not matrix_item:
                self.errors.append(
                    str(
                        sheet + 'No Matrix Item with the ID "{0}" exists; please change your file or add this chip.'
                    ).format(matrix_item_name)
                )
            else:
                matrix_item_id = matrix_item.id

            # Raise error when an assay does not exist
            study_assay = assay_data.get((
                target_name.upper(),
                method_name.upper(),
                value_unit_name
            ), None)

            study_assay_id = None
            if not study_assay:
                self.errors.append(
                    str(
                        sheet + '{0}: No assay with the target "{1}", the method "{2}", and the unit "{3}" exists. '
                                'Please review your data and add this assay to your study if necessary.').format(
                        matrix_item_name,
                        target_name,
                        method_name,
                        value_unit_name
                    )
                )
            else:
                study_assay_id = study_assay.id

            # Check every value to make sure it can resolve to a float
            try:
                # Keep empty strings, though they technically can not be converted to floats
                if value != '':
                    value = float(value)
            except:
                self.errors.append(
                    sheet + 'The value "{}" is invalid; please make sure all values are numerical'.format(value)
                )

            # Check to make certain the time is a valid float
            for time_unit, conversion in list(TIME_CONVERSIONS.items()):
                current_time_value = times.get(time_unit, 0)

                if current_time_value == '':
                    current_time_value = 0

                try:
                    current_time_value = float(current_time_value)
                    time += current_time_value * conversion
                except:
                    self.errors.append(
                        sheet + 'The {0} "{1}" is invalid; please make sure all times are numerical'.format(
                            time_unit,
                            current_time_value
                        )
                    )

            # Treat empty strings as None
            if value == '':
                value = None

            if not self.errors:
                # Deal with conflicting data
                current_conflicting_entries = possible_conflicting_data.get(
                    (
                        matrix_item_id,
                        assay_plate_id,
                        assay_well_id,
                        study_assay_id,
                        sample_location_id,
                        time,
                        replicate,
                        subtarget.name,
                    ), []
                )

                # If value is the same, don't bother considering at all
                total_duplicate = False
                for conflict in current_conflicting_entries:
                    if conflict.value == value:
                        total_duplicate = True
                        number_of_total_duplicates += 1
                        break

                if not total_duplicate:
                    conflicting_entries.extend(current_conflicting_entries)

                # Get possible duplicate current entries
                duplicate_current = current_data.get(
                    (
                        matrix_item_id,
                        assay_plate_id,
                        assay_well_id,
                        study_assay_id,
                        sample_location_id,
                        time,
                        replicate,
                        # ADD VALUE!
                        subtarget.name,
                        # value
                    ), []
                )

                number_duplicate_current = len(duplicate_current)
                number_conflicting_entries = len(current_conflicting_entries)

                # Discern what update_number this is (default 0)
                update_number = 0 + number_conflicting_entries + number_duplicate_current

                if self.save and not total_duplicate:
                    query_list.append((
                        self.study.id,
                        matrix_item_id,
                        cross_reference,
                        assay_plate_id,
                        assay_well_id,
                        study_assay_id,
                        subtarget.id,
                        sample_location_id,
                        value,
                        time,
                        caution_flag,
                        excluded,
                        notes,
                        replicate,
                        update_number,
                        self.data_file_upload.id,
                        False
                    ))
                elif not total_duplicate:
                    readout_data.append(
                        AssayDataPoint(
                            matrix_item=matrix_item,
                            cross_reference=cross_reference,
                            assay_plate_id=assay_plate_id,
                            assay_well_id=assay_well_id,
                            study_assay=study_assay,
                            sample_location=sample_location,
                            value=value,
                            time=time,
                            caution_flag=caution_flag,
                            excluded=excluded,
                            notes=notes,
                            replicate=replicate,
                            update_number=update_number,
                            # data_file_upload=self.data_file_upload
                        )
                    )

                # Add to current_data
                current_data.setdefault(
                    (
                        matrix_item_id,
                        assay_plate_id,
                        assay_well_id,
                        study_assay_id,
                        sample_location_id,
                        time,
                        replicate,
                        # ADD VALUE!
                        subtarget.name,
                        # value
                    ), []
                ).append(1)

        # If errors
        if self.errors:
            self.errors = list(set(self.errors))
            raise forms.ValidationError(self.errors)
        # If there wasn't anything
        elif len(query_list) < 1 and len(readout_data) < 1 and not number_of_total_duplicates:
            raise forms.ValidationError(
                'This file does not contain any valid data. Please make sure every row has values in required columns.'
            )
        elif len(query_list) < 1 and len(readout_data) < 1 and number_of_total_duplicates:
            raise forms.ValidationError(
                'This file contains only duplicate data. Please make sure this is the correct file.'
            )

        # TODO TODO TODO TODO
        # If the intention is to save
        elif self.save:
            # Connect to the database
            cursor = connection.cursor()
            # The generic query
            # TODO TODO TODO TODO
            query = ''' INSERT INTO "assays_assaydatapoint"
                      ("study_id", "matrix_item_id", "cross_reference", "assay_plate_id", "assay_well_id", "study_assay_id", "subtarget_id", "sample_location_id", "value", "time", "caution_flag", "excluded", "notes", "replicate", "update_number", "data_file_upload_id", "replaced")
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

            cursor.executemany(query, query_list)
            transaction.commit()
            cursor.close()

            # CRUDE: MARK ALL CONFLICTING AS REPLACED
            # OBVIOUSLY BAD IDEA TO ITERATE LIKE THIS: VERY SLOW
            for conflicting_entry in conflicting_entries:
                conflicting_entry.replaced = True
                conflicting_entry.save()

        # Be sure to subtract the number of replaced points!
        self.preview_data['readout_data'].extend(readout_data)
        self.preview_data['number_of_conflicting_entries'] += len(conflicting_entries)
        self.preview_data['number_of_total_duplicates'] += number_of_total_duplicates

    def process_excel_file(self):
        file_data = self.current_file.read()
        excel_file = xlrd.open_workbook(file_contents=file_data)

        sheet_names = excel_file.sheet_names()

        at_least_one_valid_sheet = False

        for index, sheet in enumerate(excel_file.sheets()):
            sheet_name = sheet_names[index]

            # Skip sheets without anything and skip sheets that are hidden
            if sheet.nrows < 1 or sheet.visibility != 0:
                continue

            # Get datalist
            data_list = []

            # Include the first row (the header)
            for row_index in range(sheet.nrows):
                data_list.append([stringify_excel_value(value) for value in sheet.row_values(row_index)])

            # Check if header is valid
            valid_header = self.get_and_validate_header(data_list)

            if valid_header:
                self.process_data(data_list, sheet_name)
                at_least_one_valid_sheet = True

        if not at_least_one_valid_sheet:
            raise forms.ValidationError(
                'No valid sheets were detected in the file. Please check to make sure your headers are correct and start in the top-left corner.'
            )

    def process_csv_file(self):
        data_reader = unicode_csv_reader(self.current_file, delimiter=',')
        data_list = data_reader

        # Check if header is valid
        valid_header = self.get_and_validate_header(data_list)

        if valid_header:
            self.process_data(data_list)

        # IF NOT VALID, THROW ERROR
        else:
            raise forms.ValidationError('The file is not formatted correctly. Please check the header of the file.')

    def process_file(self):
        # Save the data upload if necessary (ostensibly save should only run after validation)
        if self.save:
            self.data_file_upload.save()

        self.current_file.seek(0, 0)
        try:
            self.process_excel_file()
        except xlrd.XLRDError:
            self.process_csv_file()


# TODO TODO TODO PLEASE REVISE STYLES WHEN POSSIBLE
# def ICC_A(X):
#    # This function is to calculate the ICC absolute agreement value for the input matrix
#    X = X.dropna()
#    icc_mat = X.values
#
#    Count_Row = icc_mat.shape[0]  # gives number of row count
#    Count_Col = icc_mat.shape[1]  # gives number of col count
#
#    # ICC row mean
#    icc_row_mean = icc_mat.mean(axis=1)
#
#    # ICC column mean
#    icc_col_mean = icc_mat.mean(axis=0)
#
#    # ICC total mean
#    icc_total_mean = icc_mat.mean()
#
#    # Sum of squre row and column means
#    SSC = sum((icc_col_mean - icc_total_mean) ** 2) * Count_Row
#
#    SSR = sum((icc_row_mean - icc_total_mean) ** 2) * Count_Col
#
#    # sum of squre errors
#    SSE = 0
#    for row in range(Count_Row):
#        for col in range(Count_Col):
#            SSE = SSE + (icc_mat[row, col] - icc_row_mean[row] - icc_col_mean[col] + icc_total_mean) ** 2
#
#    # SSW = SSE + SSC
#    MSR = SSR / (Count_Row - 1)
#    MSE = SSE / ((Count_Row - 1) * (Count_Col - 1))
#    MSC = SSC / (Count_Col - 1)
#    # MSW = SSW / (Count_Row*(Count_Col-1))
#    ICC_A = (MSR - MSE) / (MSR + (Count_Col - 1) * MSE + Count_Col * (MSC - MSE) / Count_Row)
#    return ICC_A

def Max_CV(X):
    #This function is to estimate the maximum CV of all chips' measurements through time (row)
    if X.isnull().sum().sum()>0:
        Y=Matrix_Fill(X)
    else:
        Y=X
    icc_mat=Y.values
    a_count=Y.shape[0]
    CV_Array=pd.DataFrame(index=Y.index,columns=['CV (%)'])
    for row in range(a_count):
        if np.std(icc_mat[row,:])>0:
            CV_Array.iloc[row][0]=np.std(icc_mat[row,:],ddof=1)/np.mean(icc_mat[row,:])*100.0
        else:
            CV_Array.iloc[row][0]=0
    #Calculate Max CV
    Max_CV = CV_Array.max(axis=0)
    return Max_CV


def CV_Array(X):
    #This fuction is to calculate the CVs on every time point
    if X.isnull().sum().sum()>0:
        Y=Matrix_Fill(X)
    else:
        Y=X
    icc_mat=Y.values
    #This fuction is to calculate the CVs on every time point
    a_count=Y.shape[0]
    CV_Array=pd.DataFrame(index=Y.index,columns=['CV (%)'])
    for row in range(a_count):
        if np.std(icc_mat[row,:])>0:
            CV_Array.iloc[row][0]=np.std(icc_mat[row,:],ddof=1)/np.mean(icc_mat[row,:])*100.0
        else:
            CV_Array.iloc[row][0]=0
    CV_Array=CV_Array.round(2)
    return CV_Array


def MAD_score(X):
    #Calculate the MAD score matrix for all chips' mesurements
    if X.isnull().sum().sum()>0:
        Y=Matrix_Fill(X)
    else:
        Y=X
    #MAD Score matrix
    icc_mat=Y.values
    Count_Row=icc_mat.shape[0] #gives number of row count
    Count_Col=icc_mat.shape[1] #gives number of col count
    mad_diff = pd.DataFrame(index=Y.index,columns=Y.columns, dtype='float') #define the empty dataframe
    icc_median=Y.median(axis=1)
    for row in range(Count_Row):
        for col in range(Count_Col):
            mad_diff.iloc[row][col]=abs(Y.iloc[row][col]-icc_median.values[row])

    mad_icc=mad_diff.median(axis=1)
    mad_score = pd.DataFrame(index=Y.index,columns=Y.columns, dtype='float') #define the empty dataframe
    for row in range(Count_Row):
        for col in range(Count_Col):
            if mad_icc.values[row]>0:
                mad_score.iloc[row][col]=0.6745*(Y.iloc[row][col]-icc_median.values[row])/mad_icc.values[row]
            else:
                mad_score.iloc[row][col]=0
    mad_score=mad_score.round(2)
    return mad_score


def chip_med_comp_ICC(X):
    #This fuction calculates the ICC absolute agreement table by comparing each chip mesurements with the median
    #of all chips' measurements. Also report the missing points for each chip
    if X.isnull().sum().sum()>0:
        Y=Matrix_Fill(X)
    else:
        Y=X
    icc_mat=Y.values
    Count_Col=icc_mat.shape[1] #gives number of column count
    col_index=Y.columns
    df_missing=X.isnull().sum(axis=0)
    #define ICC list dataframe
    icc_comp_value=pd.DataFrame(index=list(range(Count_Col)),columns=['Chip ID','ICC Absolute Agreement','Missing Data Points'])
    icc_median=Y.median(axis=1)
    for col in range(Count_Col):
        df=pd.DataFrame(Y,columns=[col_index[col]])
        icc_comp_mat=pd.concat([icc_median, df], join='outer', axis=1)
        icc_comp_value.iloc[col][0]=col_index[col]
        icc_comp_value.iloc[col][1]=ICC_A(icc_comp_mat)
        icc_comp_value.iloc[col][2]=df_missing[col]
    icc_comp_value['ICC Absolute Agreement']=icc_comp_value['ICC Absolute Agreement'].apply(lambda x: round(x,2))
    return icc_comp_value


def Matrix_Fill(X):
    #This function fill the missing data points by average data through time (row)
    missing_stat= X.isnull()
    row_mean=X.mean(axis=1)
    icc_mat=X.values
    Count_Row=icc_mat.shape[0] #gives number of row count
    Count_Col=icc_mat.shape[1] #gives number of col count
    fill_mat = pd.DataFrame(index=X.index,columns=X.columns, dtype='float') #define the empty dataframe
    for row in range(Count_Row):
        for col in range(Count_Col):
            if missing_stat.iloc[row][col] == True:
               fill_mat.iloc[row][col]=row_mean.values[row]
            else:
                fill_mat.iloc[row][col]=X.iloc[row][col]

    return fill_mat


def Reproducibility_Index(X):
    #This function is to calculate the Max CV and ICC absolute agreement data table
    if X.isnull().sum().sum()>0:
        Y=Matrix_Fill(X)
    else:
        Y=X
    Max_CV_value=Max_CV(Y) #Call Max CV function
    ICC_Value=ICC_A(Y) #Call ICC function
    #Create a reproducibility index dataframe
    rep_index=pd.DataFrame(index=list(range(1)),columns=['Max CV','ICC Absolute Agreement'], dtype='float') #define the empty dataframe
    rep_index.iloc[0][0]=Max_CV_value
    rep_index.iloc[0][1]=ICC_Value
    rep_index=rep_index.round(2)
    return rep_index


def Single_Time_Reproducibility_Index(X):
    #This function is to calculate the CV, mean, Median and standard deviation for evaluate the reproducibility of single
    #time measurements
    rep_mean=X.mean(axis=1)
    rep_sd=X.std(axis=1,ddof=1)
    rep_med=X.median(axis=1)
    rep_index=pd.DataFrame(index=list(range(1)),columns=['CV','Mean','Standard Deviation','Median'], dtype='float')
    if rep_sd.iloc[0] > 0:
        rep_index.iloc[0][0]=X.std(axis=1,ddof=1)/X.mean(axis=1)*100

    rep_index.iloc[0][1]=rep_mean
    rep_index.iloc[0][2]=rep_sd
    rep_index.iloc[0][3]=rep_med
    rep_index=rep_index.round(2)
    return rep_index


def Reproducibility_Report(group_count, study_data):
    #Calculate and report the reproducibility index and status and other parameters
    #Select unique group rows by study, organ model,sample location, assay and unit
    #Drop null value rows
    study_data= study_data.dropna(subset=['Value'])
    #Define the Chip ID column to string type
    study_data[['Chip ID']] = study_data[['Chip ID']].astype(str)

    # OLD
    # study_group=study_data[["Organ Model","Cells","Compound Treatment(s)","Target/Analyte","Method/Kit","Sample Location","Value Unit","Settings"]]
    # study_unique_group=study_group.drop_duplicates()
    # study_unique_group.set_index([range(study_unique_group.shape[0])],drop=True, append=False, inplace=True)
    chip_data = study_data.groupby(['Treatment Group', 'Chip ID', 'Time (day)', 'Study ID'], as_index=False)['Value'].mean()

    #create reproducibility report table
    header_list=chip_data.columns.values.tolist()
    header_list.append('Max CV')
    header_list.append('ICC Absolute Agreement')
    header_list.append('Reproducibility Status')
    header_list.append('Treatment Group')
    header_list.append('# of Chips/Wells')
    header_list.append('# of Time Points')
    header_list.append('Reproducibility Note')

    reproducibility_results_table = []

    for x in range(group_count+1):
        reproducibility_results_table.append(header_list)

    reproducibility_results_table = pd.DataFrame(columns=header_list)

    # Define all columns of reproducibility report table
    # Loop every unique replicate group
    # group_count=len(study_unique_group.index)
    for row in range(group_count):
        # rep_matrix=study_data[study_data['Organ Model']==study_unique_group['Organ Model'][row]]
        # rep_matrix=rep_matrix[rep_matrix['Cells']==study_unique_group['Cells'][row]]
        # rep_matrix=rep_matrix[rep_matrix['Compound Treatment(s)']==study_unique_group['Compound Treatment(s)'][row]]
        # rep_matrix=rep_matrix[rep_matrix['Target/Analyte']==study_unique_group['Target/Analyte'][row]]
        # rep_matrix=rep_matrix[rep_matrix['Method/Kit']==study_unique_group['Method/Kit'][row]]
        # rep_matrix=rep_matrix[rep_matrix['Sample Location']==study_unique_group['Sample Location'][row]]
        # rep_matrix=rep_matrix[rep_matrix['Value Unit']==study_unique_group['Value Unit'][row]]
        # rep_matrix=rep_matrix[rep_matrix['Settings']==study_unique_group['Settings'][row]]
        # create replicate matrix for intra reproducibility analysis
        rep_matrix = chip_data[chip_data['Treatment Group'] == str(row + 1)]
        icc_pivot = pd.pivot_table(rep_matrix, values='Value', index='Time (day)',columns=['Chip ID'], aggfunc=np.mean)

        group_id = str(row+1) #Define group ID

        group_rep_matrix = pd.DataFrame(index=[0], columns=header_list)
        reproducibility_results_table = reproducibility_results_table.append(group_rep_matrix, ignore_index=True)

        reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Treatment Group')] = group_id
        reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('# of Chips/Wells')] = icc_pivot.shape[1]
        reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('# of Time Points')] = icc_pivot.shape[0]

        # Check all coulmns are redundent
        if icc_pivot.shape[1]>1 and all(icc_pivot.eq(icc_pivot.iloc[:, 0], axis=0).all(1)):
            reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='NA'
            reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Note')] ='Duplicate data on chips/wells'
        elif icc_pivot.shape[0]>1 and all(icc_pivot.eq(icc_pivot.iloc[0, :], axis=1).all(1)):
            reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='NA'
            reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Note')] ='Duplicate data on all time points'
        else:
            if icc_pivot.shape[0]>1 and icc_pivot.shape[1]>1:
                #Call a chip time series reproducibility index dataframe
                rep_index=Reproducibility_Index(icc_pivot)
                if pd.isnull(rep_index.iloc[0][0]) != True:
                    reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Max CV')] =rep_index.iloc[0][0]
                    reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('ICC Absolute Agreement')] =rep_index.iloc[0][1]

                    if rep_index.iloc[0][0] <= 15 and rep_index.iloc[0][0] >0:
                        if rep_index.iloc[0][0] <= 5:
                            reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Excellent (CV)'
                        elif rep_index.iloc[0][1] >= 0.8:
                            reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Excellent (ICC)'
                        else:
                            reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Acceptable (CV)'
                    else:
                        if rep_index.iloc[0][1] >= 0.8:
                            reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Excellent (ICC)'
                        elif rep_index.iloc[0][1] >= 0.2:
                            reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Acceptable (ICC)'
                        else:
                            reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Poor (ICC)'
                else:
                    reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='NA'
            elif icc_pivot.shape[0]<2 and icc_pivot.shape[1]>1:
                 #Call a single time reproducibility index dataframe
                rep_index=Single_Time_Reproducibility_Index(icc_pivot)
                reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Max CV')] =rep_index.iloc[0][0]
                if rep_index.iloc[0][0] <= 5 and rep_index.iloc[0][0] > 0:
                    reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Excellent (CV)'
                elif rep_index.iloc[0][0] <= 15 and rep_index.iloc[0][0] > 5:
                    reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Acceptable (CV)'
                elif rep_index.iloc[0][0] > 15:
                    reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Poor (CV)'
                elif rep_index.iloc[0][0] < 0:
                    reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='NA'
                    reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Note')] ='CV cannot be calculated from negative data.'
                else:
                    reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='NA'
            else:
                reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='NA'
                reproducibility_results_table.iloc[row, reproducibility_results_table.columns.get_loc('Reproducibility Note')] ='Insufficient replicate chips/wells to calculate reproducibility. At least 2 replicates are needed.'
            reproducibility_results_table=reproducibility_results_table.round(2)
    return reproducibility_results_table

# ?
# Used anywhere...?
def study_group_setting(study_unique_group,row):
    group_setting=pd.DataFrame(index=list(range(study_unique_group.shape[1])),columns=['Replicate Set Parameters','Setting'])
    for i in range(study_unique_group.shape[1]):
        group_setting.iloc[i][0]=study_unique_group.columns.tolist()[i]

    for i in range(study_unique_group.shape[1]):
        group_setting.iloc[i][1]=study_unique_group.iloc[row][i]
    return group_setting


def pivot_data_matrix(study_data,group_index):
    rep_matrix = study_data[study_data['Treatment Group']==group_index]
    # #Drop null value rows
    # study_data= study_data.dropna(subset=['Value'])
    # #Define the Chip ID column to string type
    # study_data[['Chip ID']] = study_data[['Chip ID']].astype(str)
    # row=group_index
    # study_group=study_data[["Organ Model","Cells","Compound Treatment(s)","Target/Analyte","Method/Kit","Sample Location","Value Unit","Settings"]]
    # study_unique_group=study_group.drop_duplicates()
    # study_unique_group.set_index([range(study_unique_group.shape[0])],drop=True, append=False, inplace=True)
    # rep_matrix=study_data[study_data['Organ Model']==study_unique_group['Organ Model'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Cells']==study_unique_group['Cells'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Compound Treatment(s)']==study_unique_group['Compound Treatment(s)'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Target/Analyte']==study_unique_group['Target/Analyte'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Method/Kit']==study_unique_group['Method/Kit'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Sample Location']==study_unique_group['Sample Location'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Value Unit']==study_unique_group['Value Unit'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Settings']==study_unique_group['Settings'][row]]
    #create replicate matrix for intra reproducibility analysis
    icc_pivot = pd.pivot_table(rep_matrix, values='Value', index='Time (day)',columns=['Chip ID'], aggfunc=np.mean)
    return icc_pivot


def scatter_plot_matrix(study_data,group_index):
    rep_matrix = study_data[study_data['Treatment Group']==group_index]
    # #Drop null value rows
    # study_data= study_data.dropna(subset=['Value'])
    # #Define the Chip ID column to string type
    # study_data[['Chip ID']] = study_data[['Chip ID']].astype(str)
    # row=group_index
    # study_group=study_data[["Organ Model","Cells","Compound Treatment(s)","Target/Analyte","Method/Kit","Sample Location","Value Unit","Settings"]]
    # study_unique_group=study_group.drop_duplicates()
    # study_unique_group.set_index([range(study_unique_group.shape[0])],drop=True, append=False, inplace=True)
    # rep_matrix=study_data[study_data['Organ Model']==study_unique_group['Organ Model'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Cells']==study_unique_group['Cells'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Compound Treatment(s)']==study_unique_group['Compound Treatment(s)'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Target/Analyte']==study_unique_group['Target/Analyte'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Method/Kit']==study_unique_group['Method/Kit'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Sample Location']==study_unique_group['Sample Location'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Value Unit']==study_unique_group['Value Unit'][row]]
    # rep_matrix=rep_matrix[rep_matrix['Settings']==study_unique_group['Settings'][row]]
    #create replicate matrix for intra reproducibility analysis

    icc_pivot = pd.pivot_table(rep_matrix, values='Value', index='Time (day)',columns=['Chip ID'], aggfunc=np.mean)
    if icc_pivot.isnull().sum().sum()>0:
        Y=Matrix_Fill(icc_pivot)
    else:
        Y=icc_pivot
    d_median = Y.median(axis=1)
    plot_matrix=icc_pivot
    plot_header_list=plot_matrix.columns.values.tolist()
    plot_header_list.insert(0, 'Median')
    plot_matrix = plot_matrix.reindex(columns = plot_header_list)
    for i in range(len(d_median)):
        plot_matrix.iloc[i, plot_matrix.columns.get_loc('Median')] = d_median.iloc[i]

    return plot_matrix


def get_repro_data(group_count, data):
    #Load the summary data into the dataframe
    study_data = pd.DataFrame(data)
    study_data.columns = study_data.iloc[0]
    study_data = study_data.drop(study_data.index[0])
    #Drop null value rows
    study_data['Value'].replace('', np.nan, inplace=True)
    study_data= study_data.dropna(subset=['Value'])
    study_data['Value'] = study_data['Value'].astype(float)
    #Define the Chip ID column to string type
    study_data[['Chip ID']] = study_data['Chip ID'].astype(str)

    #Add Time (day) calculated from three time column
    study_data["Time (day)"] = study_data['Time']/1440.0
    study_data["Time (day)"] = study_data["Time (day)"].apply(lambda x: round(x,2))

    # #Select unique group rows by study, organ model,sample location, assay and unit
    # study_group=study_data[["Organ Model","Cells","Compound Treatment(s)","Target/Analyte","Method/Kit","Sample Location","Value Unit","Settings"]]
    # study_unique_group=study_group.drop_duplicates()
    # study_unique_group.set_index([range(study_unique_group.shape[0])],drop=True, append=False, inplace=True)

    #create reproducibility report table
    reproducibility_results_table=Reproducibility_Report(group_count, study_data)

    datadict = {}

    #Define all columns of reproducibility report table
    reproducibility_results_table_nanless = reproducibility_results_table.fillna('')
    datadict['reproducibility_results_table'] = reproducibility_results_table_nanless.to_dict('split')

    #Loop every unique replicate group
    # group_count=len(study_unique_group.index)

    for row in range(group_count):
        datadict[row] = {}

        group_id = str(row+1) #Define group ID

        icc_pivot = pivot_data_matrix(study_data, group_id)

        #Call MAD score function
        mad_score_matrix=MAD_score(icc_pivot)#.round(2)
        datadict[row]['mad_score_matrix'] = mad_score_matrix.to_dict('split')

        cv_chart=scatter_plot_matrix(study_data,group_id).fillna('')
        datadict[row]['cv_chart'] = cv_chart.to_dict('split')

        if icc_pivot.shape[0]>1 and all(icc_pivot.eq(icc_pivot.iloc[0, :], axis=1).all(1)):
            CV_array= CV_Array(icc_pivot).round(2).fillna('')
            datadict[row]['CV_array'] = CV_array.to_dict('split')

        elif icc_pivot.shape[0]>1 and icc_pivot.shape[1]>1:
            #Call ICC values by Comparing each chip's observations with the Median of the Chip Observations
            comp_ICC_Value=chip_med_comp_ICC(icc_pivot).fillna('').round(2)
            datadict[row]['comp_ICC_Value'] = comp_ICC_Value.to_dict('list')
            #Call calculated CV array for all time points
            CV_array = CV_Array(icc_pivot).round(2).fillna('')
            datadict[row]['CV_array'] = CV_array.to_dict('split')
            #Call a chip time series reproducibility index dataframe
            rep_index=Reproducibility_Index(icc_pivot).round(2)
            datadict[row]['rep_index'] = rep_index.to_dict('list')
        elif icc_pivot.shape[1]>1:
            #Call a single time reproducibility index dataframe
            rep_index=Single_Time_Reproducibility_Index(icc_pivot).round(2)
            datadict[row]['rep_index'] = rep_index.to_dict('list')
        # group_index=study_group_setting(study_data,group_id)

    return datadict


def consecutive_one_new(data):
    longest = 0
    current = 0
    start_row = 0
    long_start_row = 0
    row = 0
    for num in data:
        row = row + 1
        if num == 1:
            current += 1
            if current == 1:
                start_row = row
        else:
            longest = max(longest, current)
            current = 0

        if current > longest:
            long_start_row = start_row

    return max(longest, current), long_start_row


def Single_Time_ANOVA(st_anova_data, inter_level):
    a_data = st_anova_data
    if inter_level == 1:
        samples = [condition[1] for condition in a_data.groupby('MPS User Group')['Value']]
    else:
        samples = [condition[1] for condition in a_data.groupby('Study ID')['Value']]

    f_val, p_val = stats.f_oneway(*samples)
    return p_val


def ICC_A(X):
    # This function is to calculate the ICC absolute agreement value for the input matrix
    X = X.dropna()
    icc_mat = X.values

    Count_Row = icc_mat.shape[0]  # gives number of row count
    Count_Col = icc_mat.shape[1]  # gives number of col count
    if Count_Row < 2:
        ICC_A = np.nan
    elif Count_Col < 2:
        ICC_A = np.nan
    else:
        # ICC row mean
        icc_row_mean = icc_mat.mean(axis=1)

        # ICC column mean
        icc_col_mean = icc_mat.mean(axis=0)

        # ICC total mean
        icc_total_mean = icc_mat.mean()

        # Sum of squre row and column means
        SSC = sum((icc_col_mean - icc_total_mean) ** 2) * Count_Row

        SSR = sum((icc_row_mean - icc_total_mean) ** 2) * Count_Col

        # sum of squre errors
        SSE = 0
        for row in range(Count_Row):
            for col in range(Count_Col):
                SSE = SSE + (icc_mat[row, col] - icc_row_mean[row] - icc_col_mean[col] + icc_total_mean) ** 2

        # SSW = SSE + SSC
        MSR = SSR / (Count_Row - 1)
        MSE = SSE / ((Count_Row - 1) * (Count_Col - 1))
        MSC = SSC / (Count_Col - 1)
        # MSW = SSW / (Count_Row*(Count_Col-1))
        ICC_A = (MSR - MSE) / (MSR + (Count_Col - 1) * MSE + Count_Col * (MSC - MSE) / Count_Row)
    return ICC_A


def Inter_Max_CV(X):
    # This function is to estimate the maximum CV of cross centers or studies' measurements through time (row)
    Y = X.dropna()
    icc_mat = Y.values
    a_count = Y.shape[0]
    CV_Array = pd.DataFrame(index=Y.index, columns=['CV (%)'])
    for row in range(a_count):
        if np.std(icc_mat[row, :]) > 0:
            CV_Array.iloc[row][0] = np.std(icc_mat[row, :], ddof=1) / np.mean(icc_mat[row, :]) * 100.0
        else:
            CV_Array.iloc[row][0] = 0
    # Calculate Max CV
    Max_CV = CV_Array.max(axis=0)
    return Max_CV


def Inter_Reproducibility_Index(X):
    # This function is to calculate the Max CV and ICC absolute agreement data table

    Y = X.dropna()
    Max_CV_value = Inter_Max_CV(Y)  # Call Max CV function
    if Y.shape[0] > 1 and Y.shape[1] > 1:
        ICC_Value = ICC_A(Y)  # Call ICC function
    else:
        ICC_Value = np.nan
    # Create a reproducibility index dataframe
    rep_index = pd.DataFrame(index=list(range(1)), columns=['Max CV', 'ICC Absolute Agreement'],
                             dtype='float')  # define the empty dataframe
    rep_index.iloc[0][0] = Max_CV_value
    rep_index.iloc[0][1] = ICC_Value
    # rep_index = rep_index.round(2)
    return rep_index


def fill_nan(A, interp_method):
    '''
    interpolate to fill nan values
    '''
    try:
        inds = np.arange(A.shape[0])
        good = np.where(np.isfinite(A))
        if interp_method == 'cubic':
            cs = CubicSpline(inds[good], A[good], extrapolate=False)
            B = np.where(np.isfinite(A), A, cs(inds))
            fill_status = True
        else:
            f = sp.interp1d(inds[good], A[good], kind=interp_method, bounds_error=False)
            B = np.where(np.isfinite(A), A, f(inds))
            fill_status = True
    except ValueError:
        B = A
        fill_status = False
    return B, fill_status


def update_missing_nan(update_missing_block, A):
    s_row = update_missing_block.iloc[0, 1] - 1
    e_row = update_missing_block.iloc[0, 1] + update_missing_block.iloc[0, 0] - 1
    for i in range(s_row, e_row):
        A[i] = 0
    return A


def search_nan_blocks(df_s):
    total_rows = len(df_s)
    missing_list = []
    for i in range(total_rows):
        if np.isnan(df_s.iloc[i]):
            missing_list.append(1)
        else:
            missing_list.append(0)

    nan_blocks_df = pd.DataFrame(columns=['nan block size', 'block_start_row', 'Out NaN'])
    block_df = pd.DataFrame(index=[1], columns=['nan block size', 'block_start_row', 'Out NaN'])

    [max_missing_len, max_missing_len_start_row] = consecutive_one_new(missing_list)
    while True:
        if max_missing_len > 0:
            block_df.iloc[0, 0] = max_missing_len
            block_df.iloc[0, 1] = max_missing_len_start_row
            if max_missing_len_start_row == 1 or max_missing_len_start_row + max_missing_len - 1 == total_rows:
                block_df.iloc[0, 2] = True
            else:
                block_df.iloc[0, 2] = False
            nan_blocks_df = nan_blocks_df.append(block_df, ignore_index=True)
            missing_list = update_missing_nan(block_df, missing_list)
            [max_missing_len, max_missing_len_start_row] = consecutive_one_new(missing_list)
        else:
            break
    return nan_blocks_df


def max_in_nan_size_array(df_s):
    nan_blocks = search_nan_blocks(df_s)
    in_nan_blocks = nan_blocks[nan_blocks['Out NaN'] == False]
    if len(in_nan_blocks.index) > 0:
        max_nan_size_array = max(in_nan_blocks.iloc[:, 0])
    else:
        max_nan_size_array = 0
    return max_nan_size_array


def max_in_nan_size_matrix(pivot_group_matrix):
    no_cols = pivot_group_matrix.shape[1]
    max_in_nan_matrix = 0
    for col in range(no_cols):
        curr_size = max_in_nan_size_array(pivot_group_matrix.iloc[:, col])
        if curr_size > max_in_nan_matrix:
            max_in_nan_matrix = curr_size
    return max_in_nan_matrix


def matrix_interpolate(group_chip_data, interp_method, inter_level):
    if inter_level == 1:
        interp_group_matrix = pd.pivot_table(group_chip_data, values='Value', index='Time', columns=['MPS User Group'],
                                             aggfunc=np.mean)
    else:
        interp_group_matrix = pd.pivot_table(group_chip_data, values='Value', index='Time', columns=['Study ID'],
                                             aggfunc=np.mean)

    fill_header_list = interp_group_matrix.columns.values.tolist()
    for col in range(interp_group_matrix.shape[1]):
        df_arr = interp_group_matrix.values[:, col]
        df_s = interp_group_matrix.iloc[:, col]
        if max_in_nan_size_array(df_s) > 0:
            [interp_group_matrix[fill_header_list[col]], fill_status] = fill_nan(df_arr, interp_method)
    return interp_group_matrix


def update_group_reproducibility_index_status(group_rep_matrix, rep_index):
    group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('ICC Absolute Agreement')] = rep_index.iloc[0, 1]
    group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Max CV')] = rep_index.iloc[0, 0]

    if group_rep_matrix.iloc[0, 4] == 0:
        group_rep_matrix.iloc[
            0, group_rep_matrix.columns.get_loc('Reproducibility Note')] = 'No overlaped time for comparing'
    else:
        if pd.isnull(rep_index.iloc[0, 1]) == True:
            if rep_index.iloc[0, 0] <= 5:
                group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Excellent (CV)'
            elif rep_index.iloc[0, 0] > 5 and rep_index.iloc[0, 0] <= 15:
                group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Acceptable (CV)'
            elif rep_index.iloc[0, 0] > 15:
                group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Poor (CV)'
            else:
                group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = np.nan
        else:
            if rep_index.iloc[0][0] <= 15 and rep_index.iloc[0][0] > 0:
                if rep_index.iloc[0][0] <= 5:
                    group_rep_matrix.iloc[
                        0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Excellent (CV)'
                elif rep_index.iloc[0][1] >= 0.8:
                    group_rep_matrix.iloc[
                        0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Excellent (ICC)'
                else:
                    group_rep_matrix.iloc[
                        0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Acceptable (CV)'
            else:
                if rep_index.iloc[0][1] >= 0.8:
                    group_rep_matrix.iloc[
                        0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Excellent (ICC)'
                elif rep_index.iloc[0][1] >= 0.2:
                    group_rep_matrix.iloc[
                        0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Acceptable (ICC)'
                elif rep_index.iloc[0][1] < 0.2:
                    group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Poor (ICC)'
                else:
                    group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = np.nan
    return group_rep_matrix


def interpolate_group_rep_index(header_list, group_chip_data, interp_method, inter_level, max_interpolation_size,
                                group_id, initial_Norm=0):
    if inter_level == 1:
        interp_group_matrix = pd.pivot_table(group_chip_data, values='Value', index='Time', columns=['MPS User Group'],
                                             aggfunc=np.mean)
    else:
        interp_group_matrix = pd.pivot_table(group_chip_data, values='Value', index='Time', columns=['Study ID'],
                                             aggfunc=np.mean)

    origin_isnull = interp_group_matrix.isnull()
    origin_isnull_col = pivot_transpose_to_column(origin_isnull, inter_level)
    interp_mat = matrix_interpolate(group_chip_data, interp_method, inter_level)  # interpolate

    # Update maximum interpolation size
    if max_in_nan_size_matrix(interp_group_matrix) > max_interpolation_size:
        for col in range(interp_group_matrix.shape[1]):
            df_s = interp_group_matrix.iloc[:, col]
            if max_in_nan_size_array(df_s) > max_interpolation_size:
                nan_blocks = search_nan_blocks(df_s)
                for b_row in range(nan_blocks.shape[0]):
                    if nan_blocks.iloc[b_row, 0] > max_interpolation_size and nan_blocks.iloc[b_row, 2] == False:
                        for i in range(nan_blocks.iloc[b_row, 1] - 1,
                                       nan_blocks.iloc[b_row, 1] - 1 + nan_blocks.iloc[b_row, 0]):
                            interp_mat.iloc[i, col] = np.nan

    if initial_Norm == 1:
        # Normalize each center data by the median value
        norm_pivot_group_matrix = interp_mat
        for norm_col in range(interp_mat.shape[1]):
            med_value = interp_mat.iloc[:, norm_col].dropna().median()

            for norm_row in range(interp_mat.shape[0]):
                if pd.isnull(interp_mat.iloc[norm_row, norm_col]) == False and med_value > 0:
                    norm_pivot_group_matrix.iloc[norm_row, norm_col] = interp_mat.iloc[
                                                                           norm_row, norm_col] / med_value
        interp_mat = norm_pivot_group_matrix

        # Build inter data set
    inter_data_set = pivot_transpose_to_column(interp_mat.dropna(), inter_level)
    inter_data_set['Value Source'] = 'Original'
    inter_data_set['Data Set'] = interp_method
    inter_data_set['Treatment Group'] = group_id

    for set_row in range(inter_data_set.shape[0]):
        time_value = inter_data_set.iloc[set_row, 0]
        inter_value = inter_data_set.iloc[set_row, 1]
        if inter_level == 1:
            null_state = origin_isnull_col[
                (origin_isnull_col['Time'] == time_value) & (origin_isnull_col['MPS User Group'] == inter_value)].iloc[
                0, 2]
        else:
            null_state = origin_isnull_col[
                (origin_isnull_col['Time'] == time_value) & (origin_isnull_col['Study ID'] == inter_value)].iloc[0, 2]

        if null_state == True:
            inter_data_set.iloc[set_row, inter_data_set.columns.get_loc('Value Source')] = 'Interpolated'

    icc_data = interp_mat.dropna()
    group_rep_matrix = pd.DataFrame(index=[0], columns=header_list)
    group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Treatment Group')] = group_id
    group_rep_matrix.iloc[0, 3] = icc_data.shape[1]
    group_rep_matrix.iloc[0, 4] = icc_data.shape[0]
    group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Interpolation Method')] = interp_method.title()
    group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Max Interpolation Size')] = max_interpolation_size
    rep_index = Inter_Reproducibility_Index(icc_data)
    group_rep_matrix = update_group_reproducibility_index_status(group_rep_matrix, rep_index)

    return group_rep_matrix, inter_data_set


def pivot_transpose_to_column(pivot_data, inter_level):
    row_count = pivot_data.shape[0]
    col_count = pivot_data.shape[1]
    if inter_level == 1:
        col_name = ['Time', 'MPS User Group', 'Value']
    else:
        col_name = ['Time', 'Study ID', 'Value']
    df_one = pd.DataFrame(index=[0], columns=col_name)
    column_data = pd.DataFrame(columns=col_name)
    for row in range(row_count):
        for col in range(col_count):
            df_one.iloc[0, 0] = pivot_data.index[row]
            df_one.iloc[0, 1] = pivot_data.columns.values[col]
            df_one.iloc[0, 2] = pivot_data.iloc[row, col]
            column_data = column_data.append(df_one, ignore_index=True)
    return column_data


def Inter_reproducibility(group_count, inter_data_df, inter_level=1, max_interpolation_size=2, initial_Norm=0):
    # Evaluate inter-center/study reproducibility

    inter_data_df[['Chip ID']] = inter_data_df[['Chip ID']].astype(str)
    inter_data_df[['Study ID']] = inter_data_df[['Study ID']].astype(str)

    # Calculate the average value group by chip level
    chip_data = inter_data_df.groupby(['Treatment Group', 'Chip ID', 'Time', 'Study ID', 'MPS User Group'], as_index=False)['Value'].mean()

    # create reproducibility report table
    # reproducibility_results_table=group_df
    # header_list=group_df.columns.values.tolist()
    inter_data_header_list = []
    inter_data_header_list.append('Time')
    if inter_level == 1:
        inter_data_header_list.append('MPS User Group')
    else:
        inter_data_header_list.append('Study ID')
    inter_data_header_list.append('Value')
    inter_data_header_list.append('Value Source')
    inter_data_header_list.append('Data Set')
    inter_data_header_list.append('Treatment Group')
    inter_data_table = pd.DataFrame(columns=inter_data_header_list)

    header_list = []
    header_list.append('Treatment Group')
    header_list.append('Interpolation Method')
    header_list.append('Max Interpolation Size')
    if inter_level == 1:
        header_list.append('# of Centers')
        header_list.append('# of Overlaped Cross-Center Time Points')
    else:
        header_list.append('# of Studies')
        header_list.append('# of Overlaped Cross-Study Time Points')
    header_list.append('Max CV')
    header_list.append('ICC Absolute Agreement')
    header_list.append('ANOVA P-Value')
    header_list.append('Reproducibility Status')
    header_list.append('Reproducibility Note')

    # Define all columns of reproducibility report table
    reproducibility_results_table = pd.DataFrame(columns=header_list)

    # Define all columns of original and
    # Loop every unique replicate group
    for row in range(group_count):
        group_id = str(row + 1)
        # group_chip_data = chip_data[chip_data['Treatment Group'] == 'Group ' + str(row + 1)]
        group_chip_data = chip_data[chip_data['Treatment Group'] == str(row + 1)]

        if group_chip_data.shape[0] < 1:
            group_rep_matrix = pd.DataFrame(index=[0], columns=header_list)
            group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Treatment Group')] = group_id
            group_rep_matrix.iloc[0, 3] = np.nan
            group_rep_matrix.iloc[
                0, group_rep_matrix.columns.get_loc('Reproducibility Note')] = 'No data for this group'
            reproducibility_results_table = reproducibility_results_table.append(group_rep_matrix, ignore_index=True)
        else:
            if inter_level == 1:
                pivot_group_matrix = pd.pivot_table(group_chip_data, values='Value', index='Time',
                                                    columns=['MPS User Group'], aggfunc=np.mean)
            else:
                pivot_group_matrix = pd.pivot_table(group_chip_data, values='Value', index='Time', columns=['Study ID'],
                                                    aggfunc=np.mean)

            if pivot_group_matrix.shape[1] < 2:

                group_rep_matrix = pd.DataFrame(index=[0], columns=header_list)
                group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Treatment Group')] = group_id
                # group_rep_matrix.iloc[0, 3] = np.nan
                group_rep_matrix.iloc[0, 3] = pivot_group_matrix.shape[1]
                group_rep_matrix.iloc[
                    0, group_rep_matrix.columns.get_loc('Reproducibility Note')] = 'Fewer than two centers/studies'
                reproducibility_results_table = reproducibility_results_table.append(group_rep_matrix,
                                                                                     ignore_index=True)
            else:
                if initial_Norm == 1 and pivot_group_matrix.shape[0] > 0:
                    # Normalize each center data by the median value
                    norm_pivot_group_matrix = pivot_group_matrix
                    for norm_col in range(pivot_group_matrix.shape[1]):
                        med_value = pivot_group_matrix.iloc[:, norm_col].dropna().median()

                        for norm_row in range(pivot_group_matrix.shape[0]):
                            if pd.isnull(pivot_group_matrix.iloc[norm_row, norm_col]) == False and med_value > 0:
                                norm_pivot_group_matrix.iloc[norm_row, norm_col] = pivot_group_matrix.iloc[
                                                                                       norm_row, norm_col] / med_value
                    pivot_group_matrix = norm_pivot_group_matrix

                # Trim nan data points
                no_nan_matrix = pivot_group_matrix.dropna()

                # Add trimmed data to the inter data table when there are overlaped time points existing
                if no_nan_matrix.shape[0] > 0:
                    inter_data_set = pivot_transpose_to_column(no_nan_matrix, inter_level)
                    inter_data_set['Value Source'] = 'Original'
                    inter_data_set['Data Set'] = 'trimmed'
                    inter_data_set['Treatment Group'] = group_id
                    inter_data_table = inter_data_table.append(inter_data_set, ignore_index=True)

                if no_nan_matrix.shape[1] < 2:
                    group_rep_matrix = pd.DataFrame(index=[0], columns=header_list)
                    group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Treatment Group')] = group_id
                    group_rep_matrix.iloc[0, 3] = no_nan_matrix.shape[1]
                    group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Reproducibility Note')] = 'Fewer than two centers/studies'
                    reproducibility_results_table = reproducibility_results_table.append(group_rep_matrix,
                                                                                         ignore_index=True)
                elif no_nan_matrix.shape[0] < 1:
                    group_rep_matrix = pd.DataFrame(index=[0], columns=header_list)
                    group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Treatment Group')] = group_id
                    group_rep_matrix.iloc[0, 3] = no_nan_matrix.shape[1]
                    group_rep_matrix.iloc[0, 4] = 0
                    group_rep_matrix.iloc[
                        0, group_rep_matrix.columns.get_loc('Reproducibility Note')] = 'No overlaped time for comparing'

                    reproducibility_results_table = reproducibility_results_table.append(group_rep_matrix,
                                                                                         ignore_index=True)
                elif no_nan_matrix.shape[0] == 1 and no_nan_matrix.shape[1] >= 2:
                    if initial_Norm == 1:
                        single_time = no_nan_matrix.index[0]
                        group_rep_matrix = pd.DataFrame(index=[0], columns=header_list)
                        group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Treatment Group')] = group_id
                        group_rep_matrix.iloc[0, 3] = no_nan_matrix.shape[1]
                        group_rep_matrix.iloc[0, 4] = no_nan_matrix.shape[0]
                        group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('ANOVA P-Value')] = np.nan
                        group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Max CV')] = np.nan
                        group_rep_matrix.iloc[
                            0, group_rep_matrix.columns.get_loc('Reproducibility Note')
                        ] = 'Normalized by median is not applicable to single time point'
                    else:
                        single_time = no_nan_matrix.index[0]
                        group_rep_matrix = pd.DataFrame(index=[0], columns=header_list)
                        group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Treatment Group')] = group_id
                        group_rep_matrix.iloc[0, 3] = no_nan_matrix.shape[1]
                        group_rep_matrix.iloc[0, 4] = no_nan_matrix.shape[0]
                        anova_data = group_chip_data[group_chip_data['Time'] == single_time]

                        p_value = Single_Time_ANOVA(anova_data, inter_level)

                        group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('ANOVA P-Value')] = '{0:.4g}'.format(p_value)

                        # Calcualate CV
                        single_array = no_nan_matrix.dropna()
                        single_array_val = single_array.values
                        single_CV = np.std(single_array_val, ddof=1) / np.mean(single_array_val) * 100

                        group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Max CV')] = '{0:.4g}'.format(single_CV)

                        if p_value >= 0.05:
                            if single_CV <= 5:
                                group_rep_matrix.iloc[
                                    0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Excellent (CV)'
                            elif single_CV > 5 and single_CV <= 15:
                                group_rep_matrix.iloc[
                                    0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Acceptable (CV)'
                            else:
                                group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc(
                                    'Reproducibility Status')] = 'Acceptable (P-Value)'
                        elif p_value < 0.05:
                            group_rep_matrix.iloc[
                                0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Poor (P-Value)'
                        else:
                            if single_CV <= 5:
                                group_rep_matrix.iloc[
                                    0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Excellent (CV)'
                            elif single_CV > 5 and single_CV <= 15:
                                group_rep_matrix.iloc[
                                    0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Acceptable (CV)'
                            else:
                                group_rep_matrix.iloc[
                                    0, group_rep_matrix.columns.get_loc('Reproducibility Status')] = 'Poor (CV)'

                        group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc(
                            'Reproducibility Note')] = 'Single overlaped time for comparing'
                    reproducibility_results_table = reproducibility_results_table.append(group_rep_matrix,
                                                                                         ignore_index=True)
                elif no_nan_matrix.shape[0] > 1 and no_nan_matrix.shape[1] >= 2:
                    group_rep_matrix = pd.DataFrame(index=[0], columns=header_list)
                    group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Treatment Group')] = group_id
                    group_rep_matrix.iloc[0, 3] = no_nan_matrix.shape[1]
                    group_rep_matrix.iloc[0, 4] = no_nan_matrix.shape[0]
                    icc_data = no_nan_matrix

                    rep_index = Inter_Reproducibility_Index(icc_data)
                    group_rep_matrix = update_group_reproducibility_index_status(group_rep_matrix, rep_index)
                    group_rep_matrix.iloc[0, group_rep_matrix.columns.get_loc('Interpolation Method')] = 'Trimmed'
                    reproducibility_results_table = reproducibility_results_table.append(group_rep_matrix,
                                                                                         ignore_index=True)

                    # Interpolation Analysis
                if pivot_group_matrix.shape[0] > 2 and pivot_group_matrix.shape[1] > 1 and max_in_nan_size_matrix(
                        pivot_group_matrix) > 0:
                    # nearest interpolation
                    [group_rep_matrix, inter_data_set] = interpolate_group_rep_index(header_list, group_chip_data,
                                                                                     'nearest', inter_level,
                                                                                     max_interpolation_size, group_id,
                                                                                     initial_Norm)
                    reproducibility_results_table = reproducibility_results_table.append(group_rep_matrix,
                                                                                         ignore_index=True)
                    inter_data_table = inter_data_table.append(inter_data_set, ignore_index=True)

                    # linear interpolation
                    [group_rep_matrix, inter_data_set] = interpolate_group_rep_index(header_list, group_chip_data,
                                                                                     'linear', inter_level,
                                                                                     max_interpolation_size, group_id,
                                                                                     initial_Norm)
                    reproducibility_results_table = reproducibility_results_table.append(group_rep_matrix,
                                                                                         ignore_index=True)
                    inter_data_table = inter_data_table.append(inter_data_set, ignore_index=True)

                    # quadratic interpolation
                    [group_rep_matrix, inter_data_set] = interpolate_group_rep_index(header_list, group_chip_data,
                                                                                     'quadratic', inter_level,
                                                                                     max_interpolation_size, group_id,
                                                                                     initial_Norm)
                    reproducibility_results_table = reproducibility_results_table.append(group_rep_matrix,
                                                                                         ignore_index=True)
                    inter_data_table = inter_data_table.append(inter_data_set, ignore_index=True)

                    # cubic interpolation
                    [group_rep_matrix, inter_data_set] = interpolate_group_rep_index(header_list, group_chip_data,
                                                                                     'cubic', inter_level,
                                                                                     max_interpolation_size, group_id,
                                                                                     initial_Norm)
                    reproducibility_results_table = reproducibility_results_table.append(group_rep_matrix,
                                                                                         ignore_index=True)
                    inter_data_table = inter_data_table.append(inter_data_set, ignore_index=True)

    return reproducibility_results_table, inter_data_table


def get_inter_study_reproducibility_report(group_count, inter_data, inter_level, max_interpolation_size, initial_norm):
    """
    @author: Tongying Shun (tos8@pitt.edu)
    """
    # Error if only headers present
    if len(inter_data) < 2:
        return [{}, {
            'errors': 'No data. Please review filter options.'
        }]

    # load inter data
    inter_head = inter_data.pop(0)
    inter_data_df = pd.DataFrame(inter_data)
    inter_data_df.columns = inter_head

    # Counter centers or studies
    if inter_level == 1:
        center_group = inter_data_df[["MPS User Group"]]
        center_unique_group = center_group.drop_duplicates()
        if len(center_unique_group.axes[0]) < 2:
            return [{}, {
                'errors': 'Only one MPS User Group! The cross-center reproducibility cannot be analyzed.'
                          '\nPlease try selecting the "By Study" option and clicking "Refresh."'
            }]
    else:
        study_group = inter_data_df[["Study ID"]]
        study_unique_group = study_group.drop_duplicates()
        if len(study_unique_group.axes[0]) < 2:
            return [{}, {
                'errors': 'Only one Study! The cross-study reproducibility cannot be analyzed.'
            }]

    # Return the summary and datatable
    return Inter_reproducibility(
        group_count,
        inter_data_df,
        inter_level,
        max_interpolation_size,
        initial_norm
    )

def intra_status_for_inter(study_data):
    #Calculate and report the reproducibility index and status and other parameters
    # Select unique group rows by study, organ model,sample location, assay and unit
    # Drop null value rows
    study_data = pd.DataFrame(study_data)
    study_data.columns = ["Time", "Value", "Chip ID"]
    study_data = study_data.dropna(subset=['Value'])
    # Define the Chip ID column to string type
    study_data[['Chip ID']] = study_data[['Chip ID']].astype(str)

    # create reproducibility report table
    reproducibility_results_table=study_data
    header_list=study_data.columns.values.tolist()
    header_list.append('Reproducibility Status')

    # Define all columns of reproducibility report table
    reproducibility_results_table = reproducibility_results_table.reindex(columns = header_list)

    # Define all columns of reproducibility report table
    reproducibility_results_table = reproducibility_results_table.reindex(columns = header_list)
   # create replicate matrix for intra reproducibility analysis
    icc_pivot = pd.pivot_table(study_data, values='Value', index='Time',columns=['Chip ID'], aggfunc=np.mean)
    # Check all coulmns are redundent
    if icc_pivot.shape[1]>1 and all(icc_pivot.eq(icc_pivot.iloc[:, 0], axis=0).all(1)):
        reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='NA'
    elif icc_pivot.shape[0]>1 and all(icc_pivot.eq(icc_pivot.iloc[0, :], axis=1).all(1)):
        reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='NA'
    else:
        if icc_pivot.shape[0]>1 and icc_pivot.shape[1]>1:
            # Call a chip time series reproducibility index dataframe
            rep_index=Reproducibility_Index(icc_pivot)
            if pd.isnull(rep_index.iloc[0][0]) != True:
                if rep_index.iloc[0][0] <= 15 and rep_index.iloc[0][0] >0:
                    if rep_index.iloc[0][0] <= 5:
                        reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Excellent (CV)'
                    elif rep_index.iloc[0][1] >= 0.8:
                        reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Excellent (ICC)'
                    else:
                        reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Acceptable (CV)'
                else:
                    if rep_index.iloc[0][1] >= 0.8:
                        reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Excellent (ICC)'
                    elif rep_index.iloc[0][1] >= 0.2:
                        reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Acceptable (ICC)'
                    else:
                        reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Poor (ICC)'
            else:
                reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='NA'
        elif icc_pivot.shape[0]<2 and icc_pivot.shape[1]>1:
             # Call a single time reproducibility index dataframe
            rep_index=Single_Time_Reproducibility_Index(icc_pivot)
            if rep_index.iloc[0][0] <= 5 and rep_index.iloc[0][0] > 0:
                reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Excellent (CV)'
            elif rep_index.iloc[0][0] <= 15 and rep_index.iloc[0][0] > 5:
                reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Acceptable (CV)'
            elif rep_index.iloc[0][0] > 15:
                reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='Poor (CV)'
            elif rep_index.iloc[0][0] < 0:
                reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='NA'
            else:
                reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='NA'
        else:
            reproducibility_results_table.iloc[0, reproducibility_results_table.columns.get_loc('Reproducibility Status')] ='NA'

    return reproducibility_results_table.loc[reproducibility_results_table.index[0], 'Reproducibility Status']


# Power Analysis
def pa_effect_size(x, y, type='d'):
    md = np.abs(np.mean(x) - np.mean(y))
    nx = len(x)
    ny = len(y)

    if type == 'gs':
        m = nx + ny - 2
        cm = gamma(m / 2) / (np.sqrt(m / 2) * gamma((m - 1) / 2))
        spsq = ((nx - 1) * np.var(x, ddof=1) +
                (ny - 1) * np.var(y, ddof=1)) / m
        theta = cm * md / np.sqrt(spsq)
    elif type == 'g':
        spsq = ((nx - 1) * np.var(x, ddof=1) + (ny - 1) *
                np.var(y, ddof=1)) / (nx + ny - 2)
        theta = md / np.sqrt(spsq)
    elif type == 'd':
        spsq = ((nx - 1) * np.var(x, ddof=1) + (ny - 1) *
                np.var(y, ddof=1)) / (nx + ny)
        theta = md / np.sqrt(spsq)
    else:
        theta = md / np.std(x, ddof=1)
    return theta


def pa_predicted_sample_size(power, es_value, sig_level=0.05):
    if power > 0 and power < 1:
        pdata = robjects.FloatVector([power, es_value, sig_level])

        rstring = """
        function(pdata){
        library(pwr)
        pp <- try(pwr.t.test(n = , d =pdata[2], sig.level =pdata[3], power =pdata[1] ,
                type = "two.sample",alternative = "two.sided"),silent = TRUE)
              if (!inherits(pp,"try-error")){
                sample_size<-pp$n}
              else
                sample_size<-0
        sample_size
        }
        """
        rfunc = robjects.r(rstring)
        r_result = rfunc(pdata)
        pr = tuple(r_result)
        sample_size = pr[0]
        if sample_size != 0:
            sample_size = sample_size
        else:
            sample_size = np.NAN
    else:
        sample_size = np.NAN
    return sample_size


def pa_predicted_power(sample_size, es_value, sig_level=0.05):
    if sig_level > 0 and sig_level < 1:
        pdata = robjects.FloatVector([sample_size, es_value, sig_level])

        rstring = """
        function(pdata){
        library(pwr)
        pp <- try(pwr.t.test(n = pdata[1], d =pdata[2], sig.level =pdata[3], power = ,
                type = "two.sample",alternative = "two.sided"),silent = TRUE)
              if (!inherits(pp,"try-error")){
                power_value<-pp$power}
              else
                power_value<-0
        power_value
        }
        """
        rfunc = robjects.r(rstring)
        r_result = rfunc(pdata)
        pr = tuple(r_result)
        power_value = pr[0]
        if power_value != 0:
            power_value = power_value
        else:
            power_value = np.NAN
    else:
        power_value = np.NAN
    return power_value


def pa_predicted_significance_level(sample_size, es_value, power=0.8):
    if power > 0 and power < 1:
        pdata = robjects.FloatVector([sample_size, es_value, power])

        rstring = """
        function(pdata){
        library(pwr)
        pp <- try(pwr.t.test(n = pdata[1], d =pdata[2], sig.level = NULL, power = pdata[3],
                type = "two.sample",alternative = "two.sided"),silent = TRUE)
              if (!inherits(pp,"try-error")){
                sig_level<-pp$sig.level}
              else
                sig_level<-0
        sig_level
        }
        """
        rfunc = robjects.r(rstring)
        r_result = rfunc(pdata)
        pr = tuple(r_result)
        sig_level = pr[0]
        if sig_level != 0:
            sig_level = sig_level
        else:
            sig_level = np.NAN
    else:
        sig_level = np.NAN
    return sig_level


def pa_power_one_sample_size(n, es_value, sig_level=0.05):
    if n > 1:
        pdata = robjects.FloatVector([n, es_value, sig_level])

        rstring = """
        function(pdata){
        library('pwr')
        pp <- try(pwr.t.test(n =pdata[1], d =pdata[2], sig.level =pdata[3], power = ,
                type = "two.sample",alternative = "two.sided"),silent = TRUE)
              if (!inherits(pp,"try-error")){
                power_v<-pp$power}
              else
                power_v<-0
        power_v
        }
        """
        rfunc = robjects.r(rstring)
        r_result = rfunc(pdata)
        pr = tuple(r_result)
        power_v = pr[0]
        if power_v != 0:
            power_value = power_v
        else:
            power_value = np.NAN
    else:
        power_value = np.NAN
    return power_value


def pa_power_two_sample_size(n1, n2, es_value, sig_level=0.05):
    if n1 > 1 and n2 > 1 and n1 != n2:
        pdata = robjects.FloatVector([n1, n2, es_value, sig_level])
        rstring = """
        function(pdata){
        library(pwr)
        pp <- try(pwr.t2n.test(n1=pdata[1], n2=pdata[2], d=pdata[3],sig.level = pdata[4],
                               power = , alternative = "two.sided"),silent = TRUE)
              if (!inherits(pp,"try-error")){
                power_v<-pp$power}
              else
                power_v<-0
        power_v
        }
        """
        rfunc = robjects.r(rstring)
        r_result = rfunc(pdata)
        pr = tuple(r_result)
        power_v = pr[0]
        if power_v != 0:
            power_value = power_v
        else:
            power_value = np.NAN
    elif n1 == n2 and n1 > 1:
        power_value = pa_power_one_sample_size(n1, es_value, sig_level)
    else:
        power_value = power_v
    return power_value


def pa_t_test(x, y):
    if (x.std() == 0.0 or y.std() == 0.0):
        p_value = None
    else:
        xp = robjects.FloatVector(x)
        yp = robjects.FloatVector(y)
        rstring = """
        function(x,y){
        t_pvalue<-t.test(x,y)$p.value
        t_pvalue
        }
        """
        rfunc = robjects.r(rstring)
        r_result = rfunc(xp, yp)
        pr = tuple(r_result)
        p_value = pr[0]
    return p_value


def pa_predicted_sample_size_time_series(power_group_data, type='d', power=0.8, sig_level=0.05):
    # Predict the sample size for two treatments' time series given power and significance level

    power_group_data = power_group_data.dropna(subset=['Value'])
    # Confirm whether there are two treatments
    study_group = power_group_data[["Compound Treatment(s)"]]
    study_unique_group = study_group.drop_duplicates()
    if study_unique_group.shape[0] != 2:
        # only two treatments can be selected"
        power_analysis_table = np.NAN
    else:
        # Power analysis results
        power_analysis_table_key = power_group_data[["Group", "Time"]]
        power_analysis_table = power_analysis_table_key.drop_duplicates()
        # create power analysis report table
        header_list = power_analysis_table.columns.values.tolist()
        header_list.append('Power')
        header_list.append('Sample Size')
        header_list.append('Significance Level')

        # Define all columns of power analysis report table
        power_analysis_table = power_analysis_table.reindex(
            columns=header_list)
        # Loop every unique replicate group
        time_count = len(power_analysis_table)
        power_analysis_table.index = pd.RangeIndex(len(power_analysis_table.index))

        if study_unique_group.shape[0] != 2:
            err_msg = "two treatments have to be selected"
            print(err_msg)
        else:
            chip_data = power_group_data.groupby(
                ['Compound Treatment(s)', 'Chip ID', 'Time'], as_index=False)['Value'].mean()
            cltr_data = chip_data[chip_data['Compound Treatment(s)'] == study_unique_group.iloc[0, 0]]
            treat_data = chip_data[chip_data['Compound Treatment(s)'] == study_unique_group.iloc[1, 0]]
            for itime in range(time_count):
                if itime not in power_analysis_table['Time']:
                    continue
                x = cltr_data[cltr_data['Time'] == power_analysis_table['Time'][itime]]['Value']
                y = treat_data[treat_data['Time'] == power_analysis_table['Time'][itime]]['Value']
                # effect size for power analysis calculation
                es_value = pa_effect_size(x, y, type)
                # Predict sample size
                predict_sample_size = pa_predicted_sample_size(
                    power, es_value, sig_level)

                power_analysis_table.iloc[
                    itime,
                    power_analysis_table.columns.get_loc('Power')
                ] = power
                power_analysis_table.iloc[
                    itime,
                    power_analysis_table.columns.get_loc('Sample Size')
                ] = predict_sample_size
                power_analysis_table.iloc[
                    itime,
                    power_analysis_table.columns.get_loc('Significance Level')
                ] = sig_level

    return power_analysis_table


def pa_predicted_significance_level_time_series(power_group_data, type='d', sample_size=3, power=0.8):
    # Predict the sample size for two treatments' time series given power and significance level

    power_group_data = power_group_data.dropna(subset=['Value'])
    # Confirm whether there are two treatments
    study_group = power_group_data[["Compound Treatment(s)"]]
    study_unique_group = study_group.drop_duplicates()
    if study_unique_group.shape[0] != 2:
        # only two treatments can be selected"
        power_analysis_table = np.NAN
    else:
        # Power analysis results
        power_analysis_table_key = power_group_data[["Group", "Time"]]
        power_analysis_table = power_analysis_table_key.drop_duplicates()
        # create power analysis report table
        header_list = power_analysis_table.columns.values.tolist()
        header_list.append('Power')
        header_list.append('Sample Size')
        header_list.append('Significance Level')

        # Define all columns of power analysis report table
        power_analysis_table = power_analysis_table.reindex(
            columns=header_list)
        # Loop every unique replicate group
        time_count = len(power_analysis_table)

        if study_unique_group.shape[0] != 2:
            err_msg = "two treatments have to be selected"
            print(err_msg)
        else:
            chip_data = power_group_data.groupby(
                ['Compound Treatment(s)', 'Chip ID', 'Time'], as_index=False)['Value'].mean()
            cltr_data = chip_data[chip_data['Compound Treatment(s)'] == study_unique_group.iloc[0, 0]]
            treat_data = chip_data[chip_data['Compound Treatment(s)'] == study_unique_group.iloc[1, 0]]
            for itime in range(time_count):
                if itime not in power_analysis_table['Time']:
                    continue
                x = cltr_data[cltr_data['Time'] == power_analysis_table['Time'][itime]]['Value']
                y = treat_data[treat_data['Time'] == power_analysis_table['Time'][itime]]['Value']
                # effect size for power analysis calculation
                es_value = pa_effect_size(x, y, type)
                # Predict sample size
                predicted_sig_level = pa_predicted_significance_level(
                    sample_size, es_value, power)

                power_analysis_table.iloc[
                    itime,
                    power_analysis_table.columns.get_loc('Power')
                ] = power
                power_analysis_table.iloc[
                    itime,
                    power_analysis_table.columns.get_loc('Sample Size')
                ] = sample_size
                power_analysis_table.iloc[
                    itime,
                    power_analysis_table.columns.get_loc('Significance Level')
                ] = predicted_sig_level

    return power_analysis_table


def pa_predicted_power_time_series(power_group_data, type='d', sample_size=3, sig_level=0.05):
    # Predict the sample size for two treatments' time series given power and significance level
    power_group_data = power_group_data.dropna(subset=['Value'])
    # Confirm whether there are two treatments
    study_group = power_group_data[["Compound Treatment(s)"]]
    study_unique_group = study_group.drop_duplicates()
    if study_unique_group.shape[0] != 2:
        # only two treatments can be selected"
        power_analysis_table = np.NAN
    else:
        # Power analysis results
        power_analysis_table_key = power_group_data[["Group", "Time"]]
        power_analysis_table = power_analysis_table_key.drop_duplicates()
        # create power analysis report table
        header_list = power_analysis_table.columns.values.tolist()
        header_list.append('Power')
        header_list.append('Sample Size')
        header_list.append('Significance Level')

        # Define all columns of power analysis report table
        power_analysis_table = power_analysis_table.reindex(
            columns=header_list)
        # Loop every unique replicate group
        time_count = len(power_analysis_table)

        if study_unique_group.shape[0] != 2:
            err_msg = "two treatments have to be selected"
            print(err_msg)
        else:
            chip_data = power_group_data.groupby(
                ['Compound Treatment(s)', 'Chip ID', 'Time'], as_index=False)['Value'].mean()
            cltr_data = chip_data[chip_data['Compound Treatment(s)'] == study_unique_group.iloc[0, 0]]
            treat_data = chip_data[chip_data['Compound Treatment(s)'] == study_unique_group.iloc[1, 0]]
            for itime in range(time_count):
                if itime not in power_analysis_table['Time']:
                    continue
                x = cltr_data[cltr_data['Time'] == power_analysis_table['Time'][itime]]['Value']
                y = treat_data[treat_data['Time'] == power_analysis_table['Time'][itime]]['Value']
                # effect size for power analysis calculation
                es_value = pa_effect_size(x, y, type)
                # Predict sample size
                predicted_power = pa_predicted_power(
                    sample_size, es_value, sig_level)

                power_analysis_table.iloc[
                    itime,
                    power_analysis_table.columns.get_loc('Power')
                ] = predicted_power
                power_analysis_table.iloc[
                    itime,
                    power_analysis_table.columns.get_loc('Sample Size')
                ] = sample_size
                power_analysis_table.iloc[
                    itime,
                    power_analysis_table.columns.get_loc('Significance Level')
                ] = sig_level

    return power_analysis_table


def pa_power_analysis_report(power_group_data, type='d', sig_level=0.05):
    # Calculate and report the power analysis for two treatments' time series from replicates assay measurements
    power_group_data = power_group_data.dropna(subset=['Value'])
    # Confirm whether there are two treatments
    study_group = power_group_data[["Compound Treatment(s)"]]
    study_unique_group = study_group.drop_duplicates()
    if study_unique_group.shape[0] != 2:
        # only two treatments can be selected"
        power_analysis_table = np.NAN
    else:
        # Power analysis results
        power_analysis_table_key = power_group_data[["Group", "Time"]]
        power_analysis_table = power_analysis_table_key.drop_duplicates()
        # create power analysis report table
        header_list = power_analysis_table.columns.values.tolist()
        header_list.append('Power')
        header_list.append('P Value')
        header_list.append('Sample Size')

        # Define all columns of power analysis report table
        power_analysis_table = power_analysis_table.reindex(
            columns=header_list)
        # Loop every unique replicate group
        time_count = len(power_analysis_table)

        #Redefine the result dataframe index
        power_analysis_table.index = pd.RangeIndex(len(power_analysis_table.index))

        if study_unique_group.shape[0] != 2:
            err_msg = "two treatments have to be selected"
            print(err_msg)
        else:
            chip_data = power_group_data.groupby(
                ['Compound Treatment(s)', 'Chip ID', 'Time'], as_index=False)['Value'].mean()
            cltr_data = chip_data[chip_data['Compound Treatment(s)'] == study_unique_group.iloc[0, 0]]
            treat_data = chip_data[chip_data['Compound Treatment(s)'] == study_unique_group.iloc[1, 0]]
            for itime in range(time_count):
                if itime not in power_analysis_table['Time']:
                    continue
                x = cltr_data[cltr_data['Time'] == power_analysis_table['Time'][itime]]['Value']
                n1 = len(x)
                y = treat_data[treat_data['Time'] == power_analysis_table['Time'][itime]]['Value']
                n2 = len(y)
                if n1 > 1 and n2 > 1:
                    # P-value and effect size for power analysis calculation
                    es_value = pa_effect_size(x, y, type)
                    p_value = pa_t_test(x, y)
                    # Power calculation
                if n1 == n2 and n1 > 1:
                    power_value = pa_power_one_sample_size(n1, es_value, sig_level)
                    sample_size = n1
                    p_value = pa_t_test(x, y)
                elif n1 > 1 and n2 > 1 and n1 != n2:
                    power_value = pa_power_two_sample_size(n1, n2, es_value, sig_level)
                    sample_size = min(n1, n2)
                    p_value = pa_t_test(x, y)
                else:
                    power_value = np.NAN
                    p_value = np.NAN
                    sample_size = np.NAN

                power_analysis_table.iloc[
                    itime,
                    power_analysis_table.columns.get_loc('Power')
                ] = power_value
                power_analysis_table.iloc[
                    itime,
                    power_analysis_table.columns.get_loc('P Value')
                ] = p_value

                power_analysis_table.iloc[itime, power_analysis_table.columns.get_loc('Sample Size')] = sample_size

    return power_analysis_table


def pa_power_sample_size_curves_matrix(power_group_data, power_inteval=0.02, type='d', sig_level=0.05):
    # Calculate and report the power analysis for two treatments' time series from replicates assay measurements
    max_power = 1
    power_inteval = 0.01

    power_group_data = power_group_data.dropna(subset=['Value'])
    # Confirm whether there are two treatments
    study_group = power_group_data[["Compound Treatment(s)"]]
    study_unique_group = study_group.drop_duplicates()
    study_unique_group.index = pd.RangeIndex(len(study_unique_group.index))
    if study_unique_group.shape[0] != 2:
        # only two treatments can be selected"
        power_analysis_table = np.NAN
        power_sample_curves_table = np.NAN
    else:
        # Power analysis results
        power_analysis_table_key = power_group_data[["Group", "Time"]]
        power_analysis_table = power_analysis_table_key.drop_duplicates()
        # create power analysis report table
        header_list = power_analysis_table.columns.values.tolist()
        header_list.append('Power')
        header_list.append('Sample Size')
        header_list.append('Note')

        power_analysis_table.index = pd.RangeIndex(len(power_analysis_table.index))

        # Define all columns of power analysis report table
        power_sample_curves_table = pd.DataFrame(columns=header_list)
        # Loop every unique replicate group
        time_count = len(power_analysis_table)

        if study_unique_group.shape[0] != 2:
            err_msg = "two treatments have to be selected"
            print(err_msg)
        else:
            chip_data = power_group_data.groupby(
                ['Compound Treatment(s)', 'Chip ID', 'Time'],
                as_index=False
            )['Value'].mean()
            cltr_data = chip_data[chip_data['Compound Treatment(s)'] == study_unique_group.iloc[0, 0]]
            treat_data = chip_data[chip_data['Compound Treatment(s)'] == study_unique_group.iloc[1, 0]]
            for itime in range(time_count):
                if itime not in power_analysis_table['Time']:
                    continue
                min_power = 0.4
                x = cltr_data[cltr_data['Time'] == power_analysis_table['Time'][itime]]['Value']
                n1 = len(x)
                y = treat_data[treat_data['Time'] == power_analysis_table['Time'][itime]]['Value']
                n2 = len(y)
                if n1 > 1 and n2 > 1:
                    es_value = pa_effect_size(x, y, type)
                else:
                    es_value = np.NAN
                if n1 == n2 and n1 > 1:
                    power_value = pa_power_one_sample_size(n1, es_value, sig_level)
                elif n1 > 1 and n2 > 1 and n1 != n2:
                    power_value = pa_power_two_sample_size(n1, n2, es_value, sig_level)
                else:
                    power_value = np.NAN

                if power_value < 0.4:
                    min_power = power_value

                power_array = np.arange(min_power, max_power, power_inteval)
                n_pc = len(power_array)
                # create dataframe for each time point
                time_power_df = pd.DataFrame(
                    index=range(n_pc), columns=header_list
                )
                if es_value > 0:
                    for k in range(n_pc):
                        input_power = power_array[k]
                        output_sample_size = pa_predicted_sample_size(
                            input_power, es_value, sig_level
                        )
                        time_power_df.iloc[k, 0] = power_analysis_table['Group'][itime]
                        time_power_df.iloc[k, 1] = power_analysis_table['Time'][itime]
                        time_power_df.iloc[k, 2] = input_power
                        time_power_df.iloc[k, 3] = output_sample_size

                # Append the calculate power and sample size matrix at each time
                power_sample_curves_table = power_sample_curves_table.append(
                    time_power_df, ignore_index=True
                )
            power_sample_curves_table = power_sample_curves_table.dropna(subset=['Sample Size'])
            power_sample_curves_table.index = pd.RangeIndex(len(power_sample_curves_table.index))

            # power_sample_curves_table = power_sample_curves_table[pd.notnull(power_sample_curves_table['Sample Size'])]

            power_results_report = pa_power_analysis_report(power_group_data, type, sig_level=sig_level)

            for itime in range(time_count):
                power_curve_set = power_sample_curves_table[power_sample_curves_table['Time'] == power_results_report['Time'][itime]]
                power_curve_row_count = power_curve_set.shape[0]
                if power_results_report['Power'][itime] > 0.99 and power_curve_row_count < 1:
                    cur_group = power_results_report['Group'][itime]
                    cur_time = power_results_report['Time'][itime]
                    cur_power = 1.0
                    cur_sample_size = power_results_report['Sample Size'][itime]
                    cur_note = 'There is no power-sample curve at this time point because the power is close to 1'
                    power_sample_curves_table = power_sample_curves_table.append({
                        'Group':  cur_group,
                        'Time': cur_time,
                        'Power': cur_power,
                        'Sample Size': float(cur_sample_size),
                        'Note': cur_note
                    }, ignore_index=True)

    return power_sample_curves_table


def two_sample_power_analysis(data, type, sig):
    # Initialize a workbook
    # Load the summary data into the dataframe
    power_group_data = pd.DataFrame(
        data,
        columns=['Group',
                 'Time',
                 'Compound Treatment(s)',
                 'Chip ID',
                 'Value']
    )
    # Four different methods for power analysis
    # If type = 'd', it's Cohen's method, this is default method
    # If type 'D', it's Glass’s ∆ method
    # If type 'g' it's Hedges’s g method
    # If type 'gs' it's Hedges’s g* method

    # Call function to get the power values for the two treatments' chip replicates at each time
    power_results_report = pa_power_analysis_report(power_group_data, type=type, sig_level=sig)

    # Call fuction to get the predicted sample size of chip replicates at each time for given power
    power_vs_sample_size_curves_matrix = pa_power_sample_size_curves_matrix(
        power_group_data, power_inteval=0.02, type=type, sig_level=sig)

    # Call Sample size prediction
    sample_size_prediction_matrix = pa_predicted_sample_size_time_series(
        power_group_data, type=type, power=0.9, sig_level=sig)

    # Call power prediction
    power_prediction_matrix = pa_predicted_power_time_series(
        power_group_data, type=type, sample_size=3, sig_level=sig)

    # Call significance level prediction
    sig_level_prediction_matrix = pa_predicted_significance_level_time_series(
        power_group_data, type=type, sample_size=3, power=0.8)

    power_results_report_data = power_results_report.where((pd.notnull(power_results_report)), None).to_dict('split')
    power_vs_sample_size_curves_matrix_data = power_vs_sample_size_curves_matrix.where((pd.notnull(power_vs_sample_size_curves_matrix)), None).to_dict('split')
    sample_size_prediction_matrix_data = sample_size_prediction_matrix.where((pd.notnull(sample_size_prediction_matrix)), None).to_dict('split')
    power_prediction_matrix_data = power_prediction_matrix.where((pd.notnull(power_prediction_matrix)), None).to_dict('split')
    sig_level_prediction_matrix_data = sig_level_prediction_matrix.where((pd.notnull(sig_level_prediction_matrix)), None).to_dict('split')

    return {
        "power_results_report": power_results_report_data['data'],
        "power_vs_sample_size_curves_matrix": power_vs_sample_size_curves_matrix_data['data'],
        "sample_size_prediction_matrix": sample_size_prediction_matrix_data['data'],
        "power_prediction_matrix": power_prediction_matrix_data['data'],
        "sig_level_prediction_matrix": sig_level_prediction_matrix_data['data'],
    }


def create_power_analysis_group_table(group_count, study_data):
    #Calculate and report the reproducibility index and status and other parameters
    #Select unique group rows by study, organ model,sample location, assay and unit
    #Drop null value rows
    study_data = pd.DataFrame(study_data)
    study_data.columns = study_data.iloc[0]
    study_data = study_data.drop(study_data.index[0])

    #Drop null value rows
    study_data['Value'].replace('', np.nan, inplace=True)
    study_data = study_data.dropna(subset=['Value'])
    study_data['Value'] = study_data['Value'].astype(float)
    #Define the Chip ID column to string type
    study_data[['Chip ID']] = study_data['Chip ID'].astype(str)

    #Add Time (day) calculated from three time column
    study_data["Time"] = study_data['Time']/1440.0
    study_data["Time"] = study_data["Time"].apply(lambda x: round(x,2))

    #Define the Chip ID column to string type
    study_data[['Chip ID']] = study_data[['Chip ID']].astype(str)
    chip_data = study_data.groupby(['Group', 'Chip ID', 'Time'], as_index=False)['Value'].mean()

    #create reproducibility report table
    header_list=chip_data.columns.values.tolist()
    header_list.append('# of Chips/Wells')
    header_list.append('# of Time Points')

    power_analysis_group_table = []

    for x in range(group_count+1):
        power_analysis_group_table.append(header_list)

    power_analysis_group_table = pd.DataFrame(columns=header_list)

    # Define all columns of reproducibility report table
    for row in range(group_count):

        rep_matrix = chip_data[chip_data['Group'] == str(row + 1)]
        icc_pivot = pd.pivot_table(rep_matrix, values='Value', index='Time',columns=['Chip ID'], aggfunc=np.mean)

        group_id = str(row+1) #Define group ID

        group_rep_matrix = pd.DataFrame(index=[0], columns=header_list)
        power_analysis_group_table = power_analysis_group_table.append(group_rep_matrix, ignore_index=True)

        power_analysis_group_table.iloc[row, power_analysis_group_table.columns.get_loc('Group')] = group_id
        power_analysis_group_table.iloc[row, power_analysis_group_table.columns.get_loc('# of Chips/Wells')] = icc_pivot.shape[1]
        power_analysis_group_table.iloc[row, power_analysis_group_table.columns.get_loc('# of Time Points')] = icc_pivot.shape[0]

    power_analysis_group_table = power_analysis_group_table.fillna('')

    return power_analysis_group_table.to_dict('split')

# One Sample Power Analysis
def pa1_predict_sample_size_given_delta_and_power(delta, power, sig_level, sd):
    if power > 0 and power < 1:
        pdata=FloatVector([delta, sd, power, sig_level])

        rstring = """
        function(pdata){
        pp <- try(power.t.test(n = NULL, delta =pdata[1], sd=pdata[2],sig.level =pdata[4], power =pdata[3] ,
                type = "one.sample",alternative = "two.sided"),silent = TRUE)
              if (!inherits(pp,"try-error")){
                sample_size<-pp$n}
              else
                sample_size<-0
        sample_size
        }
        """
        rfunc = robjects.r(rstring)
        r_result = rfunc(pdata)
        pr = tuple(r_result)
        sample_size = pr[0]
        if sample_size != 0:
            sample_size = sample_size
        else:
            sample_size = np.NAN
    else:
        sample_size = np.NAN
    return sample_size


def pa1_predicted_power_given_delta_and_sample_size(delta, sample_size, sig_level, sd):
    if sig_level > 0 and sig_level < 1:
        pdata = FloatVector([delta, sd, sample_size, sig_level])

        rstring = """
        function(pdata){
        pp <- try(power.t.test(n = pdata[3], delta =pdata[1], sd=pdata[2],sig.level =pdata[4], power = NULL,
                type = "one.sample",alternative = "two.sided"),silent = TRUE)
              if (!inherits(pp,"try-error")){
                power_value<-pp$power}
              else
                power_value<-0
        power_value
        }
        """
        rfunc = robjects.r(rstring)
        r_result = rfunc(pdata)
        pr = tuple(r_result)
        power_value = pr[0]
        if power_value != 0:
            power_value = power_value
        else:
            power_value = np.NAN
    else:
        power_value = np.NAN
    return power_value


def pa1_predicted_delta_given_sample_size_and_power(sample_size, power, sig_level, sd):
    if power > 0 and power < 1:
        pdata = FloatVector([sd, sample_size, power, sig_level])

        rstring = """
        function(pdata){
        pp <- try(power.t.test(n = pdata[2], delta = NULL, sd=pdata[1],sig.level =pdata[4], power = pdata[3],
                type = "one.sample",alternative = "two.sided"),silent = TRUE)
              if (!inherits(pp,"try-error")){
                delta<-pp$delta}
              else
                delta<-0
        delta
        }
        """
        rfunc = robjects.r(rstring)
        r_result = rfunc(pdata)
        pr = tuple(r_result)
        delta = pr[0]
        if delta != 0:
            delta = delta
        else:
            delta = np.NAN
    else:
        delta = np.NAN
    return delta


def one_sample_power_analysis_calculation(sample_data, sig_level, differences, sample_size, power):

    # Calculate the standard deviation of sample data
    sd=np.std(sample_data, ddof=1)
    if np.isnan(differences) and np.isnan(power) and np.isnan(sample_size):
        power_analysis_result='The differences,sample_size and power are null for all.'
    else:
        ##############Given Diffrences
        if ~np.isnan(differences):
            if np.isnan(power) and np.isnan(sample_size):
                pw_columns = ['Sample Size', 'Power']
                sample_size_array = np.arange(2, 101, 1)  # Sample size is up to 100
                power_analysis_result = pd.DataFrame(index=range(len(sample_size_array)),columns=pw_columns)
                for i_size in range(len(sample_size_array)):
                    sample_size_loc=sample_size_array[i_size]
                    power_value = pa1_predicted_power_given_delta_and_sample_size(differences, sample_size_loc, sig_level, sd)
                    power_analysis_result.iloc[i_size, 0] = sample_size_loc
                    power_analysis_result.iloc[i_size, 1] = power_value

        #################### Given sample size
        if ~np.isnan(sample_size):
            if np.isnan(differences) and np.isnan(power):
                pw_columns = ['Differences', 'Power']
                power_array = np.arange(0, 1, 0.01)  # power is between 0 and 1
                power_analysis_result = pd.DataFrame(index=range(len(power_array)), columns=pw_columns)
                for i_size in range(len(power_array)):
                    power_loc = power_array[i_size]
                    differences_value = pa1_predicted_delta_given_sample_size_and_power(sample_size, power_loc, sig_level, sd)
                    if differences_value > 0:
                        power_analysis_result.iloc[i_size, 0] = differences_value
                    power_analysis_result.iloc[i_size, 1] = power_loc

        #################### Given power
        if ~np.isnan(power):
            if np.isnan(differences) and np.isnan(sample_size):
                pw_columns = ['Sample Size', 'Differences']
                sample_size_array = np.arange(2, 101, 1)  # power is between 0 and 1
                power_analysis_result = pd.DataFrame(index=range(len(sample_size_array)), columns=pw_columns)
                for i_size in range(len(sample_size_array)):
                    sample_size_loc = sample_size_array[i_size]
                    differences_value = pa1_predicted_delta_given_sample_size_and_power(sample_size_loc, power, sig_level, sd)
                    if differences_value > 0:
                        power_analysis_result.iloc[i_size, 1] = differences_value
                    power_analysis_result.iloc[i_size, 0] = sample_size_loc

        ####### Given power and sample size predict differences
        if (np.isnan(differences)) and (~np.isnan(power)) and (~np.isnan(sample_size)):
            power_analysis_result = pa1_predicted_delta_given_sample_size_and_power(sample_size, power, sig_level, sd)

        ####### Given differences and sample size predict power
        if (~np.isnan(differences)) and (np.isnan(power)) and (~np.isnan(sample_size)):
            power_analysis_result=pa1_predicted_power_given_delta_and_sample_size(differences, sample_size, sig_level, sd)

        ######## Given differences and power predict sample size
        if (~np.isnan(differences)) and (~np.isnan(power)) and (np.isnan(sample_size)):
            power_analysis_result = round(pa1_predict_sample_size_given_delta_and_power(differences, power, sig_level, sd))

    return power_analysis_result


def one_sample_power_analysis(one_sample_data, sig_level, one_sample_compound, one_sample_tp):
    # Load the summary data into the dataframe
    power_group_data = pd.DataFrame(
        one_sample_data,
        columns=['Group',
                 'Time',
                 'Compound Treatment(s)',
                 'Chip ID',
                 'Value']
    )

    power_group_data = power_group_data.dropna(subset=['Value'])
    # number of unique compounds
    compound_group = power_group_data[["Compound Treatment(s)"]]
    compound_unique_group = compound_group.drop_duplicates()
    # select compound
    compound_index = 2

    # query the target data for selected compound
    # compound_data = power_group_data[power_group_data['Compound Treatment(s)'] == compound_unique_group.iloc[compound_index, 0]]
    compound_data = power_group_data[power_group_data['Compound Treatment(s)'] == one_sample_compound]

    # Get unique time points for selected compound data
    compound_time = compound_data[["Time"]]
    time_unique_group = compound_time.drop_duplicates()

    # Select time point
    # Row of the user's selected time point - PASSED after selection in the the power curves table
    time = int(one_sample_tp*1440)

    # Query sample data series for selected compound and time point
    sample_data = compound_data[compound_data['Time'] == time]['Value']
    # sample_data = compound_data[compound_data['Time'] == time_unique_group.iloc[time_index, 0]]['Value']
    sample_mean = np.mean(sample_data)

    # Sample population size4_Or_More
    number_sample_population = len(sample_data)
    # The power analysis will be exceuted only when the sample population has more than one sample
    # Based the GUI's setting, return the power analysis results by calculated data or 2D curve
    # At defined significance level, given Differences, predict sample size vs power curve

    if number_sample_population < 2:
        print('Less than 2 samples')
    else:
        ########################One Sample Power Analysis Parameter Setting   ###############################
        opt_percent_change = 'No'  # set input option for differences

        percent_change = 20  # percentage change from the sample population mean
        if opt_percent_change == 'Yes':
            differences = sample_mean*percent_change/100
        else:
            differences = 800  # If you want to predict differences, set it to be np.NAN otherwise input the dirrences or percentage change from the mean

        sample_size = np.NAN  # If you want to predict sample size, set it to be np.NAN otherwise input your sample size
        power = 0.7          # If you want to predict power, set it to be np.NAN otherwise input the power value between 0 and 1

        # Power analysis results will be returned by user's input
        power_analysis_result = one_sample_power_analysis_calculation(sample_data, sig_level, differences, sample_size, power)
