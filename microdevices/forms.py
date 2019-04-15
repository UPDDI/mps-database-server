from django import forms
from django.forms.models import BaseInlineFormSet
from django.contrib.auth.models import Group
from .models import (
    Microdevice,
    OrganModel,
    OrganModelLocation,
    OrganModelProtocol,
    MicrophysiologyCenter,
    GroupDeferral,
    OrganModelReference,
    MicrodeviceReference
)
from assays.models import AssayMatrixItem, AssaySampleLocation
from diseases.models import Disease
from mps.forms import SignOffMixin, BootstrapForm
from django.forms.models import inlineformset_factory

# These are all of the tracking fields
tracking = ('created_by', 'created_on', 'modified_on', 'modified_by', 'signed_off_by', 'signed_off_date')


class MicrodeviceForm(SignOffMixin, BootstrapForm):
    """Form for Microdevices"""
    class Meta(object):
        model = Microdevice
        exclude = tracking + ('center', 'organ')

        widgets = {
            'number_of_columns': forms.NumberInput(attrs={'style': 'width: 100px;'}),
            'number_of_rows': forms.NumberInput(attrs={'style': 'width: 100px;'}),
            'name': forms.Textarea(attrs={'rows': 1}),
            'references': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class OrganModelForm(SignOffMixin, BootstrapForm):
    """Form for Organ Models"""
    class Meta(object):
        model = OrganModel
        exclude = tracking

        widgets = {
            'name': forms.Textarea(attrs={'rows': 1}),
            'alt_name': forms.Textarea(attrs={'rows': 1}),
            'references': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(OrganModelForm, self).__init__(*args, **kwargs)

        disease_queryset = Disease.objects.all().order_by(
            'name'
        )

        self.fields['disease'].queryset = disease_queryset


class OrganModelLocationForm(BootstrapForm):
    class Meta(object):
        model = OrganModelLocation
        exclude = ('',)


class OrganModelLocationInlineFormset(BaseInlineFormSet):
    """Form for Organ Model Locations"""
    class Meta(object):
        model = OrganModelLocation
        exclude = ('',)

    def __init__(self, *args, **kwargs):
        super(OrganModelLocationInlineFormset, self).__init__(*args, **kwargs)

        sample_location_queryset = AssaySampleLocation.objects.all().order_by(
            'name'
        )

        for form in self.forms:
            form.fields['sample_location'].queryset = sample_location_queryset


OrganModelLocationFormsetFactory = inlineformset_factory(
    OrganModel,
    OrganModelLocation,
    form=OrganModelLocationForm,
    formset=OrganModelLocationInlineFormset,
    extra=1,
    exclude=[],
    widgets={
        'notes': forms.Textarea(attrs={'rows': 6})
    }
)


class OrganModelProtocolForm(BootstrapForm):
    """Form for Organ Model Protocols (as part of an inline)"""
    class Meta(object):
        model = OrganModelProtocol
        exclude = ('',)


class OrganModelProtocolInlineFormset(BaseInlineFormSet):
    """Formset of organ model protocols"""
    class Meta(object):
        model = OrganModelProtocol
        exclude = ('',)

    def clean(self):
        forms_data = [f for f in self.forms if f.cleaned_data]

        for form in forms_data:
            data = form.cleaned_data
            protocol_id = data.get('id', '')
            delete_checked = data.get('DELETE', False)

            # Make sure that no protocol in use is checked for deletion
            if protocol_id and delete_checked:
                if AssayMatrixItem.objects.filter(organ_model_protocol_id=protocol_id):
                    raise forms.ValidationError('You cannot remove protocols that are referenced by a chip/well.')


OrganModelProtocolFormsetFactory = inlineformset_factory(
    OrganModel,
    OrganModelProtocol,
    form=OrganModelProtocolForm,
    formset=OrganModelProtocolInlineFormset,
    extra=1,
    exclude=[],
    widgets={
        'version': forms.TextInput(attrs={'size': 10})
    }
)

OrganModelReferenceFormSetFactory = inlineformset_factory(
    OrganModel,
    OrganModelReference,
    extra=1,
    exclude=[]
)

MicrodeviceReferenceFormSetFactory = inlineformset_factory(
    Microdevice,
    MicrodeviceReference,
    extra=1,
    exclude=[]
)


class MicrophysiologyCenterForm(BootstrapForm):
    class Meta(object):
        model = MicrophysiologyCenter
        exclude = []

        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
        }


class GroupDeferralForm(BootstrapForm):
    class Meta(object):
        model = GroupDeferral
        exclude = []

        widgets = {
            'notes': forms.Textarea(attrs={'rows': 6}),
        }

    def __init__(self, *args, **kwargs):
        super(GroupDeferralForm, self).__init__(*args, **kwargs)

        groups_with_center = MicrophysiologyCenter.objects.all().values_list('groups', flat=True)
        groups_with_center_full = Group.objects.filter(
            id__in=groups_with_center
        ).order_by(
            'name'
        )

        self.fields['group'].queryset = groups_with_center_full
