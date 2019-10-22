# coding=utf-8
"""CellSamples Models"""

from django.db import models

# Use our own model base classes instead of models.Model
from mps.base.models import LockableModel, FlaggableModel
from django.contrib.auth.models import Group
from django.urls import reverse

from mps.utils import *

import reversion


@reversion.register(follow=['celltype_set'])
class Organ(LockableModel):
    """Organ details an organ name and (with an inline) the cell types associated with it"""
    organ_name = models.CharField(max_length=255, unique=True)

    class Meta(object):
        ordering = ('organ_name', )

    def __str__(self):
        return '{}'.format(self.organ_name)

    # TODO
    def get_post_submission_url(self):
        return reverse('')


@reversion.register(follow=['cellsubtype_set'])
class CellType(LockableModel):
    """CellType details a type (e.g. hepatocyte), a species, and an organ"""
    class Meta(object):
        verbose_name = 'Cell Type'
        ordering = ('species', 'cell_type')
        unique_together = ('cell_type', 'species', 'organ')


    # TODO refactor to be a FK instead, should not be using a charfield here
    SPECIESTYPE = (
        ('Human', 'Human'),
        ('Rat', 'Rat'),
        ('Mouse', 'Mouse'),
    )
    # Unsemantic name (should just be name)
    cell_type = models.CharField(
        max_length=255,
        help_text='Example: hepatocyte, muscle, kidney, etc'
    )
    species = models.CharField(
        max_length=10,
        choices=SPECIESTYPE,
        default='Human',
        blank=True
    )

    # Deprecated
    # cell_subtype = models.ForeignKey('CellSubtype', null=True, blank=True, on_delete=models.CASCADE)
    organ = models.ForeignKey('Organ', on_delete=models.CASCADE)

    def __str__(self):
        return '{} ({} {})'.format(
            self.cell_type,
            self.species,
            self.organ
        )

    def get_absolute_url(self):
        return "/cellsamples/celltype/{}".format(self.id)

    def get_post_submission_url(self):
        return reverse('celltype_list')


@reversion.register(follow=['cell_type'])
class CellSubtype(LockableModel):
    """CellSubtype details a subtype (e.g. a cell line)

    It is important to note that CellSubtypes without cell_type are "generic" and can be applied to any cell type
    """
    class Meta(object):
        ordering = ('cell_subtype', )

    # Unsemantic name (should just be name)
    cell_subtype = models.CharField(max_length=255, unique=True,
                                    help_text="Example: motor (type of neuron), "
                                              "skeletal (type of muscle), etc.")

    # Cell Subtypes with a None value for cell_type are generic
    cell_type = models.ForeignKey(CellType, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return '{}'.format(self.cell_subtype)

    def get_absolute_url(self):
        return "/cellsamples/cellsubtype/{}".format(self.id)

    def get_post_submission_url(self):
        return reverse('cellsubtype_list')


# TODO: Just having this be "supplier" is confusing, supplier of what? Should be specific or general
@reversion.register(follow=['cellsample_set'])
class Supplier(LockableModel):
    """Supplier gives information for institutions that distribute cell samples and related materials"""
    class Meta(object):
        ordering = ('name', )
    name = models.CharField(max_length=255, unique=True)
    phone = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return '{}'.format(self.name)

    # TODO
    def get_post_submission_url(self):
        return reverse('')


@reversion.register(follow=['assaysetupcell_set'])
class Biosensor(LockableModel):
    """Biosensor describes a biosensor used on cell samples"""
    class Meta(object):
        ordering = ('name', )
    name = models.CharField(max_length=255, unique=True)
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE)
    product_id = models.CharField(max_length=255, blank=True)
    lot_number = models.CharField(max_length=255, blank=True,
                                  verbose_name='Lot#')
    description = models.CharField(max_length=512, blank=True)

    def __str__(self):
        return '{}'.format(self.name)

    # TODO
    def get_post_submission_url(self):
        return reverse('')


@reversion.register(follow=['cell_type', 'cell_subtype'])
class CellSample(FlaggableModel):
    """A Cell Sample describes a particular selection of cells used for experiments"""

    class Meta(object):
        verbose_name = 'Cell Sample'
        # NOT USEFUL NOW THAT IT IS NO LONGER REQUIRED
        # ordering = ('-receipt_date', )

    cell_type = models.ForeignKey('CellType', on_delete=models.CASCADE)
    cell_subtype = models.ForeignKey('CellSubtype', on_delete=models.CASCADE)

    # Group may need to be explicitly defined here as opposed to using a mixin
    # group = models.ForeignKey('auth.Group', help_text='Bind to a group', on_delete=models.CASCADE)

    # DEPRECATED
    # cell_source CONSIDERED UNINTUITIVE
    # CELLSOURCETYPE = (
    #     ('Freshly isolated', 'Freshly isolated'),
    #     ('Cryopreserved', 'Cryopreserved'),
    #     ('Cultured', 'Cultured'),
    #     ('Other', 'Other'),
    # )
    #
    # cell_source = models.CharField(max_length=20,
    #                                choices=CELLSOURCETYPE, default='Primary',
    #                                blank=True)

    notes = models.TextField(blank=True, default='')
    receipt_date = models.DateField(null=True, blank=True)

    # SAMPLE
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE)
    barcode = models.CharField(max_length=255, blank=True, verbose_name='Barcode/Lot#')
    product_id = models.CharField(max_length=255, blank=True, default='')

    # PATIENT (move to subtype?)
    # Technically, these are sexes, not genders
    GENDER_CHOICES = (
        ('N', 'Not-specified'),
        ('F', 'Female'),
        ('M', 'Male'),
    )
    patient_age = models.IntegerField(null=True, blank=True)
    patient_gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default=GENDER_CHOICES[0][0],
        blank=True
    )
    patient_condition = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    # ISOLATION
    isolation_datetime = models.DateField(
        "Isolation",
        blank=True,
        null=True
    )
    isolation_method = models.CharField(
        "Method",
        max_length=255,
        blank=True,
        default=''
    )
    isolation_notes = models.CharField(
        "Notes",
        max_length=255,
        blank=True,
        default=''
    )

    # VIABILITY
    viable_count = models.FloatField(null=True, blank=True)

    # Removed: Deemed confusing/not useful
    # VIABLE_COUNT_UNIT_CHOICES = (
    #     ('N', 'Not-specified'),
    #     ('A', 'per area'),
    #     ('V', 'per volume'),
    # )
    # viable_count_unit = models.CharField(max_length=1,
    #                                      choices=VIABLE_COUNT_UNIT_CHOICES,
    #                                      default=VIABLE_COUNT_UNIT_CHOICES[0][
    #                                          0], blank=True)

    percent_viability = models.FloatField(null=True, blank=True)
    cell_image = models.ImageField(
        upload_to='cellsamples',
        null=True,
        blank=True
    )

    # THIS IS NOW EXPLICITLY LISTED
    group = models.ForeignKey(Group, help_text='Bind to a group', on_delete=models.CASCADE)

    def __str__(self):
        if self.barcode:
            return '{0} {1} ({2}-{3})'.format(
                self.cell_subtype,
                self.cell_type,
                self.supplier,
                self.barcode
            )
        else:
            return '{0} {1} ({2})'.format(
                self.cell_subtype,
                self.cell_type,
                self.supplier
            )

    # CRUDE
    def get_string_for_processing(self):
        if self.patient_age or self.patient_gender != 'N' or self.patient_condition:
            return COMBINED_VALUE_DELIMITER.join(str(x) for x in [
                self.receipt_date,
                self.cell_type,
                self.cell_subtype,
                self.supplier,
                self.barcode,
                '{} year old {} {}'.format(self.patient_age, self.patient_gender, self.patient_condition),
                str(self),
            ])
        else:
            return COMBINED_VALUE_DELIMITER.join(str(x) for x in [
                self.receipt_date,
                self.cell_type,
                self.cell_subtype,
                self.supplier,
                self.barcode,
                '',
                str(self),
            ])

    def get_absolute_url(self):
        return "/cellsamples/cellsample/{}".format(self.id)

    def get_post_submission_url(self):
        return reverse('cellsample_list')
