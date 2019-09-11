# coding=utf-8

from django.db import models
from microdevices.models import (
    Microdevice,
    OrganModel,
    OrganModelProtocol,
    MicrophysiologyCenter,
)
from mps.base.models import (
    LockableModel,
    FlaggableModel,
    FlaggableRestrictedModel
)
from django.contrib.auth.models import Group, User

from django.utils.safestring import mark_safe

import urllib.request, urllib.parse, urllib.error
import collections

import django.forms as forms


# These are here to avoid potentially messy imports, may change later
def attr_getter(item, attributes):
    """attribute getter for individual items"""
    for a in attributes:
        try:
            item = getattr(item, a)
        except AttributeError:
            return None

    return item


def tuple_attrgetter(*items):
    """Custom attrgetter that ALWAYS returns a tuple"""
    # NOTE WILL NEED TO CHANGE IF MOVED TO PYTHON 3
    if any(not (isinstance(item, str) or isinstance(item, str)) for item in items):
        raise TypeError('attribute name must be a string')

    def g(obj):
        return tuple(resolve_attr(obj, attr) for attr in items)

    return g


def resolve_attr(obj, attr):
    """Helper function for tuple_attrgetter"""
    for name in attr.split("."):
        obj = getattr(obj, name)
    return obj


# TODO MAKE MODEL AND FIELD NAMES MORE CONSISTENT/COHERENT

# TODO DEPRECATED, REMOVE SOON
PHYSICAL_UNIT_TYPES = (
    ('V', 'Volume'),
    ('C', 'Concentration'),
    ('M', 'Mass'),
    ('T', 'Time'),
    ('F', 'Frequency'),
    ('RA', 'Rate'),
    ('RE', 'Relative'),
    ('O', 'Other'),
)

types = (
    ('TOX', 'Toxicity'), ('DM', 'Disease'), ('EFF', 'Efficacy'), ('CC', 'Cell Characterization')
)

# This shouldn't be repeated like so
# Converts: days -> minutes, hours -> minutes, minutes->minutes
TIME_CONVERSIONS = [
    ('day', 1440),
    ('hour', 60),
    ('minute', 1)
]

TIME_CONVERSIONS = collections.OrderedDict(TIME_CONVERSIONS)

# SUBJECT TO CHANGE
DEFAULT_SETUP_CRITERIA = (
    # 'matrix.study_id',
    # 'device_id',
    'organ_model_id',
    # 'organ_model_protocol_id',
    # 'variance_from_organ_model_protocol'
)

DEFAULT_SETTING_CRITERIA = (
    'setting_id',
    'unit_id',
    'value',
    'addition_time',
    'duration',
    'addition_location_id'
)

DEFAULT_COMPOUND_CRITERIA = (
    # 'compound_instance_id',
    'compound_instance.compound_id',
    'concentration',
    'concentration_unit_id',
    'addition_time',
    'duration',
    'addition_location_id'
)

DEFAULT_CELL_CRITERIA = (
    # Alternative
    'cell_sample_id',
    # 'cell_sample.cell_type_id',
    # 'cell_sample.cell_subtype_id',
    'biosensor_id',
    'density',
    'density_unit_id',
    'passage',
    'addition_location_id'
)

# TODO EMPLOY THIS FUNCTION ELSEWHERE
def get_split_times(time_in_minutes):
    """Takes time_in_minutes and returns a dic with the time split into day, hour, minute"""
    times = {
        'day': 0,
        'hour': 0,
        'minute': 0
    }
    time_in_minutes_remaining = time_in_minutes
    for time_unit, conversion in list(TIME_CONVERSIONS.items()):
        initial_time_for_current_field = int(time_in_minutes_remaining / conversion)
        if initial_time_for_current_field:
            times[time_unit] = initial_time_for_current_field
            time_in_minutes_remaining -= initial_time_for_current_field * conversion
    # Add fractions of minutes if necessary
    if time_in_minutes_remaining:
        times['minute'] += time_in_minutes_remaining

    return times


# May be moved
def get_center_id(group_id):
    """Get a center ID from a group ID"""
    data = {}

    try:
        center_data = MicrophysiologyCenter.objects.filter(groups__id=group_id)[0]

        data.update({
            'center_id': center_data.center_id,
            'center_name': center_data.name,
        })

    except IndexError:
        data.update({
            'center_id': '',
            'center_name': '',
        })

    return data


class UnitType(LockableModel):
    """Unit types for physical units"""

    unit_type = models.CharField(max_length=100)
    description = models.CharField(max_length=256,
                                   blank=True, default='')

    def __str__(self):
        return '{}'.format(self.unit_type)


# TODO THIS NEEDS TO BE REVISED (IDEALLY REPLACED WITH PHYSICALUNIT BELOW)
class PhysicalUnits(LockableModel):
    """Measures of concentration and so on"""

    # USE NAME IN LIEU OF UNIT (unit.unit is confusing and dumb)
    # name = models.CharField(max_length=255)
    unit = models.CharField(max_length=255)
    description = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    unit_type = models.ForeignKey(UnitType, on_delete=models.CASCADE)

    # Base Unit for conversions and scale factor
    base_unit = models.ForeignKey(
        'assays.PhysicalUnits',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    # Scale factor gives the conversion to get to the base unit, can also act to sort
    scale_factor = models.FloatField(
        blank=True,
        null=True
    )

    availability = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text=('Type a series of strings for indicating '
                   'where this unit should be listed:'
                   '\ntest = test results\nreadouts = readouts\ncells = cell samples')
    )

    # verbose_name_plural is used to avoid a double 's' on the model name
    class Meta(object):
        verbose_name_plural = 'Physical Units'
        ordering = ['unit_type', 'unit']

    def __str__(self):
        return '{}'.format(self.unit)


# DEPRECATED: SLATED FOR DELETION
class AssayModelType(LockableModel):
    """Defines the type of an ASSAY (biochemical, mass spec, and so on)"""

    class Meta(object):
        ordering = ('assay_type_name',)

    assay_type_name = models.CharField(max_length=200, unique=True)
    assay_type_description = models.TextField(blank=True, default='')

    def __str__(self):
        return self.assay_type_name


# DEPRECATED: SLATED FOR DELETION
class AssayModel(LockableModel):
    """Defines an ASSAY such as albumin, BUN, and so on"""

    class Meta(object):
        ordering = ('assay_name',)

    assay_name = models.CharField(max_length=200, unique=True)

    # Remember, adding a unique field to existing entries needs to be null during migration
    assay_short_name = models.CharField(max_length=10, default='', unique=True)

    assay_type = models.ForeignKey(AssayModelType, on_delete=models.CASCADE)
    version_number = models.CharField(max_length=200, verbose_name='Version',
                                      blank=True, default='')
    assay_description = models.TextField(verbose_name='Description', blank=True,
                                         default='')
    assay_protocol_file = models.FileField(upload_to='assays',
                                           verbose_name='Protocol File',
                                           null=True, blank=True)
    test_type = models.CharField(max_length=13,
                                 choices=types,
                                 verbose_name='Test Type')

    def __str__(self):
        return '{0} ({1})'.format(self.assay_name, self.assay_short_name)


# DEPRECATED: SLATED FOR DELETION
# Assay layout is now a flaggable model
class AssayLayout(FlaggableRestrictedModel):
    """Defines the layout of a PLATE (parent of all associated wells)"""

    class Meta(object):
        verbose_name = 'Assay Layout'
        ordering = ('layout_name',)

    layout_name = models.CharField(max_length=200, unique=True)
    device = models.ForeignKey(Microdevice, on_delete=models.CASCADE)

    # Specifies whether this is a standard (oft used layout)
    standard = models.BooleanField(default=False)

    # base_layout = models.ForeignKey(AssayBaseLayout, on_delete=models.CASCADE)

    def __str__(self):
        return self.layout_name

    def get_post_submission_url(self):
        return '/assays/assaylayout/'

    def get_absolute_url(self):
        return '/assays/assaylayout/{}/'.format(self.id)

    def get_delete_url(self):
        return '/assays/assaylayout/{}/delete/'.format(self.id)


# DEPRECATED: SLATED FOR DELETION
class AssayWellType(LockableModel):
    """PLATE well type

    Includes the color well types appear as in the interface
    """

    class Meta(object):
        ordering = ('well_type',)

    well_type = models.CharField(max_length=200, unique=True)
    well_description = models.TextField(blank=True, default='')
    background_color = models.CharField(max_length=20,
                                        help_text='Provide color code or name. '
                                                  'You can pick one from: '
                                                  'http://www.w3schools.com'
                                                  '/html/html_colornames.asp')

    def __str__(self):
        return self.well_type

    @mark_safe
    def colored_display(self):
        """Colored display for admin list view."""

        return ('<span style="background-color: {}; padding: 2px">{}</span>'
                .format(self.background_color, self.well_type))

    colored_display.allow_tags = True


# DEPRECATED: SLATED FOR DELETION
class AssayWell(models.Model):
    """An individual PLATE well"""

    class Meta(object):
        unique_together = [('assay_layout', 'row', 'column')]

    # base_layout = models.ForeignKey(AssayBaseLayout, on_delete=models.CASCADE)
    assay_layout = models.ForeignKey(AssayLayout, on_delete=models.CASCADE)
    well_type = models.ForeignKey(AssayWellType, on_delete=models.CASCADE)

    row = models.CharField(max_length=25)
    column = models.CharField(max_length=25)


# DEPRECATED: SLATED FOR DELETION
class AssayWellTimepoint(models.Model):
    """Timepoints for PLATE wells"""
    assay_layout = models.ForeignKey(AssayLayout, on_delete=models.CASCADE)
    timepoint = models.FloatField(default=0)
    row = models.CharField(max_length=25)
    column = models.CharField(max_length=25)


# DEPRECATED: SLATED FOR DELETION
class AssayWellLabel(models.Model):
    """Arbitrary string label for PLATE wells"""
    assay_layout = models.ForeignKey(AssayLayout, on_delete=models.CASCADE)
    label = models.CharField(max_length=150)
    row = models.CharField(max_length=25)
    column = models.CharField(max_length=25)


# DEPRECATED: SLATED FOR DELETION
class AssayCompoundInstance(models.Model):
    """An instance of a compound used in an assay; used as an inline"""

    class Meta(object):
        unique_together = [
            (
                'chip_setup',
                'compound_instance',
                'concentration',
                'concentration_unit',
                'addition_time',
                'duration'
            )
        ]

        ordering = (
            'addition_time',
            'compound_instance_id',
            'concentration_unit_id',
            'concentration',
            'duration',
        )

    # Stop-gap, subject to change
    chip_setup = models.ForeignKey('assays.AssayChipSetup', null=True, blank=True, on_delete=models.CASCADE)

    # COMPOUND INSTANCE IS REQUIRED, however null=True was done to avoid a submission issue
    compound_instance = models.ForeignKey('compounds.CompoundInstance', null=True, blank=True, on_delete=models.CASCADE)
    concentration = models.FloatField()
    concentration_unit = models.ForeignKey(
        'assays.PhysicalUnits',
        verbose_name='Concentration Unit',
        on_delete=models.CASCADE
    )

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    addition_time = models.FloatField(blank=True)

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    duration = models.FloatField(blank=True)

    def get_addition_time_string(self):
        split_times = get_split_times(self.addition_time)
        return 'D{0:02} H{1:02} M{2:02}'.format(
            split_times.get('day'),
            split_times.get('hour'),
            split_times.get('minute'),
        )

    def get_duration_string(self):
        split_times = get_split_times(self.duration)
        return 'D{0:02} H{1:02} M{2:02}'.format(
            split_times.get('day'),
            split_times.get('hour'),
            split_times.get('minute'),
        )

    def __str__(self):
        return '{0} ({1} {2})\n-Added on: {3}; Duration of: {4}'.format(
            self.compound_instance.compound.name,
            self.concentration,
            self.concentration_unit.unit,
            self.get_addition_time_string(),
            self.get_duration_string()
        )


# DEPRECATED: SLATED FOR DELETION
class AssayWellCompound(models.Model):
    """Compound for PLATE wells"""
    assay_layout = models.ForeignKey(AssayLayout, on_delete=models.CASCADE)
    # TO BE DEPRECATED: USE AssayCompoundInstance instead
    compound = models.ForeignKey('compounds.Compound', null=True, blank=True, on_delete=models.CASCADE)
    # Null=True temporarily
    assay_compound_instance = models.ForeignKey('assays.AssayCompoundInstance', null=True, blank=True, on_delete=models.CASCADE)
    # TO BE DEPRECATED: USE AssayCompoundInstance instead
    concentration = models.FloatField(default=0, null=True, blank=True)
    # TO BE DEPRECATED: USE AssayCompoundInstance instead
    concentration_unit = models.ForeignKey(PhysicalUnits, null=True, blank=True, on_delete=models.CASCADE)
    row = models.CharField(max_length=25)
    column = models.CharField(max_length=25)


# DEPRECATED: SLATED FOR DELETION
class AssayQualityIndicator(LockableModel):
    """AssayQualityIndicators show whether a data point needs to be excluded"""
    # Name of the indicator
    name = models.CharField(max_length=255, unique=True)

    # Short version of the indicator for input in the quality field
    # Theoretically, the code should be a single character, but I will err on the side of caution
    code = models.CharField(max_length=10, unique=True)

    # Description of the indicator (for tooltips)
    description = models.CharField(max_length=2000)

    # Is this necessary? Do we assume that all need to be excluded?
    # exclude = models.BooleanField(default=True)


# TO BE DEPRECATED To be merged into single "AssayCells" model
class AssayPlateCells(models.Model):
    """Individual cell parameters for PLATE setup used in inline"""

    assay_plate = models.ForeignKey('AssayPlateSetup', on_delete=models.CASCADE)
    cell_sample = models.ForeignKey('cellsamples.CellSample', on_delete=models.CASCADE)
    cell_biosensor = models.ForeignKey('cellsamples.Biosensor', on_delete=models.CASCADE)
    cellsample_density = models.FloatField(verbose_name='density', default=0)

    cellsample_density_unit = models.CharField(verbose_name='Unit',
                                               max_length=8,
                                               default='WE',
                                               choices=(('WE', 'cells/well'),
                                                        ('ML', 'cells/mL'),
                                                        ('MM', 'cells/mm^2')))
    cell_passage = models.CharField(max_length=16, verbose_name='Passage#',
                                    blank=True, default='')


# TO BE DEPRECATED To be merged into single "AssaySetup" model
class AssayPlateSetup(FlaggableRestrictedModel):
    """Setup for MICROPLATES"""

    class Meta(object):
        verbose_name = 'Plate Setup'

    # Might as well be consistent
    assay_run_id = models.ForeignKey('assays.AssayRun', verbose_name='Study', on_delete=models.CASCADE)

    # The assay layout is approximately equivalent to a chip's Organ Model
    assay_layout = models.ForeignKey('assays.AssayLayout', verbose_name='Assay Layout', on_delete=models.CASCADE)

    setup_date = models.DateField(help_text='YYYY-MM-DD')

    # Plate identifier
    assay_plate_id = models.CharField(max_length=512, verbose_name='Plate ID/ Barcode')

    scientist = models.CharField(max_length=100, blank=True, default='')
    notebook = models.CharField(max_length=256, blank=True, default='')
    notebook_page = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=2048, blank=True, default='')

    def __str__(self):
        return '{}'.format(self.assay_plate_id)

    def get_absolute_url(self):
        return '/assays/assayplatesetup/{}/'.format(self.id)

    def get_post_submission_url(self):
        return '/assays/{}/'.format(self.assay_run_id_id)

    def get_clone_url(self):
        return '/assays/{0}/assayplatesetup/add?clone={1}'.format(self.assay_run_id_id, self.id)

    def get_delete_url(self):
        return '/assays/assayplatesetup/{}/delete/'.format(self.id)


# DEPRECATED: SLATED FOR DELETION
class AssayReader(LockableModel):
    """Chip and Plate readers"""

    class Meta(object):
        ordering = ('reader_name',)

    reader_name = models.CharField(max_length=128)
    reader_type = models.CharField(max_length=128)

    def __str__(self):
        return '{0} - {1}'.format(self.reader_name, self.reader_type)


# TO BE DEPRECATED To be merged into single "AssayInstance" model
class AssayPlateReadoutAssay(models.Model):
    """Inline for PLATE readout assays"""

    class Meta(object):
        # Remove restriction that readout can only have one copy of an assay
        # unique_together = [('readout_id', 'assay_id')]
        # Assay-Feature pairs must be unique
        unique_together = [('readout_id', 'assay_id', 'feature')]

    readout_id = models.ForeignKey('assays.AssayPlateReadout', verbose_name='Readout', on_delete=models.CASCADE)
    assay_id = models.ForeignKey('assays.AssayModel', verbose_name='Assay', null=True, on_delete=models.CASCADE)
    reader_id = models.ForeignKey('assays.AssayReader', verbose_name='Reader', on_delete=models.CASCADE)
    # Object excluded for now (presumably will be just well)
    # object_type = models.CharField(max_length=6,
    #                         choices=object_types,
    #                         verbose_name='Object of Interest',
    #                         default='F')
    readout_unit = models.ForeignKey('assays.PhysicalUnits', on_delete=models.CASCADE)

    # For the moment, features will be just strings (this avoids potentially complex management)
    feature = models.CharField(max_length=150)

    def __str__(self):
        return '{0}-{1}'.format(self.assay_id.assay_short_name, self.feature)


# TO BE DEPRECATED To be merged into single "AssayData" model
class AssayReadout(models.Model):
    """An individual value for a PLATE readout"""

    assay_device_readout = models.ForeignKey('assays.AssayPlateReadout', on_delete=models.CASCADE)
    # A plate can have multiple assays, this differentiates between those assays
    assay = models.ForeignKey('assays.AssayPlateReadoutAssay', on_delete=models.CASCADE)
    row = models.CharField(max_length=25)
    column = models.CharField(max_length=25)
    value = models.FloatField()
    elapsed_time = models.FloatField(default=0)

    # Quality, if it is not the empty string, indicates that a readout is INVALID
    quality = models.CharField(default='', max_length=10)

    # IT WAS DECIDED THAT A FK WOULD NOT BE USED
    # Use quality with each flag separated with a '-' (SUBJECT TO CHANGE)
    # Quality indicator from QualityIndicator table (so that additional can be added)
    # quality_indicator = models.ForeignKey(AssayQualityIndicator, null=True, blank=True, on_delete=models.CASCADE)

    # This value contains notes for the data point
    notes = models.CharField(max_length=255, default='')

    # Indicates what replicate this is (0 is for original)
    update_number = models.IntegerField(default=0)


# class ReadoutUnit(LockableModel):
#    """
#    Units specific to readouts (AU, RFU, so on)
#    """
#
#    class Meta(object):
#        ordering = ('readout_unit',)
#
#    readout_unit = models.CharField(max_length=512,unique=True)
#    description = models.CharField(max_length=512,blank=True,null=True)
#
#    def __str__(self):
#        return self.readout_unit


# Likely to become deprecated
# Get readout file location
def plate_readout_file_location(instance, filename):
    return '/'.join(['csv', str(instance.setup.assay_run_id_id), 'plate', filename])


# TO BE DEPRECATED To be merged into single "AssayDataset" model
class AssayPlateReadout(FlaggableRestrictedModel):
    """Readout data collected from MICROPLATES"""

    class Meta(object):
        verbose_name = 'Plate Readout'

    # the unique readout identifier
    # can be a barcode or a hand written identifier
    # REMOVING READOUT ID FOR NOW
    # assay_device_id = models.CharField(max_length=512,
    #                                    verbose_name='Readout ID/ Barcode')

    # Cell samples are to be handled in AssayPlateSetup from now on

    setup = models.ForeignKey(AssayPlateSetup, on_delete=models.CASCADE)

    timeunit = models.ForeignKey(PhysicalUnits, default=23, on_delete=models.CASCADE)

    treatment_time_length = models.FloatField(verbose_name='Treatment Duration',
                                              blank=True, null=True)

    # Assay start time is now in AssayPlateSetup

    readout_start_time = models.DateField(verbose_name='Readout Date', help_text="YYYY-MM-DD")

    notebook = models.CharField(max_length=256, blank=True, default='')
    notebook_page = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=2048, blank=True, default='')
    scientist = models.CharField(max_length=100, blank=True, default='')
    file = models.FileField(upload_to=plate_readout_file_location, verbose_name='Data File',
                            blank=True, null=True)

    def __str__(self):
        return '{0}'.format(self.setup)

    def get_absolute_url(self):
        return '/assays/assayplatereadout/{}/'.format(self.id)

    def get_post_submission_url(self):
        return '/assays/{}/'.format(self.setup.assay_run_id_id)

    def get_clone_url(self):
        return '/assays/{0}/assayplatereadout/add?clone={1}'.format(self.setup.assay_run_id_id, self.id)

    def get_delete_url(self):
        return '/assays/assayplatereadout/{}/delete/'.format(self.id)


SEVERITY_SCORE = (
    ('-1', 'UNKNOWN'), ('0', 'NEGATIVE'), ('1', '+'), ('2', '+ +'),
    ('3', '+ + +'), ('4', '+ + + +'), ('5', '+ + + + +')
)

POSNEG = (
    ('0', 'Negative'), ('1', 'Positive'), ('x', 'Failed')
)


# DEPRECATED: SLATED FOR DELETION
class AssayResultFunction(LockableModel):
    """Function for analysis of CHIP RESULTS"""
    class Meta(object):
        verbose_name = 'Function'
        ordering = ('function_name',)

    function_name = models.CharField(max_length=100, unique=True)
    function_results = models.CharField(max_length=100, blank=True, default='')
    description = models.CharField(max_length=200, blank=True, default='')

    def __str__(self):
        return self.function_name


# DEPRECATED: SLATED FOR DELETION
class AssayResultType(LockableModel):
    """Result types for CHIP RESULTS"""

    class Meta(object):
        verbose_name = 'Result type'
        ordering = ('assay_result_type',)

    assay_result_type = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True, default='')

    def __str__(self):
        return self.assay_result_type


# TO BE DEPRECATED To be merged into single "AssayResult" model
class AssayPlateResult(models.Model):
    """Individual result parameters for PLATE RESULTS used in inline"""

    assay_name = models.ForeignKey(
        'assays.AssayPlateReadoutAssay',
        verbose_name='Assay',
        on_delete=models.CASCADE
    )

    assay_result = models.ForeignKey('assays.AssayPlateTestResult', on_delete=models.CASCADE)

    result_function = models.ForeignKey(
        AssayResultFunction,
        blank=True,
        null=True,
        verbose_name='Function',
        on_delete=models.CASCADE
    )

    result = models.CharField(default='1',
                              max_length=8,
                              choices=POSNEG,
                              verbose_name='Result')

    severity = models.CharField(default='-1',
                                max_length=5,
                                choices=SEVERITY_SCORE,
                                verbose_name='Severity',
                                blank=True)

    result_type = models.ForeignKey(
        AssayResultType,
        blank=True,
        null=True,
        verbose_name='Measure',
        on_delete=models.CASCADE
    )

    value = models.FloatField(blank=True, null=True)

    test_unit = models.ForeignKey(
        PhysicalUnits,
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )


# TO BE DEPRECATED To be merged into single "AssayResultset" model
class AssayPlateTestResult(FlaggableRestrictedModel):
    """Test Results from MICROPLATES"""

    class Meta(object):
        verbose_name = 'Plate Result'

    readout = models.ForeignKey(
        'assays.AssayPlateReadout',
        verbose_name='Plate ID/ Barcode',
        on_delete=models.CASCADE
    )
    summary = models.TextField(default='', blank=True)

    def __str__(self):
        return 'Results for: {}'.format(self.readout)

    def get_absolute_url(self):
        return '/assays/assayplatetestresult/{}/'.format(self.id)

    def get_post_submission_url(self):
        return '/assays/{}/'.format(self.readout.setup.assay_run_id_id)

    def get_delete_url(self):
        return '/assays/assayplatetestresult/{}/delete/'.format(self.id)


class AssayStudyConfiguration(LockableModel):
    """Defines how chips are connected together (for integrated studies)"""

    class Meta(object):
        verbose_name = 'Study Configuration'

    # Length subject to change
    name = models.CharField(max_length=255, unique=True)

    # DEPRECATED when would we ever want an individual configuration?
    # study_format = models.CharField(
    #     max_length=11,
    #     choices=(('individual', 'Individual'), ('integrated', 'Integrated'),),
    #     default='integrated'
    # )

    media_composition = models.CharField(max_length=4000, blank=True, default='')
    hardware_description = models.CharField(max_length=4000, blank=True, default='')
    # Subject to removal
    # image = models.ImageField(upload_to="configuration",null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return '/assays/studyconfiguration/{}/'.format(self.id)

    def get_post_submission_url(self):
        return '/assays/studyconfiguration/'


class AssayStudyModel(models.Model):
    """Individual connections for integrated models"""

    study_configuration = models.ForeignKey(AssayStudyConfiguration, on_delete=models.CASCADE)
    label = models.CharField(max_length=2)
    organ = models.ForeignKey(OrganModel, on_delete=models.CASCADE)
    sequence_number = models.IntegerField()
    output = models.CharField(max_length=20, blank=True, default='')
    # Subject to change
    integration_mode = models.CharField(max_length=13, default='1', choices=(('0', 'Functional'), ('1', 'Physical')))


# Get readout file location
def bulk_readout_file_location(instance, filename):
    return '/'.join(['csv', str(instance.id), 'bulk', filename])


# DEPRECATED: SLATED FOR DELETION
# To be renamed "AssayStudy" for clarity
# Handling of study type will be changed
# Nature of assay_run_id subject to revision
class AssayRun(FlaggableRestrictedModel):
    """The encapsulation of all data concerning some plate/chip project"""

    class Meta(object):
        verbose_name = 'Old Study'
        verbose_name_plural = 'Old Studies'
        ordering = ('assay_run_id',)

    # Removed center_id for now: this field is basically for admins anyway
    # May add center_id back later, but group mostly serves the same purpose
    # center_id = models.ForeignKey('microdevices.MicrophysiologyCenter', verbose_name='Center(s)', on_delete=models.CASCADE)
    # Study type now multiple boolean fields; May need to add more in the future
    toxicity = models.BooleanField(default=False)
    efficacy = models.BooleanField(default=False)
    disease = models.BooleanField(default=False)
    # TODO PLEASE REFACTOR
    # NOW REFERRED TO AS "Chip Characterization"
    cell_characterization = models.BooleanField(default=False)
    # Subject to change
    study_configuration = models.ForeignKey(AssayStudyConfiguration, blank=True, null=True, on_delete=models.CASCADE)
    name = models.TextField(default='Study-01', verbose_name='Study Name',
                            help_text='Name-###')
    start_date = models.DateField(help_text='YYYY-MM-DD')
    # TODO REMOVE AS SOON AS POSSIBLE
    assay_run_id = models.TextField(unique=True, verbose_name='Study ID',
                                    help_text="Standard format 'CenterID-YYYY-MM-DD-Name-###'")
    description = models.TextField(blank=True, default='')

    protocol = models.FileField(
        upload_to='study_protocol',
        verbose_name='Protocol File',
        blank=True,
        null=True,
        help_text='Protocol File for Study'
    )

    bulk_file = models.FileField(
        upload_to=bulk_readout_file_location,
        verbose_name='Data File',
        blank=True, null=True
    )

    # Deprecated
    # File (an Excel file, I assume) of supporting data
    # supporting_data = models.FileField(
    #     upload_to='supporting_data',
    #     blank=True,
    #     null=True,
    #     help_text='Supporting Data for Study'
    # )

    # Image for the study (some illustrative image)
    image = models.ImageField(upload_to='studies', null=True, blank=True)

    use_in_calculations = models.BooleanField(
        default=False,
        help_text='Set this to True if this data should be included in Compound Reports and other data aggregations.'
    )

    access_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name='access_groups',
        help_text='Level 2 Access Groups Assignation'
    )

    # Special addition, would put in base model, but don't want excess...
    signed_off_notes = models.CharField(max_length=255, blank=True, default='')

    # THESE ARE NOW EXPLICIT FIELDS IN STUDY
    # group = models.ForeignKey(Group, help_text='Bind to a group', on_delete=models.CASCADE)

    # restricted = models.BooleanField(default=True, help_text='Check box to restrict to selected group')

    def study_types(self):
        current_types = ''
        if self.toxicity:
            current_types += 'TOX '
        if self.efficacy:
            current_types += 'EFF '
        if self.disease:
            current_types += 'DM '
        if self.cell_characterization:
            current_types += 'CC '
        return '{0}'.format(current_types)

    def __str__(self):
        return str(self.assay_run_id)

    def get_absolute_url(self):
        return '/assays/{}/'.format(self.id)

    def get_summary_url(self):
        return '/assays/{}/summary/'.format(self.id)

    def get_delete_url(self):
        return '/assays/{}/delete/'.format(self.id)

    def get_images_url(self):
        return '{}images/'.format(self.get_absolute_url())

    # Dubiously useful, but maybe
    def get_list_url(self):
        return '/assays/'


# Get readout file location
def study_supporting_data_location(instance, filename):
    return '/'.join(['supporting_data', str(instance.study_id), filename])


# DEPRECATED: SLATED FOR DELETION
class StudySupportingData(models.Model):
    """A file (with description) that gives extra data for a Study"""
    study = models.ForeignKey(AssayRun, on_delete=models.CASCADE)

    description = models.CharField(
        max_length=1000,
        help_text='Describes the contents of the supporting data file'
    )

    # Not named file in order to avoid shadowing
    supporting_data = models.FileField(
        upload_to=study_supporting_data_location,
        help_text='Supporting Data for Study'
    )


# TO BE DEPRECATED To be merged into single "AssayData" model
class AssayChipRawData(models.Model):
    """Individual lines of readout data"""

    # class Meta(object):
    #     unique_together = [('assay_chip_id', 'assay_id', 'field_id', 'time')]

    # TO BE REPLACED (readouts likely will not exist in future versions)
    assay_chip_id = models.ForeignKey('assays.AssayChipReadout', on_delete=models.CASCADE)
    # DEPRECATED: ACRA WILL BE REPLACED BY ASSAY INSTANCE
    assay_id = models.ForeignKey('assays.AssayChipReadoutAssay', null=True, blank=True, on_delete=models.CASCADE)

    # Cross reference for users if study ids diverge
    cross_reference = models.CharField(max_length=255, default='')

    # DEPRECATED: REPLACED BY SAMPLE LOCATION
    field_id = models.CharField(max_length=255, default='0', null=True, blank=True)

    value = models.FloatField(null=True)

    # TO BE RENAMED SIMPLY "time" IN FUTURE MODELS
    # PLEASE NOTE THAT THIS IS NOW ALWAYS MINUTES <-IMPORTANT
    elapsed_time = models.FloatField(default=0, null=True, blank=True)

    # This value will act as quality control, if it evaluates True then the value is considered invalid
    quality = models.CharField(max_length=20, default='')

    # Caution flags for the user
    # Errs on the side of larger flags, currently
    caution_flag = models.CharField(max_length=255, default='')

    # IT WAS DECIDED THAT A FK WOULD NOT BE USED
    # Use quality with each flag separated with a '-' (SUBJECT TO CHANGE)
    # Quality indicator from QualityIndicator table (so that additional can be added)
    # quality_indicator = models.ForeignKey(AssayQualityIndicator, null=True, blank=True, on_delete=models.CASCADE)

    # This value contains notes for the data point
    notes = models.CharField(max_length=255, default='')

    # Indicates what replicate this is (0 is for original)
    update_number = models.IntegerField(default=0)

    # New fields
    # TEMPORARILY NOT REQUIRED
    sample_location = models.ForeignKey('assays.AssaySampleLocation', null=True, blank=True, on_delete=models.CASCADE)
    # TEMPORARILY NOT REQUIRED
    assay_instance = models.ForeignKey('assays.AssayInstance', null=True, blank=True, on_delete=models.CASCADE)

    # DEFAULTS SUBJECT TO CHANGE
    assay_plate_id = models.CharField(max_length=255, default='N/A')
    assay_well_id = models.CharField(max_length=255, default='N/A')

    # Indicates "technical replicates"
    # SUBJECT TO CHANGE
    replicate = models.CharField(max_length=255, default='')

    # Replaces elapsed_time
    time = models.FloatField(default=0)

    # Affiliated upload
    data_upload = models.ForeignKey('assays.AssayDataUpload', null=True, blank=True, on_delete=models.CASCADE)

# Expedient solution to absurd problem with choice field (which I dislike)
cell_choice_dict = {
    'WE': 'cells / well',
    'CP': 'cells / chip',
    'ML': 'cells / mL',
    'MM': 'cells / mm^2'
}


# DEPRECATED: SLATED FOR DELETION
class AssayChipCells(models.Model):
    """Individual cell parameters for CHIP setup used in inline"""

    class Meta(object):
        ordering = (
            'cell_sample_id',
            'cell_biosensor_id',
            'cellsample_density',
            'cellsample_density_unit',
            'cell_passage'
        )

    assay_chip = models.ForeignKey('AssayChipSetup', on_delete=models.CASCADE)
    cell_sample = models.ForeignKey('cellsamples.CellSample', on_delete=models.CASCADE)
    cell_biosensor = models.ForeignKey('cellsamples.Biosensor', on_delete=models.CASCADE)
    cellsample_density = models.FloatField(verbose_name='density', default=0)

    cellsample_density_unit = models.CharField(verbose_name='Unit',
                                               max_length=8,
                                               default="CP",
                                               choices=(('WE', 'cells / well'),
                                                        ('CP', 'cells / chip'),
                                                        ('ML', 'cells / mL'),
                                                        ('MM', 'cells / mm^2')))
    cell_passage = models.CharField(max_length=16, verbose_name='Passage#',
                                    blank=True, default='')

    def __str__(self):
        return '{0}\n~{1:.0e} {2}'.format(
            self.cell_sample,
            self.cellsample_density,
            cell_choice_dict.get(self.cellsample_density_unit, 'Unknown Unit')
        )


# TO BE DEPRECATED To be merged into single "AssaySetup" model
class AssayChipSetup(FlaggableRestrictedModel):
    """The configuration of a Chip for implementing an assay"""
    class Meta(object):
        verbose_name = 'Chip Setup'
        ordering = ('-assay_chip_id', 'assay_run_id',)

    assay_run_id = models.ForeignKey(AssayRun, verbose_name='Study', on_delete=models.CASCADE)
    setup_date = models.DateField(help_text='YYYY-MM-DD')

    device = models.ForeignKey(Microdevice, verbose_name='Device', on_delete=models.CASCADE)

    # RENAMED (previously field was erroneously device)
    organ_model = models.ForeignKey(OrganModel, verbose_name='MPS Model Name', null=True, blank=True, on_delete=models.CASCADE)

    organ_model_protocol = models.ForeignKey(
        OrganModelProtocol,
        verbose_name='MPS Model Protocol',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    variance = models.CharField(max_length=3000, verbose_name='Variance from Protocol', default='', blank=True)

    # the unique chip identifier
    # can be a barcode or a hand written identifier
    assay_chip_id = models.CharField(max_length=512, verbose_name='Chip ID/ Barcode')

    # Control => control, Compound => compound; Abbreviate? Capitalize?
    chip_test_type = models.CharField(max_length=8, choices=(
        ("control", "Control"), ("compound", "Compound")), default="control"
    )

    compound = models.ForeignKey('compounds.Compound', null=True, blank=True, on_delete=models.CASCADE)
    concentration = models.FloatField(default=0, verbose_name='Conc.',
                                      null=True, blank=True)
    unit = models.ForeignKey(
        'assays.PhysicalUnits',
        default=4,
        verbose_name='conc. Unit',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    scientist = models.CharField(max_length=100, blank=True, default='')
    notebook = models.CharField(max_length=256, blank=True, default='')
    notebook_page = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=2048, blank=True, default='')

    def __str__(self):
        return '{}'.format(self.assay_chip_id)
        # if self.compound:
        #     return u'Chip-{}:{}({}{})'.format(
        #         self.assay_chip_id,
        #         self.compound,
        #         self.concentration,
        #         self.unit
        #     )
        # else:
        #     return u'Chip-{}:Control'.format(self.assay_chip_id)

    def devolved_cells(self):
        """Makes a tuple of cells (for comparison)"""
        cell_tuple = []
        for cell in self.assaychipcells_set.all():
            cell_tuple.append((
                cell.cell_sample_id,
                cell.cell_biosensor_id,
                cell.cellsample_density,
                # cell.cellsample_density_unit_id,
                cell.cellsample_density_unit,
                cell.cell_passage
            ))

        return tuple(sorted(cell_tuple))

    def stringify_cells(self):
        """Stringified cells for a setup"""
        cells = []
        for cell in self.assaychipcells_set.all():
            cells.append(str(cell))

        if not cells:
            cells = ['-No Cell Samples-']

        return '\n'.join(cells)

    def devolved_compounds(self):
        """Makes a tuple of compounds (for comparison)"""
        compound_tuple = []
        for compound in self.assaycompoundinstance_set.all():
            compound_tuple.append((
                compound.compound_instance_id,
                compound.concentration,
                compound.concentration_unit_id,
                compound.addition_time,
                compound.duration,
            ))

        return tuple(sorted(compound_tuple))

    def stringify_compounds(self):
        """Stringified cells for a setup"""
        compounds = []
        for compound in self.assaycompoundinstance_set.all():
            compounds.append(str(compound))

        if not compounds:
            compounds = ['-No Compounds-']

        return '\n'.join(compounds)

    def quick_dic(self):
        dic = {
            # 'device': self.device.name,
            'organ_model': self.get_hyperlinked_model_or_device(),
            'compounds': self.stringify_compounds(),
            'cells': self.stringify_cells(),
            'setups_with_same_group': []
        }
        return dic

    def get_hyperlinked_name(self):
        return '<a href="{0}">{1}</a>'.format(self.get_absolute_url(), self.assay_chip_id)

    def get_hyperlinked_model_or_device(self):
        if not self.organ_model:
            return '<a href="{0}">{1} (No MPS Model)</a>'.format(self.device.get_absolute_url(), self.device.name)
        else:
            return '<a href="{0}">{1}</a>'.format(self.organ_model.get_absolute_url(), self.organ_model.name)

    def get_absolute_url(self):
        return '/assays/assaychipsetup/{}/'.format(self.id)

    def get_post_submission_url(self):
        return '/assays/{}/'.format(self.assay_run_id_id)

    def get_clone_url(self):
        return '/assays/{0}/assaychipsetup/add?clone={1}'.format(self.assay_run_id_id, self.id)

    def get_delete_url(self):
        return '/assays/assaychipsetup/{}/delete/'.format(self.id)

object_types = (
    ('F', 'Field'), ('C', 'Colony'), ('M', 'Media'), ('X', 'Other')
)


# TO BE DEPRECATED To be merged into single "AssayInstance" model
# FURTHERMORE assays will probably be captured at a study, rather than "readout" level
class AssayChipReadoutAssay(models.Model):
    """Inline for CHIP readout assays"""

    class Meta(object):
        # Changed uniqueness check to include unit (extend to include object?)
        unique_together = [('readout_id', 'assay_id', 'readout_unit')]

    readout_id = models.ForeignKey('assays.AssayChipReadout', verbose_name='Readout', on_delete=models.CASCADE)
    # DEPRECATED
    assay_id = models.ForeignKey('assays.AssayModel', verbose_name='Assay', null=True, blank=True, on_delete=models.CASCADE)
    # DEPRECATED
    reader_id = models.ForeignKey('assays.AssayReader', verbose_name='Reader', null=True, blank=True, on_delete=models.CASCADE)
    # DEPRECATED
    object_type = models.CharField(
        max_length=6,
        choices=object_types,
        verbose_name='Object of Interest',
        default='F',
        blank=True
    )
    # Will be renamed unit in future table
    readout_unit = models.ForeignKey(PhysicalUnits, on_delete=models.CASCADE)

    # New fields that will be in AssaySpecificAssay (or AssayInstance, not sure about name)
    # target = models.ForeignKey(AssayTarget, on_delete=models.CASCADE)
    # method = models.ForeignKey(AssayMethod, on_delete=models.CASCADE)

    def __str__(self):
        return '{}'.format(self.assay_id)


# Likely to become deprecated
# Get readout file location
def chip_readout_file_location(instance, filename):
    return '/'.join(['csv', str(instance.chip_setup.assay_run_id_id), 'chip', filename])


# TO BE DEPRECATED To be merged into single "AssayDataset" model
class AssayChipReadout(FlaggableRestrictedModel):
    """Readout data for CHIPS"""

    class Meta(object):
        verbose_name = 'Chip Readout'
        ordering = ('chip_setup',)

    chip_setup = models.ForeignKey(AssayChipSetup, on_delete=models.CASCADE)

    timeunit = models.ForeignKey(PhysicalUnits, default=23, on_delete=models.CASCADE)
    treatment_time_length = models.FloatField(verbose_name='Assay Treatment Duration',
                                              blank=True, null=True)

    readout_start_time = models.DateField(verbose_name='Readout Start Date', help_text="YYYY-MM-DD")

    notebook = models.CharField(max_length=256, blank=True, default='')
    notebook_page = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=2048, blank=True, default='')
    scientist = models.CharField(max_length=100, blank=True, default='')
    file = models.FileField(upload_to=chip_readout_file_location, verbose_name='Data File',
                            blank=True, null=True, help_text='Green = Data from database;'
                                                             ' Red = Line that will not be read'
                                                             '; Gray = Reading with null value'
                                                             ' ***Uploading overwrites old data***')

    # Get a list of every assay for list view
    def assays(self):
        list_of_assays = []
        assays = AssayChipReadoutAssay.objects.filter(
            readout_id=self.id
        ).prefetch_related(
            'assay_id',
            'reader_id',
            'readout_unit'
        )
        for assay in assays:
            list_of_assays.append(str(assay))
        # Convert to unicode for consistency
        return '{0}'.format(', '.join(list_of_assays))

    def __str__(self):
        return '{0}'.format(self.chip_setup)

    def get_absolute_url(self):
        return '/assays/assaychipreadout/{}/'.format(self.id)

    def get_post_submission_url(self):
        return '/assays/{}/'.format(self.chip_setup.assay_run_id.id)

    def get_clone_url(self):
        return '/assays/{0}/assaychipreadout/add?clone={1}'.format(self.chip_setup.assay_run_id_id, self.id)

    def get_delete_url(self):
        return '/assays/assaychipreadout/{}/delete/'.format(self.id)


# TO BE DEPRECATED To be merged into single "AssayResultSet" model
class AssayChipTestResult(FlaggableRestrictedModel):
    """Results calculated from Raw Chip Data"""

    class Meta(object):
        verbose_name = 'Chip Result'

    chip_readout = models.ForeignKey('assays.AssayChipReadout', verbose_name='Chip Readout', on_delete=models.CASCADE)
    summary = models.TextField(default='', blank=True)

    def __str__(self):
        return 'Results for: {}'.format(self.chip_readout)

    def assay(self):
        if self.id and not len(AssayChipResult.objects.filter(assay_result_id=self.id).order_by('id')) == 0:
            return AssayChipResult.objects.filter(assay_result_id=self.id).order_by('id')[0].assay_name
        return ''

    def result(self):
        if self.id and not len(AssayChipResult.objects.filter(assay_result_id=self.id).order_by('id')) == 0:
            abbreviation = AssayChipResult.objects.filter(assay_result_id=self.id).order_by('id')[0].result
            if abbreviation == '1':
                return 'Positive'
            else:
                return 'Negative'
        return ''

    def result_function(self):
        if self.id and not len(AssayChipResult.objects.filter(assay_result_id=self.id).order_by('id')) == 0:
            return AssayChipResult.objects.filter(assay_result_id=self.id).order_by('id')[0].result_function
        return ''

    def result_type(self):
        if self.id and not len(AssayChipResult.objects.filter(assay_result_id=self.id).order_by('id')) == 0:
            return AssayChipResult.objects.filter(assay_result_id=self.id).order_by('id')[0].result_type
        return ''

    def severity(self):
        severity_score_dict = dict(SEVERITY_SCORE)
        if self.id and not len(AssayChipResult.objects.filter(assay_result_id=self.id).order_by('id')) == 0:
            return severity_score_dict.get(AssayChipResult.objects.filter(
                assay_result_id=self.id
            ).order_by('id')[0].severity, 'None')
        return ''

    def get_absolute_url(self):
        return '/assays/assaychiptestresult/{}/'.format(self.id)

    def get_post_submission_url(self):
        return '/assays/{}/'.format(self.chip_readout.chip_setup.assay_run_id_id)

    def get_delete_url(self):
        return '/assays/assaychiptestresult/{}/delete/'.format(self.id)


# TO BE DEPRECATED To be merged into single "AssayResult" model
class AssayChipResult(models.Model):
    """Individual result parameters for CHIP RESULTS used in inline"""

    assay_name = models.ForeignKey(
        'assays.AssayInstance',
        verbose_name='Assay',
        on_delete=models.CASCADE
    )

    assay_result = models.ForeignKey(AssayChipTestResult, on_delete=models.CASCADE)

    result_function = models.ForeignKey(
        AssayResultFunction,
        blank=True,
        null=True,
        verbose_name='Function',
        on_delete=models.CASCADE
    )

    result = models.CharField(default='1',
                              max_length=8,
                              choices=POSNEG,
                              verbose_name='Pos/Neg?')

    severity = models.CharField(default='-1',
                                max_length=5,
                                choices=SEVERITY_SCORE,
                                verbose_name='Severity',
                                blank=True)

    result_type = models.ForeignKey(
        AssayResultType,
        blank=True,
        null=True,
        verbose_name='Measure',
        on_delete=models.CASCADE
    )

    value = models.FloatField(blank=True, null=True)

    test_unit = models.ForeignKey(
        PhysicalUnits,
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )


class AssayDataUpload(FlaggableRestrictedModel):
    """Shows the history of data uploads for a readout; functions as inline"""

    # TO BE DEPRECATED
    # date_created, created_by, and other fields are used but come from FlaggableRestrictedModel
    file_location = models.URLField(null=True, blank=True)

    # Store the file itself, rather than the location
    # NOTE THAT THIS IS NOT SIMPLY "file" DUE TO COLLISIONS WITH RESERVED WORDS
    # TODO SET LOCATION
    # TODO REQUIRE EVENTUALLY
    # data_file = models.FileField(null=True, blank=True)

    # Note that there are both chip and plate readouts listed as one file may supply both
    # TO BE DEPRECATED
    chip_readout = models.ManyToManyField(AssayChipReadout)
    # TO BE DEPRECATED
    plate_readout = models.ManyToManyField(AssayPlateReadout)

    # Supplying study may seem redundant, however:
    # This ensures that uploads for readouts that have been (for whatever reason) deleted will no longer be hidden
    study = models.ForeignKey(AssayRun, on_delete=models.CASCADE)

    def __str__(self):
        return urllib.parse.unquote(self.file_location.split('/')[-1])


class AssayDataFileUpload(FlaggableModel):
    """Shows the history of data uploads for a study; functions as inline"""

    # TO BE DEPRECATED
    # date_created, created_by, and other fields are used but come from FlaggableModel
    file_location = models.URLField(null=True, blank=True)

    # Store the file itself, rather than the location
    # NOTE THAT THIS IS NOT SIMPLY "file" DUE TO COLLISIONS WITH RESERVED WORDS
    # TODO SET LOCATION
    # TODO REQUIRE EVENTUALLY
    # data_file = models.FileField(null=True, blank=True)

    # NOT VERY USEFUL
    # items = models.ManyToManyField(AssayChipReadout)

    study = models.ForeignKey('assays.AssayStudy', on_delete=models.CASCADE)

    def __str__(self):
        return urllib.parse.unquote(self.file_location.split('/')[-1])


# NEW MODELS, TO BE INTEGRATED FURTHER LATER
class AssayTarget(LockableModel):
    """Describes what was sought by a given Assay"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    short_name = models.CharField(max_length=20, unique=True)

    # Tentative
    alt_name = models.CharField(max_length=1000, blank=True, default='')

    # List of all methods
    methods = models.ManyToManyField('assays.AssayMethod')

    def __str__(self):
        return '{0}'.format(self.name)


class AssaySubtarget(models.Model):
    """Describes a target for situations where manually curated lists are prohibitively expensive (TempoSeq, etc.)"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    def __str__(self):
        return self.name


class AssayMeasurementType(LockableModel):
    """Describes what was measures with a given method"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    def __str__(self):
        return self.name


class AssaySupplier(LockableModel):
    """Assay Supplier so we can track where kits came from"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    def __str__(self):
        return self.name


class AssayMethod(LockableModel):
    """Describes how an assay was performed"""
    # We may want to modify this so that it is unique on name in combination with measurement type?
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)
    measurement_type = models.ForeignKey(AssayMeasurementType, on_delete=models.CASCADE)

    # May or may not be required in the future
    supplier = models.ForeignKey(AssaySupplier, blank=True, null=True, on_delete=models.CASCADE)

    # TODO STORAGE LOCATION
    # TODO TEMPORARILY NOT REQUIRED
    protocol_file = models.FileField(upload_to='assays', null=True, blank=True)

    # Tentative
    alt_name = models.CharField(max_length=1000, blank=True, default='')

    def __str__(self):
        return self.name


class AssaySampleLocation(LockableModel):
    """Describes a location for where a sample was acquired"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    def __str__(self):
        return self.name


# TODO WE WILL NEED TO ADD INSTRUMENT/READER IT SEEMS
class AssayInstance(models.Model):
    """Specific assays used in the 'inlines'"""
    study = models.ForeignKey(AssayRun, null=True, blank=True, on_delete=models.CASCADE)
    # study_new = models.ForeignKey('assays.AssayStudy', null=True, blank=True, on_delete=models.CASCADE)
    target = models.ForeignKey(AssayTarget, on_delete=models.CASCADE)
    method = models.ForeignKey(AssayMethod, on_delete=models.CASCADE)
    # Name of model "PhysicalUnits" should be renamed, methinks
    unit = models.ForeignKey(PhysicalUnits, on_delete=models.CASCADE)

    def __str__(self):
        return '{0}|{1}|{2}'.format(self.target, self.method, self.unit)


# Preliminary schema
# Please note that I opted to use CharFields in lieu of TextFields (we can limit characters that way)
# class AssayStudyType(LockableModel):
#     """Used as in a many-to-many field in Assay Study to indicate the purpose(s) of the Study"""
#     name = models.CharField(max_length=255, unique=True)
#     # Abbreviation for the study type
#     code = models.CharField(max_length=20, unique=True)
#     # Description as per usual
#     description = models.CharField(max_length=2000, default='')
#
#     def __str__(self):
#         return self.name


# TODO SUBJECT TO CHANGE
# Get upload file location
def upload_file_location(instance, filename):
    return '/'.join(['data_points', str(instance.id), filename])


class AssayStudy(FlaggableModel):
    """The encapsulation of all data concerning a project"""
    class Meta(object):
        verbose_name = 'Study'
        verbose_name_plural = 'Studies'
        # TEMPORARY, SUBJECT TO REVISION
        # This would be useless if I decided to use a M2M instead
        unique_together = ((
            'name',
            'efficacy',
            'disease',
            'cell_characterization',
            'start_date',
            'group'
        ))

    toxicity = models.BooleanField(default=False)
    efficacy = models.BooleanField(default=False)
    disease = models.BooleanField(default=False)
    # TODO PLEASE REFACTOR
    # NOW REFERRED TO AS "Chip Characterization"
    cell_characterization = models.BooleanField(default=False)

    # Subject to change
    # NOTE THAT THE TABLE IS NOW NAMED AssayStudyConfiguration to adhere to standards
    study_configuration = models.ForeignKey(AssayStudyConfiguration, blank=True, null=True, on_delete=models.CASCADE)
    # Whether or not the name should be unique is an interesting question
    # We could have a constraint on the combination of name and start_date
    # But to constrain by name, start_date, and study_types, we will need to do that in the forms.py file
    # Otherwise we can change study_types such that it is not longer a ManyToMany
    name = models.CharField(max_length=1000, verbose_name='Study Name')

    # Uncertain whether or not I will do this
    # This will be used to avoid having to call related fields to get the full name all the time
    # full_name = models.CharField(max_length=1200, verbose_name='Full Study Name')

    start_date = models.DateField(help_text='YYYY-MM-DD')
    description = models.CharField(max_length=8000, blank=True, default='')

    protocol = models.FileField(
        upload_to='study_protocol',
        verbose_name='Protocol File',
        blank=True,
        null=True,
        help_text='Protocol File for Study'
    )

    # TODO USE THIS INSTEAD OR GET RID OF IT
    # study_types = models.ManyToManyField(AssayStudyType)

    # Image for the study (some illustrative image)
    image = models.ImageField(upload_to='studies', null=True, blank=True)

    use_in_calculations = models.BooleanField(default=False)

    # Access groups
    access_groups = models.ManyToManyField(Group, blank=True, related_name='study_access_groups')

    # Collaborator groups
    collaborator_groups = models.ManyToManyField(Group, blank=True, related_name='study_collaborator_groups')

    # THESE ARE NOW EXPLICIT FIELDS IN STUDY
    group = models.ForeignKey(Group, verbose_name='Data Group', help_text='Select the Data Group. The study will be bound to this group', on_delete=models.CASCADE)

    restricted = models.BooleanField(
        default=True,
        help_text='Check box to restrict to the Access Groups selected below.'
                  ' Access is granted to access group(s) after Data Group admin and all designated'
                  ' Stakeholder Group admin(s) sign off on the study'
    )

    # Special addition, would put in base model, but don't want excess...
    signed_off_notes = models.CharField(max_length=255, blank=True, default='')

    # Delimited string of reproducibility (Excellent|Acceptable|Poor)
    repro_nums = models.CharField(max_length=40, blank=True, default='', help_text='Excellent|Acceptable|Poor')

    # TODO SOMEWHAT CONTRIVED
    bulk_file = models.FileField(
        upload_to=upload_file_location,
        verbose_name='Data File',
        blank=True, null=True
    )


    # TODO MAKE REQUIRED
    # TODO DEAL WITH CONFLICTS
    organ_model = models.ForeignKey(OrganModel, blank=True, null=True, on_delete=models.CASCADE)
    organ_model_protocol = models.ForeignKey(OrganModelProtocol, blank=True, null=True, on_delete=models.CASCADE)

    # Whether or not to show on the front end
    archived = models.BooleanField(
        default=False,
        help_text='Archived Studies do not appear on the front end'
    )


    # TODO
    # def get_study_types_string(self):
    #     study_types = '-'.join(
    #         sorted([study_type.code for study_type in self.study_types.all()])
    #     )
    #     return study_types

    # TODO INEFFICIENT BUT SHOULD WORK
    def stakeholder_approval_needed(self):
        return AssayStudyStakeholder.objects.filter(
            study_id=self.id,
            sign_off_required=True,
            signed_off_by=None
        ).count()

    # TODO VERY INEFFICIENT, BUT SHOULD WORK
    def get_indexing_information(self):
        """Exceedingly inefficient way to add some data for indexing studies"""
        matrix_items = AssayMatrixItem.objects.filter(matrix__study_id=self.id).prefetch_related(
            'matrix',
            'assaysetupsetting_set__setting',
            'assaysetupsetting_set__addition_location',
            'assaysetupsetting_set__unit',
            'assaysetupcell_set__cell_sample__cell_subtype',
            'assaysetupcell_set__cell_sample__cell_type__organ',
            'assaysetupcell_set__cell_sample__supplier',
            'assaysetupcell_set__density_unit',
            'assaysetupcell_set__addition_location',
            'assaysetupcompound_set__compound_instance__compound',
            'assaysetupcompound_set__concentration_unit',
            'assaysetupcompound_set__addition_location',
        )

        current_study = {}

        for matrix_item in matrix_items:
            organ_model_name = ''

            if matrix_item.organ_model:
                organ_model_name = matrix_item.organ_model.name

            current_study.setdefault('items', {}).update({
                matrix_item.name: True
            })
            current_study.setdefault('organ_models', {}).update({
                organ_model_name: True
            })
            current_study.setdefault('devices', {}).update({
                matrix_item.device.name: True
            })

            for compound in matrix_item.assaysetupcompound_set.all():
                current_study.setdefault('compounds', {}).update({
                    str(compound): True
                })

            for cell in matrix_item.assaysetupcell_set.all():
                current_study.setdefault('cells', {}).update({
                    str(cell): True
                })

            for setting in matrix_item.assaysetupsetting_set.all():
                current_study.setdefault('settings', {}).update({
                    str(setting): True
                })

        return '\n'.join([' '.join(x) for x in list(current_study.values())])

    def get_study_types_string(self):
        current_types = []
        if self.toxicity:
            current_types.append('TOX')
        if self.efficacy:
            current_types.append('EFF')
        if self.disease:
            current_types.append('DM')
        if self.cell_characterization:
            current_types.append('CC')
        return '-'.join(current_types)

    # TODO
    def __str__(self):
        center_id = self.group.microphysiologycenter_set.first().center_id
        # study_types = self.get_study_types_string()
        return '-'.join([
            center_id,
            self.get_study_types_string(),
            str(self.start_date),
            self.name
        ])

    def get_absolute_url(self):
        return '/assays/assaystudy/{}/'.format(self.id)

    def get_post_submission_url(self):
        return self.get_absolute_url()

    def get_delete_url(self):
        return '{}delete/'.format(self.get_absolute_url())

    def get_summary_url(self):
        return '{}summary/'.format(self.get_absolute_url())

    def get_reproducibility_url(self):
        return '{}reproducibility/'.format(self.get_absolute_url())

    def get_images_url(self):
        return '{}images/'.format(self.get_absolute_url())

    def get_power_analysis_url(self):
        return '{}power_analysis/'.format(self.get_absolute_url())

    # Dubiously useful, but maybe
    def get_list_url(self):
        return '/assays/assaystudy/'


# ON THE FRONT END, MATRICES ARE LIKELY TO BE CALLED STUDY SETUPS
class AssayMatrix(FlaggableModel):
    """Used to organize data in the interface. An Matrix is a set of setups"""
    class Meta(object):
        verbose_name_plural = 'Assay Matrices'
        unique_together = [('study', 'name')]

    # TODO Name made unique within Study? What will the constraint be?
    name = models.CharField(max_length=255)

    # TODO THINK OF HOW TO HANDLE PLATES HERE
    # TODO REALLY NEEDS TO BE REVISED
    representation = models.CharField(
        max_length=255,
        choices=(
            ('chips', 'Multiple Chips'),
            # Should there be an option for single chips?
            # Probably not!
            # ('chip', 'Chip'),
            ('plate', 'Plate'),
            # What other things might interest us?
            ('', '')
        )
    )

    study = models.ForeignKey(AssayStudy, on_delete=models.CASCADE)

    device = models.ForeignKey(Microdevice, null=True, blank=True, on_delete=models.CASCADE)

    # Decided against the inclusion of organ model here
    # organ_model = models.ForeignKey(OrganModel, null=True, blank=True, on_delete=models.CASCADE)
    #
    # organ_model_protocol = models.ForeignKey(
    #     OrganModelProtocol,
    #     verbose_name='Model Protocol',
    #     null=True,
    #     blank=True
    # )
    #
    # # formerly just 'variance'
    # variance_from_organ_model_protocol = models.CharField(
    #     max_length=3000,
    #     verbose_name='Variance from Protocol',
    #     default='',
    #     blank=True
    # )

    # Number of rows and columns
    # Only required for representations without dimensions already
    number_of_rows = models.IntegerField(null=True, blank=True)
    number_of_columns = models.IntegerField(null=True, blank=True)

    # May be useful
    notes = models.CharField(max_length=2048, blank=True, default='')

    def __str__(self):
        return '{0}'.format(self.name)

    # def get_organ_models(self):
    #     organ_models = []
    #     for matrix_item in self.assaymatrixitem_set.all():
    #         organ_models.append(matrix_item.organ_model)
    #
    #     if not organ_models:
    #         return '-No MPS Models-'
    #     else:
    #         return ','.join(list(set(organ_models)))

    # TODO
    def get_absolute_url(self):
        return '/assays/assaymatrix/{}/'.format(self.id)

    def get_post_submission_url(self):
        return self.study.get_post_submission_url()

    def get_delete_url(self):
        return '{}delete/'.format(self.get_absolute_url())


class AssayFailureReason(FlaggableModel):
    """Describes a type of failure"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

# TODO TODO TODO
# These choices need to change
# Please note contrivance with respect to compound/"Treated"
TEST_TYPE_CHOICES = (
    ('', '--------'), ('control', 'Control'), ('compound', 'Treated')
)

# SUBJECT TO REMOVAL (MAY JUST USE ASSAY SETUP)
class AssayMatrixItem(FlaggableModel):
    class Meta(object):
        verbose_name = 'Matrix Item'
        # TODO Should this be by study or by matrix?
        unique_together = [
            ('study', 'name'),
            ('matrix', 'row_index', 'column_index')
        ]

    # Technically the study here is redundant (contained in matrix)
    study = models.ForeignKey(AssayStudy, on_delete=models.CASCADE)

    # Probably shouldn't use this trick!
    # This is in fact required, just listed as not being so due to quirk in cleaning
    matrix = models.ForeignKey(AssayMatrix, null=True, blank=True, on_delete=models.CASCADE)

    # This is in fact required, just listed as not being so due to quirk in cleaning
    # setup = models.ForeignKey('assays.AssaySetup', null=True, blank=True, on_delete=models.CASCADE)

    name = models.CharField(max_length=512)
    setup_date = models.DateField(help_text='YYYY-MM-DD')

    # Do we still want this? Should it be changed?
    scientist = models.CharField(max_length=100, blank=True, default='')
    notebook = models.CharField(max_length=256, blank=True, default='')
    # Should this be an integer field instead?
    notebook_page = models.CharField(max_length=256, blank=True, default='')
    notes = models.CharField(max_length=2048, blank=True, default='')

    # If setups and items are to be merged, these are necessary
    row_index = models.IntegerField()
    column_index = models.IntegerField()

    # TODO DEPRECATED: PURGE
    # HENCEFORTH ALL ITEMS WILL HAVE AN ORGAN MODEL PROTOCOL
    device = models.ForeignKey(Microdevice, verbose_name='Device', on_delete=models.CASCADE)

    # TODO DEPRECATED: PURGE
    # HENCEFORTH ALL ITEMS WILL HAVE AN ORGAN MODEL PROTOCOL
    organ_model = models.ForeignKey(OrganModel, verbose_name='Model', null=True, blank=True, on_delete=models.CASCADE)

    organ_model_protocol = models.ForeignKey(
        OrganModelProtocol,
        verbose_name='Model Protocol',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    # TODO DEPRECATED: PURGE
    # formerly just 'variance'
    variance_from_organ_model_protocol = models.CharField(
        max_length=3000,
        verbose_name='Variance from Protocol',
        default='',
        blank=True
    )

    # Likely to change in future
    test_type = models.CharField(
        max_length=8,
        choices=TEST_TYPE_CHOICES,
        # default='control'
    )

    # Tentative
    # Do we want a time on top of this?
    # failure_date = models.DateField(help_text='YYYY-MM-DD', null=True, blank=True)
    # Failure time in minutes
    failure_time = models.FloatField(null=True, blank=True)
    # Do we want this is to be table or a static list?
    failure_reason = models.ForeignKey(AssayFailureReason, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.name)

    def devolved_settings(self, criteria=DEFAULT_SETTING_CRITERIA):
        """Makes a tuple of cells (for comparison)"""
        setting_tuple = []
        attribute_getter = tuple_attrgetter(*criteria)
        for setting in self.assaysetupsetting_set.all():
            current_tuple = attribute_getter(setting)

            setting_tuple.append(current_tuple)

        return tuple(sorted(set(setting_tuple)))

    def stringify_settings(self, criteria=None):
        """Stringified cells for a setup"""
        settings = []
        for setting in self.assaysetupsetting_set.all():
            settings.append(setting.flex_string(criteria))

        if not settings:
            settings = ['-No Extra Settings-']

        return '\n'.join(collections.OrderedDict.fromkeys(settings))

    def devolved_cells(self, criteria=DEFAULT_CELL_CRITERIA):
        """Makes a tuple of cells (for comparison)"""
        cell_tuple = []
        attribute_getter = tuple_attrgetter(*criteria)
        for cell in self.assaysetupcell_set.all():
            current_tuple = attribute_getter(cell)

            cell_tuple.append(current_tuple)

        return tuple(sorted(set(cell_tuple)))

    def stringify_cells(self, criteria=None):
        """Stringified cells for a setup"""
        cells = []
        for cell in self.assaysetupcell_set.all():
            cells.append(cell.flex_string(criteria))

        if not cells:
            cells = ['-No Cell Samples-']

        return '\n'.join(collections.OrderedDict.fromkeys(cells))

    def devolved_compounds(self, criteria=DEFAULT_COMPOUND_CRITERIA):
        """Makes a tuple of compounds (for comparison)"""
        compound_tuple = []
        attribute_getter = tuple_attrgetter(*criteria)
        for compound in self.assaysetupcompound_set.all():
            current_tuple = attribute_getter(compound)

            compound_tuple.append(current_tuple)

        return tuple(sorted(set(compound_tuple)))

    def stringify_compounds(self, criteria=None):
        """Stringified cells for a setup"""
        compounds = []
        for compound in self.assaysetupcompound_set.all():
            compounds.append(compound.flex_string(criteria))

        if not compounds:
            compounds = ['-No Compounds-']

        return '\n'.join(collections.OrderedDict.fromkeys(compounds))

    def get_compound_profile(self, matrix_item_compound_post_filters):
        """Compound profile for determining concentration at time point"""
        compound_profile = []

        for compound in self.assaysetupcompound_set.all():
            valid_compound = True

            # Makes sure the compound doesn't violate filters
            # This is because a compound can be excluded even if its parent matrix item isn't!
            for filter, values in list(matrix_item_compound_post_filters.items()):
                if str(attr_getter(compound, filter.split('__'))) not in values:
                    valid_compound = False
                    break

            compound_profile.append({
                'valid_compound': valid_compound,
                'addition_time': compound.addition_time,
                'duration': compound.duration,
                # SCALE INITIALLY
                'concentration': compound.concentration * compound.concentration_unit.scale_factor,
                # JUNK
                # 'scale_factor': compound.concentration_unit.scale_factor,
                'name': compound.compound_instance.compound.name,
                'base_unit': compound.concentration_unit.base_unit.unit,
            })

        return compound_profile

    # SPAGHETTI CODE
    # TERRIBLE, BLOATED
    def quick_dic(
        self,
        compound_profile=False,
        matrix_item_compound_post_filters=None,
        criteria=None
    ):
        if not criteria:
            criteria = {}
        dic = {
            # 'device': self.device.name,
            # OBJECTIVELY BAD
            'Center': self.study.group.microphysiologycenter_set.first().name,
            'MPS User Group': self.study.group.name,
            'Study': self.get_hyperlinked_study(),
            'Matrix': self.get_hyperlinked_matrix(),
            'MPS Model': self.get_hyperlinked_model_or_device(),
            'Compounds': self.stringify_compounds(criteria.get('compound', None)),
            'Cells': self.stringify_cells(criteria.get('cell', None)),
            'Settings': self.stringify_settings(criteria.get('setting', None)),
            'Trimmed Compounds': self.stringify_compounds({
                'compound_instance.compound_id': True,
                'concentration': True
            }),
            'Items with Same Treatment': [],
            'item_ids': []
        }

        if compound_profile:
            dic.update({
                'compound_profile': self.get_compound_profile(matrix_item_compound_post_filters)
            })

        return dic

    # TODO THESE ARE NOT DRY
    def get_hyperlinked_name(self):
        return '<a target="_blank" href="{0}">{1}</a>'.format(self.get_absolute_url(), self.name)

    def get_hyperlinked_model_or_device(self):
        if not self.organ_model:
            return '<a target="_blank" href="{0}">{1} (No MPS Model)</a>'.format(self.device.get_absolute_url(), self.device.name)
        else:
            return '<a target="_blank" href="{0}">{1}</a>'.format(self.organ_model.get_absolute_url(), self.organ_model.name)

    def get_hyperlinked_study(self):
        return '<a target="_blank" href="{0}">{1}</a>'.format(self.study.get_absolute_url(), self.study.name)

    def get_hyperlinked_matrix(self):
        return '<a target="_blank" href="{0}">{1}</a>'.format(self.matrix.get_absolute_url(), self.matrix.name)

    # TODO TODO TODO CHANGE
    def get_absolute_url(self):
        return '/assays/assaymatrixitem/{}/'.format(self.id)

    def get_post_submission_url(self):
        return self.study.get_absolute_url()

    def get_delete_url(self):
        return '{}delete/'.format(self.get_absolute_url())


# Controversy has arisen over whether to put this in an organ model or not
# This name is somewhat deceptive, it describes the quantity of cells, not a cell (rename please)
class AssaySetupCell(models.Model):
    """Individual cell parameters for setup used in inline"""
    class Meta(object):
        unique_together = [
            (
                # 'setup',
                'matrix_item',
                'cell_sample',
                'biosensor',
                # Skip density?
                'density',
                'density_unit',
                'passage',
                'addition_time',
                'addition_location'
                # Will we need addition time and location here?
            )
        ]

        ordering = (
            'addition_time',
            'cell_sample__cell_type__name',
            'cell_sample',
            'addition_location__name',
            'biosensor__name',
            'density',
            'density_unit__name',
            'passage'
        )

    # Now binds directly to items
    matrix_item = models.ForeignKey(AssayMatrixItem, on_delete=models.CASCADE)

    # No longer bound one-to-one
    # setup = models.ForeignKey('AssaySetup', on_delete=models.CASCADE)
    cell_sample = models.ForeignKey('cellsamples.CellSample', on_delete=models.CASCADE)
    biosensor = models.ForeignKey(
        'cellsamples.Biosensor',
        on_delete=models.CASCADE,
        # Default is naive
        default=2
    )
    density = models.FloatField(verbose_name='density', default=0)

    # TODO THIS IS TO BE HAMMERED OUT
    # density_unit = models.CharField(
    #     verbose_name='Unit',
    #     max_length=8,
    #     default='WE',
    #     # TODO ASK ABOUT THESE CHOICES?
    #     choices=(('WE', 'cells / well'),
    #             ('ML', 'cells / mL'),
    #             ('MM', 'cells / mm^2'))
    # )
    density_unit = models.ForeignKey('assays.PhysicalUnits', on_delete=models.CASCADE)
    passage = models.CharField(
        max_length=16,
        verbose_name='Passage#',
        blank=True,
        default=''
    )

    # DO WE WANT ADDITION TIME AND DURATION?
    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_time = models.FloatField(null=True, blank=True)

    # TODO TODO TODO DO WE WANT DURATION????
    # duration = models.FloatField(null=True, blank=True)

    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_location = models.ForeignKey(AssaySampleLocation, blank=True, default=1, on_delete=models.CASCADE)

    # NOT DRY
    def get_addition_time_string(self):
        split_times = get_split_times(self.addition_time)
        return 'D{0:02} H{1:02} M{2:02}'.format(
            split_times.get('day'),
            split_times.get('hour'),
            split_times.get('minute'),
        )

    # def get_duration_string(self):
    #     split_times = get_split_times(self.duration)
    #     return 'D{0:02} H{1:02} M{2:02}'.format(
    #         split_times.get('day'),
    #         split_times.get('hour'),
    #         split_times.get('minute'),
    #     )

    # CRUDE
    def flex_string(self, criteria=None):
        if criteria:
            full_string = []
            if 'cell_sample_id' in criteria:
                full_string.append(str(self.cell_sample))
            if 'cell_sample_id' not in criteria and 'cell_sample.cell_type_id' in criteria:
                full_string.append(str(self.cell_sample.cell_type))
            if 'cell_sample_id' not in criteria and 'cell_sample.cell_subtype_id' in criteria:
                full_string.append(str(self.cell_sample.cell_subtype))
            if 'passage' in criteria:
                full_string.append(self.passage)
            if 'density' in criteria:
                full_string.append('{:g}'.format(self.density))
                full_string.append(self.density_unit.unit)
            if 'addition_time' in criteria:
                full_string.append('Added on: ' + self.get_addition_time_string())
            # if 'duration' in criteria:
            #     full_string.append('Duration of: ' + self.get_duration_string())
            if 'addition_location_id' in criteria:
                full_string.append(str(self.addition_location))
            return '{}; '.format(' '.join(full_string))
        else:
            return str(self)

    def __str__(self):
        passage = ''

        if self.passage:
            passage = 'p{}'.format(self.passage)

        if self.addition_location:
            return '{0} {1}\n~{2:.2e} {3}, Added to: {4}'.format(
                self.cell_sample,
                passage,
                self.density,
                self.density_unit.unit,
                self.addition_location
            )
        else:
            return '{0} {1}\n~{2:.2e} {3}'.format(
                self.cell_sample,
                passage,
                self.density,
                self.density_unit.unit,
            )


# DO WE WANT TRACKING INFORMATION FOR INDIVIDUAL POINTS?
class AssayDataPoint(models.Model):
    """Individual points of data"""

    class Meta(object):
        unique_together = [
            (
                'matrix_item',
                'study_assay',
                'sample_location',
                'time',
                'update_number',
                'assay_plate_id',
                'assay_well_id',
                'replicate',
                # Be sure to include subtarget!
                'subtarget'
            )
        ]

    # setup = models.ForeignKey('assays.AssaySetup', on_delete=models.CASCADE)

    # May seem excessive, but chaining through fields can be inconvenient
    study = models.ForeignKey('assays.AssayStudy', on_delete=models.CASCADE)

    # Cross reference for users if study ids diverge
    cross_reference = models.CharField(max_length=255, default='')

    matrix_item = models.ForeignKey('assays.AssayMatrixItem', on_delete=models.CASCADE)

    study_assay = models.ForeignKey('assays.AssayStudyAssay', on_delete=models.CASCADE)

    sample_location = models.ForeignKey('assays.AssaySampleLocation', on_delete=models.CASCADE)

    value = models.FloatField(null=True)

    # PLEASE NOTE THAT THIS IS IN MINUTES
    time = models.FloatField(default=0)

    # Caution flags for the user
    # Errs on the side of larger flags, currently
    caution_flag = models.CharField(max_length=255, default='')

    # TODO PROPOSED: CHANGE QUALITY TO TWO BOOLEANS: exclude and replaced
    # Kind of sloppy right now, I do not like it!
    # This value will act as quality control, if it evaluates True then the value is considered invalid
    # quality = models.CharField(max_length=20, default='')

    excluded = models.BooleanField(default=False)

    replaced = models.BooleanField(default=False)

    # This value contains notes for the data point
    notes = models.CharField(max_length=255, default='')

    # Indicates what replicate this is (0 is for original)
    update_number = models.IntegerField(default=0)

    # DEFAULTS SUBJECT TO CHANGE
    assay_plate_id = models.CharField(max_length=255, default='N/A')
    assay_well_id = models.CharField(max_length=255, default='N/A')

    # Indicates "technical replicates"
    # SUBJECT TO CHANGE
    replicate = models.CharField(max_length=255, default='')

    # OPTIONAL FOR NOW
    data_file_upload = models.ForeignKey('assays.AssayDataFileUpload', null=True, blank=True, on_delete=models.CASCADE)

    # OPTIONAL
    subtarget = models.ForeignKey(AssaySubtarget, null=True, blank=True, on_delete=models.CASCADE)

    def get_time_string(self):
        split_times = get_split_times(self.time)
        return 'D{0:02} H{1:02} M{2:02}'.format(
            split_times.get('day'),
            split_times.get('hour'),
            split_times.get('minute'),
        )


class AssaySetupCompound(models.Model):
    """An instance of a compound used in an assay; used in M2M with setup"""

    class Meta(object):
        unique_together = [
            (
                # 'setup',
                'matrix_item',
                'compound_instance',
                'concentration',
                'concentration_unit',
                'addition_time',
                'duration',
                'addition_location'
            )
        ]

        ordering = (
            'addition_time',
            'compound_instance__compound__name',
            'addition_location__name',
            'concentration_unit__scale_factor',
            'concentration',
            'concentration_unit__name',
            'duration',
        )

    # Now binds directly to items
    matrix_item = models.ForeignKey(AssayMatrixItem, on_delete=models.CASCADE)

    # COMPOUND INSTANCE IS REQUIRED, however null=True was done to avoid a submission issue
    compound_instance = models.ForeignKey(
        'compounds.CompoundInstance',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    concentration = models.FloatField()
    concentration_unit = models.ForeignKey(
        'assays.PhysicalUnits',
        verbose_name='Concentration Unit',
        on_delete=models.CASCADE
    )

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    addition_time = models.FloatField(blank=True)

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    duration = models.FloatField(blank=True)

    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_location = models.ForeignKey(AssaySampleLocation, blank=True, default=1, on_delete=models.CASCADE)

    # NOT DRY
    def get_addition_time_string(self):
        split_times = get_split_times(self.addition_time)
        return 'D{0:02} H{1:02} M{2:02}'.format(
            split_times.get('day'),
            split_times.get('hour'),
            split_times.get('minute'),
        )

    def get_duration_string(self):
        split_times = get_split_times(self.duration)
        return 'D{0:02} H{1:02} M{2:02}'.format(
            split_times.get('day'),
            split_times.get('hour'),
            split_times.get('minute'),
        )

    # CRUDE
    def flex_string(self, criteria=None):
        if criteria:
            full_string = []
            if 'compound_instance.compound_id' in criteria:
                full_string.append(self.compound_instance.compound.name)
            if 'concentration' in criteria:
                full_string.append('{:g}'.format(self.concentration))
                full_string.append(self.concentration_unit.unit)
            if 'addition_time' in criteria:
                full_string.append('Added on: ' + self.get_addition_time_string())
            if 'duration' in criteria:
                full_string.append('Duration of: ' + self.get_duration_string())
            if 'addition_location_id' in criteria:
                full_string.append(str(self.addition_location))
            return '{}; '.format(' '.join(full_string))
        else:
            return str(self)

    def clean(self):
        # PREVENT DURATION OF 0
        if not self.duration or self.duration <= 0:
            raise forms.ValidationError({'duration': ['Duration cannot be zero or negative.']})

    def __str__(self):
        if self.addition_location:
            return '{0} ({1} {2})\nAdded on: {3}; Duration of: {4}; Added to: {5}'.format(
                self.compound_instance.compound.name,
                self.concentration,
                self.concentration_unit.unit,
                self.get_addition_time_string(),
                self.get_duration_string(),
                self.addition_location
            )
        else:
            return '{0} ({1} {2})\nAdded on: {3}; Duration of: {4}'.format(
                self.compound_instance.compound.name,
                self.concentration,
                self.concentration_unit.unit,
                self.get_addition_time_string(),
                self.get_duration_string(),
            )


# TODO MODIFY StudySupportingData
class AssayStudySupportingData(models.Model):
    """A file (with description) that gives extra data for a Study"""
    study = models.ForeignKey(AssayStudy, on_delete=models.CASCADE)

    description = models.CharField(
        max_length=1000,
        help_text='Describes the contents of the supporting data file'
    )

    # Not named file in order to avoid shadowing
    supporting_data = models.FileField(
        upload_to=study_supporting_data_location,
        help_text='Supporting Data for Study'
    )


# TODO Probably should have a ControlledVocabularyMixin for defining name and description consistently
class AssaySetting(LockableModel):
    """Defines a type of setting (flowrate etc.)"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    def __str__(self):
        return self.name


class AssaySetupSetting(models.Model):
    """Defines a setting as it relates to a setup"""
    class Meta(object):
        unique_together = [
            (
                # 'setup',
                'matrix_item',
                'setting',
                'addition_location',
                'unit',
                'addition_time',
                'duration',
            )
        ]

        ordering = (
            'addition_time',
            'setting__name',
            'addition_location__name',
            'unit__name',
            'value',
            'duration',
        )

    # Now binds directly to items
    matrix_item = models.ForeignKey(AssayMatrixItem, on_delete=models.CASCADE)

    # No longer one-to-one
    # setup = models.ForeignKey('assays.AssaySetup', on_delete=models.CASCADE)
    setting = models.ForeignKey('assays.AssaySetting', on_delete=models.CASCADE)
    # DEFAULTS TO NONE, BUT IS REQUIRED
    unit = models.ForeignKey('assays.PhysicalUnits', blank=True, default=14, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    # Will we include these??
    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    addition_time = models.FloatField(blank=True)

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    duration = models.FloatField(blank=True)

    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_location = models.ForeignKey(AssaySampleLocation, blank=True, default=1, on_delete=models.CASCADE)

    # NOT DRY
    def get_addition_time_string(self):
        split_times = get_split_times(self.addition_time)
        return 'D{0:02} H{1:02} M{2:02}'.format(
            split_times.get('day'),
            split_times.get('hour'),
            split_times.get('minute'),
        )

    def get_duration_string(self):
        split_times = get_split_times(self.duration)
        return 'D{0:02} H{1:02} M{2:02}'.format(
            split_times.get('day'),
            split_times.get('hour'),
            split_times.get('minute'),
        )

    # CRUDE
    def flex_string(self, criteria=None):
        if criteria:
            full_string = []
            if 'setting_id' in criteria:
                full_string.append(str(self.setting))
            if 'value' in criteria:
                full_string.append(self.value)
                if self.unit:
                    full_string.append(self.unit.unit)
            if 'addition_time' in criteria:
                full_string.append('Added on: ' + self.get_addition_time_string())
            if 'duration' in criteria:
                full_string.append('Duration of: ' + self.get_duration_string())
            if 'addition_location_id' in criteria:
                full_string.append(str(self.addition_location))
            return '{}; '.format(' '.join(full_string))
        else:
            return str(self)

    def clean(self):
        # PREVENT DURATION OF 0
        if not self.duration or self.duration <= 0:
            raise forms.ValidationError({'duration': ['Duration cannot be zero or negative.']})

    def __str__(self):
        return '{} {} {}'.format(self.setting.name, self.value, self.unit)


# DEPRECATED
class AssayRunStakeholder(models.Model):
    """An institution that has interest in a particular study

    Stakeholders needs to be consulted (sign off) before data can become available
    """

    study = models.ForeignKey(AssayRun, on_delete=models.CASCADE)

    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    # Explicitly declared rather than from inheritance to avoid unecessary fields
    signed_off_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    signed_off_date = models.DateTimeField(blank=True, null=True)

    signed_off_notes = models.CharField(max_length=255, blank=True, default='')

    # TODO NEED MEDIA LOCATION
    # approval_for_sign_off = models.FileField(null=True, blank=True)

    sign_off_required = models.BooleanField(default=True)


class AssayStudyStakeholder(models.Model):
    """An institution that has interest in a particular study

    Stakeholders needs to be consulted (sign off) before data can become available
    """

    study = models.ForeignKey(AssayStudy, on_delete=models.CASCADE)

    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    # Explicitly declared rather than from inheritance to avoid unecessary fields
    signed_off_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    signed_off_date = models.DateTimeField(blank=True, null=True)

    signed_off_notes = models.CharField(max_length=255, blank=True, default='')

    sign_off_required = models.BooleanField(default=True)


class AssayStudyAssay(models.Model):
    """Specific assays used in the 'inlines'"""
    study = models.ForeignKey(AssayStudy, null=True, blank=True, on_delete=models.CASCADE)
    # study_new = models.ForeignKey('assays.AssayStudy', null=True, blank=True, on_delete=models.CASCADE)
    target = models.ForeignKey(AssayTarget, on_delete=models.CASCADE)
    method = models.ForeignKey(AssayMethod, on_delete=models.CASCADE)
    # Name of model "PhysicalUnits" should be renamed, methinks
    unit = models.ForeignKey(PhysicalUnits, on_delete=models.CASCADE)

    # CATEGORY IS NOT ACTUALLY STORED
    # category = models.ForeignKey(
    #     'assays.AssayCategory',
    #     null=True,
    #     blank=True,
    #     on_delete=models.CASCADE
    # )

    # TODO TODO TODO NOTE THAT ADDING CATEGORY HERE WILL INTERUPT OTHER SCRIPTS
    def __str__(self):
        return '{0}~@|{1}~@|{2}~@|{3}'.format(self.study_id, self.target, self.method, self.unit)


class AssayImageSetting(models.Model):
    # Requested, not sure how useful
    # May want to remove soon, why have this be specific to a study? Deletion cascade?
    study = models.ForeignKey(AssayStudy, on_delete=models.CASCADE)
    # This is necessary in TongYing's scheme, but it is kind of confusing in a way
    label_id = models.CharField(max_length=40, default='', blank=True)
    label_name = models.CharField(max_length=255)
    label_description = models.CharField(max_length=500, default='', blank=True)
    wave_length = models.CharField(max_length=255)
    magnification = models.CharField(max_length=40)
    resolution = models.CharField(max_length=40)
    resolution_unit = models.CharField(max_length=40)
    # May be useful later
    notes = models.CharField(max_length=500, default='', blank=True)
    color_mapping = models.CharField(max_length=255, default='', blank=True)

    def __str__(self):
        return '{} {}'.format(self.study.name, self.label_name)


class AssayImage(models.Model):
    # May want to have an FK to study for convenience?
    # study = models.ForeignKey(AssayStudy, on_delete=models.CASCADE)
    # The associated item
    matrix_item = models.ForeignKey(AssayMatrixItem, on_delete=models.CASCADE)
    # The file name
    file_name = models.CharField(max_length=255)
    field = models.CharField(max_length=255)
    field_description = models.CharField(max_length=500, default='')
    # Stored in minutes
    time = models.FloatField()
    # Possibly used later, who knows
    assay_plate_id = models.CharField(max_length=255, default='N/A')
    assay_well_id = models.CharField(max_length=255, default='N/A')
    # PLEASE NOTE THAT I USE TARGET AND METHOD SEPARATE FROM ASSAY INSTANCE
    method = models.ForeignKey(AssayMethod, on_delete=models.CASCADE)
    target = models.ForeignKey(AssayTarget, on_delete=models.CASCADE)
    # May become useful
    subtarget = models.ForeignKey(AssaySubtarget, on_delete=models.CASCADE)
    sample_location = models.ForeignKey(AssaySampleLocation, on_delete=models.CASCADE)
    notes = models.CharField(max_length=500, default='')
    replicate = models.CharField(max_length=255, default='')
    setting = models.ForeignKey(AssayImageSetting, on_delete=models.CASCADE)

    def get_metadata(self):
        return {
            'matrix_item_id': self.matrix_item_id,
            'chip_id': self.matrix_item.name,
            'plate_id': self.assay_plate_id,
            'well_id': self.assay_well_id,
            'time': "D"+str(int(self.time/24/60))+" H"+str(int(self.time/60%24))+" M" + str(int(self.time%60)),
            'method_kit': self.method.name,
            'stain_pairings': self.method.alt_name,
            'target_analyte': self.target.name,
            'subtarget': self.subtarget.name,
            'sample_location': self.sample_location.name,
            'replicate': self.replicate,
            'notes': self.notes,
            'file_name': self.file_name,
            'field': self.field,
            'field_description': self.field_description,
            'magnification': self.setting.magnification,
            'resolution': self.setting.resolution,
            'resolution_unit': self.setting.resolution_unit,
            'sample_label': self.setting.label_name,
            'sample_label_description': self.setting.label_description,
            'wavelength': self.setting.wave_length,
            'color_mapping': self.setting.color_mapping,
            'setting_notes': self.setting.notes,
        }

    def __str__(self):
        return '{}'.format(self.file_name)


class AssayStudySet(FlaggableModel):
    # Name for the set
    name = models.CharField(max_length=255, unique=True)
    # Description
    description = models.CharField(max_length=2000, default='', blank=True)

    studies = models.ManyToManyField(AssayStudy)
    assays = models.ManyToManyField(AssayStudyAssay)

    def get_post_submission_url(self):
        return self.get_absolute_url()

    def get_absolute_url(self):
        return '/assays/assaystudyset/{}/'.format(self.id)

    def __str__(self):
        return self.name


class AssayReference(FlaggableModel):
    pubmed_id = models.CharField(verbose_name='PubMed ID', max_length=40, blank=True, default='N/A')
    title = models.CharField(verbose_name='Title', max_length=2000, unique=True)
    authors = models.CharField(verbose_name='Authors', max_length=2000)
    abstract = models.CharField(verbose_name='Abstract', max_length=4000, blank=True, default='')
    publication = models.CharField(verbose_name='Publication', max_length=255)
    year = models.CharField(verbose_name='Year', max_length=4)
    doi = models.CharField(verbose_name='DOI', max_length=100, blank=True, default='N/A')

    # Somewhat odd
    def get_metadata(self):
        return {
            'pubmed_id': self.pubmed_id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'publication': self.publication,
            'year': self.year,
            'doi': self.doi,
        }

    def __str__(self):
        return '{}. {}. {}. {}. doi:{}. PMID:{}'.format(self.authors, self.title, self.publication, self.year, self.doi, self.pubmed_id)

    def get_post_submission_url(self):
        return '/assays/references/'

    def get_absolute_url(self):
        return '/assays/references/{}/'.format(self.id)

    def get_delete_url(self):
        return '{}delete/'.format(self.get_absolute_url())


class AssayStudyReference(models.Model):
    class Meta(object):
        unique_together = [
            (
                'reference',
                'reference_for'
            )
        ]

    reference = models.ForeignKey(AssayReference, on_delete=models.CASCADE)
    reference_for = models.ForeignKey(AssayStudy, on_delete=models.CASCADE)


# TODO TODO TODO
class AssayStudySetReference(models.Model):
    class Meta(object):
        unique_together = [
            (
                'reference',
                'reference_for'
            )
        ]

    reference = models.ForeignKey(AssayReference, on_delete=models.CASCADE)
    reference_for = models.ForeignKey(AssayStudySet, on_delete=models.CASCADE)


class AssayCategory(FlaggableModel):
    """Describes a genre of assay"""

    class Meta(object):
        verbose_name = 'Assay Category'
        verbose_name_plural = 'Assay Categories'

    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    # List of all related targets
    targets = models.ManyToManyField('assays.AssayTarget')

    def __str__(self):
        return '{}'.format(self.name)
