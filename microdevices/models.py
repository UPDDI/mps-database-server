# coding=utf-8

from django.db import models
from django.contrib.auth.models import Group

from mps.base.models import LockableModel, TrackableModel, FlaggableModel, FrontEndModel
from django.core.validators import MaxValueValidator

import json

# Avoid wildcards when possible
from mps.utils import *


class MicrophysiologyCenter(LockableModel):
    """Microphysiology Center gives details for a collaborating center

    Note that this is the model by which groups are affiliated with assays, cells, etc.
    """
    class Meta(object):
        verbose_name = 'Microphysiology Center'
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
        help_text='***PLEASE DO NOT INCLUDE "Admin" OR "Viewer": ONLY SELECT THE BASE GROUP (ie "Taylor_MPS" NOT "Taylor_MPS Admin")***<br>',
        related_name='center_groups'
    )

    # Groups which can be selected as collaborator or access groups on the front-end
    accessible_groups = models.ManyToManyField(
        Group,
        blank=True,
        help_text='***PLEASE DO NOT INCLUDE "Admin" OR "Viewer": ONLY SELECT THE BASE GROUP (ie "Taylor_MPS" NOT "Taylor_MPS Admin")***<br>',
        related_name='center_accessible_groups'
    )

    def __str__(self):
        return self.name


class Manufacturer(FrontEndModel, LockableModel):
    """Manufacturer gives details for a manufacturer of devices and/or componentry"""
    class Meta(object):
        ordering = ('name',)
        verbose_name = 'Manufacturer'

    name = models.CharField(
        max_length=100,
        unique=True
    )
    contact_person = models.CharField(
        max_length=250,
        blank=True,
        default='',
        verbose_name='Contact Person'
    )
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class Microdevice(FrontEndModel, LockableModel):
    """A Microdevice describes a physical vessel for performing experiments (a plate, chip, etc.)"""
    class Meta(object):
        verbose_name = 'Device'
        ordering = ('name', 'organ',)

    # TODO TODO THIS SHOULD BE JUST NAME
    # device_name = models.CharField(max_length=200, unique=True)
    name = models.CharField(
        max_length=200,
        unique=True
    )

    organ = models.ForeignKey(
        'cellsamples.Organ',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='Organ'
    )
    center = models.ForeignKey(
        MicrophysiologyCenter,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='Center'
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='Manufacturer'
    )
    barcode = models.CharField(
        max_length=200,
        verbose_name='Version/Catalog#',
        default='',
        blank=True,
    )

    description = models.CharField(
        max_length=4000,
        default='',
        blank=True,
        verbose_name='Description'
    )

    device_width = models.FloatField(
        verbose_name='Device Width (mm)',
        null=True,
        blank=True,
    )
    device_length = models.FloatField(
        verbose_name='Device Length (mm)',
        null=True,
        blank=True,
    )
    device_thickness = models.FloatField(
        verbose_name='Device Thickness (mm)',
        null=True,
        blank=True,
    )

    # What is this for? Residue to be purged
    device_size_unit = models.CharField(
        max_length=50,
        default='',
        blank=True,
        verbose_name='Device Size Unit'
    )

    device_image = models.ImageField(
        upload_to='assays',
        null=True,
        blank=True,
        verbose_name='Device Image'
    )
    device_cross_section_image = models.ImageField(
        upload_to='assays',
        null=True,
        blank=True,
        verbose_name='Device Cross Section Image'
    )

    device_fluid_volume = models.FloatField(
        verbose_name='Device Fluid Volume (μL)',
        null=True,
        blank=True
    )
    # device fluid volume will now always be micro liters
    # device_fluid_volume_unit = models.CharField(
    #     max_length=50, null=True, blank=True)

    substrate_thickness = models.FloatField(
        verbose_name='Substrate Thickness (um)',
        null=True,
        blank=True
    )
    substrate_material = models.CharField(
        max_length=150,
        default='',
        blank=True,
        verbose_name='Substrate Material'
    )

    # Specify whether the device is a plate or a chip
    device_type = models.CharField(
        max_length=8,
        choices=(
            ('chip', 'Microchip'),
            ('plate', 'Plate')
        ),
        verbose_name='Device Type'
    )

    # Optional fields primarily intended for plates
    # (though certain chips appear in a series)
    number_of_rows = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MaxValueValidator(100)
        ],
        verbose_name='Number of Row'
    )
    number_of_columns = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MaxValueValidator(100)
        ],
        verbose_name='Number of Columns'
    )

    # DEPRECATED
    row_labels = models.CharField(
        blank=True,
        default='',
        max_length=1000,
        help_text='Space separated list of unique labels, '
            'e.g. "A B C D ..."'
            ' Number of items must match'
            ' number of columns.'
    )
    # DEPRECATED
    column_labels = models.CharField(
        blank=True,
        default='',
        max_length=1000,
        help_text='Space separated list of unique '
            'labels, e.g. "1 2 3 4 ...". '
           'Number of items must match '
           'number of columns.'
    )

    # DEPRECATED
    references = models.CharField(max_length=2000, blank=True, default='')

    # NEED DIMENSIONS FOR MODEL AS WELL
    model_width = models.FloatField(
        verbose_name='Model Region Width (mm)',
        null=True,
        blank=True,
    )
    model_length = models.FloatField(
        verbose_name='Model Region Length (mm)',
        null=True,
        blank=True,
    )
    model_thickness = models.FloatField(
        verbose_name='Model Region Thickness (mm)',
        null=True,
        blank=True,
    )

    model_fluid_volume = models.FloatField(
        verbose_name='Model Region Fluid Volume (μL)',
        null=True,
        blank=True
    )

    # Additional info
    product_sheet = models.FileField(
        upload_to='device_product_sheets',
        verbose_name='Product Sheet',
        null=True,
        blank=True,
    )

    device_webpage = models.URLField(
        null=True,
        blank=True,
        verbose_name='Device Webpage'
    )

    device_material = models.CharField(
        max_length=150,
        default='',
        blank=True,
        verbose_name='Device Material'
    )


    def __str__(self):
        return self.name


class OrganModel(FrontEndModel, LockableModel):
    """An Organ Model describes a way of preparing a device to emulate a particular organ"""
    class Meta(object):
        verbose_name = 'MPS Model'
        ordering = ('name', 'organ',)

    # model_name = models.CharField(max_length=200, unique=True)
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Name'
    )
    organ = models.ForeignKey(
        'cellsamples.Organ',
        on_delete=models.CASCADE,
        verbose_name='Organ'
    )
    disease = models.ForeignKey(
        'diseases.Disease',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='Disease'
    )
    # Centers are now required
    center = models.ForeignKey(
        MicrophysiologyCenter,
        on_delete=models.CASCADE,
        verbose_name='Center'
    )
    device = models.ForeignKey(
        Microdevice,
        on_delete=models.CASCADE,
        verbose_name='Device'
    )
    description = models.CharField(
        max_length=4000,
        default='',
        blank=True,
        verbose_name='Description'
    )

    # TO BE DEPRECATED
    model_image = models.ImageField(
        upload_to='models',
        null=True,
        blank=True,
        verbose_name='Model Image'
    )

    # "Base Model" represents the "parent" of the model in question
    # While the default is not listed here, please note that it is in fact the instance in question
    # ie unspecified base_models point back to the same entry
    base_model = models.ForeignKey(
        'microdevices.OrganModel',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='Base Model'
    )
    # Alternative name, especially for filters
    alt_name = models.CharField(
        max_length=1000,
        blank=True,
        default='',
        verbose_name='Alternative Name'
    )

    # May or may not need to be converted to FK fields
    model_type = models.CharField(
        max_length=2,
        choices=(
            ('F2', 'Fluidic-2D'),
            ('F3', 'Fluidic-3D'),
            ('S2', 'Static-2D'),
            ('S3', 'Static-3D'),
        ),
        verbose_name='Model Type'
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
        default='',
        verbose_name='Disease Trigger'
    )

    # DEPRECATED
    # NAIVE
    epa = models.BooleanField(
        default=False,
        help_text='Whether this compound is part of the EPA project',
        verbose_name='EPA'
    )
    mps = models.BooleanField(
        default=False,
        help_text='Whether this compound is part of the MPS project',
        verbose_name='MPS'
    )
    tctc = models.BooleanField(
        default=False,
        help_text='Whether this compound is part of the TCTC project',
        verbose_name='TCTC'
    )

    # Removed in favor of protocol inline
    # protocol = models.FileField(upload_to='protocols', verbose_name='Protocol File',
    #                        blank=True, null=True, help_text='File detailing the protocols for this model')

    # TO BE DEPRECATED
    references = models.CharField(max_length=2000, blank=True, default='')

    def __str__(self):
        return self.name

    def user_is_in_center(self, user_group_names):
        # Get a dic of groups
        groups_to_check = {}
        for current_group in self.center.groups.all():
            groups_to_check.update({
                current_group.name: True
            })

        if len(user_group_names) == 0 or self.center and not any(
            current_name in groups_to_check for current_name in user_group_names.keys()
        ):
            return False
        else:
            return True

    # TODO REVIEW
    def get_group_data_string(self):
        # Probably should change structure?
        data = {
            # Probably should change name?
            'series_data': [],
        }

        # If we so desired, we could order these
        # One option is PK to get order of addition?
        versions = OrganModelProtocol.objects.filter(
            organ_model_id=self.id
        ).prefetch_related(
            # Prefetch the cells etc.
            # Kind of rough, but on the bright side we don't need chaining
            'organmodelprotocolcell_set',
            'organmodelprotocolsetting_set',
        ).order_by(
            'id'
        )

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
            'organ_model_protocol_id',
        ]

        for group_index, version in enumerate(versions):
            current_group = {
                # I know it seems odd to have NAME rather than ID...
                # But we need to deal with submissions where the protocol doesn't exist yet
                # This way we can hopefully other (somehow) jankier solutions
                # We still want the ID, of course
                # That way we can ignore name matching when possible
                'id': version.id,
                'name': version.name,
                'cell': [],
                'setting': [],
            }

            # Not very DRY
            for cell in version.organmodelprotocolcell_set.all():
                current_group.get('cell').append(
                    {
                        key: cell.__dict__.get(key) for key in cell.__dict__.keys() if key not in excluded_keys
                    }
                )

            for setting in version.organmodelprotocolsetting_set.all():
                current_group.get('setting').append(
                    {
                        key: setting.__dict__.get(key) for key in setting.__dict__.keys() if key not in excluded_keys
                    }
                )

            data.get('series_data').append(current_group)

        return json.dumps(data)


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
class OrganModelProtocol(FrontEndModel, FlaggableModel):
    """Organ Model Protocols point to a file detailing the preparation of a model

    This model is intended to be an inline
    """

    class Meta(object):
        unique_together = [('name', 'organ_model')]
        # TODO SWITCH TO THIS UNIQUE TOGETHER RESTRICTION ASAP
        # unique_together = [('name', 'organ_model')]
        verbose_name = 'MPS Model Version'

    organ_model = models.ForeignKey(
        OrganModel,
        verbose_name='MPS Model',
        on_delete=models.CASCADE
    )
    # Uhh... this should probably just be "name"...
    # TRANSFER ALL VERSIONS TO NAMES
    version = models.CharField(
        max_length=20,
        default='',
        blank=True,
        verbose_name='Version'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Name'
    )
    # THIS SHOULD DEFINITELY NOT BE CALLED SIMPLY "FILE"
    # file = models.FileField(upload_to='protocols', verbose_name='Protocol File')
    protocol_file = models.FileField(
        upload_to='protocols',
        verbose_name='Protocol File'
    )

    description = models.CharField(
        max_length=4000,
        default='',
        blank=True,
        verbose_name='Description'
    )

    disease = models.ForeignKey(
        'diseases.Disease',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='Disease'
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
        default='',
        verbose_name='Disease Trigger'
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
    sample_location = models.ForeignKey(
        'assays.AssaySampleLocation',
        on_delete=models.CASCADE,
        verbose_name='Sample Location'
    )
    notes = models.CharField(
        max_length=1024,
        verbose_name='Notes'
    )
    organ_model = models.ForeignKey(
        OrganModel,
        on_delete=models.CASCADE,
        verbose_name='MPS Model'
    )


# PROTOTYPE
class OrganModelCell(models.Model):
    organ_model = models.ForeignKey(
        OrganModel,
        on_delete=models.CASCADE,
        verbose_name='MPS Model'
    )
    cell_type = models.ForeignKey(
        'cellsamples.CellType',
        on_delete=models.CASCADE,
        verbose_name='Cell Type'
    )
    # HIDDEN AND NOT REQUIRED
    count = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Count'
    )


# JUST INCLUDE EVERYTHING FOR NOW
# SOMEWHAT UNUSUAL TO HAVE THIS DECOUPLED FROM SETUPCELL
# THERE SHOULD BE A MIXIN TO ENSURE SAME AS ASSAYS COPY
class OrganModelProtocolCell(models.Model):
    organ_model_protocol = models.ForeignKey(
        OrganModelProtocol,
        on_delete=models.CASCADE,
        verbose_name='MPS Model Protocol'
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
        default=0,
        verbose_name='Density'
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

    addition_location = models.ForeignKey(
        'assays.AssaySampleLocation',
        on_delete=models.CASCADE,
        verbose_name='Addition Location'
    )

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


# JUST INCLUDE EVERYTHING FOR NOW
class OrganModelProtocolSetting(models.Model):
    organ_model_protocol = models.ForeignKey(
        OrganModelProtocol,
        on_delete=models.CASCADE,
        verbose_name='MPS Model Protocol'
    )

    # No longer one-to-one
    # setup = models.ForeignKey('assays.AssaySetup', on_delete=models.CASCADE)
    setting = models.ForeignKey(
        'assays.AssaySetting',
        on_delete=models.CASCADE,
        verbose_name='Setting'
    )
    unit = models.ForeignKey(
        'assays.PhysicalUnits',
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

    addition_location = models.ForeignKey(
        'assays.AssaySampleLocation',
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
