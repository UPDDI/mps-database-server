# coding=utf-8

from django.db import models
from microdevices.models import (
    Microdevice,
    OrganModel,
    OrganModelProtocol,
    MicrophysiologyCenter,
    # MicrodeviceSection
)
from mps.base.models import LockableModel, FlaggableModel, FlaggableRestrictedModel
from django.contrib.auth.models import Group, User

import urllib
import collections

# TODO MAKE MODEL AND FIELD NAMES MORE CONSISTENT/COHERENT

# TODO DEPRECATED, REMOVE SOON
PHYSICAL_UNIT_TYPES = (
    (u'V', u'Volume'),
    (u'C', u'Concentration'),
    (u'M', u'Mass'),
    (u'T', u'Time'),
    (u'F', u'Frequency'),
    (u'RA', u'Rate'),
    (u'RE', u'Relative'),
    (u'O', u'Other'),
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


# TODO EMPLOY THIS FUNCTION ELSEWHERE
def get_split_times(time_in_minutes):
    """Takes time_in_minutes and returns a dic with the time split into day, hour, minute"""
    times = {
        'day': 0,
        'hour': 0,
        'minute': 0
    }
    time_in_minutes_remaining = time_in_minutes
    for time_unit, conversion in TIME_CONVERSIONS.items():
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

    def __unicode__(self):
        return u'{}'.format(self.unit_type)


# TODO THIS NEEDS TO BE REVISED (IDEALLY REPLACED WITH PHYSICALUNIT BELOW)
class PhysicalUnits(LockableModel):
    """Measures of concentration and so on"""

    # USE NAME IN LIEU OF UNIT (unit.unit is confusing and dumb)
    # name = models.CharField(max_length=255)
    unit = models.CharField(max_length=255)
    description = models.CharField(max_length=255,
                                   blank=True, default='')

    unit_type = models.ForeignKey(UnitType)

    # Base Unit for conversions and scale factor
    base_unit = models.ForeignKey('assays.PhysicalUnits',
                                  blank=True,
                                  null=True)

    # Scale factor gives the conversion to get to the base unit, can also act to sort
    scale_factor = models.FloatField(blank=True,
                                     null=True)

    availability = models.CharField(max_length=255,
                                    blank=True,
                                    default='',
                                    help_text=(u'Type a series of strings for indicating '
                                               u'where this unit should be listed:'
                                               u'\ntest = test results\nreadouts = readouts\ncells = cell samples'))

    # verbose_name_plural is used to avoid a double 's' on the model name
    class Meta(object):
        verbose_name_plural = 'Physical Units'
        ordering = ['unit_type', 'unit']

    def __unicode__(self):
        return u'{}'.format(self.unit)


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

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return '/assays/studyconfiguration/{}/'.format(self.id)

    def get_post_submission_url(self):
        return '/assays/studyconfiguration/'


class AssayStudyModel(models.Model):
    """Individual connections for integrated models"""

    study_configuration = models.ForeignKey(AssayStudyConfiguration)
    label = models.CharField(max_length=2)
    organ = models.ForeignKey(OrganModel)
    sequence_number = models.IntegerField()
    output = models.CharField(max_length=20, blank=True, default='')
    # Subject to change
    integration_mode = models.CharField(max_length=13, default='1', choices=(('0', 'Functional'), ('1', 'Physical')))


# Get readout file location
def bulk_readout_file_location(instance, filename):
    return '/'.join(['csv', str(instance.id), 'bulk', filename])


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

    study = models.ForeignKey('assays.AssayStudy')

    def __unicode__(self):
        return urllib.unquote(self.file_location.split('/')[-1])


# NEW MODELS, TO BE INTEGRATED FURTHER LATER
class AssayTarget(LockableModel):
    """Describes what was sought by a given Assay"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    short_name = models.CharField(max_length=20, unique=True)

    # Tentative
    alt_name = models.CharField(max_length=1000, blank=True, default='')

    def __unicode__(self):
        return u'{0} ({1})'.format(self.name, self.short_name)


class AssaySubtarget(models.Model):
    """Describes a target for situations where manually curated lists are prohibitively expensive (TempoSeq, etc.)"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    def __unicode__(self):
        return self.name


class AssayMeasurementType(LockableModel):
    """Describes what was measures with a given method"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    def __unicode__(self):
        return self.name


class AssaySupplier(LockableModel):
    """Assay Supplier so we can track where kits came from"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    def __unicode__(self):
        return self.name


class AssayMethod(LockableModel):
    """Describes how an assay was performed"""
    # We may want to modify this so that it is unique on name in combination with measurement type?
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)
    measurement_type = models.ForeignKey(AssayMeasurementType)

    # May or may not be required in the future
    supplier = models.ForeignKey(AssaySupplier, blank=True, null=True)

    # TODO STORAGE LOCATION
    # TODO TEMPORARILY NOT REQUIRED
    protocol_file = models.FileField(upload_to='assays', null=True, blank=True)

    # Tentative
    alt_name = models.CharField(max_length=1000, blank=True, default='')

    def __unicode__(self):
        return self.name


class AssaySampleLocation(LockableModel):
    """Describes a location for where a sample was acquired"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    def __unicode__(self):
        return self.name


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
    study_configuration = models.ForeignKey(AssayStudyConfiguration, blank=True, null=True)
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

    # THESE ARE NOW EXPLICIT FIELDS IN STUDY
    group = models.ForeignKey(Group, help_text='Bind to a group')

    restricted = models.BooleanField(default=True, help_text='Check box to restrict to selected group')

    # Special addition, would put in base model, but don't want excess...
    signed_off_notes = models.CharField(max_length=255, blank=True, default='')

    # TODO SOMEWHAT CONTRIVED
    bulk_file = models.FileField(
        upload_to=upload_file_location,
        verbose_name='Data File',
        blank=True, null=True
    )

    # TODO
    # def get_study_types_string(self):
    #     study_types = '-'.join(
    #         sorted([study_type.code for study_type in self.study_types.all()])
    #     )
    #     return study_types

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
        return u'-'.join(current_types)

    # TODO
    def __unicode__(self):
        center_id = self.group.microphysiologycenter_set.first().center_id
        # study_types = self.get_study_types_string()
        return '-'.join([
            center_id,
            self.get_study_types_string(),
            unicode(self.start_date),
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

    study = models.ForeignKey(AssayStudy)

    device = models.ForeignKey(Microdevice, null=True, blank=True)

    # Decided against the inclusion of organ model here
    # organ_model = models.ForeignKey(OrganModel, null=True, blank=True)
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

    def __unicode__(self):
        return u'{0}'.format(self.name)

    # def get_organ_models(self):
    #     organ_models = []
    #     for matrix_item in self.assaymatrixitem_set.all():
    #         organ_models.append(matrix_item.organ_model)
    #
    #     if not organ_models:
    #         return '-No Organ Models-'
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

TEST_TYPE_CHOICES = (
    ('', '--------'), ('control', 'Control'), ('compound', 'Compound')
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
    study = models.ForeignKey(AssayStudy)

    # Probably shouldn't use this trick!
    # This is in fact required, just listed as not being so due to quirk in cleaning
    matrix = models.ForeignKey(AssayMatrix, null=True, blank=True)

    # This is in fact required, just listed as not being so due to quirk in cleaning
    # setup = models.ForeignKey('assays.AssaySetup', null=True, blank=True)

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

    device = models.ForeignKey(Microdevice, verbose_name='Device')

    organ_model = models.ForeignKey(OrganModel, verbose_name='Model', null=True, blank=True)

    organ_model_protocol = models.ForeignKey(
        OrganModelProtocol,
        verbose_name='Model Protocol',
        null=True,
        blank=True
    )

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
    failure_reason = models.ForeignKey(AssayFailureReason, blank=True, null=True)

    def __unicode__(self):
        return unicode(self.name)

    def devolved_settings(self):
        """Makes a tuple of cells (for comparison)"""
        setting_tuple = []
        for setting in self.assaysetupsetting_set.all():
            setting_tuple.append((
                setting.setting_id,
                setting.unit_id,
                setting.addition_location
            ))

        return tuple(sorted(setting_tuple))

    def stringify_settings(self):
        """Stringified cells for a setup"""
        settings = []
        for setting in self.assaysetupsetting_set.all():
            settings.append(unicode(setting))

        if not settings:
            settings = ['-No Extra Settings-']

        return '\n'.join(settings)

    def devolved_cells(self):
        """Makes a tuple of cells (for comparison)"""
        cell_tuple = []
        for cell in self.assaysetupcell_set.all():
            cell_tuple.append((
                cell.cell_sample_id,
                cell.biosensor_id,
                cell.density,
                cell.density_unit,
                cell.passage,
                cell.addition_location
            ))

        return tuple(sorted(cell_tuple))

    def stringify_cells(self):
        """Stringified cells for a setup"""
        cells = []
        for cell in self.assaysetupcell_set.all():
            cells.append(unicode(cell))

        if not cells:
            cells = ['-No Cell Samples-']

        return '\n'.join(cells)

    def devolved_compounds(self):
        """Makes a tuple of compounds (for comparison)"""
        compound_tuple = []
        for compound in self.assaysetupcompound_set.all():
            compound_tuple.append((
                compound.compound_instance_id,
                compound.concentration,
                compound.concentration_unit_id,
                compound.addition_time,
                compound.duration,
                compound.addition_location
            ))

        return tuple(sorted(compound_tuple))

    def stringify_compounds(self):
        """Stringified cells for a setup"""
        compounds = []
        for compound in self.assaysetupcompound_set.all():
            compounds.append(unicode(compound))

        if not compounds:
            compounds = ['-No Compounds-']

        return '\n'.join(compounds)

    def quick_dic(self):
        dic = {
            # 'device': self.device.name,
            'organ_model': self.get_hyperlinked_model_or_device(),
            'compounds': self.stringify_compounds(),
            'cells': self.stringify_cells(),
            'settings': self.stringify_settings(),
            'setups_with_same_group': []
        }
        return dic

    def get_hyperlinked_name(self):
        return '<a href="{0}">{1}</a>'.format(self.get_absolute_url(), self.name)

    def get_hyperlinked_model_or_device(self):
        if not self.organ_model:
            return '<a href="{0}">{1} (No Organ Model)</a>'.format(self.device.get_absolute_url(), self.device.name)
        else:
            return '<a href="{0}">{1}</a>'.format(self.organ_model.get_absolute_url(), self.organ_model.name)

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
            'cell_sample',
            'addition_location',
            'biosensor',
            'density',
            'density_unit',
            'passage'
        )

    # Now binds directly to items
    matrix_item = models.ForeignKey(AssayMatrixItem)

    # No longer bound one-to-one
    # setup = models.ForeignKey('AssaySetup')
    cell_sample = models.ForeignKey('cellsamples.CellSample')
    biosensor = models.ForeignKey('cellsamples.Biosensor')
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
    density_unit = models.ForeignKey('assays.PhysicalUnits')
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
    addition_location = models.ForeignKey(AssaySampleLocation, null=True, blank=True)

    def __unicode__(self):
        if self.addition_location:
            return u'{0} [{1}]\n-{2:.0e} {3}\nAdded to: {4}'.format(
                self.cell_sample,
                self.passage,
                self.density,
                self.density_unit.unit,
                self.addition_location
            )
        else:
            return u'{0} [{1}]\n-{2:.0e} {3}'.format(
                self.cell_sample,
                self.passage,
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

    # setup = models.ForeignKey('assays.AssaySetup')

    # May seem excessive, but chaining through fields can be inconvenient
    study = models.ForeignKey('assays.AssayStudy')

    # Cross reference for users if study ids diverge
    cross_reference = models.CharField(max_length=255, default='')

    matrix_item = models.ForeignKey('assays.AssayMatrixItem')

    study_assay = models.ForeignKey('assays.AssayStudyAssay')

    sample_location = models.ForeignKey('assays.AssaySampleLocation')

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
    data_file_upload = models.ForeignKey('assays.AssayDataFileUpload', null=True, blank=True)

    # OPTIONAL
    subtarget = models.ForeignKey(AssaySubtarget, null=True, blank=True)


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
            'compound_instance',
            'addition_location',
            'concentration_unit',
            'concentration',
            'duration',
        )

    # Now binds directly to items
    matrix_item = models.ForeignKey(AssayMatrixItem)

    # COMPOUND INSTANCE IS REQUIRED, however null=True was done to avoid a submission issue
    compound_instance = models.ForeignKey(
        'compounds.CompoundInstance',
        null=True,
        blank=True
    )
    concentration = models.FloatField()
    concentration_unit = models.ForeignKey(
        'assays.PhysicalUnits',
        verbose_name='Concentration Unit'
    )

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    addition_time = models.FloatField(blank=True)

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    duration = models.FloatField(blank=True)

    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_location = models.ForeignKey(AssaySampleLocation, null=True, blank=True)

    def get_addition_time_string(self):
        split_times = get_split_times(self.addition_time)
        return 'D{0} H{1} M{2}'.format(
            split_times.get('day'),
            split_times.get('hour'),
            split_times.get('minute'),
        )

    def get_duration_string(self):
        split_times = get_split_times(self.duration)
        return 'D{0} H{1} M{2}'.format(
            split_times.get('day'),
            split_times.get('hour'),
            split_times.get('minute'),
        )

    def __unicode__(self):
        if self.addition_location:
            return u'{0} ({1} {2})\n-Added on: {3}; Duration of: {4}; Added to: {5}'.format(
                self.compound_instance.compound.name,
                self.concentration,
                self.concentration_unit.unit,
                self.get_addition_time_string(),
                self.get_duration_string(),
                self.addition_location
            )
        else:
            return u'{0} ({1} {2})\n-Added on: {3}; Duration of: {4}'.format(
                self.compound_instance.compound.name,
                self.concentration,
                self.concentration_unit.unit,
                self.get_addition_time_string(),
                self.get_duration_string(),
            )

# Get readout file location
def study_supporting_data_location(instance, filename):
    return '/'.join(['supporting_data', str(instance.study_id), filename])


# TODO MODIFY StudySupportingData
class AssayStudySupportingData(models.Model):
    """A file (with description) that gives extra data for a Study"""
    study = models.ForeignKey(AssayStudy)

    description = models.CharField(
        max_length=1000,
        help_text='Describes the contents of the supporting data file'
    )

    # Not named file in order to avoid shadowing
    supporting_data = models.FileField(
        upload_to=study_supporting_data_location,
        help_text='Supporting Data for Study'
    )


# Proposed, may or may not include
# TODO Probably should have a ControlledVocabularyMixin for defining name and description consistently
class AssaySetting(LockableModel):
    """Defines a type of setting (flowrate etc.)"""
    name = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=2000)

    def __unicode__(self):
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

    # Now binds directly to items
    matrix_item = models.ForeignKey(AssayMatrixItem)

    # No longer one-to-one
    # setup = models.ForeignKey('assays.AssaySetup')
    setting = models.ForeignKey('assays.AssaySetting')
    unit = models.ForeignKey('assays.PhysicalUnits')
    value = models.FloatField()

    # Will we include these??
    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    addition_time = models.FloatField(blank=True)

    # PLEASE NOTE THAT THIS IS IN MINUTES, CONVERTED FROM D:H:M
    duration = models.FloatField(blank=True)

    # TODO TODO TODO TEMPORARILY NOT REQUIRED
    addition_location = models.ForeignKey(AssaySampleLocation, null=True, blank=True)

    def __unicode__(self):
        return u'{} {} {}'.format(self.setting.name, self.value, self.unit)


class AssayStudyStakeholder(models.Model):
    """An institution that has interest in a particular study

    Stakeholders needs to be consulted (sign off) before data can become available
    """

    study = models.ForeignKey(AssayStudy)

    group = models.ForeignKey(Group)
    # Explicitly declared rather than from inheritance to avoid unecessary fields
    signed_off_by = models.ForeignKey(
        User,
        blank=True,
        null=True
    )
    signed_off_date = models.DateTimeField(blank=True, null=True)

    signed_off_notes = models.CharField(max_length=255, blank=True, default='')

    sign_off_required = models.BooleanField(default=True)


class AssayStudyAssay(models.Model):
    """Specific assays used in the 'inlines'"""
    study = models.ForeignKey(AssayStudy, null=True, blank=True)
    # study_new = models.ForeignKey('assays.AssayStudy', null=True, blank=True)
    target = models.ForeignKey(AssayTarget)
    method = models.ForeignKey(AssayMethod)
    # Name of model "PhysicalUnits" should be renamed, methinks
    unit = models.ForeignKey(PhysicalUnits)

    def __unicode__(self):
        return u'{0}|{1}|{2}'.format(self.target, self.method, self.unit)


class AssayImageSetting(models.Model):
    # Requested, not sure how useful
    # May want to remove soon, why have this be specific to a study? Deletion cascade?
    study = models.ForeignKey(AssayStudy)
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

    def __unicode__(self):
        return u'{} {}'.format(self.study.name, self.label_name)


class AssayImage(models.Model):
    # May want to have an FK to study for convenience?
    # study = models.ForeignKey(AssayStudy)
    # The associated item
    matrix_item = models.ForeignKey(AssayMatrixItem)
    # The file name
    file_name = models.CharField(max_length=255)
    field = models.CharField(max_length=255)
    field_description = models.CharField(max_length=500, default='')
    # Stored in minutes
    time = models.FloatField()
    # Possibly used later, who knows
    assay_plate_id = models.CharField(max_length=40, default='N/A')
    assay_well_id = models.CharField(max_length=40, default='N/A')
    # PLEASE NOTE THAT I USE TARGET AND METHOD SEPARATE FROM ASSAY INSTANCE
    method = models.ForeignKey(AssayMethod)
    target = models.ForeignKey(AssayTarget)
    # May become useful
    subtarget = models.ForeignKey(AssaySubtarget)
    sample_location = models.ForeignKey(AssaySampleLocation)
    notes = models.CharField(max_length=500, default='')
    replicate = models.CharField(max_length=40, default='')
    setting = models.ForeignKey(AssayImageSetting)

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

    def __unicode__(self):
        return u'{}'.format(self.file_name)
