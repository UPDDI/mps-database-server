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
    MicrodeviceReference,
    OrganModelCell,
    OrganModelProtocolCell,
    OrganModelProtocolSetting,
    Manufacturer
)
from cellsamples.models import CellType
from assays.models import AssayMatrixItem, AssaySampleLocation
from diseases.models import Disease
from mps.forms import SignOffMixin, BootstrapForm, tracking
from django.forms.models import inlineformset_factory

from mps.templatetags.custom_filters import (
    ADMIN_SUFFIX,
    VIEWER_SUFFIX,
)

# A little strange to import this way: spaghetti
from assays.forms import ModelFormSplitTime, PhysicalUnits

# These are all of the tracking fields
# tracking = ('created_by', 'created_on', 'modified_on', 'modified_by', 'signed_off_by', 'signed_off_date')


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


class OrganModelProtocolInlineForm(BootstrapForm):
    class Meta(object):
        model = OrganModelProtocol
        fields = ('name', 'protocol_file')

        widgets = {
            'name': forms.Textarea(attrs={'rows': 1}),
        }


class OrganModelProtocolForm(BootstrapForm):
    class Meta(object):
        model = OrganModelProtocol
        exclude = tracking + ('organ_model',)

        widgets = {
            'name': forms.Textarea(attrs={'rows': 1}),
            'description': forms.Textarea(attrs={'rows': 6}),
        }


class OrganModelProtocolInlineFormset(BaseInlineFormSet):
    """Formset of organ model protocols"""
    class Meta(object):
        model = OrganModelProtocol
        exclude = tracking

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
    form=OrganModelProtocolInlineForm,
    formset=OrganModelProtocolInlineFormset,
    fields=('name', 'protocol_file'),
    extra=1
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

    def __init__(self, *args, **kwargs):
        super(MicrophysiologyCenterForm, self).__init__(*args, **kwargs)

        non_admin_non_viewer_groups = Group.objects.exclude(
            name__contains=ADMIN_SUFFIX
        ).exclude(
            name__contains=VIEWER_SUFFIX
        )

        bound_to_center = non_admin_non_viewer_groups.exclude(
            center_groups__isnull=True
        )

        self.fields['groups'].queryset = non_admin_non_viewer_groups
        self.fields['accessible_groups'].queryset = bound_to_center


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


class OrganModelProtocolCellForm(ModelFormSplitTime):
    class Meta(object):
        model = OrganModelProtocolCell
        exclude = tracking

    def __init__(self, *args, **kwargs):
        # self.static_choices = kwargs.pop('static_choices', None)
        super(OrganModelProtocolCellForm, self).__init__(*args, **kwargs)

        # Change widget size
        self.fields['cell_sample'].widget.attrs['style'] = 'width:75px;'
        self.fields['passage'].widget.attrs['style'] = 'width:75px;'

        self.fields['density_unit'].queryset = PhysicalUnits.objects.filter(availability__contains='cell').order_by('unit')


class OrganModelProtocolSettingForm(ModelFormSplitTime):
    class Meta(object):
        model = OrganModelProtocolSetting
        exclude = tracking


class OrganModelCellForm(BootstrapForm):
    def __init__(self, *args, **kwargs):
        # self.static_choices = kwargs.pop('static_choices', None)
        super(OrganModelCellForm, self).__init__(*args, **kwargs)

        # Avoid N+1 problem
        self.fields['cell_type'].queryset = CellType.objects.all().prefetch_related('organ')

    class Meta(object):
        model = OrganModelProtocolCell
        exclude = tracking


OrganModelProtocolCellFormsetFactory = inlineformset_factory(
    OrganModelProtocol,
    OrganModelProtocolCell,
    form=OrganModelProtocolCellForm,
    extra=1,
    exclude=[],
)

OrganModelProtocolSettingFormsetFactory = inlineformset_factory(
    OrganModelProtocol,
    OrganModelProtocolSetting,
    form=OrganModelProtocolSettingForm,
    extra=1,
    exclude=[],
)


OrganModelCellFormsetFactory = inlineformset_factory(
    OrganModel,
    OrganModelCell,
    form=OrganModelCellForm,
    extra=1,
    exclude=[],
)


class ManufacturerForm(BootstrapForm):
    class Meta(object):
        model = Manufacturer
        exclude = tracking

        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }
