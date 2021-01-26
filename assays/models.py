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
    FlaggableRestrictedModel,
    FrontEndModel
)

from django.contrib.postgres.fields import JSONField

from django.contrib.auth.models import Group, User

from django.utils.safestring import mark_safe

import urllib.request, urllib.parse, urllib.error

# Avoid wildcards when possible
from mps.utils import *



import datetime
from django.urls import reverse
# THIS WILL ONLY BE USED FOR PROTOTYPE
from django.contrib.postgres.fields import JSONField

import ujson as json
# Copying dictionaries and the like
import copy


from django.urls import reverse

# THIS WILL ONLY BE USED FOR PROTOTYPE
from django.contrib.postgres.fields import JSONField

# TODO REORGANIZE
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
    # NOTE CONSIDER REFACTORING
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

    unit_type = models.CharField(
        max_length=100,
        verbose_name='Name'
    )
    description = models.CharField(
        max_length=256,
        blank=True,
        default=''
    )

    def __str__(self):
        return '{}'.format(self.unit_type)


# Doing follows for units would be difficult, there are a lot of relations!
# TODO THIS NEEDS TO BE REVISED (IDEALLY REPLACED WITH PHYSICALUNIT BELOW)
class PhysicalUnits(FrontEndModel, LockableModel):
    """Measures of concentration and so on"""

    class Meta(object):
        verbose_name = 'Unit'
        ordering = ['unit_type', 'unit']

    # USE NAME IN LIEU OF UNIT (unit.unit is confusing and dumb)
    # name = models.CharField(max_length=255)
    unit = models.CharField(
        max_length=255,
        verbose_name='Name'
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    unit_type = models.ForeignKey(
        UnitType,
        on_delete=models.CASCADE,
        verbose_name='Unit Type'
    )

    # Base Unit for conversions and scale factor
    base_unit = models.ForeignKey(
        'assays.PhysicalUnits',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='Base Unit'
    )

    # Scale factor gives the conversion to get to the base unit, can also act to sort
    scale_factor = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Scale Factor'
    )

    availability = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text=(
            'Type a series of strings for indicating '
            'where this unit should be listed:'
            '\ntest = test results\nreadouts = readouts\ncells = cell samples'
        ),
       verbose_name='Availability'
    )

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

    setup_date = models.DateField(help_text='Format: YYYY-MM-DD')

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

    readout_start_time = models.DateField(verbose_name='Readout Date', help_text="Format: YYYY-MM-DD")

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


# DEPRECATED: Slated to be removed
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


# DEPRECATED
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


# DEPRECATED
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

    class Meta(object):
        verbose_name = 'Processed Data File'

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

    def get_absolute_url(self):
        return reverse('assays-assaydatafileupload-detail', args=[self.pk])


class AssayTarget(FrontEndModel, LockableModel):
    """Describes what was sought by a given Assay"""

    class Meta(object):
        verbose_name = 'Target'

    name = models.CharField(
        max_length=512,
        unique=True,
        verbose_name='Name'
    )
    description = models.CharField(
        max_length=2000,
        verbose_name='Description'
    )

    short_name = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Short Name'
    )

    # Tentative
    alt_name = models.CharField(
        max_length=1000,
        blank=True,
        default='',
        verbose_name='Alternative Name'
    )

    # List of all methods
    methods = models.ManyToManyField(
        'assays.AssayMethod',
        verbose_name='Methods'
    )

    def __str__(self):
        return '{0}'.format(self.name)


class AssaySubtarget(FlaggableModel):
    """Describes a target for situations where manually curated lists are prohibitively expensive (TempoSeq, etc.)"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    def __str__(self):
        return self.name


class AssayMeasurementType(FrontEndModel, LockableModel):
    """Describes what was measures with a given method"""

    class Meta(object):
        verbose_name = 'Measurement Type'

    name = models.CharField(
        max_length=512,
        unique=True,
        verbose_name='Name'
    )
    description = models.CharField(
        max_length=2000,
        verbose_name='Description'
    )

    def __str__(self):
        return self.name


class AssaySupplier(FrontEndModel, LockableModel):
    """Assay Supplier so we can track where kits came from"""

    class Meta(object):
        verbose_name = 'Assay Supplier'

    name = models.CharField(
        max_length=512,
        unique=True,
        verbose_name='Name'
    )
    description = models.CharField(
        max_length=2000,
        verbose_name='Description'
    )

    def __str__(self):
        return self.name


class AssayMethod(FrontEndModel, LockableModel):
    """Describes how an assay was performed"""
    # We may want to modify this so that it is unique on name in combination with measurement type?

    class Meta(object):
        verbose_name = 'Method'

    name = models.CharField(
        max_length=512,
        unique=True,
        verbose_name='Name'
    )
    description = models.CharField(
        max_length=2000,
        verbose_name='Description'
    )
    measurement_type = models.ForeignKey(
        AssayMeasurementType,
        on_delete=models.CASCADE,
        verbose_name='Measurement Type'
    )

    # May or may not be required in the future
    supplier = models.ForeignKey(
        AssaySupplier,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='Supplier'
    )

    # TODO STORAGE LOCATION
    # TODO TEMPORARILY NOT REQUIRED
    protocol_file = models.FileField(
        upload_to='assays',
        null=True,
        blank=True,
        verbose_name='Protocol File'
    )

    # Tentative
    alt_name = models.CharField(
        max_length=1000,
        blank=True,
        default='',
        verbose_name='Alternative Name'
    )

    def __str__(self):
        return self.name


class AssaySampleLocation(FrontEndModel, LockableModel):
    """Describes a location for where a sample was acquired"""

    class Meta(object):
        verbose_name = 'MPS Model Location'

    name = models.CharField(
        max_length=512,
        unique=True,
        verbose_name='Name'
    )
    description = models.CharField(
        max_length=2000,
        verbose_name='Description'
    )

    def __str__(self):
        return self.name


# DEPRECATED
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
            'omics',
            'pbpk_steady_state',
            'pbpk_bolus',
            'start_date',
            'group'
        ))

    toxicity = models.BooleanField(
        default=False,
        verbose_name='Toxicity'
    )
    efficacy = models.BooleanField(
        default=False,
        verbose_name='Efficacy'
    )
    disease = models.BooleanField(
        default=False,
        verbose_name='Disease'
    )
    # TODO PLEASE REFACTOR
    # NOW REFERRED TO AS "Chip Characterization"
    cell_characterization = models.BooleanField(
        default=False,
        verbose_name='Cell Characterization'
    )

    # TODO: THESE REALLY SHOULDN'T BE ATTRIBUTES
    omics = models.BooleanField(
        default=False,
        verbose_name='Omics'
    )

    # Subject to change
    # NOTE THAT THE TABLE IS NOW NAMED AssayStudyConfiguration to adhere to standards
    study_configuration = models.ForeignKey(
        AssayStudyConfiguration,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='Study Configuration'
    )
    # Whether or not the name should be unique is an interesting question
    # We could have a constraint on the combination of name and start_date
    # But to constrain by name, start_date, and study_types, we will need to do that in the forms.py file
    # Otherwise we can change study_types such that it is not longer a ManyToMany
    name = models.CharField(max_length=1000, verbose_name='Study Name')

    # Uncertain whether or not I will do this
    # This will be used to avoid having to call related fields to get the full name all the time
    # full_name = models.CharField(max_length=1200, verbose_name='Full Study Name')

    start_date = models.DateField(
        help_text='This date specifies when treatment of devices began.\nFormat: YYYY-MM-DD',
        verbose_name='Start Date'
    )
    description = models.CharField(
        max_length=8000,
        blank=True,
        default='',
        verbose_name='Description'
    )

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
    image = models.ImageField(
        upload_to='studies',
        null=True,
        blank=True,
        verbose_name='Image'
    )

    use_in_calculations = models.BooleanField(
        default=False,
        help_text='Check this if this data should be included in Compound Reports and other data aggregations.',
        verbose_name='Use Data in Compound Report'
    )

    # Access groups
    access_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name='study_access_groups',
        verbose_name='Access Groups'
    )

    # Collaborator groups
    collaborator_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name='study_collaborator_groups',
        verbose_name='Collaborator Groups'
    )

    # THESE ARE NOW EXPLICIT FIELDS IN STUDY
    group = models.ForeignKey(
        Group,
        verbose_name='Data Group',
        help_text='Select the Data Group. The study will be bound to this group',
        on_delete=models.CASCADE
    )

    restricted = models.BooleanField(
        default=True,
        help_text='Check box to restrict to the Access Groups selected below.'
                  ' Access is granted to access group(s) after Data Group admin and all designated'
                  ' Stakeholder Group admin(s) sign off on the study',
        verbose_name='Restricted'
    )

    # Special addition, would put in base model, but don't want excess...
    signed_off_notes = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Signed Off Notes'
    )

    # Delimited string of reproducibility (Excellent|Acceptable|Poor)
    repro_nums = models.CharField(
        max_length=40,
        blank=True,
        default='',
        help_text='Excellent|Acceptable|Poor',
        verbose_name='Reproducibility'
    )

    # TODO SOMEWHAT CONTRIVED
    bulk_file = models.FileField(
        upload_to=upload_file_location,
        verbose_name='Data File',
        blank=True,
        null=True
    )

    # DEPRECATED: TO BE REMOVED
    organ_model = models.ForeignKey(
        OrganModel,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='MPS Model'
    )
    organ_model_protocol = models.ForeignKey(
        OrganModelProtocol,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='MPS Model Version'
    )

    # Whether or not to show on the front end
    archived = models.BooleanField(
        default=False,
        help_text='Archived Studies do not appear on the front end'
    )

    # For PBPK
    # PLEASE NOTE THAT WE LIKELY WILL NEED TO REFACTOR STUDY TYPES
    # Study types for pbpk
    pbpk_steady_state = models.BooleanField(
        default=False,
        # verbose_name='PBPK Steady State'
        # verbose_name='Constant Infusion'
        verbose_name='Continuous Infusion'
    )
    pbpk_bolus = models.BooleanField(
        default=False,
        # verbose_name='PBPK Bolus'
        # verbose_name='Single Bolus'
        verbose_name='Bolus'
    )

    # Estimate of PBPK relevant cells
    # Require int
    number_of_relevant_cells = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Number of PK Relevant Cells per MPS Model'
    )
    # Relevant PBPK volume
    total_device_volume = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Total Device Volume (μL)'
    )
    # Relevant PBPK flow rate
    flow_rate = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Flow Rate (μL/hour)'
    )

    # TODO
    # def get_study_types_string(self):
    #     study_types = '-'.join(
    #         sorted([study_type.code for study_type in self.study_types.all()])
    #     )
    #     return study_types

    # Specify when to release the Study
    release_date = models.DateField(
        help_text='YYYY-MM-DD',
        verbose_name='Release Date',
        # NEEDS TO BE ABLE TO BE NULL AND BLANK
        null=True,
        blank=True,
    )

    # CONDITIONAL ON DISEASE MODEL SELECTION
    diseases = models.ManyToManyField(
        'diseases.Disease',
        blank=True,
        help_text='Indicates what disease or diseases were tested'
    )

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
        groups = AssayGroup.objects.filter(study_id=self.id).prefetch_related(
            'organ_model',
            'assaygroupsetting_set__setting',
            'assaygroupsetting_set__addition_location',
            'assaygroupsetting_set__unit',
            'assaygroupcell_set__cell_sample__cell_subtype',
            'assaygroupcell_set__cell_sample__cell_type__organ',
            'assaygroupcell_set__cell_sample__supplier',
            'assaygroupcell_set__density_unit',
            'assaygroupcell_set__addition_location',
            'assaygroupcell_set__biosensor',
            'assaygroupcompound_set__compound_instance__compound',
            'assaygroupcompound_set__concentration_unit',
            'assaygroupcompound_set__addition_location',
        )

        current_study = {}

        for group in groups:
            organ_model_name = group.organ_model.name

            # current_study.setdefault('items', {}).update({
            #     group.name: True
            # })
            current_study.setdefault('organ_models', {}).update({
                organ_model_name: True
            })
            # current_study.setdefault('devices', {}).update({
            #     group.device.name: True
            # })

            for compound in group.assaygroupcompound_set.all():
                current_study.setdefault('compounds', {}).update({
                    str(compound): True
                })

            for cell in group.assaygroupcell_set.all():
                current_study.setdefault('cells', {}).update({
                    str(cell): True
                })

            for setting in group.assaygroupsetting_set.all():
                current_study.setdefault('settings', {}).update({
                    str(setting): True
                })

        return '\n'.join([' '.join(x) for x in list(current_study.values())])

    # TODO REVIEW
    def get_group_data_string(self, get_chips=False, plate_id=None):
        data = {
            # Probably should change name?
            'series_data': [],
            # Mode defines which get populated
            # May need modify for a 'both' option
            'chips': [],
            'plates': {},
            # For matching groups to items
            # This really isn't the place for this:
            # We ought not put information here when it is better suited elsewhere
            'group_name_to_items': {},
        }

        # If we so desired, we could order these
        # One option is PK to get order of addition?
        groups = AssayGroup.objects.filter(
            study_id=self.id
        ).prefetch_related(
            # Prefetch the cells etc.
            # Kind of rough, but on the bright side we don't need chaining
            'assaygroupcell_set',
            # Shame we need to do this
            # BUT COMPOUND SCHEMA IS STUPID
            'assaygroupcompound_set__compound_instance__supplier',
            'assaygroupsetting_set',
            # Guess I need to eat the cost...
            'organ_model__device'
        ).order_by(
            'id'
        )

        # For mapping chips
        group_id_to_index = {}

        # No junk
        # We actually do want to get the id for updates and the like
        excluded_keys = [
            '_state',
            # Interestingly, we are going to exclude id for now
            # Since we are killing all of the related data on save anyway...
            # We just end up making a mess keeping this
            # TODO TODO TODO BRING BACK WHEN WE REFACTOR PLEASE
            'id',
            '_prefetched_objects_cache',
            # WE DON'T WANT THE GROUP ID
            # THIS WILL RUIN THE DIFFERENCE CHECKER
            'group_id',
        ]

        for group_index, group in enumerate(groups):
            current_group = {
                'cell': [],
                'compound': [],
                'setting': [],
                # Why stringify this?
                'id': group.id,
                # 'id': str(group.id),
                'name': group.name,
                # Tricky, these are passed as strings
                'organ_model_id': group.organ_model_id,
                # TRICKY! TODO BE CAREFUL MAY NOT EXIST
                'organ_model_protocol_id': group.organ_model_protocol_id,
                'test_type': group.test_type,
                # TECHNICALLY ONLY RELEVANT WHEN GETTING CHIPS
                # SEE BELOW
                'number_of_items': 0,
                # Prevents AJAX requests, I guess
                'device_type': group.organ_model.device.device_type
            }

            # Not very DRY
            for cell in group.assaygroupcell_set.all():
                current_group.get('cell').append(
                    {
                        key: cell.__dict__.get(key) for key in cell.__dict__.keys() if key not in excluded_keys
                    }
                )

            # OH BOY! BECAUSE THE SCHEMA FOR COMPOUNDS ARE STUPID, WE NEED SPECIAL HANDLING
            # WOO WOO!
            # We need the compound instances to be devolved, unfortunately
            # Either that, or we, you know, revise the compound schema
            # To meet deadlines, I guess that isn't really an option
            # Here we go!
            for compound in group.assaygroupcompound_set.all():
                current_dic = {
                    key: compound.__dict__.get(key) for key in compound.__dict__.keys() if key not in excluded_keys
                }

                # Because compound schema is stupid
                current_dic.update({
                    'compound_id': compound.compound_instance.compound_id,
                    'supplier_text': compound.compound_instance.supplier.name,
                    'lot_text': compound.compound_instance.lot,
                    'receipt_date': compound.compound_instance.receipt_date,
                })

                current_group.get('compound').append(
                    current_dic
                )

            for setting in group.assaygroupsetting_set.all():
                current_group.get('setting').append(
                    {
                        key: setting.__dict__.get(key) for key in setting.__dict__.keys() if key not in excluded_keys
                    }
                )

            data.get('series_data').append(current_group)
            group_id_to_index.update({
                group.id: group_index
            })

        if get_chips:
            # TODO TODO TODO
            # PLEASE NOTE: WE WILL HAVE TO GO BACK AND CONSOLIDATE ALL CHIPS IN EXISTING STUDIES TO A SINGLE MATRIX
            # We can't get the matrix in question with a name (the study name can change)
            # We can get the correct chips by either seeing if the organ model is for chips or checking the representation of the matrix
            # For the moment we will assume only one chip matrix
            chips = AssayMatrixItem.objects.filter(
                # Must be for this study
                study_id=self.id,
                # Must be in the chip matrix
                matrix__representation='chips'
            ).prefetch_related(
                # Unfortunately, to avoid N+1, we need to prefetch
                'matrix'
            # Possibly annoying, I don't know
            ).order_by(
                'id'
            )

            # For every chip, tack on an object with
            for chip in chips:
                data.get('chips').append(
                    {
                        'name': chip.name,
                        'group_id': chip.group_id,
                        # We use group index in the group page rather than id because groups may or may not exist on that page
                        # Default *ideally* is not necessary here
                        'group_index': group_id_to_index.get(chip.group_id, None),
                        'id': chip.id
                    }
                )

                data.get('series_data')[group_id_to_index.get(chip.group_id, None)]['number_of_items'] += 1

        # Get the plate information
        # It is worth noting that for the purposes of a plate edit page, we really only need the one...
        # Maybe we could have a plate_id arg as a filter?
        # TODO REVIEW
        if plate_id:
            current_plate_data = {}

            # We don't really care about much outside of the column, row, group_id, name
            # Passing the plate_id is what tells us the current plate
            current_plate = AssayMatrix.objects.filter(
                id=plate_id,
                # Insurance
                study_id=self.id
            )[0]

            for well in AssayMatrixItem.objects.filter(matrix_id=current_plate.id):
                current_well_data = {
                    'group_id': well.group_id,
                    'group_index': group_id_to_index.get(well.group_id, None),
                    'name': well.name,
                    'id': well.id
                }
                current_plate_data.update({
                    '{}_{}'.format(
                        well.row_index,
                        well.column_index,
                    ) : current_well_data
                })

            # It probably isn't ideal to pass the plate this way?
            # data.get('plates').append(current_plate_data
            data.update({
                'plates': current_plate_data
            })

        # STUPID
        # Repetitive
        for item in AssayMatrixItem.objects.filter(study_id=self.id).prefetch_related('group'):
            data.get('group_name_to_items').setdefault(
                item.group.name, []
            ).append(
                # PREVENTS MAGIC STRINGS FOR URL
                '<a href="{}">{}</a>'.format(
                    item.get_absolute_url(),
                    item.name
                )
            )

        return json.dumps(data)

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
        if self.omics:
            current_types.append('OMICS')
        if self.pbpk_steady_state or self.pbpk_bolus:
            current_types.append('PK')
        return '-'.join(current_types)

    # TODO REVISE REVISE
    def __str__(self):
        first_center = self.group.center_groups.first()
        if first_center:
            center_id = first_center.center_id
        else:
            center_id = 'NO_CENTER'
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


class AssayMatrix(FlaggableModel):
    """Used to organize data in the interface. An Matrix is a set of setups"""
    class Meta(object):
        verbose_name = 'Plate/Study Chips'
        # verbose_name_plural = 'Assay Matrices'

        unique_together = [('study', 'name')]

    # TODO Name made unique within Study? What will the constraint be?
    name = models.CharField(
        max_length=255,
        verbose_name='Name'
    )

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
            # We exclude null, for now
            # ('', '')
        ),
        verbose_name='Representation'
    )

    study = models.ForeignKey(
        AssayStudy,
        on_delete=models.CASCADE,
        verbose_name='Study'
    )

    # DEPRECATED!
    device = models.ForeignKey(
        Microdevice,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        # verbose_name='Device'
        # Requested change
        # Is it always accurate, however?
        verbose_name='Plate Type'
    )

    # Decided against the inclusion of organ model here
    # NEVER MIND, I GUESS WE ARE GOING TO ALLOW ORGAN MODEL HERE
    # PLATES NOW REQUIRE ORGAN MODEL, I THINK
    organ_model = models.ForeignKey(
        OrganModel,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='MPS Model'
    )
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
    number_of_rows = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Number of Rows'
    )
    number_of_columns = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Number of Columns'
    )

    # May be useful
    notes = models.CharField(
        max_length=2048,
        blank=True,
        default='',
        verbose_name='Notes'
    )

    # TEMPORARY: FOR PROTOTYPE SCHEMA
    # REMOVE ASAP
    # plate_data = JSONField(default=dict, blank=True)

    # def __str__(self):
    #     return '{0}'.format(self.name)

    # ALTERNATIVE TO BEING DONE EXPLICITLY
    def __str__(self):
        if self.representation == 'plate':
            return '{0}'.format(self.name)
        else:
            return 'Chips for {}'.format(self.study.name)

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
        # NO!
        # return '/assays/assaymatrix/{}/'.format(self.id)
        # Not update! Detail will redirect anyway
        # return reverse('assays-assaymatrix-plate-update', args=[self.pk])
        # If this is a plate
        if self.representation == 'plate':
            return reverse('assays-assaymatrix-plate-detail', args=[self.pk])
        # Otherwise
        else:
            return reverse('assays-assaymatrix-chips-detail', args=[self.pk])

    def get_post_submission_url(self):
        # return self.study.get_post_submission_url()
        # Assumes the new interface
        return reverse('assays-assaystudy-update-plates', args=[self.study.pk])

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


# Having an abstract class will cut down on problems with repetition
class AbstractSetupCompound(models.Model):
    """Defines an abstract compound configuration for binding to a group"""

    class Meta(object):
        abstract = True

        # Default needs to be revised in models extending this, but for reference
        unique_together = [
            (
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

    # COMPOUND INSTANCE IS REQUIRED, however null=True was done to avoid a submission issue
    # IDEALLY WE WILL RESOLVE THIS ASAP
    compound_instance = models.ForeignKey(
        'compounds.CompoundInstance',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='Compound Instance'
    )
    concentration = models.FloatField(verbose_name='Concentration')
    concentration_unit = models.ForeignKey(
        'assays.PhysicalUnits',
        verbose_name='Concentration Unit',
        on_delete=models.CASCADE,
    )

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    addition_time = models.FloatField(
        blank=True,
        verbose_name='Addition Time'
    )

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    duration = models.FloatField(
        blank=True,
        verbose_name='Duration'
    )

    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_location = models.ForeignKey(
        AssaySampleLocation,
        # MAKE REQUIRED FOR NOW!
        # blank=True,
        # default=1,
        on_delete=models.CASCADE,
        verbose_name='Addition Location'
    )

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


class AbstractSetupCell(models.Model):
    """Defines an abstract cell configuration for binding to either a group or an MPS Model Version"""
    class Meta(object):
        abstract = True

        # Default needs to be revised in models extending this, but for reference
        unique_together = [
            (
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

    cell_sample = models.ForeignKey(
        'cellsamples.CellSample',
        on_delete=models.CASCADE,
        verbose_name='Cell Sample'
    )
    biosensor = models.ForeignKey(
        'cellsamples.Biosensor',
        on_delete=models.CASCADE,
        # Default is naive
        default=2,
        verbose_name='Biosensor'
    )
    density = models.FloatField(
        verbose_name='density',
        default=0
    )

    density_unit = models.ForeignKey(
        'assays.PhysicalUnits',
        on_delete=models.CASCADE,
        verbose_name='Density Unit'
    )
    passage = models.CharField(
        max_length=16,
        verbose_name='Passage#',
        blank=True,
        default=''
    )

    # DO WE WANT ADDITION TIME AND DURATION?
    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Addition Time'
    )

    # TODO TODO TODO DO WE WANT DURATION????
    # duration = models.FloatField(null=True, blank=True)

    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_location = models.ForeignKey(
        AssaySampleLocation,
        blank=True,
        default=1,
        on_delete=models.CASCADE,
        verbose_name='Addition Location'
    )

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
            if 'biosensor_id' in criteria:
                full_string.append(str(self.biosensor))
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


class AbstractSetupSetting(models.Model):
    """Defines an abstract setting for binding to either a group or an MPS Model Version"""
    class Meta(object):
        abstract = True

        # Default needs to be revised in models extending this, but for reference
        # NOTE: VALUE IS EXCLUDED BY REQUEST
        unique_together = [
            (
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

    setting = models.ForeignKey(
        'assays.AssaySetting',
        on_delete=models.CASCADE,
        verbose_name='Setting'
    )
    # DEFAULTS TO NONE, BUT IS REQUIRED
    unit = models.ForeignKey(
        'assays.PhysicalUnits',
        blank=True,
        default=14,
        on_delete=models.CASCADE,
        verbose_name='Unit'
    )
    value = models.CharField(
        max_length=255,
        verbose_name='Value'
    )

    # Will we include these??
    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    addition_time = models.FloatField(
        blank=True,
        verbose_name='Addition Time'
    )

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    duration = models.FloatField(
        blank=True,
        verbose_name='Duration'
    )

    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_location = models.ForeignKey(
        AssaySampleLocation,
        blank=True,
        default=1,
        on_delete=models.CASCADE,
        verbose_name='Addition Location'
    )

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

    def __str__(self):
        return '{} {} {}'.format(self.setting.name, self.value, self.unit)


# Previously considered the name "AssaySetupGroup"
class AssayGroup(models.Model):
    class Meta(object):
        verbose_name = 'Group'

        # Do not allow duplicates of name per study
        unique_together = [
            (
                'name',
                'study'
            )
        ]

    # We are not considering series at the moment
    # series = models.ForeignKey(
    #     AssayItemSeries,
    #     on_delete=models.CASCADE,
    #     verbose_name='Series'
    # )

    # Groups are bound to a study for the moment
    study = models.ForeignKey(
        AssayStudy,
        on_delete=models.CASCADE,
        verbose_name='Study'
    )

    # For clarity, groups should have a name
    # Should we require this? Or should it be optional?
    name = models.CharField(
        max_length=255,
        verbose_name='Name',
        # Ought to be required
        # Additionally, ought to be unique with study
        # blank=True,
        # default=''
    )

    # Need to store test type here, acquiring it implicitly is unpleasant
    test_type = models.CharField(
        max_length=8,
        choices=TEST_TYPE_CHOICES,
        # default='control',
        verbose_name='Test Type'
    )

    # NOTE that I probably will not put device in here explicitly
    # We should, at least, store the organ model here
    organ_model = models.ForeignKey(
        OrganModel,
        verbose_name='MPS Model',
        # Ought to be required
        # null=True,
        # blank=True,
        on_delete=models.CASCADE
    )

    # Will we also store the version?
    # Yes, but it will not be required
    organ_model_protocol = models.ForeignKey(
        OrganModelProtocol,
        verbose_name='MPS Model Version',
        # Not required
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    # TODO TODO TODO
    # ALL OF THIS COULD BE HANDLED MORE... DELICATELY
    def devolved_settings(self, criteria=DEFAULT_SETTING_CRITERIA):
        """Makes a tuple of cells (for comparison)"""
        setting_tuple = []
        attribute_getter = tuple_attrgetter(*criteria)
        for setting in self.assaygroupsetting_set.all():
            current_tuple = attribute_getter(setting)

            setting_tuple.append(current_tuple)

        return tuple(sorted(set(setting_tuple)))

    def stringify_settings(self, criteria=None):
        """Stringified cells for a setup"""
        settings = []
        for setting in self.assaygroupsetting_set.all():
            settings.append(setting.flex_string(criteria))

        if not settings:
            settings = ['-No Extra Settings-']

        return '\n'.join(collections.OrderedDict.fromkeys(settings))

    def devolved_cells(self, criteria=DEFAULT_CELL_CRITERIA):
        """Makes a tuple of cells (for comparison)"""
        cell_tuple = []
        attribute_getter = tuple_attrgetter(*criteria)
        for cell in self.assaygroupcell_set.all():
            current_tuple = attribute_getter(cell)

            cell_tuple.append(current_tuple)

        return tuple(sorted(set(cell_tuple)))

    def stringify_cells(self, criteria=None):
        """Stringified cells for a setup"""
        cells = []
        for cell in self.assaygroupcell_set.all():
            cells.append(cell.flex_string(criteria))

        if not cells:
            cells = ['-No Cell Samples-']

        return '\n'.join(collections.OrderedDict.fromkeys(cells))

    def devolved_compounds(self, criteria=DEFAULT_COMPOUND_CRITERIA):
        """Makes a tuple of compounds (for comparison)"""
        compound_tuple = []
        attribute_getter = tuple_attrgetter(*criteria)
        for compound in self.assaygroupcompound_set.all():
            current_tuple = attribute_getter(compound)

            compound_tuple.append(current_tuple)

        return tuple(sorted(set(compound_tuple)))

    def stringify_compounds(self, criteria=None):
        """Stringified cells for a setup"""
        compounds = []
        for compound in self.assaygroupcompound_set.all():
            compounds.append(compound.flex_string(criteria))

        if not compounds:
            compounds = ['-No Compounds-']

        return '\n'.join(collections.OrderedDict.fromkeys(compounds))

    def get_compound_profile(self, matrix_item_compound_post_filters):
        """Compound profile for determining concentration at time point"""
        compound_profile = []

        for compound in self.assaygroupcompound_set.all():
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
            # TODO May need to prefetch device (potential n+1)
            # 'Device': self.device.name,
            # ???
            # OBJECTIVELY BAD
            'Center': self.study.group.center_groups.first().name,
            # TODO May need to prefetch device (potential n+1)
            # 'Device': self.organ_model.device.name,
            'MPS User Group': self.study.group.name,
            'Study': self.get_hyperlinked_study(),
            # We don't get the matrix here, we cram it in from the matrix item
            # 'Matrix': 'TO BE REVISED TODO',
            'MPS Model': self.get_hyperlinked_model(),
            'MPS Model Version': self.get_hyperlinked_protocol(),
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
    # We can be sure that there will always be a Model
    def get_hyperlinked_model(self):
        return '<a target="_blank" href="{0}">{1}</a>'.format(self.organ_model.get_absolute_url(), self.organ_model.name)

    def get_hyperlinked_protocol(self):
        if self.organ_model_protocol:
            return '<a target="_blank" href="{0}">{1}</a>'.format(self.organ_model_protocol.get_absolute_url(), self.organ_model_protocol.name)
        else:
            return '-No MPS Model Version-'

    def get_hyperlinked_study(self):
        return '<a target="_blank" href="{0}">{1}</a>'.format(self.study.get_absolute_url(), self.study.name)

    def get_absolute_url(self):
        return reverse('assays-assaygroup-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class AssayGroupCompound(AbstractSetupCompound):
    class Meta(object):
        # Needs to include series
        unique_together = [
            (
                'group',
                'compound_instance',
                'concentration',
                'concentration_unit',
                'addition_time',
                'duration',
                'addition_location'
            )
        ]

    group = models.ForeignKey(
        AssayGroup,
        on_delete=models.CASCADE,
        verbose_name='Group'
    )


class AssayGroupCell(AbstractSetupCell):
    class Meta(object):
        unique_together = [
            (
                'group',
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

    group = models.ForeignKey(
        AssayGroup,
        on_delete=models.CASCADE,
        verbose_name='Group'
    )


class AssayGroupSetting(AbstractSetupSetting):
    class Meta(object):
        unique_together = [
            (
                'group',
                'setting',
                'addition_location',
                'unit',
                'addition_time',
                'duration',
            )
        ]

    group = models.ForeignKey(
        AssayGroup,
        on_delete=models.CASCADE,
        verbose_name='Group'
    )


# SUBJECT TO REMOVAL (MAY JUST USE ASSAY SETUP)
class AssayMatrixItem(FlaggableModel):
    class Meta(object):
        verbose_name = 'Study Item'
        # TODO Should this be by study or by matrix?
        unique_together = [
            ('study', 'name'),
            ('matrix', 'row_index', 'column_index')
        ]

    # Technically the study here is redundant (contained in matrix)
    study = models.ForeignKey(
        AssayStudy,
        on_delete=models.CASCADE,
        verbose_name='Study'
    )

    # Probably shouldn't use this trick!
    # This is in fact required, just listed as not being so due to quirk in cleaning
    matrix = models.ForeignKey(
        AssayMatrix,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='Matrix'
    )

    # This is in fact required, just listed as not being so due to quirk in cleaning
    # setup = models.ForeignKey('assays.AssaySetup', null=True, blank=True, on_delete=models.CASCADE)

    name = models.CharField(
        max_length=512,
        verbose_name='Name'
    )
    setup_date = models.DateField(
        help_text='YYYY-MM-DD',
        verbose_name='Setup Date'
    )

    # Do we still want this? Should it be changed?
    scientist = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Scientist'
    )
    notebook = models.CharField(
        max_length=256,
        blank=True,
        default='',
        verbose_name='Notebook'
    )
    # Should this be an integer field instead?
    notebook_page = models.CharField(
        max_length=256,
        blank=True,
        default='',
        verbose_name='Notebook Page'
    )
    notes = models.CharField(
        max_length=2048,
        blank=True,
        default='',
        verbose_name='Notes'
    )

    # If setups and items are to be merged, these are necessary
    row_index = models.IntegerField(verbose_name='Row Index')
    column_index = models.IntegerField(verbose_name='Column Index')

    # These are repetitive, as they can be found in the group
    # (With the exception of device, which is implicitly present via organ_model in group)
    device = models.ForeignKey(
        Microdevice,
        verbose_name='Device',
        on_delete=models.CASCADE
    )

    organ_model = models.ForeignKey(
        OrganModel,
        verbose_name='MPS Model',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    organ_model_protocol = models.ForeignKey(
        OrganModelProtocol,
        verbose_name='MPS Model Version',
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
        # default='control',
        verbose_name='Test Type'
    )

    # Tentative
    # Do we want a time on top of this?
    # failure_date = models.DateField(help_text='YYYY-MM-DD', null=True, blank=True)
    # Failure time in minutes
    failure_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Failure Time'
    )
    # Do we want this is to be table or a static list?
    failure_reason = models.ForeignKey(
        AssayFailureReason,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='Failure Reason'
    )

    # Link to a group
    # NEW SCHEMA
    group = models.ForeignKey(
        AssayGroup,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='Group'
    )

    def __str__(self):
        return str(self.name)

    # REVISED: Just alias to the respective group methods, maybe a bit clumsy
    def devolved_settings(self, criteria=DEFAULT_SETTING_CRITERIA):
        """Makes a tuple of cells (for comparison)"""
        if self.group:
            return self.group.devolved_settings(criteria)
        else:
            return tuple()

    def stringify_settings(self, criteria=None):
        """Stringified cells for a setup"""
        if self.group:
            return self.group.stringify_settings(criteria)
        else:
            return ''

    def devolved_cells(self, criteria=DEFAULT_CELL_CRITERIA):
        """Makes a tuple of cells (for comparison)"""
        if self.group:
            return self.group.devolved_cells(criteria)
        else:
            return tuple()

    def stringify_cells(self, criteria=None):
        """Stringified cells for a setup"""
        if self.group:
            return self.group.stringify_cells(criteria)
        else:
            return ''

    def devolved_compounds(self, criteria=DEFAULT_COMPOUND_CRITERIA):
        """Makes a tuple of compounds (for comparison)"""
        if self.group:
            return self.group.devolved_compounds(criteria)
        else:
            return tuple()

    def stringify_compounds(self, criteria=None):
        """Stringified cells for a setup"""
        if self.group:
            return self.group.stringify_compounds(criteria)
        else:
            return ''

    def get_compound_profile(self, matrix_item_compound_post_filters):
        """Compound profile for determining concentration at time point"""
        if self.group:
            return self.group.stringify_compounds(matrix_item_compound_post_filters)
        else:
            return []

    # OLD!
    # def devolved_settings(self, criteria=DEFAULT_SETTING_CRITERIA):
    #     """Makes a tuple of cells (for comparison)"""
    #     setting_tuple = []
    #     attribute_getter = tuple_attrgetter(*criteria)
    #     for setting in self.assaysetupsetting_set.all():
    #         current_tuple = attribute_getter(setting)

    #         setting_tuple.append(current_tuple)

    #     return tuple(sorted(set(setting_tuple)))

    # def stringify_settings(self, criteria=None):
    #     """Stringified cells for a setup"""
    #     settings = []
    #     for setting in self.assaysetupsetting_set.all():
    #         settings.append(setting.flex_string(criteria))

    #     if not settings:
    #         settings = ['-No Extra Settings-']

    #     return '\n'.join(collections.OrderedDict.fromkeys(settings))

    # def devolved_cells(self, criteria=DEFAULT_CELL_CRITERIA):
    #     """Makes a tuple of cells (for comparison)"""
    #     cell_tuple = []
    #     attribute_getter = tuple_attrgetter(*criteria)
    #     for cell in self.assaysetupcell_set.all():
    #         current_tuple = attribute_getter(cell)

    #         cell_tuple.append(current_tuple)

    #     return tuple(sorted(set(cell_tuple)))

    # def stringify_cells(self, criteria=None):
    #     """Stringified cells for a setup"""
    #     cells = []
    #     for cell in self.assaysetupcell_set.all():
    #         cells.append(cell.flex_string(criteria))

    #     if not cells:
    #         cells = ['-No Cell Samples-']

    #     return '\n'.join(collections.OrderedDict.fromkeys(cells))

    # def devolved_compounds(self, criteria=DEFAULT_COMPOUND_CRITERIA):
    #     """Makes a tuple of compounds (for comparison)"""
    #     compound_tuple = []
    #     attribute_getter = tuple_attrgetter(*criteria)
    #     for compound in self.assaysetupcompound_set.all():
    #         current_tuple = attribute_getter(compound)

    #         compound_tuple.append(current_tuple)

    #     return tuple(sorted(set(compound_tuple)))

    # def stringify_compounds(self, criteria=None):
    #     """Stringified cells for a setup"""
    #     compounds = []
    #     for compound in self.assaysetupcompound_set.all():
    #         compounds.append(compound.flex_string(criteria))

    #     if not compounds:
    #         compounds = ['-No Compounds-']

    #     return '\n'.join(collections.OrderedDict.fromkeys(compounds))

    # def get_compound_profile(self, matrix_item_compound_post_filters):
    #     """Compound profile for determining concentration at time point"""
    #     compound_profile = []

    #     for compound in self.assaysetupcompound_set.all():
    #         valid_compound = True

    #         # Makes sure the compound doesn't violate filters
    #         # This is because a compound can be excluded even if its parent matrix item isn't!
    #         for filter, values in list(matrix_item_compound_post_filters.items()):
    #             if str(attr_getter(compound, filter.split('__'))) not in values:
    #                 valid_compound = False
    #                 break

    #         compound_profile.append({
    #             'valid_compound': valid_compound,
    #             'addition_time': compound.addition_time,
    #             'duration': compound.duration,
    #             # SCALE INITIALLY
    #             'concentration': compound.concentration * compound.concentration_unit.scale_factor,
    #             # JUNK
    #             # 'scale_factor': compound.concentration_unit.scale_factor,
    #             'name': compound.compound_instance.compound.name,
    #             'base_unit': compound.concentration_unit.base_unit.unit,
    #         })

    #     return compound_profile

    # SPAGHETTI CODE
    # TERRIBLE, BLOATED
    # def quick_dic(
    #     self,
    #     compound_profile=False,
    #     matrix_item_compound_post_filters=None,
    #     criteria=None
    # ):
    #     if not criteria:
    #         criteria = {}
    #     dic = {
    #         # TODO May need to prefetch device (potential n+1)
    #         'Device': self.device.name,
    #         'MPS User Group': self.study.group.name,
    #         'Study': self.get_hyperlinked_study(),
    #         'Matrix': self.get_hyperlinked_matrix(),
    #         'MPS Model': self.get_hyperlinked_model_or_device(),
    #         'Compounds': self.stringify_compounds(criteria.get('compound', None)),
    #         'Cells': self.stringify_cells(criteria.get('cell', None)),
    #         'Settings': self.stringify_settings(criteria.get('setting', None)),
    #         'Trimmed Compounds': self.stringify_compounds({
    #             'compound_instance.compound_id': True,
    #             'concentration': True
    #         }),
    #         'Items with Same Treatment': [],
    #         'item_ids': []
    #     }

    #     if compound_profile:
    #         dic.update({
    #             'compound_profile': self.get_compound_profile(matrix_item_compound_post_filters)
    #         })

    #     return dic

    # Basically, stitch together the groups dictionary and the matrix's dictionary with this
    # A suboptimal approach: Revise when possible
    # Strictly speaking, we only *really* need the matrix
    # But perhaps something else will come up?
    def quick_dic(
        self,
        group_dic
    ):
        dic = copy.deepcopy(group_dic)
        dic.update({
            # Ought this be here? Should it likewise be a hyperlink?
            'Device': self.device.name,
            'Matrix': self.get_hyperlinked_matrix(),
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
        # Go to either the plate details or chip details
        # This is built-in to the absolute url
        return '<a target="_blank" href="{0}">{1}</a>'.format(self.matrix.get_absolute_url(), str(self.matrix))

    # TODO TODO TODO CHANGE
    def get_absolute_url(self):
        return '/assays/assaymatrixitem/{}/'.format(self.id)

    def get_post_submission_url(self):
        return self.study.get_absolute_url()

    def get_delete_url(self):
        return '{}delete/'.format(self.get_absolute_url())


# Controversy has arisen over whether to put this in an organ model or not
# This name is somewhat deceptive, it describes the quantity of cells, not a cell (rename please)
# DEPRECATED
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
    matrix_item = models.ForeignKey(
        AssayMatrixItem,
        on_delete=models.CASCADE,
        verbose_name='Matrix Item'
    )

    # No longer bound one-to-one
    # setup = models.ForeignKey('AssaySetup', on_delete=models.CASCADE)
    cell_sample = models.ForeignKey(
        'cellsamples.CellSample',
        on_delete=models.CASCADE,
        verbose_name='Cell Sample'
    )
    biosensor = models.ForeignKey(
        'cellsamples.Biosensor',
        on_delete=models.CASCADE,
        # Default is naive
        default=2,
        verbose_name='Biosensor'
    )
    density = models.FloatField(
        verbose_name='density',
        default=0
    )

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
    density_unit = models.ForeignKey(
        'assays.PhysicalUnits',
        on_delete=models.CASCADE,
        verbose_name='Density Unit'
    )
    passage = models.CharField(
        max_length=16,
        verbose_name='Passage#',
        blank=True,
        default=''
    )

    # DO WE WANT ADDITION TIME AND DURATION?
    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Addition Time'
    )

    # TODO TODO TODO DO WE WANT DURATION????
    # duration = models.FloatField(null=True, blank=True)

    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_location = models.ForeignKey(
        AssaySampleLocation,
        blank=True,
        default=1,
        on_delete=models.CASCADE,
        verbose_name='Addition Location'
    )

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
    study = models.ForeignKey(
        'assays.AssayStudy',
        on_delete=models.CASCADE,
        verbose_name='Study'
    )

    # Cross reference for users if study ids diverge
    cross_reference = models.CharField(
        max_length=255,
        default='',
        verbose_name='Cross Reference'
    )

    matrix_item = models.ForeignKey(
        'assays.AssayMatrixItem',
        on_delete=models.CASCADE,
        verbose_name='Matrix Item'
    )

    study_assay = models.ForeignKey(
        'assays.AssayStudyAssay',
        on_delete=models.CASCADE,
        verbose_name='Study Assay'
    )

    sample_location = models.ForeignKey(
        'assays.AssaySampleLocation',
        on_delete=models.CASCADE,
        verbose_name='Sample Location'
    )

    value = models.FloatField(
        null=True,
        verbose_name='Value'
    )

    # PLEASE NOTE THAT THIS IS IN MINUTES
    time = models.FloatField(
        default=0,
        verbose_name='Time'
    )

    # Caution flags for the user
    # Errs on the side of larger flags, currently
    caution_flag = models.CharField(
        max_length=255,
        default='',
        verbose_name='Caution Flag'
    )

    # TODO PROPOSED: CHANGE QUALITY TO TWO BOOLEANS: exclude and replaced
    # Kind of sloppy right now, I do not like it!
    # This value will act as quality control, if it evaluates True then the value is considered invalid
    # quality = models.CharField(max_length=20, default='')

    excluded = models.BooleanField(
        default=False,
        verbose_name='Excluded'
    )

    # TODO: replaced should be removed
    # It is confusing and functionally useless
    replaced = models.BooleanField(
        default=False,
        verbose_name='Replaced'
    )

    # This value contains notes for the data point
    notes = models.CharField(
        max_length=255,
        default='',
        verbose_name='Notes'
    )

    # Indicates what replicate this is (0 is for original)
    update_number = models.IntegerField(
        default=0,
        verbose_name='Update Number'
    )

    # DEFAULTS SUBJECT TO CHANGE
    assay_plate_id = models.CharField(
        max_length=255,
        default='N/A',
        verbose_name='Assay Plate ID'
    )
    assay_well_id = models.CharField(
        max_length=255,
        default='N/A',
        verbose_name='Assay Well ID'
    )

    # Indicates "technical replicates"
    # SUBJECT TO CHANGE
    replicate = models.CharField(
        max_length=255,
        default='',
        verbose_name='Replicate'
    )

    # OPTIONAL FOR NOW
    data_file_upload = models.ForeignKey(
        'assays.AssayDataFileUpload',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='Data File Upload'
    )

    # OPTIONAL
    subtarget = models.ForeignKey(
        AssaySubtarget,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='Subtarget'
    )

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
    matrix_item = models.ForeignKey(
        AssayMatrixItem,
        on_delete=models.CASCADE,
        verbose_name='Matrix Item'
    )

    # COMPOUND INSTANCE IS REQUIRED, however null=True was done to avoid a submission issue
    compound_instance = models.ForeignKey(
        'compounds.CompoundInstance',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='Compound Instance'
    )
    concentration = models.FloatField(verbose_name='Concentration')
    concentration_unit = models.ForeignKey(
        'assays.PhysicalUnits',
        verbose_name='Concentration Unit',
        on_delete=models.CASCADE,
    )

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    addition_time = models.FloatField(
        blank=True,
        verbose_name='Addition Time'
    )

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    duration = models.FloatField(
        blank=True,
        verbose_name='Duration'
    )

    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_location = models.ForeignKey(
        AssaySampleLocation,
        blank=True,
        default=1,
        on_delete=models.CASCADE,
        verbose_name='Addition Location'
    )

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
    study = models.ForeignKey(
        AssayStudy,
        on_delete=models.CASCADE,
        verbose_name='Study'
    )

    description = models.CharField(
        max_length=1000,
        help_text='Describes the contents of the supporting data file',
        verbose_name='Description'
    )

    # Not named file in order to avoid shadowing
    supporting_data = models.FileField(
        upload_to=study_supporting_data_location,
        help_text='Supporting Data for Study',
        verbose_name='File'
    )


# TODO Probably should have a ControlledVocabularyMixin for defining name and description consistently
class AssaySetting(FrontEndModel, LockableModel):
    """Defines a type of setting (flowrate etc.)"""

    class Meta(object):
        verbose_name = 'Setting'

    name = models.CharField(
        max_length=512,
        unique=True,
        verbose_name='Name'
    )
    description = models.CharField(
        max_length=2000,
        verbose_name='Description'
    )

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
    matrix_item = models.ForeignKey(
        AssayMatrixItem,
        on_delete=models.CASCADE,
        verbose_name='Matrix Item'
    )

    # No longer one-to-one
    # setup = models.ForeignKey('assays.AssaySetup', on_delete=models.CASCADE)
    setting = models.ForeignKey(
        'assays.AssaySetting',
        on_delete=models.CASCADE,
        verbose_name='Setting'
    )
    # DEFAULTS TO NONE, BUT IS REQUIRED
    unit = models.ForeignKey(
        'assays.PhysicalUnits',
        blank=True,
        default=14,
        on_delete=models.CASCADE,
        verbose_name='Unit'
    )
    value = models.CharField(
        max_length=255,
        verbose_name='Value'
    )

    # Will we include these??
    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    addition_time = models.FloatField(
        blank=True,
        verbose_name='Addition Time'
    )

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    duration = models.FloatField(
        blank=True,
        verbose_name='Duration'
    )

    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_location = models.ForeignKey(
        AssaySampleLocation,
        blank=True,
        default=1,
        on_delete=models.CASCADE,
        verbose_name='Addition Location'
    )

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

    study = models.ForeignKey(
        AssayStudy,
        on_delete=models.CASCADE,
        verbose_name='Study'
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        verbose_name='Group'
    )
    # Explicitly declared rather than from inheritance to avoid unecessary fields
    signed_off_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='Signed Off By'
    )
    signed_off_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Signed Off Date'
    )

    signed_off_notes = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Signed Off Notes'
    )

    sign_off_required = models.BooleanField(
        default=True,
        verbose_name='Signed Off Required'
    )


class AssayStudyAssay(models.Model):
    """Specific assays used in the 'inlines'"""
    study = models.ForeignKey(
        AssayStudy,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='Study'
    )
    # study_new = models.ForeignKey('assays.AssayStudy', null=True, blank=True, on_delete=models.CASCADE)
    target = models.ForeignKey(
        AssayTarget,
        on_delete=models.CASCADE,
        verbose_name='Target'
    )
    method = models.ForeignKey(
        AssayMethod,
        on_delete=models.CASCADE,
        verbose_name='Method'
    )
    # Name of model "PhysicalUnits" should be renamed, methinks
    unit = models.ForeignKey(
        PhysicalUnits,
        on_delete=models.CASCADE,
        verbose_name='Unit'
    )

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


class AssayImageSetting(FlaggableModel):
    # Requested, not sure how useful
    # May want to remove soon, why have this be specific to a study? Deletion cascade?
    study = models.ForeignKey(
        AssayStudy,
        on_delete=models.CASCADE,
        verbose_name='Study'
    )
    # This is necessary in TongYing's scheme, but it is kind of confusing in a way
    label_id = models.CharField(
        max_length=40,
        default='',
        blank=True,
        verbose_name='Label ID'
    )
    label_name = models.CharField(
        max_length=255,
        verbose_name='Label Name'
    )
    label_description = models.CharField(
        max_length=500,
        default='',
        blank=True,
        verbose_name='Label Description'
    )
    wave_length = models.CharField(
        max_length=255,
        verbose_name='Wave Length'
    )
    magnification = models.CharField(
        max_length=40,
        verbose_name='Magnification'
    )
    resolution = models.CharField(
        max_length=40,
        verbose_name='Resolution'
    )
    resolution_unit = models.CharField(
        max_length=40,
        verbose_name='Resolution Unit'
    )
    # May be useful later
    notes = models.CharField(
        max_length=500,
        default='',
        blank=True,
        verbose_name='Notes'
    )
    color_mapping = models.CharField(
        max_length=255,
        default='',
        blank=True,
        verbose_name='Color Mapping'
    )

    def __str__(self):
        return '{} {}'.format(self.study.name, self.label_name)


class AssayImage(models.Model):
    # May want to have an FK to study for convenience?
    # YEAH: WE SHOULD ADD STUDY HERE METHINKS, WHY EVER NOT?!
    # study = models.ForeignKey(AssayStudy, on_delete=models.CASCADE)
    # The associated item
    matrix_item = models.ForeignKey(
        AssayMatrixItem,
        on_delete=models.CASCADE,
        verbose_name='Matrix Item'
    )
    # The file name
    file_name = models.CharField(
        max_length=255,
        verbose_name='File Name'
    )
    field = models.CharField(
        max_length=255,
        verbose_name='Field'
    )
    field_description = models.CharField(
        max_length=500,
        default='',
        verbose_name='Field Description'
    )
    # Stored in minutes
    time = models.FloatField(verbose_name='Time')
    # Possibly used later, who knows
    assay_plate_id = models.CharField(
        max_length=255,
        default='N/A',
        verbose_name='Assay Plate ID'
    )
    assay_well_id = models.CharField(
        max_length=255,
        default='N/A',
        verbose_name='Assay Well ID'
    )
    # PLEASE NOTE THAT I USE TARGET AND METHOD SEPARATE FROM ASSAY INSTANCE
    method = models.ForeignKey(
        AssayMethod,
        on_delete=models.CASCADE,
        verbose_name='Method'
    )
    target = models.ForeignKey(
        AssayTarget,
        on_delete=models.CASCADE,
        verbose_name='Target'
    )
    # May become useful
    subtarget = models.ForeignKey(
        AssaySubtarget,
        on_delete=models.CASCADE,
        verbose_name='Subtarget'
    )
    sample_location = models.ForeignKey(
        AssaySampleLocation,
        on_delete=models.CASCADE,
        verbose_name='Sample Location'
    )
    notes = models.CharField(
        max_length=500,
        default='',
        verbose_name='Notes'
    )
    replicate = models.CharField(
        max_length=255,
        default='',
        verbose_name='Replicate'
    )
    setting = models.ForeignKey(
        AssayImageSetting,
        on_delete=models.CASCADE,
        verbose_name='Setting'
    )

    # ?
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

    class Meta(object):
        verbose_name = 'Study Set'

    # Name for the set
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Name'
    )
    # Description
    description = models.CharField(
        max_length=2000,
        default='',
        blank=True,
        verbose_name='Description'
    )

    studies = models.ManyToManyField(
        AssayStudy,
        verbose_name='Studies'
    )
    assays = models.ManyToManyField(
        AssayStudyAssay,
        verbose_name='Assays'
    )

    def get_post_submission_url(self):
        return self.get_absolute_url()

    def get_absolute_url(self):
        return '/assays/assaystudyset/{}/'.format(self.id)

    def __str__(self):
        return self.name


class AssayReference(FrontEndModel, FlaggableModel):

    class Meta(object):
        verbose_name = 'Reference'

    pubmed_id = models.CharField(
        verbose_name='PubMed ID',
        max_length=40,
        blank=True,
        default='N/A'
    )
    title = models.CharField(
        verbose_name='Title',
        max_length=2000,
        unique=True
    )
    authors = models.CharField(
        verbose_name='Authors',
        max_length=2000
    )
    abstract = models.CharField(
        verbose_name='Abstract',
        max_length=4000,
        blank=True,
        default=''
    )
    publication = models.CharField(
        verbose_name='Publication',
        max_length=255
    )
    year = models.CharField(
        verbose_name='Year',
        max_length=4
    )
    doi = models.CharField(
        verbose_name='DOI',
        max_length=100,
        blank=True,
        default='N/A'
    )

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

    # CRUDE
    def get_string_for_processing(self):
        return COMBINED_VALUE_DELIMITER.join(str(x) for x in [
            self.authors,
            self.title,
            self.pubmed_id
        ])

    def __str__(self):
        return '{}. {}. {}. {}. doi:{}. PMID:{}'.format(self.authors, self.title, self.publication, self.year, self.doi, self.pubmed_id)

    def get_post_submission_url(self):
        return '/assays/assayreference/'

    def get_absolute_url(self):
        return '/assays/assayreference/{}/'.format(self.id)

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

    reference = models.ForeignKey(
        AssayReference,
        on_delete=models.CASCADE,
        verbose_name='Reference'
    )
    reference_for = models.ForeignKey(
        AssayStudy,
        on_delete=models.CASCADE,
        verbose_name='Reference For'
    )


# TODO TODO TODO
class AssayStudySetReference(models.Model):
    class Meta(object):
        unique_together = [
            (
                'reference',
                'reference_for'
            )
        ]

    reference = models.ForeignKey(
        AssayReference,
        on_delete=models.CASCADE,
        verbose_name='Reference'
    )
    reference_for = models.ForeignKey(
        AssayStudySet,
        on_delete=models.CASCADE,
        verbose_name='Reference For'
    )


# ADMIN ONLY
class AssayCategory(FlaggableModel):
    """Describes a genre of assay"""

    class Meta(object):
        verbose_name = 'Assay Category'
        verbose_name_plural = 'Assay Categories'

    name = models.CharField(
        max_length=512,
        unique=True,
        verbose_name='Name'
    )
    description = models.CharField(
        max_length=2000,
        verbose_name='Description'
    )

    # List of all related targets
    targets = models.ManyToManyField(
        'assays.AssayTarget',
        verbose_name='Targets'
    )

    def __str__(self):
        return '{}'.format(self.name)


# sck - ASSAY PLATE MAP SECTION
assay_plate_reader_time_unit_choices = [
    ('day', 'Day'),
    ('hour', 'Hour'),
    ('minute', 'Minute')
]
assay_plate_reader_main_well_use_choices = [
    ('sample', 'Sample'),
    ('standard', 'Standard'),
    ('blank', 'Blank'),
    ('empty', 'Empty/Unused')
]
# here here if decide to do this later
assay_plate_reader_blank_well_use_choices = [
    ('sample_blank', 'Sample Blank'),
    ('standard_blank', 'Standard Blank')
]
# in some places, need specific lists, but ultimately, each well in a plate gets only ONE
# well use assigned to it that will be used in logic downstream that will be this cumulative list
assay_plate_reader_cumulative_well_use_choices = [
    ('sample', 'Sample'),
    ('standard', 'Standard'),
    ('blank', 'Blank'),
    ('empty', 'Empty/Unused'),
    # here here if decide to do this - this will degrade form load performance
    # ('sample_blank', 'Sample Blank'),
    # ('standard_blank', 'Standard Blank')
]

assay_plate_reader_volume_unit_choices = [
    ('mL', 'mL'),
    ('µL', 'µL'),
    ('nL', 'nL')
]
assay_plate_reader_file_delimiter_choices = [
    ('comma', 'comma'),
    ('space', 'space'),
    ('tab', 'tab')
]
# PI indicated only need to build for these three sizes
# general treatment of sizes here, but some size HARDCODing throughout...search for 24, 96, or 384
assay_plate_reader_map_info_plate_size_choices_list = [24, 96, 384]
assay_plate_reader_map_info_plate_size_choices = [
    (24, '24 Well Plate'),
    (96, '96 Well Plate'),
    (384, '384 Well Plate')
]
assay_plate_reader_map_info_row_labels_384 = [
'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P'
]
assay_plate_reader_map_info_col_labels_384 = [
'1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24'
]
# ['A', 'B', 'C', 'D'];
# ['1', '2', '3', '4', '5', '6'];
assay_plate_reader_map_info_row_labels_24 = assay_plate_reader_map_info_row_labels_384[:4]
assay_plate_reader_map_info_col_labels_24 = assay_plate_reader_map_info_col_labels_384[:6]

# ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
# ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];
assay_plate_reader_map_info_row_labels_96 = assay_plate_reader_map_info_row_labels_384[:8]
assay_plate_reader_map_info_col_labels_96 = assay_plate_reader_map_info_col_labels_384[:12]

assay_plate_reader_map_info_row_contents_24 = [
["A1", "A2", "A3", "A4", "A5", "A6"],
["B1", "B2", "B3", "B4", "B5", "B6"],
["C1", "C2", "C3", "C4", "C5", "C6"],
["D1", "D2", "D3", "D4", "D5", "D6"]
]
assay_plate_reader_map_info_row_contents_96 = [
["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11", "A12"],
["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "B11", "B12"],
["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12"],
["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12"],
["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "E10", "E11", "E12"],
["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"],
["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11", "G12"],
["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9", "H10", "H11", "H12"]
]
assay_plate_reader_map_info_row_contents_384 = [
["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11", "A12", "A13", "A14", "A15", "A16", "A17", "A18", "A19", "A20", "A21", "A22", "A23", "A24"],
["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "B11", "B12", "B13", "B14", "B15", "B16", "B17", "B18", "B19", "B20", "B21", "B22", "B23", "B24"],
["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18", "C19", "C20", "C21", "C22", "C23", "C24"],
["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12", "D13", "D14", "D15", "D16", "D17", "D18", "D19", "D20", "D21", "D22", "D23", "D24"],
["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "E10", "E11", "E12", "E13", "E14", "E15", "E16", "E17", "E18", "E19", "E20", "E21", "E22", "E23", "E24"],
["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "F13", "F14", "F15", "F16", "F17", "F18", "F19", "F20", "F21", "F22", "F23", "F24"],
["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11", "G12", "G13", "G14", "G15", "G16", "G17", "G18", "G19", "G20", "G21", "G22", "G23", "G24"],
["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9", "H10", "H11", "H12", "H13", "H14", "H15", "H16", "H17", "H18", "H19", "H20", "H21", "H22", "H23", "H24"],
["I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9", "I10", "I11", "I12", "I13", "I14", "I15", "I16", "I17", "I18", "I19", "I20", "I21", "I22", "I23", "I24"],
["J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8", "J9", "J10", "J11", "J12", "J13", "J14", "J15", "J16", "J17", "J18", "J19", "J20", "J21", "J22", "J23", "J24"],
["K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9", "K10", "K11", "K12", "K13", "K14", "K15", "K16", "K17", "K18", "K19", "K20", "K21", "K22", "K23", "K24"],
["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9", "L10", "L11", "L12", "L13", "L14", "L15", "L16", "L17", "L18", "L19", "L20", "L21", "L22", "L23", "L24"],
["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10", "M11", "M12", "M13", "M14", "M15", "M16", "M17", "M18", "M19", "M20", "M21", "M22", "M23", "M24"],
["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8", "N9", "N10", "N11", "N12", "N13", "N14", "N15", "N16", "N17", "N18", "N19", "N20", "N21", "N22", "N23", "N24"],
["O1", "O2", "O3", "O4", "O5", "O6", "O7", "O8", "O9", "O10", "O11", "O12", "O13", "O14", "O15", "O16", "O17", "O18", "O19", "O20", "O21", "O22", "O23", "O24"],
["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10", "P11", "P12", "P13", "P14", "P15", "P16", "P17", "P18", "P19", "P20", "P21", "P22", "P23", "P24"]
]
assay_plate_reader_map_info_shape_col_dict = {24: len(assay_plate_reader_map_info_row_contents_24[0]),
                                              96: len(assay_plate_reader_map_info_row_contents_96[0]),
                                              384: len(assay_plate_reader_map_info_row_contents_384[0])}
assay_plate_reader_map_info_shape_row_dict = {24: len(assay_plate_reader_map_info_row_contents_24),
                                              96: len(assay_plate_reader_map_info_row_contents_96),
                                              384: len(assay_plate_reader_map_info_row_contents_384)}


class AssayPlateReaderMap(FlaggableModel):
    """Assay Plate Reader Map for processing plate reader data."""

    class Meta(object):
        verbose_name = 'Assay Plate Reader Map'
        # Singular plural verbose name?
        # verbose_name_plural = 'Assay Plate Reader Map'
        # unique_together = [
        #     ('study', 'name')
        # ]

    study = models.ForeignKey(
        AssayStudy,
        blank=True,
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=255,
        blank=True
    )
    description = models.CharField(
        max_length=2000,
        blank=True, default=''
    )
    device = models.IntegerField(
        default=96,
        blank=True,
        choices=assay_plate_reader_map_info_plate_size_choices
    )
    # default and file sample time and collection time unit
    time_unit = models.CharField(
        max_length=8,
        default='day',
        null=True,
        blank=True,
        choices=assay_plate_reader_time_unit_choices
    )
    volume_unit = models.CharField(
        max_length=2,
        default='mL',
        null=True,
        blank=True,
        choices=assay_plate_reader_volume_unit_choices
    )
    well_volume = models.FloatField(null=True, blank=True)
    cell_count = models.FloatField(null=True, blank=True)
    study_assay = models.ForeignKey(
        'assays.AssayStudyAssay',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    standard_unit = models.ForeignKey(
        PhysicalUnits,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    standard_molecular_weight = models.FloatField(null=True, blank=True)

    def __str__(self):
        # return '{0}'.format(self.name)
        return '{0} ({1})'.format(self.name, self.device)

    def get_absolute_url(self):
        return '/assays/assayplatereadermap/{}/'.format(self.id)

    def get_post_submission_url(self):
        return '/assays/assaystudy/{}/assayplatereadermap/'.format(self.study_id)

    def get_delete_url(self):
        return '{}delete/'.format(self.get_absolute_url())


# Get for default plate reader file upload description
def set_default_description():
    return "file added - " + datetime.datetime.now().strftime("%Y%m%d") + "-" + datetime.datetime.now().strftime('%H:%M:%S')


# Get upload file location (not needed, but migrations choke when removed)
# def upload_plate_reader_file_location(instance, filename):
#     return '/'.join(['plate_reader_file', str(instance.id), filename])


# 20201104 needed to be a lockable model so permissions will allow for file deletion when not superuser
class AssayPlateReaderMapDataFile(LockableModel):
    """Assay plate reader data file for plate reader integration."""

    class Meta(object):
        verbose_name = 'Assay Plate Reader Imported Data File'
        unique_together = [
            ('study', 'plate_reader_file', 'description')
        ]

    study = models.ForeignKey(
        AssayStudy,
        blank=True,
        on_delete=models.CASCADE
    )
    description = models.CharField(
        max_length=2000,
        blank=True,
        null=True,
        default=set_default_description()
    )
    plate_reader_file = models.FileField(
        upload_to='over_write_in_views.py',
        verbose_name='Plate Reader Data File',
        blank=True,
        null=True
    )
    file_delimiter = models.CharField(
        max_length=8,
        default='tab', blank=True,
        choices=assay_plate_reader_file_delimiter_choices
    )
    # using to check that the user can see plate size selected when uploading data (help will adding plate map)
    upload_plate_size = models.IntegerField(
        blank=True,
        null=True,
        choices=assay_plate_reader_map_info_plate_size_choices
    )

    def __str__(self):
        return '{0}'.format(self.id)

    def get_absolute_url(self):
        return '/assays/assayplatereaderfile/{}/'.format(self.id)

    def get_post_submission_url(self):
        return '/assays/assaystudy/{}/assayplatereaderfile/'.format(self.study_id)

    def get_post_add_submission_url(self):
        return '/assays/assayplatereaderfile/{}/update'.format(self.id)

    def get_delete_url(self):
        return '{}delete/'.format(self.get_absolute_url())


class AssayPlateReaderMapDataFileBlock(models.Model):
    """Information about each block of data in an assay plate reader imported data file."""

    class Meta(object):
        verbose_name = 'Assay Plate Reader File Data Block'
        # the unique together was causing problems when editing existing data blocks
        # not sure the file was being used in the evaluation
        # unique_together = [
        #     ('study', 'data_block', 'assayplatereadermapdatafile'),
        # ]

    study = models.ForeignKey(
        AssayStudy,
        blank=True,
        on_delete=models.CASCADE
    )
    assayplatereadermap = models.ForeignKey(
        AssayPlateReaderMap,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    assayplatereadermapdatafile = models.ForeignKey(
        AssayPlateReaderMapDataFile,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    # assayplatereadermapdataprocessing = models.ForeignKey(
    #     AssayPlateReaderMapDataProcessing,
    #     null=True,
    #     blank=True,
    #     on_delete=models.CASCADE)

    # not sure going to use this...so far, not, putting it in the file to send to study instead
    # may want to make a custom save that writes it here too...
    data_processing_parsable = models.CharField(
        max_length=2000,
        blank=True,
        default=''
    )

    data_block = models.IntegerField(
        default=999,
        null=True
    )
    data_block_metadata = models.CharField(
        max_length=255,
        blank=True
    )
    line_start = models.IntegerField(
        default=999,
        null=True
    )
    line_end = models.IntegerField(
        default=999,
        null=True
    )
    delimited_start = models.IntegerField(
        default=999,
        null=True
    )
    delimited_end = models.IntegerField(
        default=999,
        null=True
    )
    # this value with be used instead of the plate reader map sample time, if provided during file upload.
    over_write_sample_time = models.IntegerField(
        null=True,
        blank=True
    )

    def __str__(self):
        return '{0}'.format(self.data_block)


class AssayPlateReaderMapItem(models.Model):
    """Model for each well in a plate map (item)."""

    class Meta(object):
        verbose_name = 'Assay Plate Reader Map Item'
        unique_together = [
            ('study', 'assayplatereadermap', 'plate_index'),
        ]

    study = models.ForeignKey(
        AssayStudy,
        blank=True,
        on_delete=models.CASCADE
    )
    assayplatereadermap = models.ForeignKey(
        AssayPlateReaderMap,
        on_delete=models.CASCADE
    )
    matrix_item = models.ForeignKey(
        AssayMatrixItem,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    location = models.ForeignKey(
        'AssaySampleLocation',
        null=True,
        blank=True,
        default=0,
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        default="none"
    )
    # legacy - remove when ready (column and row)
    # row_index = models.IntegerField(
    #     default=999,
    #     blank=True
    # )
    # column_index = models.IntegerField(
    #     default=999,
    #     blank=True
    # )
    plate_index = models.IntegerField(
        default=999,
        blank=True
    )
    # each well on the plate will have a specific well use (only one) from the cumulative list
    # in some of the GUI, the list is separated logically for easier entry by user
    well_use = models.CharField(
        verbose_name='Well Use',
        max_length=8,
        default='empty',
        blank=True,
        choices=assay_plate_reader_cumulative_well_use_choices
    )
    # should be the standard concentration input (associated unit should be in the plate map model)
    standard_value = models.FloatField(
        default=0,
        null=True,
        blank=True
    )
    dilution_factor = models.FloatField(
        default=1,
        null=True,
        blank=True
    )
    collection_volume = models.FloatField(
        default=1,
        null=True,
        blank=True
    )
    collection_time = models.FloatField(
        default=1,
        null=True,
        blank=True
    )
    # default sample time - show until file added and data uploaded
    default_time = models.FloatField(
        default=0,
        null=True,
        blank=True
    )

    def __str__(self):
        return '{0}'.format(self.name)

    def get_absolute_url(self):
        return '/assays/assayplatereadermapitem/{}/'.format(self.id)

    def get_post_submission_url(self):
        return '/assays/assayplatereadermapitem/'

    def get_delete_url(self):
        return '{}delete/'.format(self.get_absolute_url())


class AssayPlateReaderMapItemValue(models.Model):
    """Model to hold multiple values (and sample times) for each well in a plate."""

    class Meta(object):
        verbose_name = 'Assay Plate Reader Map Raw Value'
        unique_together = [
            ('study', 'assayplatereadermap', 'assayplatereadermapdatafile', 'assayplatereadermapdatafileblock', 'assayplatereadermapitem', 'time'),
        ]

    study = models.ForeignKey(
        AssayStudy,
        blank=True,
        on_delete=models.CASCADE
    )
    assayplatereadermap = models.ForeignKey(
        AssayPlateReaderMap,
        on_delete=models.CASCADE
    )
    assayplatereadermapdatafile = models.ForeignKey(
        AssayPlateReaderMapDataFile,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    assayplatereadermapdatafileblock = models.ForeignKey(
        AssayPlateReaderMapDataFileBlock,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    assayplatereadermapitem = models.ForeignKey(
        AssayPlateReaderMapItem,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    # 20200522 removing since redid logic
    # plate_index = models.IntegerField(
    #     default=999,
    #     blank=True
    # )
    # well_use = models.CharField(
    #     verbose_name='Well Use',
    #     max_length=8,
    #     default='empty',
    #     blank=True,
    #     choices=assay_plate_reader_cumulative_well_use_choices
    # )

    # raw value read from the plate for all wells in this plate
    raw_value = models.FloatField(
        null=True,
        blank=True
    )
    time = models.FloatField(
        default=0,
        null=True,
        blank=True
    )

    # when commented this out, got a save error. Must have a reference somewhere I didn't find....
    replaced = models.BooleanField(
        default=False
    )

    def __str__(self):
        return '{0}'.format(self.id)

    def get_absolute_url(self):
        return '/assays/assayplatereadermapitem/{}/'.format(self.id)


    def get_post_submission_url(self):
        return '/assays/assayplatereadermapitem/'

    def get_delete_url(self):
        return '{}delete/'.format(self.get_absolute_url())

##### END ASSAY PLATE MAP SECTION


class SpeciesParameters(models.Model):
    species = models.ForeignKey(
        'drugtrials.Species',
        on_delete=models.CASCADE,
        verbose_name='Species'
    )
    organ = models.ForeignKey(
        'cellsamples.Organ',
        on_delete=models.CASCADE,
        verbose_name='Organ'
    )
    reference = models.ForeignKey(
        AssayReference,
        on_delete=models.CASCADE,
        verbose_name='Reference'
    )
    body_mass = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Body Mass (kg)',
        help_text='Body Mass'
    )
    total_organ_weight = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Total Organ Weight (g)',
        help_text='Total Organ Weight'
    )
    organ_tissue = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Organ Tissue (cells/g)',
        help_text='Organ Tissue'
    )
    plasma_volume = models.FloatField(
        null=True,
        blank=True,
        verbose_name='VP (L)',
        help_text='Plasma Volume'
    )
    vp = models.FloatField(
        null=True,
        blank=True,
        verbose_name='VP (L/kg)',
        help_text='Plasma Volume'
    )
    ve = models.FloatField(
        null=True,
        blank=True,
        verbose_name='VE (L/kg)',
        help_text='Extracellular Volume'
    )
    rei = models.FloatField(
        null=True,
        blank=True,
        verbose_name='RE/I',
        help_text='Extravascular/Intravascular Ratio'
    )
    vr = models.FloatField(
        null=True,
        blank=True,
        verbose_name='VR',
        help_text='Volume of Drug Distribution Minus Extracellular Space'
    )
    absorptive_surface_area = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Absorptive Surface Area',
        help_text='Absorptive Surface Area (m^2)'
    )
    ki = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Ki (1/min)',
        help_text='Inverse of Small Intestine Transit Time'
    )

    def __str__(self):
        return '{} - {} ({})'.format(self.species, self.organ, self.reference)


class AssayOmicAnalysisTarget(models.Model):
    """A cross reference for omic file headers """
    # this table is queried in the code to return the 'name', which = import file header

    class Meta(object):
        verbose_name = 'Assay Omic Analysis Target'
        unique_together = [
            ('name', 'data_type', 'method'),
        ]
    # The omic data upload will search this table for the name (header) and data_type to return a list to work with
    name = models.CharField(
        max_length=512,
        help_text='Input File Headers for omics upload (e.g. baseMean, normscount). Do not change without checking with omic upload developer.',
        verbose_name='Input File Headers'
    )
    data_type = models.CharField(
        max_length=25,
        default='log2fc',
        help_text='Data Type (must match exactly the hardcoded assay omic data type choices). Do not change without checking with omic upload developer.',
        verbose_name='Data Type'
    )
    # need this here to query the this table in the code
    method = models.ForeignKey(
        AssayMethod,
        on_delete=models.CASCADE,
        help_text='Data Analysis Method - The method (i.e. data processing tool, pipeline, etc.) used to process data. Do not change without checking with omic upload developer.',
        verbose_name='Data Analysis Method'
    )
    target = models.ForeignKey(
        AssayTarget,
        on_delete=models.CASCADE,
        help_text='Data Analysis Target - computational feature.',
        verbose_name='Data Analysis Target'
    )
    # not sure if need the unit but keep for now
    unit = models.ForeignKey(
        PhysicalUnits,
        on_delete=models.CASCADE,
        help_text='Data Analysis Unit - unit of computational feature.',
        verbose_name='Data Analysis Unit'
    )

    def __str__(self):
        return '{0}'.format(self.name)


# the keys from this dict are used in other places (hardcoded)
# and in the AssayOmicAnalysisTarget table
# be mindful of changing them
# OMIC RULES - do not change assay_omic_data_type_choices unless change EVERYWHERE they are hardcoded!
assay_omic_data_type_choices = [
    ('log2fc', 'Log 2 Fold Change'),
    ('normcounts', 'Normalized Counts'),
    ('rawcounts', 'Raw Counts')
]

assay_omic_file_header_type_choices = [
    ('well', 'Well Names (e.g., A01, A02, DA01, etc)'),
    ('sample', 'Sample Names'),
    ('target', 'Computational Targets'),
    ('other', 'Something Else')
]

# This is the why we allowed grouping while Luke was finishing the treatment group naming
# probably will not need this, but keep unitl we are sure we do not want a separate group
# class AssayOmicDataGroup(LockableModel):
#     """Assay omic data groups - pk used to tie chip and sample metadata to a data group."""
#     # plan is to replace this with "treatment groups"
#
#     class Meta(object):
#         verbose_name = 'Assay Omic Data Group'
#         verbose_name_plural = 'Assay Omic Data Groups'
#         unique_together = [('study', 'name')]
#
#     study = models.ForeignKey(
#         AssayStudy,
#         default=1,
#         on_delete=models.CASCADE,
#         verbose_name='This Study'
#     )
#     name = models.CharField(
#         max_length=100,
#         default=set_default_description(),
#         verbose_name='Group Name'
#     )
#     number = models.IntegerField(
#         default=999,
#         blank=True,
#         verbose_name='Group Number'
#     )
#
#     def __str__(self):
#         return '{}'.format(self.name)

assay_omic_gene_name_choices = [
    ('temposeq_probe', 'TempO-Seq Probe ID'),
    ('entrez_gene', 'NCBI Gene ID (Entrez)'),
    ('ensembl_gene', 'Ensemble Gene ID'),
    ('refseq_gene', 'RefSeq ID'),
    ('affymerix_probe', 'Affymerix Probeset ID'),
    ('gene_symbol', 'Gene Symbol')
]

# Get omic data file location
def omic_data_file_location(instance, filename):
    return '/'.join(['omic_data_file', str(instance.study_id), filename])


# this is for all omics files
# we were going to separate into two group data and one group data
# but the project PI strongly opposed this idea (he wanted all the files together)
# if changes mind later, leave this for two group data and make a new one for count data without the group, time, and location metadata (since that will go in a separate table
class AssayOmicDataFileUpload(LockableModel):
    """Assay omic data - usually export from a DEG tool."""

    class Meta(object):
        verbose_name = 'Assay Omic Data File Upload'
        verbose_name_plural = 'Assay Omic Data File Uploads'
        unique_together = [('study', 'omic_data_file')]

    study = models.ForeignKey(
        AssayStudy,
        on_delete=models.CASCADE,
        verbose_name='This Study'
    )

    description = models.CharField(
        max_length=2000,
        default=set_default_description(),
        help_text='A description of the data being uploaded in this file (e.g., "Treated vrs Control" or "Treated with 1uM Calcifidiol".',
        verbose_name='Data Description'
    )
    # if not required, and user tries to have two empty, will get error
    omic_data_file = models.FileField(
        upload_to=omic_data_file_location,
        help_text='The omic data file to be uploaded to the database.',
        verbose_name='Omic Data File*'
    )

    name_reference = models.CharField(
        max_length=25,
        default='temposeq_probe',
        choices=assay_omic_gene_name_choices,
        help_text='The gene or probe ID (nomenclature used in omic file).',
        verbose_name='Gene or Probe ID'
    )

    study_assay = models.ForeignKey(
        'assays.AssayStudyAssay',
        on_delete=models.CASCADE,
        help_text='The category, Target, Method, Unit as entered in the Study Assay Setup.',
        verbose_name='Upload File Assay'
    )
    # this is also stored, as part of the link to AssayOmicAnalysisTarget, in the data point file
    # it is here only to limit the list of targets selected from the AssayOmicAnalysisTarget table
    # could make is just a form field, but, it may be helpful to have it stored here
    # could remove it from one or the other, maybe, but leave for now
    analysis_method = models.ForeignKey(
        AssayMethod,
        on_delete=models.CASCADE,
        help_text='The data analysis method or computational tool (e.g. DESeq2).',
        verbose_name='Data Analysis Method'
    )

    data_type = models.CharField(
        max_length=25,
        default='log2fc',
        choices=assay_omic_data_type_choices,
        help_text='The type of the computational results.',
        verbose_name='Data Type'
    )

    # these were during development when we were using separate groups
    # probably will not need again, but keep just in case
    # # data groups could be empty for the norm count and raw count data
    # group_1 = models.ForeignKey(
    #     AssayOmicDataGroup,
    #     null=True,
    #     blank=True,
    #     on_delete=models.CASCADE,
    #     related_name='group_1',
    #     help_text='Data Processing Group 1',
    #     verbose_name='Group 1*'
    # )
    # group_2 = models.ForeignKey(
    #     AssayOmicDataGroup,
    #     null=True,
    #     blank=True,
    #     on_delete=models.CASCADE,
    #     related_name='group_2',
    #     help_text='Data Processing Group 2',
    #     verbose_name='Group 2*'
    # )

    # data groups WILL be empty for the norm count and raw count data (not stored for counts data, can pull from study setup)
    # when they are visible on the form, they are required, so put the * here
    group_1 = models.ForeignKey(
        AssayGroup,
        on_delete=models.CASCADE,
        related_name='group_1',
        null=True,
        blank=True,
        help_text='The data analysis test group.',
        verbose_name='Test Group*'
    )
    group_2 = models.ForeignKey(
        AssayGroup,
        on_delete=models.CASCADE,
        related_name='group_2',
        null=True,
        blank=True,
        help_text='The data analysis reference group.',
        verbose_name='Reference Group*'
    )
    # times WILL be empty for the norm count and raw count data (in AssayOmicSampleMetadata instead)
    time_1 = models.FloatField(
        default=0,
        null=True,
        blank=True,
        help_text='The sample collection time for the data test group.',
        verbose_name='Sample Time 1*'
    )
    time_2 = models.FloatField(
        default=0,
        null=True,
        blank=True,
        help_text='The sample collection time for the data reference group.',
        verbose_name='Sample Time 2*'
    )
    # locations WILL be empty for the norm count and raw count data (in AssayOmicSampleMetadata instead)
    location_1 = models.ForeignKey(
        'AssaySampleLocation',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="location_1",
        help_text='The sample collection location for the data test group.',
        verbose_name='Sample Location 1*'
    )
    location_2 = models.ForeignKey(
        'AssaySampleLocation',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="location_2",
        help_text='The sample collection location for the data reference group.',
        verbose_name='Sample Location 2'
    )

    def __str__(self):
        return '{0}'.format(self.id)

    def get_absolute_url(self):
        return '/assays/assayomicdatafileupload/{}/'.format(self.id)

    def get_post_submission_url(self):
        return '/assays/assaystudy/{}/assayomicdatafileupload/'.format(self.study_id)

    def get_delete_url(self):
        return '{}delete/'.format(self.get_absolute_url())


#This is for the metadata when need to collect by individual omic sample (counts data)
class AssayOmicSampleMetadata(models.Model):
    """Model for omic sample metadata associated to count data."""

    class Meta(object):
        verbose_name = 'Omic Sample Name and Metadata'
        unique_together = [('study', 'sample_name')]

    study = models.ForeignKey(
        'assays.AssayStudy',
        on_delete=models.CASCADE,
        verbose_name='Study'
    )

    sample_name = models.CharField(
        max_length=255,
        default='',
        help_text='The sample name - must match EXACTLY the headers found in the omic counts data files',
        verbose_name='Cross Reference'
    )

    matrix_item = models.ForeignKey(
        'assays.AssayMatrixItem',
        on_delete=models.CASCADE,
        verbose_name='Matrix Item'
    )

    sample_location = models.ForeignKey(
        'assays.AssaySampleLocation',
        on_delete=models.CASCADE,
        verbose_name='Sample Location'
    )

    # PLEASE NOTE THAT THIS IS IN MINUTES
    sample_time = models.FloatField(
        default=0,
        verbose_name='Time'
    )

    def __str__(self):
        return '{0}'.format(self.id)

# for the two group data points
class AssayOmicDataPoint(models.Model):
    """Individual points of omic data for two group data with metadata by group"""

    class Meta(object):
        verbose_name = 'Assay Omic Data Point (two group)'
        verbose_name_plural = 'Assay Omic Data Points (two group)'

    study = models.ForeignKey(
        'assays.AssayStudy',
        on_delete=models.CASCADE,
        verbose_name='This Study'
    )

    omic_data_file = models.ForeignKey(
        AssayOmicDataFileUpload,
        on_delete=models.CASCADE,
        verbose_name='Data File'
    )
    # this might be replaced later with a pk to a master table
    name = models.CharField(
        max_length=100,
        help_text='Gene or Probe ID',
        verbose_name='Name'
    )
    # to a table with the header and analysis target that is controlled by the admins
    analysis_target = models.ForeignKey(
        AssayOmicAnalysisTarget,
        on_delete=models.CASCADE,
        help_text='Analysis Target (e.g., p-value, log2FoldChange, baseMean)',
        verbose_name='Analysis Target'
    )

    value = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Computed Value'
    )

    def __str__(self):
        return '{0}'.format(self.id)

# for the counts data points
# class AssayOmicDataPointCounts(models.Model):
#     """Individual points of omic data with individual sample metadata"""
#
#     class Meta(object):
#         verbose_name = 'Assay Omic Data Point (counts)'
#         verbose_name_plural = 'Assay Omic Data Points (counts)'

#
#     study = models.ForeignKey(
#         'assays.AssayStudy',
#         on_delete=models.CASCADE,
#         verbose_name='This Study'
#     )
# need this here
#     omic_data_file = models.ForeignKey(
#         AssayOmicDataFileUpload,
#         on_delete=models.CASCADE,
#         verbose_name='Data File'
#     )
# this is what is different from the other omic data point table
#     sample_metadata = models.ForeignKey(
#         AssayOmicSampleMetadata,
#         on_delete=models.CASCADE,
#         verbose_name='Metadata'
#     )
#
#     # this might be replaced later with a pk to a master table
#     name = models.CharField(
#         max_length=100,
#         help_text='Gene or Probe ID',
#         verbose_name='Name'
#     )
#     # to a table with the header and analysis target that is controlled by the admins
#     analysis_target = models.ForeignKey(
#         AssayOmicAnalysisTarget,
#         on_delete=models.CASCADE,
#         help_text='Analysis Target (e.g., Normalized Counts, Raw Counts',
#         verbose_name='Analysis Target'
#     )
#
#     value = models.FloatField(
#         blank=True,
#         null=True,
#         verbose_name='Computed Value'
#     )
#
#     def __str__(self):
#         return '{0}'.format(self.id)

##### End Assay Omic Section - Phase 1 and 2 design
