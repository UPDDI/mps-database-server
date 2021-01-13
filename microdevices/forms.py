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
from assays.forms import ModelFormSplitTime, PhysicalUnits, SetupFormsMixin

import json

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


# Convoluted NOT DRY
# PLEASE CONSOLIDATE
def process_error_with_annotation(prefix, row, column, full_error):
    current_error = dict(full_error)
    modified_error = []

    for error_field, error_values in current_error.items():
        for error_value in error_values:
            modified_error.append([
                '|'.join([str(x) for x in [
                    prefix,
                    row,
                    column,
                    error_field
                ]]) + '-' + error_value
            ])

    return modified_error


class OrganModelForm(SetupFormsMixin, SignOffMixin, BootstrapForm):
    """Form for Organ Models"""
    # CONTRIVED!
    series_data = forms.CharField(required=False)

    class Meta(object):
        model = OrganModel
        exclude = tracking

        fields = (
            'name',
            'organ',
            'disease',
            'center',
            'device',
            'description',
            'model_image',
            'base_model',
            'alt_name',
            'model_type',
            'disease_trigger',
            # TEMPORARY ->
            'series_data',
            # <- TEMPORARY
            'cell_cell_sample',
            'cell_biosensor',
            'cell_density',
            'cell_density_unit',
            'cell_passage',
            'cell_addition_location',
            'setting_setting',
            'setting_unit',
            'setting_value',
            'setting_addition_location',
        )

        widgets = {
            'name': forms.Textarea(attrs={'rows': 1}),
            'alt_name': forms.Textarea(attrs={'rows': 1}),
            'references': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # We use this to determine whether to process the protocols or not
        self.process_protocols = kwargs.pop('process_protocols', False)
        super(OrganModelForm, self).__init__(*args, **kwargs)

        disease_queryset = Disease.objects.all().order_by(
            'name'
        )

        self.fields['disease'].queryset = disease_queryset

        self.fields['series_data'].initial = self.instance.get_group_data_string()

    def clean(self):
        """Initial processing for groups and checking"""
        # clean the form data, before validation
        data = super(OrganModelForm, self).clean()

        # WE ALWAYS CLEAN THE VERSION DATA
        # SLOPPY NOT DRY
        new_setup_data = {}

        # GET PROTOCOLS
        # Unless something bad happened, then we will have the protocols and an Organ Model
        protocols = OrganModelProtocol.objects.filter(organ_model_id=self.instance.id)

        protocol_ids = {protocol.id: True for protocol in protocols}
        protocol_name_to_id = {protocol.name: protocol.id for protocol in protocols}

        # Just have the errors be non-field errors for the moment
        all_errors = {'series_data': [], '__all__': []}
        current_errors = all_errors.get('series_data')
        non_field_errors = all_errors.get('__all__')

        # Am I sticking with the name 'series_data'?
        if self.cleaned_data.get('series_data', None):
            all_data = json.loads(self.cleaned_data.get('series_data', '[]'))
        else:
            # Contrived defaults
            all_data = {
                'series_data': [],
            }

        # The data for groups is currently stored in series_data
        all_setup_data = all_data.get('series_data')

        # Catch technically empty setup data
        setup_data_is_empty = True

        for group_set in all_setup_data:
            if group_set:
                setup_data_is_empty = not any(group_set.values())

        if setup_data_is_empty:
            all_setup_data = []

        # if commit and all_setup_data:
        # SEE BASE MODELS.PY FOR WHY COMMIT IS NOT HERE
        if all_setup_data:
            new_cells = []
            update_cells = []
            deleted_cells = []

            new_settings = []
            update_settings = []
            deleted_settings = []

            # For now, chips are are all in one row
            for setup_row, setup_group in enumerate(all_setup_data):
                # If there is an ID, check to see if this is a valid protocol
                # Skip if it is not
                current_protocol_id = setup_group.get('id', None)

                if current_protocol_id:
                    current_protocol_id = int(current_protocol_id)

                if current_protocol_id and current_protocol_id not in protocol_ids:
                    current_protocol_id = None
                # If there is not an id, then use the name and get the id
                # If self.process_protocols is True, then we need to make sure that all of the protocols DEFINITELY exist
                elif current_protocol_id is None and self.process_protocols:
                    current_protocol_id = protocol_name_to_id.get(setup_group.get('name', None), None)
                # If we aren't saving yet, then the id for new protocols doesn't really matter (they don't exist yet, we just need it to have truthiness)
                elif current_protocol_id is None and not self.process_protocols:
                    current_protocol_id = setup_group.get('name', None)

                # Skip if invalid
                if not current_protocol_id:
                    continue

                # Always iterate for cells and settings
                # Keep in mind that to decrease sparsity related data is now tied to a protocol
                for prefix, current_objects in setup_group.items():
                    if prefix in ['cell', 'setting'] and setup_group[prefix]:
                        for setup_column, current_object in enumerate(current_objects):
                            # Skip if nothing
                            if not current_object:
                                continue

                            # Crudely convert to int
                            for current_field, current_value in current_object.items():
                                if current_field.endswith('_id'):
                                    if current_value:
                                        current_object.update({
                                            current_field: int(current_value)
                                        })
                                    else:
                                        current_object.update({
                                            current_field: None
                                        })

                            # NOTE TODO TODO TODO
                            # I am probably just going to blow up all of the old related data for the moment and always add
                            # This is much faster to write but more expensive than it needs to be
                            # On the bright side, it won't orphan any data because data is bound to a Protocol rather than the constituent pieces...

                            # TRICKY: in theory, this could be totally wrong
                            # HOWEVER: the only time that it should ever try to save is if self.process_protocols is True
                            current_object.update({
                                'organ_model_protocol_id': current_protocol_id
                            })

                            if prefix == 'cell':
                                new_cell = OrganModelProtocolCell(**current_object)

                                try:
                                    new_cell.full_clean(exclude=['organ_model_protocol'])
                                    new_cells.append(new_cell)
                                except forms.ValidationError as e:
                                    # May need to revise process_error
                                    current_errors.append(
                                        process_error_with_annotation(
                                            prefix,
                                            setup_row,
                                            setup_column,
                                            e
                                        )
                                    )
                                    group_has_error = True

                            elif prefix == 'setting':
                                new_setting = OrganModelProtocolSetting(**current_object)
                                try:
                                    new_setting.full_clean(exclude=['organ_model_protocol'])
                                    new_settings.append(new_setting)
                                except forms.ValidationError as e:
                                    current_errors.append(
                                        process_error_with_annotation(
                                            prefix,
                                            setup_row,
                                            setup_column,
                                            e
                                        )
                                    )
                                    group_has_error = True

        if current_errors or non_field_errors:
            non_field_errors.append(['Please review the table below for errors.'])
            raise forms.ValidationError(all_errors)

        new_setup_data.update({
            # Everything will be passed to new, for now
            'new_cells': new_cells,
            'new_settings': new_settings,

            # TODO TODO TODO
            # First pass we are not going to bother with this
            'update_cells': update_cells,
            'update_settings': update_settings,

            # THESE GET TRICKY! IDEALLY WE WANT TO DELETE AS FEW RELATED AS POSSIBLE
            # TODO TODO TODO
            # First pass we are not going to bother with this
            'deleted_cells': deleted_cells,
            'deleted_settings': deleted_settings,
        })

        data.update({
            'processed_setup_data': new_setup_data
        })

        return data

    # TODO: REVISE TO PROPERLY DEAL WITH UPDATES WITH bulk_update
    def save(self, commit=True):
        organ_model = super(OrganModelForm, self).save(commit)

        protocols = OrganModelProtocol.objects.filter(organ_model_id=self.instance.id)

        if self.process_protocols and commit:
            all_setup_data = self.cleaned_data.get('processed_setup_data', None)

            if all_setup_data and commit:
                # Why?
                new_cells = all_setup_data.get('new_cells', None)
                new_settings = all_setup_data.get('new_settings', None)

                update_cells = all_setup_data.get('update_cells', None)
                update_settings = all_setup_data.get('update_settings', None)

                deleted_cells = all_setup_data.get('deleted_cells', None)
                deleted_settings = all_setup_data.get('deleted_settings', None)

                # Barbaric, just obscene in its grotesque cruelty
                # How could one do such a thing and not be deemed heartless?
                # KILL ALL CELLS AND SETTINGS:
                OrganModelProtocolCell.objects.filter(organ_model_protocol__in=protocols).delete()
                OrganModelProtocolSetting.objects.filter(organ_model_protocol__in=protocols).delete()

                if new_cells:
                    OrganModelProtocolCell.objects.bulk_create((new_cells))

                if new_settings:
                    OrganModelProtocolSetting.objects.bulk_create((new_settings))

        return organ_model


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
        fields = (
            'name',
            'protocol_file',
            'disease',
            'disease_trigger',
            'description'
        )

        widgets = {
            'name': forms.Textarea(attrs={'rows': 1}),
            'description': forms.Textarea(attrs={'rows': 6}),
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
    # fields=('name', 'protocol_file'),
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
