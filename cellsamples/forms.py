from django import forms
from .models import (
    CellSample,
    CellType,
    CellSubtype,
    Supplier,
    Biosensor
)
from mps.forms import SignOffMixin, BootstrapForm, tracking

# ODD, not exactly semantic to import from this file
from mps.templatetags.custom_filters import filter_groups

# TODO: WHY AREN'T THESE IN A CONSOLIDATED PLACE AND THEN IMPORTED?
# These are all of the tracking fields
# tracking = ('created_by', 'created_on', 'modified_on', 'modified_by', 'signed_off_by', 'signed_off_date')


class CellSampleForm(SignOffMixin, BootstrapForm):
    """Form for Cell Samples"""
    def __init__(self, *args, **kwargs):
        """Init the CellSample Form

        Parameters:
        groups -- a queryset of groups (allows us to avoid N+1 problem)
        """
        super(CellSampleForm, self).__init__(*args, **kwargs)
        self.fields['group'].queryset = filter_groups(self.user)
        self.fields['cell_type'].queryset = CellType.objects.all().prefetch_related('organ')
        self.fields['cell_subtype'].queryset = CellSubtype.objects.all().prefetch_related('cell_type')

    class Meta(object):
        model = CellSample
        exclude = tracking
        widgets = {
            'isolation_method': forms.Textarea(attrs={'rows': 3}),
            'isolation_notes': forms.Textarea(attrs={'rows': 3}),
            'patient_condition': forms.Textarea(attrs={'rows': 3}),
        }


class CellTypeForm(SignOffMixin, BootstrapForm):
    """Form for Cell Types"""
    class Meta(object):
        model = CellType
        exclude = tracking
        widgets = {
            'cell_type': forms.Textarea(attrs={'rows': 1}),
        }


class CellSubtypeForm(SignOffMixin, BootstrapForm):
    """Form for Cell Subtypes"""
    def __init__(self, *args, **kwargs):
        super(CellSubtypeForm, self).__init__(*args, **kwargs)
        self.fields['cell_type'].queryset = CellType.objects.all().prefetch_related('organ')

    class Meta(object):
        model = CellSubtype
        exclude = tracking
        widgets = {
            'cell_subtype': forms.Textarea(attrs={'rows': 1}),
        }


class SupplierForm(BootstrapForm):
    """Form for Cell Suppliers (distinct from assay suppliers)"""

    class Meta(object):
        model = Supplier
        exclude = tracking

        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }


class BiosensorForm(BootstrapForm):
    """Form for Cell Suppliers (distinct from assay suppliers)"""

    class Meta(object):
        model = Biosensor
        exclude = tracking

        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }
