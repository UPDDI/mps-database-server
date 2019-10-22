# coding=utf-8

from django.db import models
from django.contrib.auth.models import Group

from mps.base.models import LockableModel, TrackableModel, FlaggableModel
from django.core.validators import MaxValueValidator

import reversion


@reversion.register(follow=['microdevice_set'])
class MicrophysiologyCenter(LockableModel):
    """Microphysiology Center gives details for a collaborating center

    Note that this is the model by which groups are affiliated with assays, cells, etc.
    """
    class Meta(object):
        ordering = ('name',)

    # TODO TODO THIS SHOULD BE JUST NAME
    # center_name = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=400, unique=True)

    center_id = models.CharField(max_length=40, unique=True)

    institution = models.CharField(max_length=400)

    description = models.CharField(max_length=4000, blank=True, default='')

    contact_person = models.CharField(max_length=250, blank=True, default='')
    contact_email = models.EmailField(blank=True, default='')
    contact_web_page = models.URLField(blank=True, null=True)

    pi = models.CharField(max_length=250, blank=True, default='', verbose_name='PI')
    pi_email = models.EmailField(blank=True, default='', verbose_name='PI Email')
    pi_web_page = models.URLField(blank=True, null=True)

    website = models.URLField(blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        blank=True,
        help_text='***PLEASE DO NOT INCLUDE "Admin" OR "Viewer": ONLY SELECT THE BASE GROUP (ie "Taylor_MPS" NOT "Taylor_MPS Admin")***<br>'
    )

    def __str__(self):
        return self.name


@reversion.register(follow=['microdevice_set'])
class Manufacturer(LockableModel):
    """Manufacturer gives details for a manufacturer of devices and/or componentry"""
    class Meta(object):
        ordering = ('name',)

    name = models.CharField(max_length=100, unique=True)
    contact_person = models.CharField(max_length=250, blank=True, default='')
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


@reversion.register(follow=[
    'organ',
    'center',
    'manufacturer',
    'organmodel_set'
])
class Microdevice(LockableModel):
    """A Microdevice describes a physical vessel for performing experiments (a plate, chip, etc.)"""
    class Meta(object):
        verbose_name = 'Device'
        ordering = ('name', 'organ',)

    # TODO TODO THIS SHOULD BE JUST NAME
    # device_name = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200, unique=True)

    organ = models.ForeignKey('cellsamples.Organ', blank=True, null=True, on_delete=models.CASCADE)
    center = models.ForeignKey(MicrophysiologyCenter, blank=True, null=True, on_delete=models.CASCADE)
    manufacturer = models.ForeignKey(Manufacturer, null=True, blank=True, on_delete=models.CASCADE)
    barcode = models.CharField(
        max_length=200, verbose_name='version/ catalog#', default='', blank=True)

    description = models.CharField(max_length=4000, default='', blank=True)

    device_width = models.FloatField(
        verbose_name='width (mm)', null=True, blank=True)
    device_length = models.FloatField(
        verbose_name='length (mm)', null=True, blank=True)
    device_thickness = models.FloatField(
        verbose_name='thickness (mm)', null=True, blank=True)

    # What is this for? Residue to be purged
    device_size_unit = models.CharField(max_length=50, default='', blank=True)

    device_image = models.ImageField(upload_to='assays', null=True, blank=True)
    device_cross_section_image = models.ImageField(
        upload_to='assays', null=True, blank=True)

    device_fluid_volume = models.FloatField(verbose_name='device fluid volume (uL)', null=True, blank=True)
    # device fluid volume will now always be micro liters
    # device_fluid_volume_unit = models.CharField(
    #     max_length=50, null=True, blank=True)

    substrate_thickness = models.FloatField(
        verbose_name='substrate thickness (um)', null=True, blank=True)
    substrate_material = models.CharField(
        max_length=150, default='', blank=True)

    # Specify whether the device is a plate or a chip
    device_type = models.CharField(max_length=8,
                                   choices=(('chip', 'Microchip'),
                                            ('plate', 'Plate')))

    # Optional fields primarily intended for plates
    # (though certain chips appear in a series)
    number_of_rows = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MaxValueValidator(100)
        ]
    )
    number_of_columns = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MaxValueValidator(100)
        ]
    )

    # DEPRECATED
    row_labels = models.CharField(blank=True,
                                  default='',
                                  max_length=1000,
                                  help_text=
                                  'Space separated list of unique labels, '
                                  'e.g. "A B C D ..."'
                                  ' Number of items must match'
                                  ' number of columns.')
    # DEPRECATED
    column_labels = models.CharField(blank=True,
                                     default='',
                                     max_length=1000,
                                     help_text='Space separated list of unique '
                                               'labels, e.g. "1 2 3 4 ...". '
                                               'Number of items must match '
                                               'number of columns.')

    references = models.CharField(max_length=2000, blank=True, default='')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "/microdevices/device/{}/".format(self.id)

    def get_post_submission_url(self):
        return '/microdevices/device/'


@reversion.register(follow=[
    'organmodelprotocol_set'
])
class OrganModel(LockableModel):
    """An Organ Model describes a way of preparing a device to emulate a particular organ"""
    class Meta(object):
        verbose_name = 'MPS Model'
        ordering = ('name', 'organ',)

    # model_name = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200, unique=True)
    organ = models.ForeignKey('cellsamples.Organ', on_delete=models.CASCADE)
    disease = models.ForeignKey('diseases.Disease', null=True, blank=True, on_delete=models.CASCADE)
    # Centers are now required
    center = models.ForeignKey(MicrophysiologyCenter, on_delete=models.CASCADE)
    device = models.ForeignKey(Microdevice, on_delete=models.CASCADE)
    description = models.CharField(max_length=4000, default='', blank=True)

    # TO BE DEPRECATED
    model_image = models.ImageField(upload_to='models', null=True, blank=True)

    # "Base Model" represents the "parent" of the model in question
    # While the default is not listed here, please note that it is in fact the instance in question
    # ie unspecified base_models point back to the same entry
    base_model = models.ForeignKey('microdevices.OrganModel', null=True, blank=True, on_delete=models.CASCADE)
    # Alternative name, especially for filters
    alt_name = models.CharField(max_length=1000, blank=True, default='')

    # May or may not need to be converted to FK fields
    model_type = models.CharField(
        max_length=2,
        choices=(
            ('F2', 'Fluidic-2D'),
            ('F3', 'Fluidic-3D'),
            ('S2', 'Static-2D'),
            ('S3', 'Static-3D'),
        )
    )
    # Obviously only really relevant for disease models
    disease_trigger = models.CharField(
        max_length=10,
        choices=(
            ('', ''),
            ('Compound', 'Induced by Compound'),
            ('Cells', 'Addition of Diseased Cells'),
        ),
        blank=True,
        default=''
    )

    # DEPRECATED
    # NAIVE
    epa = models.BooleanField(
        default=False,
        help_text='Whether this compound is part of the EPA project'
    )
    mps = models.BooleanField(
        default=False,
        help_text='Whether this compound is part of the MPS project'
    )
    tctc = models.BooleanField(
        default=False,
        help_text='Whether this compound is part of the TCTC project'
    )

    # Removed in favor of protocol inline
    # protocol = models.FileField(upload_to='protocols', verbose_name='Protocol File',
    #                        blank=True, null=True, help_text='File detailing the protocols for this model')

    # TO BE DEPRECATED
    references = models.CharField(max_length=2000, blank=True, default='')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "/microdevices/model/{}/".format(self.id)

    def get_post_submission_url(self):
        return '/microdevices/model/'


# class OrganModelImage(models.Model):
#     pass


# TODO DEPRECATED
# It is somewhat odd that ValidatedAssays are inlines in lieu of a manytomany field
# This was done originally so that additional fields could be added to a validated assay
# If no new fields become apparent, it may be worthwhile to do away with inlines and move to M2M
class ValidatedAssay(models.Model):
    """Validated Assays show which assays have been approved for a particular Organ Model"""
    # Validated assays for an organ model used in inline
    organ_model = models.ForeignKey(OrganModel, verbose_name='MPS Model', on_delete=models.CASCADE)
    assay = models.ForeignKey('assays.AssayModel', verbose_name='Assay Model', on_delete=models.CASCADE)


# TODO PLEASE NOTE THIS WILL BE REFERRED TO AS SIMPLY A "VERSION"
@reversion.register(follow=[
    'organ_model',
])
class OrganModelProtocol(FlaggableModel):
    """Organ Model Protocols point to a file detailing the preparation of a model

    This model is intended to be an inline
    """

    class Meta(object):
        unique_together = [('name', 'organ_model')]
        # TODO SWITCH TO THIS UNIQUE TOGETHER RESTRICTION ASAP
        # unique_together = [('name', 'organ_model')]
        verbose_name = 'MPS Model Version'

    organ_model = models.ForeignKey(OrganModel, verbose_name='MPS Model', on_delete=models.CASCADE)
    # Uhh... this should probably just be "name"...
    # TRANSFER ALL VERSIONS TO NAMES
    version = models.CharField(max_length=20, default='', blank=True)
    name = models.CharField(max_length=200)
    # THIS SHOULD DEFINITELY NOT BE CALLED SIMPLY "FILE"
    # file = models.FileField(upload_to='protocols', verbose_name='Protocol File')
    protocol_file = models.FileField(upload_to='protocols', verbose_name='Protocol File')

    description = models.CharField(max_length=4000, default='', blank=True)

    disease = models.ForeignKey('diseases.Disease', null=True, blank=True, on_delete=models.CASCADE)
    # Obviously only really relevant for disease models
    disease_trigger = models.CharField(
        max_length=10,
        choices=(
            ('', ''),
            ('Compound', 'Induced by Compound'),
            ('Cells', 'Addition of Diseased Cells'),
        ),
        blank=True,
        default=''
    )

    def __str__(self):
        # return self.version
        return self.name

    def get_absolute_url(self):
        return "/microdevices/protocol/{}/".format(self.id)

    def get_post_submission_url(self):
        return '{}update'.format(self.organ_model.get_absolute_url())


# TODO SEEMS TO BE UNUSED
class GroupDeferral(TrackableModel):
    """This indicates the status of a group and whether they have deferred their ability to approve studies"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    notes = models.CharField(max_length=1024)
    approval_file = models.FileField(
        null=True,
        blank=True,
        upload_to='deferral'
    )


# PLEASE KEEP IN MIND
class OrganModelLocation(models.Model):
    """This is an inline for models that permits us to list relevant sample locations"""
    sample_location = models.ForeignKey('assays.AssaySampleLocation', on_delete=models.CASCADE)
    notes = models.CharField(max_length=1024)
    organ_model = models.ForeignKey(OrganModel, on_delete=models.CASCADE)


# PROTOTYPE
class OrganModelCell(models.Model):
    organ_model = models.ForeignKey(OrganModel, on_delete=models.CASCADE)
    cell_type = models.ForeignKey('cellsamples.CellType', on_delete=models.CASCADE)
    # HIDDEN AND NOT REQUIRED
    count = models.IntegerField(blank=True, null=True)


# JUST INCLUDE EVERYTHING FOR NOW
# SOMEWHAT UNUSUAL TO HAVE THIS DECOUPLED FROM SETUPCELL
class OrganModelProtocolCell(models.Model):
    organ_model_protocol = models.ForeignKey(OrganModelProtocol, on_delete=models.CASCADE)

    cell_sample = models.ForeignKey('cellsamples.CellSample', on_delete=models.CASCADE)
    biosensor = models.ForeignKey(
        'cellsamples.Biosensor',
        on_delete=models.CASCADE,
        # Default is naive
        default=2
    )
    density = models.FloatField(verbose_name='density', default=0)

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
    addition_location = models.ForeignKey('assays.AssaySampleLocation', blank=True, default=1, on_delete=models.CASCADE)


# JUST INCLUDE EVERYTHING FOR NOW
class OrganModelProtocolSetting(models.Model):
    organ_model_protocol = models.ForeignKey(OrganModelProtocol, on_delete=models.CASCADE)

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
    addition_location = models.ForeignKey('assays.AssaySampleLocation', blank=True, default=1, on_delete=models.CASCADE)


# REMOVED FOR NOW
# class MicrodeviceSublayout(models.Model):
#     """Describes a the layout of sections for a device"""
#     device = models.ForeignKey(Microdevice, on_delete=models.CASCADE)
#
#     number_of_rows = models.IntegerField()
#     number_of_columns = models.IntegerField()
#
#
# class MicrodeviceSection(models.Model):
#     """Describes a section of a device, for instance if a device has to compartments (apical and basal)"""
#     device_sublayout = models.ForeignKey(MicrodeviceSublayout, on_delete=models.CASCADE)
#
#     row_index = models.IntegerField()
#     column_index = models.IntegerField()
#
#     name = models.CharField(max_length=255)
#
#     volume = models.FloatField()
#
#     # VOLUME UNITS TOO?
#
#     def __str__(self):
#         return self.name


class OrganModelReference(models.Model):
    class Meta(object):
        unique_together = [
            (
                'reference',
                'reference_for'
            )
        ]

    reference = models.ForeignKey('assays.AssayReference', on_delete=models.CASCADE)
    reference_for = models.ForeignKey(OrganModel, on_delete=models.CASCADE)


class MicrodeviceReference(models.Model):
    class Meta(object):
        unique_together = [
            (
                'reference',
                'reference_for'
            )
        ]

    reference = models.ForeignKey('assays.AssayReference', on_delete=models.CASCADE)
    reference_for = models.ForeignKey(Microdevice, on_delete=models.CASCADE)
