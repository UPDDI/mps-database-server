import datetime
from django import forms
from django.contrib.auth.models import Group
from django.forms.models import (
    BaseInlineFormSet,
    inlineformset_factory,
    BaseModelFormSet,
    modelformset_factory,
)
from cellsamples.models import Biosensor
from assays.models import (
    AssayStudyConfiguration,
    AssayStudy,
    AssayStudySupportingData,
    AssayStudyAssay,
    AssayMatrix,
    AssayCategory,
    TEST_TYPE_CHOICES,
    PhysicalUnits,
    AssaySampleLocation,
    AssaySetting,
    AssaySetupCompound,
    AssaySetupCell,
    AssaySetupSetting,
    AssayMatrixItem,
    AssayStudyStakeholder,
    AssayTarget,
    AssayMethod,
    AssayStudyModel,
    AssayStudySet,
    AssayReference,
    AssayStudyReference,
    AssayStudySetReference,
    AssayTarget,
    AssayMeasurementType,
    AssayMethod,
    AssaySetting,
    AssaySupplier,
    AssayCategory,
    AssayPlateReaderMap,
    AssayPlateReaderMapItem,
    AssayPlateReaderMapItemValue,
    AssayPlateReaderMapDataFile,
    AssayPlateReaderMapDataFileBlock,
    # ...
    AssayGroup,
    AssayGroupCell,
    AssayGroupCompound,
    AssayGroupSetting,
    assay_plate_reader_time_unit_choices,
    assay_plate_reader_main_well_use_choices,
    assay_plate_reader_blank_well_use_choices,
    assay_plate_reader_map_info_plate_size_choices,
    assay_plate_reader_volume_unit_choices,
    assay_plate_reader_file_delimiter_choices,
    upload_file_location,
    AssayOmicDataFileUpload,
    AssayOmicDataPoint,
    # AssayOmicDataGroup,
)
from compounds.models import Compound, CompoundInstance, CompoundSupplier
from microdevices.models import (
    MicrophysiologyCenter,
    Microdevice,
    OrganModel,
    OrganModelProtocol
)
from mps.forms import SignOffMixin, BootstrapForm, tracking
import string
from captcha.fields import CaptchaField

from .utils import (
    # validate_file,
    # get_chip_details,
    # get_plate_details,
    TIME_CONVERSIONS,
    # EXCLUDED_DATA_POINT_CODE,
    AssayFileProcessor,
    get_user_accessible_studies,
    plate_reader_data_file_process_data,
    CALIBRATION_CURVE_MASTER_DICT,
    calibration_choices,
    omic_data_file_process_data,
    COLUMN_HEADERS,
)

from django.utils import timezone

from mps.templatetags.custom_filters import is_group_admin, filter_groups, ADMIN_SUFFIX

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError

from mps.settings import MEDIA_ROOT
import ujson as json
import os
import csv
import re
import copy

from mps.utils import (
    get_split_times,
)

# TODO REFACTOR WHITTLING TO BE HERE IN LIEU OF VIEW
# TODO REFACTOR FK QUERYSETS TO AVOID N+1

# These are all of the tracking fields
# tracking = (
#     'created_by',
#     'created_on',
#     'modified_on',
#     'modified_by',
#     'signed_off_by',
#     'signed_off_date',
#     'locked',
#     'restricted'
# )
# Excluding restricted is likewise useful
restricted = ('restricted',)
# Group
group = ('group',)


def get_dic_for_custom_choice_field(form, filters=None):
    dic = {}

    fields = form.custom_fields
    parent = form.model

    for field in fields:
        model = parent._meta.get_field(field).related_model
        if filters and filters.get(field, None):
            dic.update({
                field: {str(instance.id): instance for instance in model.objects.filter(**filters.get(field))}
            })
        else:
            dic.update({
                field: {str(instance.id): instance for instance in model.objects.all()}
            })

    return dic


class SetupFormsMixin(BootstrapForm):
    ### ADDING SETUP CELLS
    cell_cell_sample = forms.IntegerField(required=False)
    cell_biosensor = forms.ModelChoiceField(
        queryset=Biosensor.objects.all().prefetch_related('supplier'),
        required=False,
        # Default is naive
        initial=2
    )
    cell_density = forms.FloatField(required=False)

    # TODO THIS IS TO BE HAMMERED OUT
    cell_density_unit = forms.ModelChoiceField(
        queryset=PhysicalUnits.objects.filter(
            availability__contains='cell'
        ).order_by('unit'),
        required=False
    )

    cell_passage = forms.CharField(required=False)

    cell_addition_location = forms.ModelChoiceField(
        # Avoid duplicate query
        queryset=AssaySampleLocation.objects.all().order_by('name'),
        # queryset=AssaySampleLocation.objects.none(),
        required=False
    )

    ### ?ADDING SETUP SETTINGS
    setting_setting = forms.ModelChoiceField(
        queryset=AssaySetting.objects.all().order_by('name'),
        required=False
    )
    setting_unit = forms.ModelChoiceField(
        queryset=PhysicalUnits.objects.all().order_by('base_unit','scale_factor'),
        required=False
    )

    setting_value = forms.CharField(required=False)

    setting_addition_location = forms.ModelChoiceField(
        # Avoid duplicate query
        queryset=AssaySampleLocation.objects.all().order_by('name'),
        # queryset=AssaySampleLocation.objects.none(),
        required=False
    )

    ### ADDING COMPOUNDS
    compound_compound = forms.ModelChoiceField(
        queryset=Compound.objects.all().order_by('name'),
        required=False
    )
    # Notice the special exception for %
    compound_concentration_unit = forms.ModelChoiceField(
        queryset=(PhysicalUnits.objects.filter(
            unit_type__unit_type='Concentration'
        ).order_by(
            'base_unit__unit',
            'scale_factor'
        ) | PhysicalUnits.objects.filter(unit='%')),
        required=False, initial=4
    )
    compound_concentration = forms.FloatField(required=False)

    compound_addition_location = forms.ModelChoiceField(
        # Avoid duplicate query
        queryset=AssaySampleLocation.objects.all().order_by('name'),
        # queryset=AssaySampleLocation.objects.none(),
        required=False
    )
    # Text field (un-saved) for supplier
    compound_supplier_text = forms.CharField(
        required=False,
        initial=''
    )
    # Text field (un-saved) for lot
    compound_lot_text = forms.CharField(
        required=False,
        initial=''
    )
    # Receipt date
    compound_receipt_date = forms.DateField(required=False)

    # For MPS Models etc.
    test_type = forms.ChoiceField(
        initial='control',
        choices=TEST_TYPE_CHOICES,
        required=False
    )
    organ_model_full = forms.ModelChoiceField(
        queryset=OrganModel.objects.all().order_by('name'),
        required=False,
        label='Matrix Item MPS Model'
    )
    organ_model_protocol_full = forms.ModelChoiceField(
        queryset=OrganModelProtocol.objects.all().order_by('name'),
        required=False,
        label='Matrix Item MPS Model Version'
    )

    def __init__(self, *args, **kwargs):
        super(SetupFormsMixin, self).__init__(*args, **kwargs)

        sections_with_times = (
            'compound',
            'cell',
            'setting'
        )

        for time_unit in list(TIME_CONVERSIONS.keys()):
            for current_section in sections_with_times:
                # Create fields for Days, Hours, Minutes
                self.fields[current_section + '_addition_time_' + time_unit] = forms.FloatField(
                    initial=0,
                    required=False,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control required',
                        'style': 'width:75px;'
                    })
                )
                self.fields[current_section + '_duration_' + time_unit] = forms.FloatField(
                    initial=0,
                    required=False,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control required',
                        'style': 'width:75px;'
                    })
                )

        self.fields['cell_cell_sample'].widget.attrs['style'] = 'width:75px;'
        self.fields['cell_passage'].widget.attrs['style'] = 'width:75px;'

        # DUMB, BAD (can't have them be "actually" required or they prevent submission
        add_required_to = [
            'cell_cell_sample',
            'cell_biosensor',
            'cell_density',
            'cell_density_unit',
            'cell_addition_location',
            'setting_setting',
            'setting_unit',
            'setting_value',
            'setting_addition_location',
            'compound_compound',
            'compound_concentration_unit',
            'compound_concentration',
            'compound_addition_location',
        ]

        for current_field in add_required_to:
            self.fields[current_field].widget.attrs['class'] += ' required'

            # Sloppy
            if hasattr(self.fields[current_field], '_queryset'):
                if hasattr(self.fields[current_field]._queryset, 'model'):
                    # Usually one would use a hyphen rather than an underscore
                    # self.fields[field].widget.attrs['data-app'] = self.fields[field]._queryset.model._meta.app_label
                    self.fields[current_field].widget.attrs['data_app'] = self.fields[current_field]._queryset.model._meta.app_label

                    # self.fields[field].widget.attrs['data-model'] = self.fields[field]._queryset.model._meta.object_name
                    self.fields[current_field].widget.attrs['data_model'] = self.fields[current_field]._queryset.model._meta.object_name

                    self.fields[current_field].widget.attrs['data_verbose_name'] = self.fields[current_field]._queryset.model._meta.verbose_name

                    # Possibly dumber
                    if hasattr(self.fields[current_field]._queryset.model, 'get_add_url_manager'):
                        self.fields[current_field].widget.attrs['data_add_url'] = self.fields[current_field]._queryset.model.get_add_url_manager()

        # Avoid duplicate queries for the sample locations
        # sample_locations = AssaySampleLocation.objects.all().order_by('name')
        # self.fields['cell_addition_location'].queryset = sample_locations
        # self.fields['compound_addition_location'].queryset = sample_locations
        # self.fields['setting_addition_location'].queryset = sample_locations

        # CRUDE: MAKE SURE NO SELECTIZE INTERFERING
        self.fields['organ_model_full'].widget.attrs['class'] = 'no-selectize'
        self.fields['organ_model_protocol_full'].widget.attrs['class'] = 'no-selectize'
        self.fields['test_type'].widget.attrs['class'] = 'no-selectize'


# DEPRECATED NO LONGER NEEDED AS CHARFIELDS NOW STRIP AUTOMATICALLY
class ModelFormStripWhiteSpace(BootstrapForm):
    """Strips the whitespace from char and text fields"""
    def clean(self):
        cd = self.cleaned_data
        for field_name, field in list(self.fields.items()):
            if isinstance(field, forms.CharField):
                if self.fields[field_name].required and not cd.get(field_name, None):
                    self.add_error(field_name, "This is a required field.")
                else:
                    cd[field_name] = cd[field_name].strip()

        return super(ModelFormStripWhiteSpace, self).clean()


class ModelFormSplitTime(BootstrapForm):
    def __init__(self, *args, **kwargs):
        super(ModelFormSplitTime, self).__init__(*args, **kwargs)

        for time_unit in list(TIME_CONVERSIONS.keys()):
            if self.fields.get('addition_time', None):
                # Create fields for Days, Hours, Minutes
                self.fields['addition_time_' + time_unit] = forms.FloatField(
                    initial=0,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'style': 'width:75px;'
                    })
                )
                # Set default
                self.fields['addition_time_' + time_unit].widget.attrs['data-default'] = 0
            if self.fields.get('duration', None):
                self.fields['duration_' + time_unit] = forms.FloatField(
                    initial=0,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'style': 'width:75px;'
                    })
                )
                # Set default
                self.fields['duration_' + time_unit].widget.attrs['data-default'] = 0

        # Fill additional time
        if self.fields.get('addition_time', None):
            addition_time_in_minutes_remaining = getattr(self.instance, 'addition_time', 0)
            if not addition_time_in_minutes_remaining:
                addition_time_in_minutes_remaining = 0
            for time_unit, conversion in list(TIME_CONVERSIONS.items()):
                initial_time_for_current_field = int(addition_time_in_minutes_remaining / conversion)
                if initial_time_for_current_field:
                    self.fields['addition_time_' + time_unit].initial = initial_time_for_current_field
                    addition_time_in_minutes_remaining -= initial_time_for_current_field * conversion
            # Add fractions of minutes if necessary
            if addition_time_in_minutes_remaining:
                self.fields['addition_time_minute'].initial += addition_time_in_minutes_remaining

        # Fill duration
        if self.fields.get('duration', None):
            duration_in_minutes_remaining = getattr(self.instance, 'duration', 0)
            if not duration_in_minutes_remaining:
                duration_in_minutes_remaining = 0
            for time_unit, conversion in list(TIME_CONVERSIONS.items()):
                initial_time_for_current_field = int(duration_in_minutes_remaining / conversion)
                if initial_time_for_current_field:
                    self.fields['duration_' + time_unit].initial = initial_time_for_current_field
                    duration_in_minutes_remaining -= initial_time_for_current_field * conversion
            # Add fractions of minutes if necessary
            if duration_in_minutes_remaining:
                self.fields['duration_minute'].initial += duration_in_minutes_remaining

    def clean(self):
        cleaned_data = super(ModelFormSplitTime, self).clean()

        if cleaned_data and not cleaned_data.get('DELETE', False):
            cleaned_data.update({
                'addition_time': 0,
                'duration': 0
            })
            for time_unit, conversion in list(TIME_CONVERSIONS.items()):
                cleaned_data.update({
                    'addition_time': cleaned_data.get('addition_time') + cleaned_data.get('addition_time_' + time_unit,
                                                                                          0) * conversion,
                    'duration': cleaned_data.get('duration') + cleaned_data.get('duration_' + time_unit, 0) * conversion
                })

        return cleaned_data


# TODO TODO TODO PLEASE, PLEASE GET RID OF THIS TRASH!
class BaseModelFormSetForcedUniqueness(BaseModelFormSet):
    def clean(self):
        self.validate_unique()

    def validate_unique(self):
        # Collect unique_checks and date_checks to run from all the forms.
        all_unique_checks = set()
        all_date_checks = set()
        forms_to_delete = self.deleted_forms
        valid_forms = [form for form in self.forms if form not in forms_to_delete and form.is_valid()]
        for form in valid_forms:
            # exclude = form._get_validation_exclusions()
            # unique_checks, date_checks = form.instance._get_unique_checks(exclude=exclude)
            unique_checks, date_checks = form.instance._get_unique_checks()
            all_unique_checks = all_unique_checks.union(set(unique_checks))
            all_date_checks = all_date_checks.union(set(date_checks))

        errors = []
        # Do each of the unique checks (unique and unique_together)
        for uclass, unique_check in all_unique_checks:
            seen_data = set()
            for form in valid_forms:
                # PLEASE NOTE: SPECIAL EXCEPTION FOR FORMS WITH NO ID TO AVOID TRIGGERING ID DUPLICATE
                if unique_check == ('id',) and not form.cleaned_data.get('id', ''):
                    # IN POOR TASTE, BUT EXPEDIENT
                    continue

                # get data for each field of each of unique_check
                # PLEASE NOTE THAT THIS GETS ALL FIELDS, EVEN IF NOT IN THE FORM
                row_data = (
                    form.cleaned_data[field] if field in form.cleaned_data else getattr(form.instance, field, None) for field in unique_check
                )

                # Reduce Model instances to their primary key values
                row_data = tuple(d._get_pk_val() if hasattr(d, '_get_pk_val') else d for d in row_data)
                # if row_data and None not in row_data:
                # if we've already seen it then we have a uniqueness failure
                if row_data in seen_data:
                    # poke error messages into the right places and mark
                    # the form as invalid
                    errors.append(self.get_unique_error_message(unique_check))
                    form._errors[NON_FIELD_ERRORS] = self.error_class([self.get_form_error()])
                    # remove the data from the cleaned_data dict since it was invalid
                    for field in unique_check:
                        if field in form.cleaned_data:
                            del form.cleaned_data[field]
                # mark the data as seen
                seen_data.add(row_data)
        # iterate over each of the date checks now
        for date_check in all_date_checks:
            seen_data = set()
            uclass, lookup, field, unique_for = date_check
            for form in valid_forms:
                # see if we have data for both fields
                if (form.cleaned_data and form.cleaned_data[field] is not None and form.cleaned_data[unique_for] is not None):
                    # if it's a date lookup we need to get the data for all the fields
                    if lookup == 'date':
                        date = form.cleaned_data[unique_for]
                        date_data = (date.year, date.month, date.day)
                    # otherwise it's just the attribute on the date/datetime
                    # object
                    else:
                        date_data = (getattr(form.cleaned_data[unique_for], lookup),)
                    data = (form.cleaned_data[field],) + date_data
                    # if we've already seen it then we have a uniqueness failure
                    if data in seen_data:
                        # poke error messages into the right places and mark
                        # the form as invalid
                        errors.append(self.get_date_error_message(date_check))
                        form._errors[NON_FIELD_ERRORS] = self.error_class([self.get_form_error()])
                        # remove the data from the cleaned_data dict since it was invalid
                        del form.cleaned_data[field]
                    # mark the data as seen
                    seen_data.add(data)

        if errors:
            raise forms.ValidationError(errors)


# TODO TODO TODO WILL NEED TO CHANGE THIS WITH DJANGO VERSION NO DOUBT
class BaseInlineFormSetForcedUniqueness(BaseModelFormSetForcedUniqueness, BaseInlineFormSet):
    def clean(self):
        self.validate_unique()


class DicModelChoiceField(forms.Field):
    """Special field using dictionary instead of queryset as choices

    This is to prevent ludicrous numbers of queries
    """
    widget = forms.TextInput

    def __init__(self, name, parent, dic, *args, **kwargs):
        self.name = name
        self.parent = parent
        self.dic = dic
        self.model = self.parent._meta.get_field(self.name).related_model

        super(DicModelChoiceField, self).__init__(*args, **kwargs)

        # Make sure required is set properly
        self.required = self.widget.required = not (
            self.parent._meta.get_field(self.name).null
            and
            self.parent._meta.get_field(self.name).blank
        )

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            value = self.dic.get(self.name).get(value)
        except:
            raise forms.ValidationError(self.error_messages['invalid_choice'], code='invalid_choice')
        return value

    def valid_value(self, value):
        """Check to see if the provided value is a valid choice"""
        if str(value.id) in self.dic.get(self.name):
            return True
        return False


class AssayStudyConfigurationForm(SignOffMixin, BootstrapForm):
    """Frontend Form for Study Configurations"""
    class Meta(object):
        model = AssayStudyConfiguration
        widgets = {
            'name': forms.Textarea(attrs={'cols': 50, 'rows': 1}),
            'media_composition': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
            'hardware_description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }
        exclude = tracking


class AssayStudyModelForm(BootstrapForm):
    class Meta(object):
        model = AssayStudyModel
        exclude = ('' ,)

    def __init__(self, *args, **kwargs):
        super(AssayStudyModelForm, self).__init__(*args, **kwargs)
        self.fields['label'].widget.attrs.update({
            'size': '4',
            'max_length': '2'
        })
        self.fields['sequence_number'].widget.attrs.update({
            'size': '4',
            'max_length': '2'
        })
        self.fields['output'].widget.attrs.update({
            'size': '20',
            'max_length': '20'
        })


# FormSet for Study Models
AssayStudyModelFormSet = inlineformset_factory(
    AssayStudyConfiguration,
    AssayStudyModel,
    extra=1,
    form=AssayStudyModelForm,
    widgets={
        'label': forms.TextInput(attrs={'size': 2}),
        'sequence_number': forms.TextInput(attrs={'size': 2})
    }
)


def label_to_number(label):
    """Returns a numeric index from an alphabetical index"""
    num = 0
    for char in label:
        if char in string.ascii_letters:
            num = num * 26 + (ord(char.upper()) - ord('A')) + 1
    return num


# Now uses unicode instead of string
def stringify_excel_value(value):
    """Given an excel value, return a unicode cast of it

    This also converts floats to integers when possible
    """
    # If the value is just a string literal, return it
    if type(value) == str or type(value) == str:
        return str(value)
    else:
        try:
            # If the value can be an integer, make it into one
            if int(value) == float(value):
                return str(int(value))
            else:
                return str(float(value))
        except:
            return str(value)


class AssayStudyAssayInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        """Init APRA inline

        Filters units so that only units marked 'readout' appear
        """
        super(AssayStudyAssayInlineFormSet, self).__init__(*args, **kwargs)

        target_queryset = AssayTarget.objects.all().order_by('name')

        method_queryset = AssayMethod.objects.all().order_by('name')

        # unit_queryset = PhysicalUnits.objects.filter(
        #     availability__icontains='readout'
        # ).order_by('unit_type__unit_type', 'base_unit__unit', 'scale_factor')

        unit_queryset = PhysicalUnits.objects.order_by('unit_type__unit_type', 'base_unit__unit', 'scale_factor')

        category_queryset = AssayCategory.objects.all().order_by('name')

        for form in self.forms:
            form.fields['target'].queryset = target_queryset
            form.fields['method'].queryset = method_queryset
            form.fields['unit'].queryset = unit_queryset

            form.fields['category'] = forms.ModelChoiceField(
                queryset=category_queryset,
                required=False,
                empty_label='All'
            )


class ReadyForSignOffForm(forms.Form):
    captcha = CaptchaField()
    message = forms.TextInput()


# TODO PLEASE REVIEW
class AssayStudyForm(SignOffMixin, BootstrapForm):
    def __init__(self, *args, **kwargs):
        """Init the Study Form

        Kwargs:
        groups -- a queryset of groups (allows us to avoid N+1 problem)
        """
        super(AssayStudyForm, self).__init__(*args, **kwargs)
        self.fields['group'].queryset = filter_groups(self.user)

        # Crudely force required class
        for current_field in ['total_device_volume', 'flow_rate', 'number_of_relevant_cells']:
            self.fields[current_field].widget.attrs['class'] += ' required'

    class Meta(object):
        model = AssayStudy
        widgets = {
            'assay_run_id': forms.Textarea(attrs={'rows': 1}),
            'name': forms.Textarea(attrs={'rows': 1}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 100}),
        }
        exclude = tracking + restricted + ('access_groups', 'signed_off_notes', 'bulk_file', 'collaborator_groups')

    def clean(self):
        """Checks for at least one study type"""
        # clean the form data, before validation
        data = super(AssayStudyForm, self).clean()

        if not any([data['toxicity'], data['efficacy'], data['disease'], data['cell_characterization'], data['pbpk_steady_state'], data['pbpk_bolus']]):
            raise forms.ValidationError('Please select at least one study type')

        if data.get('pbpk_steady_state', '') and (not data.get('number_of_relevant_cells', '') or not data.get('flow_rate', '')):
            raise forms.ValidationError('Continuous Infusion PBPK Requires Number of Cells Per MPS Model and Flow Rate')

        if data.get('pbpk_bolus', '') and (not data.get('number_of_relevant_cells', '') or not data.get('total_device_volume', '')):
            raise forms.ValidationError('Bolus PBPK Requires Number of Cells Per MPS Model and Total Device Volume')

        return data


class AssayStudyDetailForm(SignOffMixin, BootstrapForm):
    def __init__(self, *args, **kwargs):
        super(AssayStudyDetailForm, self).__init__(*args, **kwargs)
        # Get valid groups for the dropdown
        self.fields['group'].queryset = filter_groups(self.user)

        # Crudely force required class
        for current_field in ['total_device_volume', 'flow_rate', 'number_of_relevant_cells']:
            self.fields[current_field].widget.attrs['class'] += ' required'

    class Meta(object):
        model = AssayStudy
        widgets = {
            'name': forms.Textarea(attrs={'rows': 1}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 100}),
        }
        # Since we are splitting into multiple forms, includes are safer
        fields = (
            'group',
            'toxicity',
            'efficacy',
            'disease',
            'cell_characterization',
            'start_date',
            'use_in_calculations',
            'protocol',
            'image',
            'pbpk_steady_state',
            'pbpk_bolus',
            'number_of_relevant_cells',
            'total_device_volume',
            'flow_rate',
            'name',
            'description',
        )

    def clean(self):
        """Checks for at least one study type"""
        # clean the form data, before validation
        data = super(AssayStudyDetailForm, self).clean()

        if not any([data['toxicity'], data['efficacy'], data['disease'], data['cell_characterization'], data['pbpk_steady_state'], data['pbpk_bolus']]):
            raise forms.ValidationError('Please select at least one study type')

        if data.get('pbpk_steady_state', '') and (not data.get('number_of_relevant_cells', '') or not data.get('flow_rate', '')):
            raise forms.ValidationError('Continuous Infusion PBPK Requires Number of Cells Per MPS Model and Flow Rate')

        if data.get('pbpk_bolus', '') and (not data.get('number_of_relevant_cells', '') or not data.get('total_device_volume', '')):
            raise forms.ValidationError('Bolus PBPK Requires Number of Cells Per MPS Model and Total Device Volume')

        return data


class AssayStudyGroupForm(SetupFormsMixin, SignOffMixin, BootstrapForm):
    # CONTRIVANCES
    # test_type = forms.ChoiceField(
    #     initial='control',
    #     choices=TEST_TYPE_CHOICES,
    #     required=False
    # )
    # organ_model_full = forms.ModelChoiceField(
    #     queryset=OrganModel.objects.all().order_by('name'),
    #     required=False,
    #     label='Matrix Item MPS Model'
    # )
    # organ_model_protocol_full = forms.ModelChoiceField(
    #     queryset=OrganModelProtocol.objects.all().order_by('name'),
    #     required=False,
    #     label='Matrix Item MPS Model Version'
    # )
    # number_of_items = forms.CharField(
    #     initial='',
    #     required=False
    # )
    # group_name = forms.CharField(
    #     initial='',
    #     required=False
    # )

    # CONTRIVED!
    series_data = forms.CharField(required=False)

    # Contrivance
    organ_model = forms.ModelChoiceField(
        queryset=OrganModel.objects.all().order_by('name'),
        required=False,
        label='Matrix Item MPS Model'
    )

    update_group_fields = [
        'name',
        'test_type',
        'organ_model_id',
        'organ_model_protocol_id',
    ]

    class Meta(object):
        model = AssayStudy
        # Since we are splitting into multiple forms, includes are safer
        # Only temporary, will change when finished
        fields = (
            # TEMPORARY ->
            'series_data',
            # <- TEMPORARY
            'test_type',
            'organ_model',
            'organ_model_full',
            # 'group_name',
            # TEMP!
            'organ_model_protocol',
            'organ_model_protocol_full',
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
            'compound_compound',
            'compound_concentration_unit',
            'compound_concentration',
            'compound_addition_location',
            'compound_supplier_text',
            'compound_lot_text',
            'compound_receipt_date',
        )

    def __init__(self, *args, **kwargs):
        super(AssayStudyGroupForm, self).__init__(*args, **kwargs)

        # Contrivances
        self.fields['test_type'].widget.attrs['class'] = 'no-selectize required form-control'

        # Prepopulate series_data from thing
        self.fields['series_data'].initial = self.instance.get_group_data_string(get_chips=True)

    def clean(self):
        """Checks for at least one study type"""
        # clean the form data, before validation
        data = super(AssayStudyGroupForm, self).clean()

        # SLOPPY NOT DRY
        new_setup_data = {}

        # This matrix is only for chips
        # WARNING: THIS WILL BREAK IN STUDIES WITH MULTIPLE CHIP SETS
        # IMPORTANT NOTE: WHEN BACK-FILLING, WE WILL NEED TO CONSOLIDATE CHIP MATRICES! Otherwise this flow will not work correctly...
        current_matrix = AssayMatrix.objects.filter(
            # The study must exist in order to visit this page, so getting the id this was is fine
            study_id=self.instance.id,
            representation='chips'
        )

        # Current group ids so that we can match for deletes and edits
        current_groups = AssayGroup.objects.filter(
            study_id=self.instance.id
        )

        current_group_ids = {
            group.id: group for group in current_groups
        }

        if current_matrix:
            current_matrix = current_matrix[0].id
        else:
            current_matrix = None

        # Ditto for items (chips, in this case as wells are managed elsewhere)
        # We only care about chips, at the moment
        current_items = AssayMatrixItem.objects.filter(
            study_id=self.instance.id,
            matrix_id=current_matrix
        )

        current_item_ids = {
            item.id: item for item in current_items
        }

        # Need to get the current groups (this could be an edit of groups)
        new_groups = None
        # Note that the instance is None for new adds, of course
        current_groups = AssayGroup.objects.filter(study_id=self.instance.id)

        new_items = None
        # Likewise with chips, some may need to be edited or removed etc.
        # DO NOT DUPLICATE QUERY
        # current_items = AssayMatrixItem.objects.filter(matrix_id=current_matrix)

        # This is supposed to contain data for cells, compounds, and settings (perhaps more later)
        new_related = None

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
                'chips': [],
                'plates': {}
            }

        # The data for groups is currently stored in series_data
        all_setup_data = all_data.get('series_data')
        all_chip_data = all_data.get('chips')

        # Catch technically empty setup data
        setup_data_is_empty = True

        for group_set in all_setup_data:
            if group_set:
                setup_data_is_empty = not any(group_set.values())

        if setup_data_is_empty:
            all_setup_data = []

        # if commit and all_setup_data:
        # SEE BASE MODELS FOR WHY COMMIT IS NOT HERE
        if all_setup_data:
            created_by = self.user
            created_on = timezone.now()

            # current_item_number = 1

            # CRUDE: JUST MAKE ONE LARGE ROW?
            number_of_items = 0

            for setup_group in all_setup_data:
                number_of_items += int(setup_group.get('number_of_items', '0'))

            # Alternative for one row per group
            # # Find max for number of columns
            # number_of_columns = 0
            # for setup_group in all_setup_data:
            #     if int(setup_group.get('number_of_items', '0')) > number_of_columns:
            #         number_of_columns = int(setup_group.get('number_of_items', '0'))

            if not current_matrix:
                new_matrix = AssayMatrix(
                    # Just name the chip matrix the same thing as the study?
                    name=self.instance.name,
                    # Does not work with plates at the moment
                    representation='chips',
                    study=self.instance,
                    # Doesn't matter for chips
                    device=None,
                    organ_model=None,
                    # Alternative that looks nicer, but these matrices probably won't be accessible anyway
                    # number_of_rows=len(all_setup_data),
                    # number_of_columns=number_of_columns,
                    number_of_rows=1,
                    number_of_columns=number_of_items,
                    created_by=created_by,
                    created_on=created_on,
                    modified_by=created_by,
                    modified_on=created_on,
                )

                try:
                    new_matrix.full_clean()
                except forms.ValidationError as e:
                    non_field_errors.append(e)
            else:
                new_matrix = None

            # COMPOUND STUFF BECAUSE COMPOUND SCHEMA IS MISERABLE
            # Get all chip setup assay compound instances
            assay_compound_instances = {}

            # Get all Compound Instances
            compound_instances = {
                (
                    instance.compound.id,
                    instance.supplier.id,
                    instance.lot,
                    str(instance.receipt_date)
                ): instance for instance in CompoundInstance.objects.all().prefetch_related(
                    'compound',
                    'supplier'
                )
            }

            # Get all suppliers
            suppliers = {
                supplier.name: supplier for supplier in CompoundSupplier.objects.all()
            }

            # SLOPPY TODO TODO TODO
            # Would be much neater to have this in an object or something
            new_groups = []
            update_groups = []
            deleted_groups = []

            # CHECK UNIQUENESS
            group_names = {}

            new_items = []
            update_items = []
            deleted_items = []

            # Superfluous?
            new_item_to_group_name = {}

            new_cells = []
            update_cells = []
            deleted_cells = []

            new_compounds = []
            update_compounds = []
            deleted_compounds = []

            new_settings = []
            update_settings = []
            deleted_settings = []

            # For now, chips are are all in one row
            for setup_row, setup_group in enumerate(all_setup_data):
                items_in_group = int(setup_group.pop('number_of_items', '0'))
                test_type = setup_group.get('test_type', '')

                # To break out to prevent repeat errors
                group_has_error = False

                # Make the group
                # Add the group to the new_groups
                # TODO DIFFERENTIATE NEW AND EXISTING GROUPS HERE
                # We can identify and existing group by checking for an id
                current_group = current_group_ids.get(int(setup_group.get('id', 0)), None)

                if current_group:
                    # ???
                    # new_group = current_group

                    if setup_group.get('deleted', False):
                        deleted_groups.append(current_group.id)
                    else:
                         # TODO LOGIC FOR UPDATE HERE?
                        # We need to update name, test_type, organ_model, and organ_model_protocol
                        # IDEALLY ONLY IF THEY NEED TO BE UPDATED
                        group_needs_to_be_updated = False
                        for field in self.update_group_fields:
                            if getattr(current_group, field) != setup_group.get(field, None):
                                # Contrived: Replace empty string with None
                                if field.endswith('id') and setup_group.get(field, None) is '':
                                    setattr(current_group, field, None)
                                else:
                                    setattr(current_group, field, setup_group.get(field, None))

                                group_needs_to_be_updated = True

                        if group_needs_to_be_updated:
                            try:
                                # I think we are fine with no exclusions
                                current_group.full_clean()
                                update_groups.append(current_group)
                            # MUST BE MODIFIED TO ADD TO CORRECT ROW (we could display all above too?)
                            except forms.ValidationError as e:
                                current_errors.append(
                                    process_error_with_annotation(
                                        'group',
                                        setup_row,
                                        0,
                                        e
                                    )
                                )
                                group_has_error = True

                        # Add to group names
                        # Check uniqueness
                        if setup_group.get('name', '') in group_names:
                            non_field_errors.append('The Group name "{}" is duplicated. The names of Groups must be unique.'.format(
                                setup_group.get('name', '')
                            ))
                        else:
                            group_names.update({
                                setup_group.get('name', ''): True
                            })
                else:
                    # CRUDE
                    current_organ_model_id = setup_group.get('organ_model_id', None)

                    if current_organ_model_id:
                        current_organ_model_id = int(current_organ_model_id)
                    else:
                        current_organ_model_id = None

                    current_organ_model_protocol_id = setup_group.get('organ_model_protocol_id', None)

                    if current_organ_model_protocol_id:
                        current_organ_model_protocol_id = int(current_organ_model_protocol_id)
                    else:
                        current_organ_model_protocol_id = None

                    new_group = AssayGroup(
                        # Study should just be instance
                        study=self.instance,
                        name=setup_group.get('name', ''),
                        test_type=setup_group.get('test_type', ''),
                        organ_model_id=current_organ_model_id,
                        organ_model_protocol_id=current_organ_model_protocol_id,
                    )

                    # TODO Logic for first clean and adding to new_groups here
                    try:
                        # I think we are fine with no exclusions
                        new_group.full_clean()
                        new_groups.append(new_group)
                    # MUST BE MODIFIED TO ADD TO CORRECT ROW (we could display all above too?)
                    except forms.ValidationError as e:
                        current_errors.append(
                            process_error_with_annotation(
                                'group',
                                setup_row,
                                0,
                                e
                            )
                        )
                        group_has_error = True

                    # Add to group names
                    # Check uniqueness
                    if setup_group.get('name', '') in group_names:
                        non_field_errors.append('The Group name "{}" is duplicated. The names of Groups must be unique.'.format(
                            setup_group.get('name', '')
                        ))
                    else:
                        group_names.update({
                            setup_group.get('name', ''): True
                        })

                # Always iterate for cells, compounds, and settings
                # Keep in mind that to decrease sparsity related data is now tied to a group
                for prefix, current_objects in setup_group.items():
                    # Related are tied to group, not item
                    # Groups are INDEX DEPENDENT, *NOT* by ID (group may or may not exist)
                    # If we don't want to wipe things every time, we CAN'T JUST DO THIS!
                    # Obviously, we would need to differentiate adds, updates, and deletes
                    # current_related_list = new_related.setdefault(
                    #     str(setup_row), []
                    # )

                    if prefix in ['cell', 'compound', 'setting'] and setup_group[prefix]:
                        for setup_column, current_object in enumerate(current_objects):
                            # Just to filter out anything that isn't related data we need
                            # TODO: NOTE: The big problem here is that we do not differentiate updates and adds!
                            # That is, we would need to wipe all of the existing related data for this to work...
                            # That is *possible*, but unwise
                            # We could, alternatively, see if there is an entry at the INDEX (setup_column)
                            # This can get quite convoluted! AND ALSO NEEDS TO ACCOMMODATE DELETIONS!
                            # TODO TODO TODO NOTE: Basically to deal with deletions, we could see if number_of_deletions > number_of_new_columns
                            # Of course, we get number_of_new_columns from the passed data
                            # On the other hand, if we didn't really care about maximizing efficiency we could just kill anything marked for deletion
                            # The performance hit for adding a new entry instead of updating an existing would be negligible
                            # Why bother twisiting oneself into a knot to do so?
                            # Besides, if we mark deletions rather than totally removing them, we would know for sure whether "they were in the right column" and thus whether they needed to be added
                            # Anyway, we would need a query that matched the data to "columns"
                            # The query for this, hopefully, shouldn't be too big!
                            # We only care about that which is associated with groups in THIS study, so it should be fine?

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
                            # On the bright side, it won't orphan any data because data is bound to a Group rather than the constituent pieces...
                            current_object.update({
                                # GROUP NOT ITEM
                                # 'group_id': new_group,
                                # SOMEWHAT TRICKY: START WITH NAME AND OVERWRITE
                                'group_id': setup_group.get('name', '')
                            })
                            # Breaks rule of 3
                            if prefix == 'cell':
                                new_cell = AssayGroupCell(**current_object)

                                try:
                                    new_cell.full_clean(exclude=['group'])
                                    # current_related_list.append(new_cell)
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
                                new_setting = AssayGroupSetting(**current_object)
                                try:
                                    new_setting.full_clean(exclude=['group'])
                                    # current_related_list.append(new_setting)
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

                            elif prefix == 'compound':
                                # CONFUSING NOT DRY BAD
                                compound = int(current_object.get('compound_id', '0'))
                                supplier_text = current_object.get('supplier_text', 'N/A').strip()
                                lot_text = current_object.get('lot_text', 'N/A').strip()
                                receipt_date = current_object.get('receipt_date', '')

                                # NOTE THE DEFAULT, PLEASE DO THIS IN A WAY THAT IS MORE DRY
                                if not supplier_text:
                                    supplier_text = 'N/A'

                                if not lot_text:
                                    lot_text = 'N/A'

                                # Check if the supplier already exists
                                supplier = suppliers.get(supplier_text, '')

                                concentration = current_object.get('concentration', '0')
                                # Annoying, bad
                                if not concentration:
                                    concentration = 0.0
                                else:
                                    concentration = float(concentration)

                                concentration_unit_id = current_object.get('concentration_unit_id', '0')

                                if concentration_unit_id:
                                    concentration_unit_id = int(concentration_unit_id)
                                else:
                                    concentration_unit_id = None

                                addition_location_id = current_object.get('addition_location_id', '0')

                                if addition_location_id:
                                    addition_location_id = int(addition_location_id)
                                else:
                                    addition_location_id = None

                                addition_time = current_object.get('addition_time', '0')
                                duration = current_object.get('duration', '0')

                                if not addition_time:
                                    addition_time = 0.0
                                else:
                                    addition_time = float(addition_time)

                                if not duration:
                                    duration = 0.0
                                else:
                                    duration = float(duration)

                                # Otherwise create the supplier
                                if not supplier:
                                    supplier = CompoundSupplier(
                                        name=supplier_text,
                                        created_by=created_by,
                                        created_on=created_on,
                                        modified_by=created_by,
                                        modified_on=created_on,
                                    )
                                    try:
                                        supplier.full_clean()
                                        supplier.save()
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

                                    suppliers.update({
                                        supplier_text: supplier
                                    })

                                # FRUSTRATING EXCEPTION
                                if not receipt_date:
                                    receipt_date = None

                                # Check if compound instance exists
                                compound_instance = compound_instances.get((compound, supplier.id, lot_text, str(receipt_date)), '')

                                if not compound_instance:
                                    compound_instance = CompoundInstance(
                                        compound_id=compound,
                                        supplier=supplier,
                                        lot=lot_text,
                                        receipt_date=receipt_date,
                                        created_by=created_by,
                                        created_on=created_on,
                                        modified_by=created_by,
                                        modified_on=created_on,
                                    )
                                    try:
                                        compound_instance.full_clean()
                                        compound_instance.save()
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

                                    compound_instances.update({
                                        (compound, supplier.id, lot_text, str(receipt_date)): compound_instance
                                    })

                                # Save the AssayCompoundInstance
                                conflicting_assay_compound_instance = assay_compound_instances.get(
                                    (
                                        # NOPE! HAVE TO USE
                                        # Hmmm... not sure what to use...
                                        # We need something that is id agnostic
                                        # But we can't use just the name!
                                        # We need the study id and group name
                                        # Should be enough!
                                        self.instance.id,
                                        setup_group.get('name', ''),
                                        compound_instance.id,
                                        concentration,
                                        concentration_unit_id,
                                        addition_time,
                                        duration,
                                        addition_location_id
                                    ), None
                                )
                                if not conflicting_assay_compound_instance:
                                    new_compound = AssayGroupCompound(
                                        # matrix_item_id=new_item.id,
                                        compound_instance_id=compound_instance.id,
                                        concentration=concentration,
                                        concentration_unit_id=concentration_unit_id,
                                        addition_time=addition_time,
                                        duration=duration,
                                        addition_location_id=addition_location_id,
                                        # MANUALLY ADD THE GROUP NAME AS A CONTRIVED VALUE
                                        group_id=setup_group.get('name', '')
                                    )

                                    try:
                                        new_compound.full_clean(exclude=['group'])
                                        # current_related_list.append(new_compound)
                                        new_compounds.append(new_compound)
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

                                assay_compound_instances.update({
                                    (
                                        self.instance.id,
                                        setup_group.get('name', ''),
                                        compound_instance.id,
                                        concentration,
                                        concentration_unit_id,
                                        addition_time,
                                        duration,
                                        addition_location_id
                                    ): True
                                })

            # We ought to process items separately for a number of reasons
            # TODO
            # Start of numbering for items
            # We begin with the number of current_items + 1
            # We assume, for the moment, that there will not be name collisions
            # TODO: FOR TOTAL ASSURANCE, PREVENT NAME COLLISIONS
            current_item_number = current_items.count() + 1

            for current_chip in all_chip_data:
                # Terminate early if no group
                # BE CAREFUL, ZERO IS FALSY
                if current_chip.get('group_index', None) is not None:
                    setup_group = all_setup_data[current_chip.get('group_index')]
                else:
                    continue

                # We know whether this is a current item if the id matches one in our list
                current_item = current_item_ids.get(int(current_chip.get('id', 0)), None)

                # TODO
                if current_item:
                    # ??
                    # new_item = current_item

                    # TODO LOGIC FOR UPDATE HERE?
                    # It might be overkill, but user could change the organ model and protocol
                    # So just always pass the organ model, protocol, test_type, modified on and by
                    # NEVER BOTHER WITH THE GROUP
                    # WE KNOW WHAT THE GROUP IS BECAUSE YOU CANNOT CHANGE IT HERE

                    # WE AREN'T BOTHERING WITH UPDATING ITEMS HERE
                    # We will delete them, though
                    if current_chip.get('deleted', False):
                        deleted_items.append(current_item.id)
                else:
                    # TODO NOTE: New chip names *theoretically* can conflict with existing chips
                    # For instance, someone can rename their 3 chips "3,4,5" and add three new chips, bad news!
                    new_item = AssayMatrixItem(
                        # study=study,
                        # matrix=new_matrix,
                        name=str(current_item_number),
                        # JUST MAKE SETUP DATE THE STUDY DATE FOR NOW
                        setup_date=self.instance.start_date,
                        # Alternative row and column
                        # row_index=setup_row,
                        # column_index=iteration,
                        row_index=0,
                        column_index=current_item_number-1,
                        # Irrelevant (but required, unfortunately, maybe will remove later)
                        # device=study.organ_model.device,
                        organ_model_id=setup_group.get('organ_model_id', None),
                        # Some nuances here that we will gloss over
                        organ_model_protocol_id=setup_group.get('organ_model_protocol_id', None),
                        test_type=setup_group.get('test_type', ''),
                        created_by=created_by,
                        created_on=created_on,
                        modified_by=created_by,
                        modified_on=created_on,
                        study_id=self.instance.id,

                        # SOMEWHAT UNORTHODOX:
                        # We put the group name here
                        # THEN OVERRIDE IT WITH THE ID LATER
                        group_id=setup_group.get('name', ''),
                    )

                    try:
                        new_item.full_clean(exclude=[
                            # The matrix needs to be excluded because it might not exist yet
                            'matrix',
                            # DEFINITELY EXCLUDE GROUP
                            'group',

                            # Why exclude these?
                            'device',
                            # 'organ_model',
                            # 'organ_model_protocol',
                        ])
                        new_items.append(new_item)
                    except forms.ValidationError as e:
                        non_field_errors.append(e)
                        group_has_error = True

                # CAN CAUSE UNUSUAL BEHAVIOR DURING UPDATES!
                current_item_number += 1

        if current_errors or non_field_errors:
            non_field_errors.append(['Please review the table below for errors.'])
            raise forms.ValidationError(all_errors)

        # Kind of odd at first blush, but we reverse to save in order
        # new_items = list(reversed(new_items))

        new_setup_data.update({
            'new_matrix': new_matrix,
            'new_items': new_items,

            # NO LONGER HOW THINGS ARE HANDLED:
            # 'new_related': new_related,
            'new_compounds': new_compounds,
            'new_cells': new_cells,
            'new_settings': new_settings,

            'new_groups': new_groups,
            # TODO current_matrix?
            # TODO updates?
            # We PROBABLY don't need to modify the matrix
            # I mean, if someone REALLY wanted to look at it, then it would be messed up if the number of chips changed
            # 'update_matrix': update_matrix,
            # Swapping groups etc (renaming is in a different interface)
            # Maybe we ought to overkill update all in current items?
            # Or, I suppose we can avoid superfluous updates by doing a comparison prior?
            'update_groups': update_groups,

            # WE DON'T REALLY HAVE TO UPDATE ITEMS, BUT WE DO HAVE TO DELETE THEM
            # Probably not needed here
            'update_items': update_items,

            # TODO TODO TODO
            # First pass we are not going to bother with this
            'update_compounds': update_compounds,
            'update_cells': update_cells,
            'update_settings': update_settings,

            # WE NEED THE GROUP IDS!
            'current_group_ids': current_group_ids,
            # WE WOULD WANT TO KNOW IF THERE IS ALREADY A MATRIX!
            'current_matrix':  current_matrix,
            # Probably not needed
            # 'item_ids': item_ids,

            'deleted_groups': deleted_groups,
            'deleted_items': deleted_items,

            # THESE GET TRICKY! IDEALLY WE WANT TO DELETE AS FEW RELATED AS POSSIBLE
            # TODO TODO TODO
            # First pass we are not going to bother with this
            'deleted_compounds': deleted_compounds,
            'deleted_cells': deleted_cells,
            'deleted_settings': deleted_settings,
        })

        data.update({
            'processed_setup_data': new_setup_data
        })

        return data

    # TODO: REVISE TO USE bulk_create
    # TODO: REVISE TO PROPERLY DEAL WITH UPDATES WITH bulk_update
    def save(self, commit=True):
        all_setup_data = self.cleaned_data.get('processed_setup_data', None)

        # Sloppy
        study = self.instance

        if all_setup_data and commit:
            # VERY SLOPPY
            created_by = self.user
            created_on = timezone.now()

            study.modified_by = created_by
            study.modified_on = created_on

            study.save()
            # SLOPPY: REVISE

            study_id = study.id

            # TODO TODO TODO: STUPID, BUT ONE WAY TO DEAL WITH THE DEVICE ISSUE
            # Otherwise I would need to cut it out and immediately revise every place it was called...
            # Light query anyway (relative to the others) I guess
            organ_model_id_to_device_id = {
                organ_model.id: organ_model.device_id for organ_model in OrganModel.objects.all()
            }

            new_matrix = all_setup_data.get('new_matrix', None)

            new_groups = all_setup_data.get('new_groups', None)

            update_groups = all_setup_data.get('update_groups', None)
            current_group_ids = all_setup_data.get('current_group_ids', None)

            new_items = all_setup_data.get('new_items', None)

            update_items = all_setup_data.get('update_items', None)

            # Why?
            new_compounds = all_setup_data.get('new_compounds', None)
            new_cells = all_setup_data.get('new_cells', None)
            new_settings = all_setup_data.get('new_settings', None)

            update_compounds = all_setup_data.get('update_compounds', None)
            update_cells = all_setup_data.get('update_cells', None)
            update_settings = all_setup_data.get('update_settings', None)

            current_matrix = all_setup_data.get('current_matrix', None)
            deleted_groups = all_setup_data.get('deleted_groups', None)
            deleted_items = all_setup_data.get('deleted_items', None)
            deleted_compounds = all_setup_data.get('deleted_compounds', None)
            deleted_cells = all_setup_data.get('deleted_cells', None)
            deleted_settings = all_setup_data.get('deleted_settings', None)

            if new_matrix:
                new_matrix.study_id = study_id
                new_matrix.save()
                new_matrix_id = new_matrix.id
                current_matrix_id = new_matrix_id
            # Uh... why use an elif here?
            # elif not new_matrix and (new_items or update_items):
            else:
                # TODO TODO TODO
                # Have some way to get the "current matrix" if there isn't a new matrix
                # TODO Be careful, if there are no chips, don't bother!
                current_matrix_id = all_setup_data.get('current_matrix')

            # UPDATE CURRENT GROUPS IF NECESSARY
            # Bulk update should be relatively fast
            if update_groups:
                AssayGroup.objects.bulk_update(update_groups, self.update_group_fields)

            # These dics match names (which are specific to this study! They are not from queries!) to ids
            # We want to avoid superfluous queries, and we might as well take advantage of the uniqueness constraints
            new_group_ids = {}

            # Combine current_group ids into new_group_ids
            # Way more verbose than it needs to be
            for current_group_id, current_group in current_group_ids.items():
                new_group_ids.update({
                    current_group.name: current_group_id
                })

            # new_item_ids = {}

            # TODO
            # for new_group in new_groups:
                # We don't really need to tie to anything?

            # Be careful with conditionals
            if new_groups:
                # Bulk create the groups BE SURE ONLY NEW GROUPS IN THIS LIST
                AssayGroup.objects.bulk_create(new_groups)

                # TODO NOTE: WE NEED ALL GROUPS, NOT JUST THESE
                for new_group in new_groups:
                    new_group_ids.update({
                        new_group.name: new_group.id
                    })

            # NOTE: WE MAY HAVE NEW ITEMS WITHOUT A NEW MATRIX
            for new_item in new_items:
                # ADD MATRIX and tracking
                # TODO TODO TODO TODO DO NOT USE new_matrix_id HERE
                new_item.matrix_id = current_matrix_id
                # IDEALLY WE WILL JUST CUT THESE ANYWAY??
                new_item.device_id = organ_model_id_to_device_id.get(new_item.organ_model_id)

                # TODO TODO TODO
                # We perform a little bit of sleight of hand here!
                current_group_name = new_item.group_id

                # Assign the correct group
                # "new_group_ids" is a misnomer!
                new_group_id = new_group_ids.get(current_group_name, None)

                new_item.group_id = new_group_id

                # To get the group id with have to use a dic TODO TODO

                # Ideally we won't save this way! We want to use bulk_create
                # new_item.save()

                # Ideally we would do this after the bulk_create
                # new_item_ids.update({
                #     new_item.name: new_item.id
                # })

            if new_items:
                AssayMatrixItem.objects.bulk_create(new_items)

                # We shouldn't actually need these for anything
                # for new_item in new_items:
                #     new_item_ids.update({
                #         new_item.name: new_item.id
                #     })

            # WE WILL WANT TO SAVE EACH COMPONENT SEPARATELY FOR BULK CREATE/UPDATE (otherwise gets odd)
            # Additionally, this data is no longer tied to an individual item
            # for current_item_name, new_related_data_set in new_related.items():
            #     new_item_id = new_item_ids.get(current_item_name, None)

            #     if new_item_id:
            #         for new_related_data in new_related_data_set:
            #             # ADD MATRIX ITEM
            #             new_related_data.matrix_item_id = new_item_id
            #             new_related_data.save()

            # Can't use ids due to the fact that some ids are new!
            # Be sure you can access ALL groups for this!
            # (EXCLUDING DELETED GROUPS, WHICH OUGHT NOT TO BE ACCESSED)

            # Barbaric, just obscene in its grotesque cruelty
            # How could one do such a thing and not be deemed heartless?
            # KILL ALL COMPOUNDS, CELL, AND SETTINGS:
            AssayGroupCompound.objects.filter(group_id__in=new_group_ids.values()).delete()
            AssayGroupCell.objects.filter(group_id__in=new_group_ids.values()).delete()
            AssayGroupSetting.objects.filter(group_id__in=new_group_ids.values()).delete()

            # Breaks rule of three
            # Stupid
            for new_compound in new_compounds:
                # We perform a little bit of sleight of hand here!
                current_group_name = new_compound.group_id

                # Assign the correct group
                # "new_group_ids" is a misnomer!
                new_group_id = new_group_ids.get(current_group_name, None)

                new_compound.group_id = new_group_id

            if new_compounds:
                AssayGroupCompound.objects.bulk_create(new_compounds)

            for new_cell in new_cells:
                # We perform a little bit of sleight of hand here!
                current_group_name = new_cell.group_id

                # Assign the correct group
                # "new_group_ids" is a misnomer!
                new_group_id = new_group_ids.get(current_group_name, None)

                new_cell.group_id = new_group_id

            if new_cells:
                AssayGroupCell.objects.bulk_create(new_cells)

            for new_setting in new_settings:
                # We perform a little bit of sleight of hand here!
                current_group_name = new_setting.group_id

                # Assign the correct group
                # "new_group_ids" is a misnomer!
                new_group_id = new_group_ids.get(current_group_name, None)

                new_setting.group_id = new_group_id

            if new_settings:
                AssayGroupSetting.objects.bulk_create(new_settings)

            # Perform deletions
            if deleted_items:
                AssayMatrixItem.objects.filter(id__in=deleted_items, matrix_id=current_matrix_id).delete()
            if deleted_groups:
                AssayGroup.objects.filter(id__in=deleted_groups, study_id=self.instance.id).delete()

        return study


class AssayStudyChipForm(SetupFormsMixin, SignOffMixin, BootstrapForm):
    series_data = forms.CharField(required=False)

    class Meta(object):
        model = AssayStudy
        # Since we are splitting into multiple forms, includes are safer
        fields = (
            'series_data',
            'organ_model_full',
            'organ_model_protocol_full'
        )

    def __init__(self, *args, **kwargs):
        super(AssayStudyChipForm, self).__init__(*args, **kwargs)

        # Prepopulate series_data from thing
        self.fields['series_data'].initial = self.instance.get_group_data_string(get_chips=True)

    # TODO NEEDS TO BE REVISED
    # TODO TODO TODO CLEAN AND SAVE
    def clean(self):
        cleaned_data = super(AssayStudyChipForm, self).clean()

        # TODO TODO TODO NOTE CRAMMED IN
        # Am I sticking with the name 'series_data'?
        if self.cleaned_data.get('series_data', None):
            all_data = json.loads(self.cleaned_data.get('series_data', '[]'))
        else:
            # Contrived defaults
            all_data = {
                'series_data': [],
                'chips': [],
                'plates': {}
            }

        # The data for groups is currently stored in series_data
        all_setup_data = all_data.get('series_data')
        all_chip_data = all_data.get('chips')

        # Catch technically empty setup data
        setup_data_is_empty = True

        for group_set in all_setup_data:
            if group_set:
                setup_data_is_empty = not any(group_set.values())

        if setup_data_is_empty:
            all_setup_data = []

        # Variables must always exist
        chip_data = []
        current_errors = []

        # if commit and all_setup_data:
        # SEE BASE MODELS FOR WHY COMMIT IS NOT HERE
        if all_chip_data:
            chip_names = {}

            current_matrix = AssayMatrix.objects.filter(
                # The study must exist in order to visit this page, so getting the id this was is fine
                study_id=self.instance.id,
                representation='chips'
            )

            # Get the group ids
            group_ids = {
                group.id: True for group in AssayGroup.objects.filter(
                    study_id=self.instance.id
                )
            }

            chip_id_to_chip = {
                chip.id: chip for chip in AssayMatrixItem.objects.filter(
                    study_id=self.instance.id,
                    matrix_id=current_matrix[0].id
                )
            }

            # We basically just modify group_id and name
            # TODO MAKE SURE THE GROUP IDS ARE VALID
            # That is, check against the group ids of the study
            for chip in all_chip_data:
                if chip_id_to_chip.get(chip.get('id', 0)):
                    current_chip = chip_id_to_chip.get(chip.get('id', 0))
                else:
                    current_chip = False
                    current_errors.append('A Chip is missing, please refresh and try again.')

                if current_chip:
                    # Add to group names
                    # Check uniqueness
                    if chip.get('name', '') in chip_names:
                        current_errors.append('The Chip name "{}" is duplicated. The names of Chips must be unique.'.format(
                            chip.get('name', '')
                        ))
                    else:
                        chip_names.update({
                            chip.get('name', ''): True
                        })

                        current_chip.name = chip.get('name', '')

                    if chip.get('group_id', '') in group_ids:
                        current_chip.group_id = chip.get('group_id', '')
                    try:
                        current_chip.full_clean()
                        chip_data.append(current_chip)
                    except forms.ValidationError as e:
                        current_errors.append(e)

        self.cleaned_data.update({
            'chip_data': chip_data
        })

        if current_errors:
            raise forms.ValidationError(current_errors)

        return cleaned_data

    def save(self, commit=True):
        # Just do the bulk update
        # We don't need to do anything else
        # TODO TODO TODO
        # NOTE NOTE NOTE
        # WE TECHNICALLY SHOULD CHANGE THE SHARED VALUES HERE (organ_model, test_type, etc.)
        # ON THE OTHER HAND, IT IS PROBABLY BEST TO LEAVE THEM OUT
        if commit:
            AssayMatrixItem.objects.bulk_update(
                self.cleaned_data.get('chip_data', None),
                [
                    'group_id',
                    'name'
                ]
            )

        return self.instance


class AssayStudyPlateForm(SetupFormsMixin, SignOffMixin, BootstrapForm):
    series_data = forms.CharField(required=False)

    class Meta(object):
        model = AssayMatrix
        fields = (
            'name',
            'notes',
            # Don't care about device anymore, I guess
            # 'device',
            # DO care about organ model, I guess
            'organ_model',
            # Maybe a bit unorthodox
            'number_of_columns',
            'number_of_rows',
            # TODO
            'series_data',
        )
        widgets = {
            'name': forms.Textarea(attrs={'rows': 1}),
            'notes': forms.Textarea(attrs={'rows': 10}),
        }

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study', None)
        super(AssayStudyPlateForm, self).__init__(*args, **kwargs)

        if self.study:
            self.instance.study = self.study
        else:
            self.study = self.instance.study

        # Crude! TEMPORARY
        if self.instance.id:
            self.fields['series_data'].initial = self.study.get_group_data_string(plate_id=self.instance.id)
        else:
            self.fields['series_data'].initial = self.study.get_group_data_string()

        # Predicate the organ model options on the current groups
        # Dumb query
        plate_groups = AssayGroup.objects.filter(
            study_id=self.instance.study.id,
            # See above
            organ_model__device__device_type='plate'
        ).prefetch_related('organ_model__device')

        self.fields['organ_model'].queryset = OrganModel.objects.filter(
            id__in=plate_groups.values_list('organ_model_id', flat=True)
        )

        # Improper, but one method to make organ model required
        self.fields['organ_model'].widget.attrs['class'] += ' required'
        self.fields['organ_model'].required = True

    # FORCE UNIQUENESS CHECK
    def clean(self):
        # RATHER CRUDE: WE FORCE THE PLATE TO HAVE A REPRESENTATION OF PLATE
        self.instance.representation = 'plate'
        cleaned_data = super(AssayStudyPlateForm, self).clean()

        # VERY SLOPPY
        created_by = self.user
        created_on = timezone.now()

        # TODO TODO TODO NOTE CRAMMED IN
        # Am I sticking with the name 'series_data'?
        if self.cleaned_data.get('series_data', None):
            all_data = json.loads(self.cleaned_data.get('series_data', '[]'))
        else:
            # Contrived defaults
            all_data = {
                'series_data': [],
                'chips': [],
                'plates': {}
            }

        # The data for groups is currently stored in series_data
        all_setup_data = all_data.get('series_data')
        all_plate_data = all_data.get('plates')

        # Catch technically empty setup data
        setup_data_is_empty = True

        for group_set in all_setup_data:
            if group_set:
                setup_data_is_empty = not any(group_set.values())

        if setup_data_is_empty:
            all_setup_data = []

        # Plate name
        if AssayMatrix.objects.filter(
                study_id=self.instance.study.id,
                name=self.cleaned_data.get('name', '')
        ).exclude(pk=self.instance.pk).count():
            raise forms.ValidationError({'name': ['Plate name must be unique within Study.']})

        current_wells = {
            well.id: well for well in AssayMatrixItem.objects.filter(
                matrix_id=self.instance.id
            )
        }

        # Technically ought to restrict to JUST PLATE GROUPS
        # However, that makes the query uglier
        # First pass, we won't make sure a check
        current_groups = {
            group.id: group for group in AssayGroup.objects.filter(
                study_id=self.instance.study.id
            )
        }

        new_wells = []
        update_wells = []
        delete_wells = []

        # NOTE: We will be alerted during clean for anything that ISN'T INTERNAL to the plate
        taken_names = {}

        current_errors = []

        for row_column, well in all_plate_data.items():
            row_column_split = row_column.split('_')
            row = int(row_column_split[0])
            column = int(row_column_split[1])

            current_well = current_wells.get(well.get('id', 0), None)
            current_group = current_groups.get(well.get('group_id', 0), None)

            # Junk data
            if not current_group:
                continue

            # BE SURE TO TEST THE NAMES!
            current_name = well.get('name', '')
            if current_name in taken_names:
                current_errors.append('The name "{}" is already in use, please make sure well names are unique.'.format(
                    current_name
                ))
            else:
                taken_names.update({
                    current_name: True
                })

            # Update if already exists
            if current_well:
                # If slated for deletion
                if well.get('deleted', ''):
                    delete_wells.append(current_well.id)
                else:
                    # Update name
                    current_well.name = current_name
                    if well.get('group_id', '') in current_groups:
                        # Update group id
                        current_well.group_id = well.get('group_id', '')

                        # Make sure nothing broke
                        try:
                            current_well.full_clean()
                            # Add it to those slated to update
                            update_wells.append(current_well)
                        except forms.ValidationError as e:
                            current_errors.append(e)
            # Add otherwise
            else:
                new_item = AssayMatrixItem(
                    # We know this one
                    study=self.instance.study,
                    # TRICKY!
                    # matrix=new_matrix,
                    name=current_name,
                    # JUST MAKE SETUP DATE THE STUDY DATE FOR NOW
                    setup_date=self.instance.study.start_date,
                    row_index=row,
                    column_index=column,
                    # Irrelevant (but required, unfortunately, maybe will remove later)
                    # device=study.organ_model.device,
                    organ_model_id=current_group.organ_model_id,
                    # Some nuances here that we will gloss over
                    organ_model_protocol_id=current_group.organ_model_protocol_id,
                    test_type=current_group.test_type,
                    created_by=created_by,
                    created_on=created_on,
                    modified_by=created_by,
                    modified_on=created_on,
                    group_id=current_group.id
                )

                try:
                    new_item.full_clean(exclude=[
                        # The matrix needs to be excluded because it might not exist yet
                        'matrix',

                        # Why exclude these?
                        # Get rid of device for now because it is still required
                        'device',
                        # 'organ_model',
                        # 'organ_model_protocol',
                    ])
                    new_wells.append(new_item)
                except forms.ValidationError as e:
                        current_errors.append(e)
                        group_has_error = True

        cleaned_data.update({
            'new_wells': new_wells,
            'update_wells': update_wells,
            'delete_wells': delete_wells,
        })

        if current_errors:
            raise forms.ValidationError(current_errors)

        return cleaned_data

    # CRUDE, TEMPORARY
    # TODO REVISE ASAP
    def save(self, commit=True):
        # Takes care of saving the Plate in and of itself
        matrix = super(AssayStudyPlateForm, self).save(commit)

        if commit:
            matrix_id = self.instance.id
            study_id = self.instance.study.id

            # TODO TODO TODO: STUPID, BUT ONE WAY TO DEAL WITH THE DEVICE ISSUE
            # Otherwise I would need to cut it out and immediately revise every place it was called...
            # Light query anyway (relative to the others) I guess
            organ_model_id_to_device_id = {
                organ_model.id: organ_model.device_id for organ_model in OrganModel.objects.all()
            }

            new_wells = self.cleaned_data.get('new_wells')
            update_wells = self.cleaned_data.get('update_wells')
            delete_wells = self.cleaned_data.get('delete_wells')

            # Add new wells
            if new_wells:
                # Need to iterate through the new wells and add the matrix id
                # (The matrix might not exist yet)
                for well in new_wells:
                    well.matrix_id = matrix_id
                    # IDEALLY WE WILL JUST CUT THESE ANYWAY??
                    well.device_id = organ_model_id_to_device_id.get(well.organ_model_id)

                AssayMatrixItem.objects.bulk_create(new_wells)

            # Update wells
            # TODO TODO TODO
            # NOTE NOTE NOTE
            # WE TECHNICALLY SHOULD CHANGE THE SHARED VALUES HERE (organ_model, test_type, etc.)
            # ON THE OTHER HAND, IT IS PROBABLY BEST TO LEAVE THEM OUT
            if update_wells:
                AssayMatrixItem.objects.bulk_update(
                    update_wells,
                    [
                        'name',
                        'group_id'
                    ]
                )

            if delete_wells:
                AssayMatrixItem.objects.filter(id__in=delete_wells).delete()

        return matrix


# Need to make plural to distinguish
# CONTRIVED ANYWAY
class AssayStudyAssaysForm(BootstrapForm):
    class Meta(object):
        model = AssayStudy
        # Since we are splitting into multiple forms, includes are safer
        fields = []


class AssayStudyFormAdmin(BootstrapForm):
    """Admin Form for Assay Runs (now referred to as Studies)"""
    class Meta(object):
        model = AssayStudy
        widgets = {
            'assay_run_id': forms.Textarea(attrs={'rows': 1}),
            'name': forms.Textarea(attrs={'rows': 1}),
            'description': forms.Textarea(attrs={'rows': 10}),
            'signed_off_notes': forms.Textarea(attrs={'rows': 10}),
        }
        exclude = ('',)

    def __init__(self, *args, **kwargs):
        super(AssayStudyFormAdmin, self).__init__(*args, **kwargs)

        groups_with_center = MicrophysiologyCenter.objects.all().values_list('groups', flat=True)
        groups_with_center_full = Group.objects.filter(
            id__in=groups_with_center
        ).order_by(
            'name'
        )

        self.fields['group'].queryset = groups_with_center_full
        groups_without_repeat = groups_with_center_full

        if self.instance and getattr(self.instance, 'group', ''):
            groups_without_repeat.exclude(pk=self.instance.group.id)

        self.fields['access_groups'].queryset = groups_without_repeat
        self.fields['collaborator_groups'].queryset = groups_without_repeat

        # Crudely force required class
        for current_field in ['total_device_volume', 'flow_rate', 'number_of_relevant_cells']:
            self.fields[current_field].widget.attrs['class'] += ' required'

    def clean(self):
        # clean the form data, before validation
        data = super(AssayStudyFormAdmin, self).clean()

        if not any([data['toxicity'], data['efficacy'], data['disease'], data['cell_characterization'], data['pbpk_steady_state'], data['pbpk_bolus']]):
            raise forms.ValidationError('Please select at least one study type')

        if data.get('pbpk_steady_state', '') and (not data.get('number_of_relevant_cells', '') or not data.get('flow_rate', '')):
            raise forms.ValidationError('Continuous Infusion PBPK Requires Number of Cells Per MPS Model and Flow Rate')

        if data.get('pbpk_bolus', '') and (not data.get('number_of_relevant_cells', '') or not data.get('total_device_volume', '')):
            raise forms.ValidationError('Bolus PBPK Requires Number of Cells Per MPS Model and Total Device Volume')


class AssayStudySupportingDataForm(BootstrapForm):
    class Meta(object):
        model = AssayStudySupportingData
        exclude = ('',)


class AssayStudyAssayForm(BootstrapForm):
    class Meta(object):
        model = AssayStudyAssay
        exclude = ('',)


class AssayStudySupportingDataInlineFormSet(BaseInlineFormSet):
    """Form for Study Supporting Data (as part of an inline)"""
    class Meta(object):
        model = AssayStudySupportingData
        exclude = ('',)

AssayStudySupportingDataFormSetFactory = inlineformset_factory(
    AssayStudy,
    AssayStudySupportingData,
    form=AssayStudySupportingDataForm,
    formset=AssayStudySupportingDataInlineFormSet,
    extra=1,
    exclude=[],
    widgets={
        'description': forms.Textarea(attrs={'rows': 3}),
    }
)

AssayStudyAssayFormSetFactory = inlineformset_factory(
    AssayStudy,
    AssayStudyAssay,
    form=AssayStudyAssayForm,
    formset=AssayStudyAssayInlineFormSet,
    extra=1,
    exclude=[]
)


# TODO ADD STUDY
class AssayMatrixForm(SetupFormsMixin, SignOffMixin, BootstrapForm):
    class Meta(object):
        model = AssayMatrix
        exclude = ('study',) + tracking
        widgets = {
            'number_of_columns': forms.NumberInput(attrs={'style': 'width: 100px;'}),
            'number_of_rows': forms.NumberInput(attrs={'style': 'width: 100px;'}),
            'name': forms.Textarea(attrs={'rows': 1}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'variance_from_organ_model_protocol': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study', None)
        # self.user = kwargs.pop('user', None)
        super(AssayMatrixForm, self).__init__(*args, **kwargs)

        if self.study:
            self.instance.study = self.study

        # sections_with_times = (
        #     'compound',
        #     'cell',
        #     'setting'
        # )
        #
        # for time_unit in list(TIME_CONVERSIONS.keys()):
        #     for current_section in sections_with_times:
        #         # Create fields for Days, Hours, Minutes
        #         self.fields[current_section + '_addition_time_' + time_unit] = forms.FloatField(
        #             initial=0,
        #             required=False,
        #             widget=forms.NumberInput(attrs={
        #                 'class': 'form-control',
        #                 'style': 'width:75px;'
        #             })
        #         )
        #         self.fields[current_section + '_duration_' + time_unit] = forms.FloatField(
        #             initial=0,
        #             required=False,
        #             widget=forms.NumberInput(attrs={
        #                 'class': 'form-control',
        #                 'style': 'width:75px;'
        #             })
        #         )

        # Changing these things in init is bad
        self.fields['matrix_item_notebook_page'].widget.attrs['style'] = 'width:75px;'
        # self.fields['cell_cell_sample'].widget.attrs['style'] = 'width:75px;'
        # self.fields['cell_passage'].widget.attrs['style'] = 'width:75px;'

        # Make sure no selectize
        # CONTRIVED
        self.fields['matrix_item_full_organ_model'].widget.attrs['class'] = 'no-selectize'
        self.fields['matrix_item_full_organ_model_protocol'].widget.attrs['class'] = 'no-selectize'

        # No selectize on action either (hides things, looks odd)
        # CONTRIVED
        # self.fields['action'].widget.attrs['class'] += ' no-selectize'

        # DUMB, BAD (can't have them be "actually" required or they prevent submission
        add_required_to = [
            'matrix_item_name',
            'matrix_item_setup_date',
            'matrix_item_test_type',
            'matrix_item_name',
            'matrix_item_device',
            'matrix_item_organ_model',
        ]

        for current_field in add_required_to:
            self.fields[current_field].widget.attrs['class'] += ' required'

    ### ADDITIONAL MATRIX FIELDS (unsaved)
    number_of_items = forms.IntegerField(required=False)

    ### ITEM FIELD HELPERS
    # action = forms.ChoiceField(choices=(
    #     ('', 'Please Select an Action'),
    #     ('add_name', 'Add Names/IDs*'),
    #     ('add_test_type', 'Add Test Type*'),
    #     ('add_date', 'Add Setup Date*'),
    #     ('add_device', 'Add Device/MPS Model Information*'),
    #     ('add_settings', 'Add Settings'),
    #     ('add_compounds', 'Add Compounds'),
    #     ('add_cells', 'Add Cells'),
    #     ('add_notes', 'Add Notes/Notebook Information'),
    #     # ADD BACK LATER
    #     # ('copy', 'Copy Contents'),
    #     # TODO TODO TODO TENTATIVE
    #     # ('clear', 'Clear Contents'),
    #     ('delete', 'Delete Selected'),
    # ), required=False)

    # The matrix_item isn't just to be annoying, I want to avoid conflicts with other fields
    ### ADDING ITEM FIELDS
    matrix_item_name = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 1}),
        label='Matrix Item Name'
    )

    matrix_item_setup_date = forms.DateField(
        required=False,
        label='Matrix Item Setup Date'
    )
    # Foolish!
    matrix_item_setup_date_popup = forms.DateField(required=False)

    matrix_item_test_type = forms.ChoiceField(
        required=False,
        choices=TEST_TYPE_CHOICES,
        label='Matrix Item Test Type'
    )

    matrix_item_scientist = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 1}),
        label='Scientist'
    )
    matrix_item_notebook = forms.CharField(
        required=False,
        label='Notebook'
    )
    matrix_item_notebook_page = forms.CharField(
        required=False,
        label='Notebook Page'
    )
    matrix_item_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Notes'
    )

    ### ADDING SETUP FIELDS
    matrix_item_device = forms.ModelChoiceField(
        queryset=Microdevice.objects.all().order_by('name'),
        required=False,
        label='Matrix Item Device'
    )
    matrix_item_organ_model = forms.ModelChoiceField(
        queryset=OrganModel.objects.all().order_by('name'),
        required=False,
        label='Matrix Item MPS Model'
    )
    matrix_item_organ_model_protocol = forms.ModelChoiceField(
        queryset=OrganModelProtocol.objects.all().order_by('version'),
        required=False,
        label='Matrix Item MPS Model Version'
    )
    matrix_item_variance_from_organ_model_protocol = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Matrix Item Variance from Protocol'
    )

    matrix_item_full_organ_model = forms.ModelChoiceField(
        queryset=OrganModel.objects.all().order_by('name'),
        required=False
    )
    matrix_item_full_organ_model_protocol = forms.ModelChoiceField(
        queryset=OrganModelProtocol.objects.all(),
        required=False
    )

    ### INCREMENTER
    compound_concentration_increment = forms.FloatField(required=False, initial=1)
    compound_concentration_increment_type = forms.ChoiceField(
        choices=(
            ('/', 'Divide'),
            ('*', 'Multiply'),
            ('+', 'Add'),
            ('-', 'Subtract')
        ),
        required=False
    )
    compound_concentration_increment_direction = forms.ChoiceField(
        choices=(
            ('lr', 'Left to Right'),
            ('d', 'Down'),
            ('rl', 'Right to Left'),
            ('u', 'Up'),
            ('lrd', 'Left to Right and Down'),
            ('rlu', 'Right to Left and Up')
        ),
        required=False,
        initial='lr'
    )

    # Options for deletion
    delete_option = forms.ChoiceField(
        required=False,
        choices=(
            ('all', 'Everything'),
            ('cell', 'Cells'),
            ('compound', 'Compounds'),
            ('setting', 'Settings'),
        ),
        label='Delete Option'
    )

    # FORCE UNIQUENESS CHECK
    def clean(self):
        super(AssayMatrixForm, self).clean()

        if AssayMatrix.objects.filter(
                study_id=self.instance.study.id,
                name=self.cleaned_data.get('name', '')
        ).exclude(pk=self.instance.pk).count():
            raise forms.ValidationError({'name': ['Matrix name must be unique within study.']})


class AssaySetupCompoundForm(ModelFormSplitTime):
    compound = forms.CharField()

    class Meta(object):
        model = AssaySetupCompound
        exclude = tracking


# TODO: IDEALLY THE CHOICES WILL BE PASSED VIA A KWARG
class AssaySetupCompoundFormSet(BaseModelFormSetForcedUniqueness):
    custom_fields = (
        'matrix_item',
        'compound_instance',
        'concentration_unit',
        'addition_location'
    )

    def __init__(self, *args, **kwargs):
        # TODO EVENTUALLY PASS WITH KWARG
        # self.suppliers = kwargs.pop('suppliers', None)
        # self.compound_instances = kwargs.pop('compound_instances', None)
        # self.compound_instances_dic = kwargs.pop('compound_instances_dic', None)
        # self.setup_compounds = kwargs.pop('setup_compounds', None)
        # Get all chip setup assay compound instances
        self.matrix = kwargs.pop('matrix', None)
        self.setup_compounds = {
            (
                instance.matrix_item_id,
                instance.compound_instance_id,
                instance.concentration,
                instance.concentration_unit_id,
                instance.addition_time,
                instance.duration,
                instance.addition_location_id
            ): True for instance in AssaySetupCompound.objects.filter(
                matrix_item__matrix=self.matrix
            )
        }

        self.compound_instances = {}
        self.compound_instances_dic = {}

        for instance in CompoundInstance.objects.all().prefetch_related('supplier'):
            self.compound_instances.update({
                (
                    instance.compound_id,
                    instance.supplier_id,
                    instance.lot,
                    instance.receipt_date
                ): instance
            })
            # NOTE use of name instead of id!
            self.compound_instances_dic.update({
                instance.id: (
                    instance.compound_id,
                    instance.supplier.name,
                    instance.lot,
                    instance.receipt_date
                )
            })

        # Get all suppliers
        self.suppliers = {
            supplier.name: supplier for supplier in CompoundSupplier.objects.all()
        }

        super(AssaySetupCompoundFormSet, self).__init__(*args, **kwargs)

        filters = {'matrix_item': {'matrix_id': self.matrix.id}}
        self.dic = get_dic_for_custom_choice_field(self, filters=filters)

        for form in self.forms:
            for field in self.custom_fields:
                form.fields[field] = DicModelChoiceField(field, self.model, self.dic)

            # Purge all classes
            for field in form.fields:
                form.fields[field].widget.attrs['class'] = ''

    def _construct_form(self, i, **kwargs):
        form = super(AssaySetupCompoundFormSet, self)._construct_form(i, **kwargs)

        # Text field (un-saved) for supplier
        form.fields['supplier_text'] = forms.CharField(initial='N/A', required=False)
        # Text field (un-saved) for lot
        form.fields['lot_text'] = forms.CharField(initial='N/A', required=False)
        # Receipt date
        form.fields['receipt_date'] = forms.DateField(required=False)

        if form.instance:
            current_compound_instance_id = form.instance.compound_instance_id
        else:
            current_compound_instance_id = None

        if current_compound_instance_id:
            current_compound_instance = self.compound_instances_dic.get(current_compound_instance_id)

            # form.fields['compound'].initial = current_compound_instance.compound
            # form.fields['supplier_text'].initial = current_compound_instance.supplier.name
            # form.fields['lot_text'].initial = current_compound_instance.lot
            # form.fields['receipt_date'].initial = current_compound_instance.receipt_date
            form.fields['compound'].initial = current_compound_instance[0]
            form.fields['supplier_text'].initial = current_compound_instance[1]
            form.fields['lot_text'].initial = current_compound_instance[2]
            form.fields['receipt_date'].initial = current_compound_instance[3]

        return form

    # TODO TODO TODO
    # Will either have to decouple compound instance and supplier or else have a dic ALL FORMSETS reference
    # Ostensibly, I can pass a pointer to a dictionary so that all of the formsets see the same thing
    def save(self, commit=True):
        # Get forms_data (excluding those with delete or no data)
        forms_data = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get('DELETE', False)]
        forms_to_delete = [f for f in self.forms if f.cleaned_data and f.cleaned_data.get('DELETE', False)]

        # Forms to be deleted
        for form in forms_to_delete:
            try:
                instance = BootstrapForm.save(form, commit=False)

                if instance and instance.id and commit:
                    instance.delete()
            # ValueError here indicates that the instance couldn't even validate and so should be ignored
            except ValueError:
                pass

        # Forms to save
        for form in forms_data:
            instance = BootstrapForm.save(form, commit=False)

            matrix_item = instance.matrix_item

            current_data = form.cleaned_data

            # Bad
            if not current_data.get('supplier_text'):
                current_data['supplier_text'] = 'N/A'

            if not current_data.get('lot_text'):
                current_data['lot_text'] = 'N/A'

            compound_id = int(current_data.get('compound'))
            supplier_text = current_data.get('supplier_text').strip()
            lot_text = current_data.get('lot_text').strip()
            receipt_date = current_data.get('receipt_date')

            # Should be acquired straight from form
            # concentration = current_data.get('concentration')
            # concentration_unit = current_data.get('concentration_unit')

            addition_time = 0
            duration = 0
            for time_unit, conversion in list(TIME_CONVERSIONS.items()):
                addition_time += current_data.get('addition_time_' + time_unit, 0) * conversion
                duration += current_data.get('duration_' + time_unit, 0) * conversion

            # Check if the supplier already exists
            supplier = self.suppliers.get(supplier_text, '')
            # Otherwise create the supplier
            if not supplier:
                supplier = CompoundSupplier(
                    name=supplier_text,
                    created_by=matrix_item.created_by,
                    created_on=matrix_item.created_on,
                    modified_by=matrix_item.modified_by,
                    modified_on=matrix_item.modified_on
                )
                # if commit:
                #     supplier.save()
                # Always save the supplier
                supplier.save()
                self.suppliers.update({
                    supplier_text: supplier
                })

            # Check if compound instance exists
            compound_instance = self.compound_instances.get((compound_id, supplier.id, lot_text, receipt_date), '')
            if not compound_instance:
                compound_instance = CompoundInstance(
                    compound_id=compound_id,
                    supplier=supplier,
                    lot=lot_text,
                    receipt_date=receipt_date,
                    created_by=matrix_item.created_by,
                    created_on=matrix_item.created_on,
                    modified_by=matrix_item.modified_by,
                    modified_on=matrix_item.modified_on
                )
                # if commit:
                #     compound_instance.save()
                # ALWAYS MAKE A NEW COMPOUND INSTANCE
                compound_instance.save()
                self.compound_instances.update({
                    (compound_id, supplier.id, lot_text, receipt_date): compound_instance
                })

            # Update the instance with new data
            # instance.matrix_item = matrix_item
            instance.compound_instance = compound_instance

            instance.addition_time = addition_time
            instance.duration = duration

            # Save the instance
            if commit:
                conflicting_assay_compound_instance = self.setup_compounds.get(
                    (
                        instance.matrix_item_id,
                        instance.compound_instance_id,
                        instance.concentration,
                        instance.concentration_unit_id,
                        instance.addition_time,
                        instance.duration,
                        instance.addition_location_id
                    ), None
                )
                # If there is not conflict or if this is an update
                if not conflicting_assay_compound_instance:
                    instance.save()

                # Do nothing otherwise (it already exists)

            self.setup_compounds.update({
                (
                    instance.matrix_item_id,
                    instance.compound_instance_id,
                    instance.concentration,
                    instance.concentration_unit_id,
                    instance.addition_time,
                    instance.duration,
                    instance.addition_location_id
                ): True
            })


# UGLY SOLUTION
class AssaySetupCompoundInlineFormSet(BaseInlineFormSet):
    """Frontend Inline FormSet for Compound Instances"""
    class Meta(object):
        model = AssaySetupCompound
        exclude = ('',)

    def __init__(self, *args, **kwargs):
        """Init Chip Setup Form

        Filters physical units to include only Concentration
        """
        super(AssaySetupCompoundInlineFormSet, self).__init__(*args, **kwargs)
        # Filter compound instances
        compound_instances = CompoundInstance.objects.all().prefetch_related(
            'compound',
            'supplier'
        )
        compound_instances_dic = {
            instance.id: instance for instance in compound_instances
        }

        # Filter on concentration but make a special exception for percent (%)
        concentration_unit_queryset = PhysicalUnits.objects.filter(
            unit_type__unit_type='Concentration'
        ).order_by(
            'base_unit__unit',
            'scale_factor'
        ) | PhysicalUnits.objects.filter(unit='%')

        for form in self.forms:
            # form.fields['start_time_unit'].queryset = time_unit_queryset
            # form.fields['duration_unit'].queryset = time_unit_queryset
            form.fields['concentration_unit'].queryset = concentration_unit_queryset
            form.fields['compound_instance'].queryset = compound_instances

            # All available compounds
            form.fields['compound'] = forms.ModelChoiceField(
                queryset=Compound.objects.all(),
                widget=forms.Select(attrs={'class': 'form-control'})
            )
            # Text field (un-saved) for supplier
            form.fields['supplier_text'] = forms.CharField(
                initial='',
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                required=False
            )
            # Text field (un-saved) for lot
            form.fields['lot_text'] = forms.CharField(
                initial='',
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                required=False
            )
            # Receipt date
            form.fields['receipt_date'] = forms.DateField(
                required=False,
                widget=forms.DateInput(attrs={
                    'class': 'form-control datepicker-input',
                    'autocomplete': 'off'
                })
            )
            # If instance, apply initial values
            if form.instance.compound_instance_id:
                current_compound_instance = compound_instances_dic.get(form.instance.compound_instance_id)

                form.fields['compound'].initial = current_compound_instance.compound
                form.fields['supplier_text'].initial = current_compound_instance.supplier.name
                form.fields['lot_text'].initial = current_compound_instance.lot
                form.fields['receipt_date'].initial = current_compound_instance.receipt_date

            # VERY SLOPPY
            form.fields['compound'].widget.attrs['class'] += ' required'

            current_field = 'compound'
            if hasattr(form.fields[current_field], '_queryset'):
                if hasattr(form.fields[current_field]._queryset, 'model'):
                    # Usually one would use a hyphen rather than an underscore
                    # form.fields[field].widget.attrs['data-app'] = form.fields[field]._queryset.model._meta.app_label
                    form.fields[current_field].widget.attrs['data_app'] = form.fields[current_field]._queryset.model._meta.app_label

                    # form.fields[field].widget.attrs['data-model'] = form.fields[field]._queryset.model._meta.object_name
                    form.fields[current_field].widget.attrs['data_model'] = form.fields[current_field]._queryset.model._meta.object_name

                    form.fields[current_field].widget.attrs['data_verbose_name'] = form.fields[current_field]._queryset.model._meta.verbose_name

                    # Possibly dumber
                    if hasattr(form.fields[current_field]._queryset.model, 'get_add_url_manager'):
                        form.fields[current_field].widget.attrs['data_add_url'] = form.fields[current_field]._queryset.model.get_add_url_manager()

    # TODO THIS IS NOT DRY
    def save(self, commit=True):
        # Get forms_data (excluding those with delete or no data)
        forms_data = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get('DELETE', False)]
        forms_to_delete = [f for f in self.forms if f.cleaned_data and f.cleaned_data.get('DELETE', False)]

        # Forms to be deleted
        for form in forms_to_delete:
            instance = super(BootstrapForm, form).save(commit=False)

            if instance and instance.id and commit:
                instance.delete()

        matrix_item = self.instance

        # Get all chip setup assay compound instances
        assay_compound_instances = {
            (
                instance.compound_instance.id,
                instance.concentration,
                instance.concentration_unit.id,
                instance.addition_time,
                instance.duration,
                instance.addition_location_id
            ): True for instance in AssaySetupCompound.objects.filter(
            matrix_item_id=matrix_item.id
            ).prefetch_related(
                'compound_instance__compound',
                'concentration_unit'
            )
        }

        # Get all Compound Instances
        compound_instances = {
            (
                instance.compound.id,
                instance.supplier.id,
                instance.lot,
                instance.receipt_date
            ): instance for instance in CompoundInstance.objects.all().prefetch_related(
                'compound',
                'supplier'
            )
        }

        # Get all suppliers
        suppliers = {
            supplier.name: supplier for supplier in CompoundSupplier.objects.all()
        }

        # Forms to save
        for form in forms_data:
            instance = super(BootstrapForm, form).save(commit=False)

            current_data = form.cleaned_data

            # Bad
            if not current_data.get('supplier_text'):
                current_data['supplier_text'] = 'N/A'

            if not current_data.get('lot_text'):
                current_data['lot_text'] = 'N/A'

            compound = current_data.get('compound')
            supplier_text = current_data.get('supplier_text').strip()
            lot_text = current_data.get('lot_text').strip()
            receipt_date = current_data.get('receipt_date')

            # Should be acquired straight from form
            # concentration = current_data.get('concentration')
            # concentration_unit = current_data.get('concentration_unit')

            addition_time = 0
            duration = 0
            for time_unit, conversion in list(TIME_CONVERSIONS.items()):
                addition_time += current_data.get('addition_time_' + time_unit, 0) * conversion
                duration += current_data.get('duration_' + time_unit, 0) * conversion

            # Check if the supplier already exists
            supplier = suppliers.get(supplier_text, '')
            # Otherwise create the supplier
            if not supplier:
                supplier = CompoundSupplier(
                    name=supplier_text,
                    created_by=matrix_item.created_by,
                    created_on=matrix_item.created_on,
                    modified_by=matrix_item.modified_by,
                    modified_on=matrix_item.modified_on
                )
                # if commit:
                #     supplier.save()
                # Always save the supplier
                supplier.save()
                suppliers.update({
                    supplier_text: supplier
                })

            # Check if compound instance exists
            compound_instance = compound_instances.get((compound.id, supplier.id, lot_text, receipt_date), '')
            if not compound_instance:
                compound_instance = CompoundInstance(
                    compound=compound,
                    supplier=supplier,
                    lot=lot_text,
                    receipt_date=receipt_date,
                    created_by=matrix_item.created_by,
                    created_on=matrix_item.created_on,
                    modified_by=matrix_item.modified_by,
                    modified_on=matrix_item.modified_on
                )
                # if commit:
                #     compound_instance.save()
                # ALWAYS MAKE A NEW COMPOUND INSTANCE
                compound_instance.save()
                compound_instances.update({
                    (compound.id, supplier.id, lot_text, receipt_date): compound_instance
                })

            # Update the instance with new data
            instance.matrix_item = matrix_item
            instance.compound_instance = compound_instance

            instance.addition_time = addition_time
            instance.duration = duration

            # Save the AssayCompoundInstance
            if commit:
                conflicting_assay_compound_instance = assay_compound_instances.get(
                    (
                        instance.compound_instance.id,
                        instance.concentration,
                        instance.concentration_unit.id,
                        instance.addition_time,
                        instance.duration,
                        instance.addition_location_id
                    ), None
                )
                if not conflicting_assay_compound_instance:
                    instance.save()

            assay_compound_instances.update({
                (
                    instance.compound_instance.id,
                    instance.concentration,
                    instance.concentration_unit.id,
                    instance.addition_time,
                    instance.duration,
                    instance.addition_location_id
                ): True
            })


class AssaySetupCellForm(ModelFormSplitTime):
    class Meta(object):
        model = AssaySetupCell
        exclude = tracking

    def __init__(self, *args, **kwargs):
        # self.static_choices = kwargs.pop('static_choices', None)
        super(AssaySetupCellForm, self).__init__(*args, **kwargs)

        # Change widget size
        self.fields['cell_sample'].widget.attrs['style'] = 'width:75px;'
        self.fields['passage'].widget.attrs['style'] = 'width:75px;'

        self.fields['density_unit'].queryset = PhysicalUnits.objects.filter(availability__contains='cell').order_by('unit')


# TODO: IDEALLY THE CHOICES WILL BE PASSED VIA A KWARG
class AssaySetupCellFormSet(BaseModelFormSetForcedUniqueness):
    custom_fields = (
        'matrix_item',
        'cell_sample',
        'biosensor',
        'density_unit',
        'addition_location'
    )

    def __init__(self, *args, **kwargs):
        self.matrix = kwargs.pop('matrix', None)
        super(AssaySetupCellFormSet, self).__init__(*args, **kwargs)

        filters = {'matrix_item': {'matrix_id': self.matrix.id}}
        self.dic = get_dic_for_custom_choice_field(self, filters=filters)

        for form in self.forms:
            for field in self.custom_fields:
                form.fields[field] = DicModelChoiceField(field, self.model, self.dic)

            # Purge all classes
            for field in form.fields:
                form.fields[field].widget.attrs['class'] = ''


class AssaySetupSettingForm(ModelFormSplitTime):
    class Meta(object):
        model = AssaySetupCell
        exclude = tracking


class AssaySetupSettingFormSet(BaseModelFormSetForcedUniqueness):
    custom_fields = (
        'matrix_item',
        'setting',
        'unit',
        'addition_location'
    )

    def __init__(self, *args, **kwargs):
        self.matrix = kwargs.pop('matrix', None)
        super(AssaySetupSettingFormSet, self).__init__(*args, **kwargs)

        filters = {'matrix_item': {'matrix_id': self.matrix.id }}
        self.dic = get_dic_for_custom_choice_field(self, filters=filters)

        for form in self.forms:
            for field in self.custom_fields:
                form.fields[field] = DicModelChoiceField(field, self.model, self.dic)

            # Purge all classes
            for field in form.fields:
                form.fields[field].widget.attrs['class'] = ''

    def _construct_form(self, i, **kwargs):
        form = super(AssaySetupSettingFormSet, self)._construct_form(i, **kwargs)
        for time_unit in list(TIME_CONVERSIONS.keys()):
            # Create fields for Days, Hours, Minutes
            form.fields['addition_time_' + time_unit] = forms.FloatField(initial=0)
            form.fields['duration_' + time_unit] = forms.FloatField(initial=0)
            # Change style
            # form.fields['addition_time_' + time_unit].widget.attrs['style'] = 'width:75px;'
            # form.fields['duration_' + time_unit].widget.attrs['style'] = 'width:75px;'

        if form.instance.addition_time:
            # Fill additional time
            addition_time_in_minutes_remaining = form.instance.addition_time
            for time_unit, conversion in list(TIME_CONVERSIONS.items()):
                initial_time_for_current_field = int(addition_time_in_minutes_remaining / conversion)
                if initial_time_for_current_field:
                    form.fields['addition_time_' + time_unit].initial = initial_time_for_current_field
                    addition_time_in_minutes_remaining -= initial_time_for_current_field * conversion
            # Add fractions of minutes if necessary
            if addition_time_in_minutes_remaining:
                form.fields['addition_time_minute'].initial += addition_time_in_minutes_remaining

        if form.instance.duration:
            # Fill duration
            duration_in_minutes_remaining = form.instance.duration
            for time_unit, conversion in list(TIME_CONVERSIONS.items()):
                initial_time_for_current_field = int(duration_in_minutes_remaining / conversion)
                if initial_time_for_current_field:
                    form.fields['duration_' + time_unit].initial = initial_time_for_current_field
                    duration_in_minutes_remaining -= initial_time_for_current_field * conversion
            # Add fractions of minutes if necessary
            if duration_in_minutes_remaining:
                form.fields['duration_minute'].initial += duration_in_minutes_remaining

        return form


AssaySetupCompoundFormSetFactory = modelformset_factory(
    AssaySetupCompound,
    extra=1,
    exclude=[tracking],
    form=AssaySetupCompoundForm,
    formset=AssaySetupCompoundFormSet,
    can_delete=True
)
AssaySetupCellFormSetFactory = modelformset_factory(
    AssaySetupCell,
    extra=1,
    exclude=[tracking],
    form=AssaySetupCellForm,
    formset=AssaySetupCellFormSet,
    can_delete=True
)
AssaySetupSettingFormSetFactory = modelformset_factory(
    AssaySetupSetting,
    extra=1,
    exclude=[tracking],
    form=AssaySetupSettingForm,
    formset=AssaySetupSettingFormSet,
    can_delete=True
)
AssaySetupCompoundInlineFormSetFactory = inlineformset_factory(
    AssayMatrixItem,
    AssaySetupCompound,
    extra=1,
    exclude=[tracking],
    form=AssaySetupCompoundForm,
    formset=AssaySetupCompoundInlineFormSet,
    can_delete=True
)
AssaySetupCellInlineFormSetFactory = inlineformset_factory(
    AssayMatrixItem,
    AssaySetupCell,
    extra=1,
    exclude=[tracking],
    form=AssaySetupCellForm,
    # formset=AssaySetupCellFormSet,
    can_delete=True
)
AssaySetupSettingInlineFormSetFactory = inlineformset_factory(
    AssayMatrixItem,
    AssaySetupSetting,
    extra=1,
    exclude=[tracking],
    form=AssaySetupSettingForm,
    # formset=AssaySetupSettingFormSet,
    can_delete=True
)


class AssayMatrixItemFullForm(SignOffMixin, BootstrapForm):
    """Frontend form for Items"""
    class Meta(object):
        model = AssayMatrixItem
        widgets = {
            'concentration': forms.NumberInput(attrs={'style': 'width:75px;'}),
            'notebook_page': forms.NumberInput(attrs={'style': 'width:75px;'}),
            'notes': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
            'variance_from_organ_model_protocol': forms.Textarea(attrs={'cols': 50, 'rows': 2}),
        }
        # Assay Run ID is always bound to the parent Study
        exclude = ('study', 'matrix', 'column_index', 'row_index') + tracking + restricted

    def clean(self):
        """Cleans the Chip Setup Form

        Ensures the the name is unique in the current study
        Ensures that the data for a compound is complete
        Prevents changes to the chip if data has been uploaded (avoiding conflicts between data and entries)
        """
        super(AssayMatrixItemFullForm, self).clean()

        # Make sure the barcode/ID is unique in the study
        if AssayMatrixItem.objects.filter(
                study_id=self.instance.study.id,
                name=self.cleaned_data.get('name')
        ).exclude(id=self.instance.id):
            raise forms.ValidationError({'name': ['ID/Barcode must be unique within study.']})

        # Make sure the device matches if necessary
        if self.instance.matrix.device and (self.instance.matrix.device != self.cleaned_data.get('device')):
            raise forms.ValidationError(
                {'device': ['The item\'s device must match the one specified in the Matrix: "{}"'.format(self.instance.matrix.device)]}
            )


# SetupFormsMixin is unfortunate, but expedient
class AssayMatrixItemForm(SetupFormsMixin, SignOffMixin, BootstrapForm):
    # CONTRIVED!
    series_data = forms.CharField(required=False)

    class Meta(object):
        model = AssayMatrixItem
        # WE OUGHT TO BE ABLE TO EDIT A SELECT FEW THINGS
        fields = (
            'name',
            'group',
            # Notes stuff worth keeping??
            'scientist',
            'notebook',
            'notebook_page',
            'notes'
        )

    def __init__(self, *args, **kwargs):
        super(AssayMatrixItemForm, self).__init__(*args, **kwargs)

        # Gee, it might be nice to have a better way to query groups!
        # Use chip groups if chip
        if self.instance.matrix.representation == 'chips':
            self.fields['group'].queryset = AssayGroup.objects.filter(
                # We will always know the study, this can never be an add page
                study_id=self.instance.study_id,
                organ_model__device__device_type='chip'
            ).prefetch_related('organ_model__device')

            # UGLY: DO NOT LIKE THIS
            # Prepopulate series_data
            self.fields['series_data'].initial = self.instance.study.get_group_data_string(get_chips=True)

        # Otherwise use plate groups
        # TODO: IF WE ARE BINDING PLATES TO MODELS, WE CANNOT DO THIS!
        else:
            self.fields['group'].queryset = AssayGroup.objects.filter(
                study_id=self.instance.study_id,
                # See above
                # OOPS! WE NEED TO RESPECT THE ORGAN MODEL OR WHATEVER
                # organ_model__device__device_type='plate'
                # MATCH THE ORGAN MODEL ID OF CURRENT GROUP!
                organ_model_id=self.instance.group.organ_model_id
            ).prefetch_related('organ_model__device')

            # UGLY: DO NOT LIKE THIS
            # Prepopulate series_data
            self.fields['series_data'].initial = self.instance.study.get_group_data_string(plate_id=self.instance.matrix_id)

# DEPRECATED JUNK
class AssayMatrixItemInlineForm(forms.ModelForm):
    class Meta(object):
        model = AssayMatrixItem
        exclude = ('study', 'matrix') + tracking


# TODO NEED TO TEST (NOTE FROM THE FUTURE: "NOT ANYMORE I DON'T, THIS IS DEPRECATED TRASH!")
class AssayMatrixItemFormSet(BaseInlineFormSetForcedUniqueness):
    custom_fields = (
        'device',
        'organ_model',
        'organ_model_protocol',
        'failure_reason'
    )

    def __init__(self, *args, **kwargs):
        # Get the study
        self.study = kwargs.pop('study', None)
        self.user = kwargs.pop('user', None)
        super(AssayMatrixItemFormSet, self).__init__(*args, **kwargs)

        if not self.study:
            self.study = self.instance.study

        self.dic = get_dic_for_custom_choice_field(self)

        for form in self.forms:
            for field in self.custom_fields:
                form.fields[field] = DicModelChoiceField(field, self.model, self.dic)

            if self.study:
                form.instance.study = self.study

            if form.instance.pk:
                form.instance.modified_by = self.user
            else:
                form.instance.created_by = self.user

        self.invalid_matrix_item_names = {
            item.name: item.id for item in AssayMatrixItem.objects.filter(study_id=self.study.id)
        }

    def clean(self):
        super(AssayMatrixItemFormSet, self).clean()

        for index, form in enumerate(self.forms):
            current_data = form.cleaned_data

            if current_data and not current_data.get('DELETE', False):
                if self.instance.number_of_columns:
                    if current_data.get('column_index') > self.instance.number_of_columns:
                        raise forms.ValidationError(
                            'An Item extends beyond the columns of the Matrix.'
                            ' Increase the size of the Matrix and/or delete the offending Item if necessary.'
                        )
                    if current_data.get('row_index') > self.instance.number_of_rows:
                        raise forms.ValidationError(
                            'An Item extends beyond the rows of the Matrix.'
                            ' Increase the size of the Matrix and/or delete the offending Item if necessary.'
                        )

                # Make sure the barcode/ID is unique in the study
                conflicting_name_item_id = self.invalid_matrix_item_names.get(current_data.get('name'), None)
                if conflicting_name_item_id and conflicting_name_item_id != form.instance.pk:
                    form.add_error('name', 'This name conflicts with existing Item names in this Study.')

                # Make sure the device matches if necessary
                if self.instance.device and (self.instance.device != current_data.get('device')):
                    form.add_error('device', 'This device conflicts with the one listed in the Matrix.')

AssayMatrixItemFormSetFactory = inlineformset_factory(
    AssayMatrix,
    AssayMatrixItem,
    formset=AssayMatrixItemFormSet,
    form=AssayMatrixItemInlineForm,
    extra=1,
    exclude=('study',) + tracking
)


class AssayStudyDeleteForm(forms.ModelForm):
    class Meta(object):
        model = AssayStudy
        fields = []


class AssayStudySignOffForm(SignOffMixin, BootstrapForm):
    class Meta(object):
        model = AssayStudy
        fields = ['signed_off', 'signed_off_notes']
        widgets = {
            'signed_off_notes': forms.Textarea(attrs={'cols': 50, 'rows': 2}),
        }


class AssayStudyStakeholderSignOffForm(SignOffMixin, BootstrapForm):
    class Meta(object):
        model = AssayStudyStakeholder
        fields = ['signed_off', 'signed_off_notes']
        widgets = {
            'signed_off_notes': forms.Textarea(attrs={'cols': 50, 'rows': 2}),
        }


class AssayStudyStakeholderFormSet(BaseInlineFormSet):
    class Meta(object):
        model = AssayStudyStakeholder

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(AssayStudyStakeholderFormSet, self).__init__(*args, **kwargs)

    def get_queryset(self):
        if not hasattr(self, '_queryset'):
            # TODO FILTER OUT THOSE USER ISN'T ADMIN OF
            # TODO REVIEW
            user_admin_groups = self.user.groups.filter(name__contains=ADMIN_SUFFIX)
            potential_groups = [group.name.replace(ADMIN_SUFFIX, '') for group in user_admin_groups]
            queryset = super(AssayStudyStakeholderFormSet, self).get_queryset()
            # Only include unsigned off forms that user is admin of!
            self._queryset = queryset.filter(
                group__name__in=potential_groups,
                signed_off_by=None
            )
        return self._queryset

    def save(self, commit=True):
        for form in self.forms:
            signed_off = form.cleaned_data.get('signed_off', False)
            if signed_off and is_group_admin(self.user, form.instance.group.name):
                form.instance.signed_off_by = self.user
                form.instance.signed_off_date = timezone.now()
                form.save(commit=True)

# Really, all factories should be declared like so (will have to do this for upcoming revision)
AssayStudyStakeholderFormSetFactory = inlineformset_factory(
    AssayStudy,
    AssayStudyStakeholder,
    form=AssayStudyStakeholderSignOffForm,
    formset=AssayStudyStakeholderFormSet,
    extra=0,
    can_delete=False
)


class AssayStudyDataUploadForm(BootstrapForm):
    """Form for Bulk Uploads"""
    # Excluded for now
    # overwrite_option = OVERWRITE_OPTIONS_BULK

    # EVIL WAY TO GET PREVIEW DATA
    preview_data = forms.BooleanField(initial=False, required=False)

    class Meta(object):
        model = AssayStudy
        fields = ('bulk_file',)

    def __init__(self, *args, **kwargs):
        """Init the Bulk Form

        kwargs:
        request -- the current request
        """
        self.request = kwargs.pop('request', None)

        super(AssayStudyDataUploadForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(AssayStudyDataUploadForm, self).clean()

        # Get the study in question
        study = self.instance

        # test_file = None

        # TODO TODO TODO TODO TODO
        if self.request and self.request.FILES and data.get('bulk_file'):
            # Make sure that this isn't the current file
            if not study.bulk_file or study.bulk_file != data.get('bulk_file'):
                test_file = data.get('bulk_file', '')

                file_processor = AssayFileProcessor(test_file, study, self.request.user)
                # Process the file
                file_processor.process_file()

                # Evil attempt to acquire preview data
                self.cleaned_data['preview_data'] = file_processor.preview_data

        return self.cleaned_data


class AssayStudySetForm(SignOffMixin, BootstrapForm):
    class Meta(object):
        model = AssayStudySet
        exclude = tracking
        widgets = {
            'description': forms.Textarea(attrs={'rows': 10})
        }

    def __init__(self, *args, **kwargs):
        super(AssayStudySetForm, self).__init__(*args, **kwargs)

        study_queryset = get_user_accessible_studies(
            self.user
        ).prefetch_related(
            'group__microphysiologycenter_set',
        )
        assay_queryset = AssayStudyAssay.objects.filter(
            study_id__in=study_queryset.values_list('id', flat=True)
        ).prefetch_related(
            'target',
            'method',
            'unit'
        )

        self.fields['studies'].queryset = study_queryset
        self.fields['assays'].queryset = assay_queryset

        # CONTRIVED
        self.fields['studies'].widget.attrs['class'] = 'no-selectize'
        self.fields['assays'].widget.attrs['class'] = 'no-selectize'


class AssayReferenceForm(BootstrapForm):

    query_term = forms.CharField(
        initial='',
        required=False,
        label='PubMed ID / DOI'
    )

    class Meta(object):
        model = AssayReference
        exclude = tracking
        widgets = {
            'query_term': forms.Textarea(attrs={'rows': 1}),
            'title': forms.Textarea(attrs={'rows': 2}),
            'authors': forms.Textarea(attrs={'rows': 1}),
            'abstract': forms.Textarea(attrs={'rows': 10}),
            'publication': forms.Textarea(attrs={'rows': 1}),
        }

AssayStudyReferenceFormSetFactory = inlineformset_factory(
    AssayStudy,
    AssayStudyReference,
    extra=1,
    exclude=[]
)

AssayStudySetReferenceFormSetFactory = inlineformset_factory(
    AssayStudySet,
    AssayStudySetReference,
    extra=1,
    exclude=[]
)


# Convoluted
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


class AssayMatrixFormNew(SetupFormsMixin, SignOffMixin, BootstrapForm):
    # ADD test_types
    test_type = forms.ChoiceField(
        initial='control',
        choices=TEST_TYPE_CHOICES
    )

    class Meta(object):
        model = AssayMatrix
        # ODD
        fields = []

    def __init__(self, *args, **kwargs):
        """Init the Study Form

        Kwargs:
        user -- the user in question
        """
        # PROBABLY DON'T NEED THIS?
        # self.user = kwargs.pop('user', None)
        super(AssayMatrixFormNew, self).__init__(*args, **kwargs)

        # SLOPPY
        self.fields['test_type'].widget.attrs['class'] += ' no-selectize test-type'
        # Bad
        self.fields['test_type'].widget.attrs['style'] = 'width:100px;'


# PLEASE NOTE CRUDE HANDLING OF m2m
class AssayTargetForm(BootstrapForm):
    # For adding to category m2m
    category = forms.ModelMultipleChoiceField(
        queryset=AssayCategory.objects.all().order_by('name'),
        # Should this be required?
        required=False,
        # empty_label='All'
    )

    class Meta(object):
        model = AssayTarget
        exclude = tracking

        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(AssayTargetForm, self).__init__(*args, **kwargs)

        # Get category if possible
        if self.instance and self.instance.id:
            self.initial_categories = AssayCategory.objects.filter(
                targets__id=self.instance.id
            )
            self.fields['category'].initial = (
                self.initial_categories
            )
        else:
            self.initial_categories = AssayCategory.objects.none()

        # Sort the methods
        # Would it be better to have this applied to all method queries?
        self.fields['methods'].queryset = AssayMethod.objects.all().order_by('name')

    def save(self, commit=True):
        new_target = super(AssayTargetForm, self).save(commit)

        if commit:
            if self.cleaned_data.get('category', None):
                for current_category in self.cleaned_data.get('category', None):
                    current_category.targets.add(self.instance)

            # Permit removals for the moment
            # Crude removal
            for initial_category in self.initial_categories:
                if initial_category not in self.cleaned_data.get('category', None):
                    initial_category.targets.remove(self.instance)

        return new_target


class AssayTargetRestrictedForm(BootstrapForm):
    # For adding to category m2m
    category = forms.ModelMultipleChoiceField(
        queryset=AssayCategory.objects.all().order_by('name'),
        # Should this be required?
        required=False,
        # empty_label='All'
    )
    # We don't actually want restricted users to meddle with the methods straight (they could remove methods)
    method_proxy = forms.ModelMultipleChoiceField(
        queryset=AssayMethod.objects.all().order_by('name'),
        label='Methods'
    )

    class Meta(object):
        model = AssayTarget
        fields = ['category', 'method_proxy']

    def __init__(self, *args, **kwargs):
        super(AssayTargetRestrictedForm, self).__init__(*args, **kwargs)

        # Get category if possible
        # (It should always be possible, this form is for editing)
        if self.instance and self.instance.id:
            self.fields['category'].initial = (
                AssayCategory.objects.filter(
                    targets__id=self.instance.id
                )
            )
            self.fields['method_proxy'].initial = (
                self.instance.methods.all()
            )
    def save(self, commit=True):
        new_target = super(AssayTargetRestrictedForm, self).save(commit)

        if commit:
            if self.cleaned_data.get('category', None):
                for current_category in self.cleaned_data.get('category', None):
                    current_category.targets.add(self.instance)
            if self.cleaned_data.get('method_proxy', None):
                for current_method in self.cleaned_data.get('method_proxy', None):
                    self.instance.methods.add(current_method)

        return new_target


class AssayMethodForm(BootstrapForm):
    # For adding to target m2m
    targets = forms.ModelMultipleChoiceField(
        queryset=AssayTarget.objects.all().order_by('name'),
        # No longer required to prevent circularity with Target
        required=False
    )

    class Meta(object):
        model = AssayMethod
        exclude = tracking

        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(AssayMethodForm, self).__init__(*args, **kwargs)

        # Get target if possible
        if self.instance and self.instance.id:
            self.initial_targets = AssayTarget.objects.filter(
                methods__id=self.instance.id
            )
            self.fields['targets'].initial = (
                self.initial_targets
            )
        else:
            self.initial_targets = AssayTarget.objects.none()

    def save(self, commit=True):
        new_method = super(AssayMethodForm, self).save(commit)

        if commit:
            for current_target in self.cleaned_data.get('targets', None):
                current_target.methods.add(self.instance)

            # Permit removals for the moment
            # Crude removal
            for initial_target in self.initial_targets:
                if initial_target not in self.cleaned_data.get('targets', None):
                    initial_target.methods.remove(self.instance)

        return new_method


class AssayMethodRestrictedForm(BootstrapForm):
    # For adding to target m2m
    targets = forms.ModelMultipleChoiceField(
        queryset=AssayTarget.objects.all().order_by('name'),
        # No longer required to prevent circularity with Target
        required=False
    )

    class Meta(object):
        model = AssayMethod
        # Only include the target, we don't want anything else to change
        fields = ['targets']

    def __init__(self, *args, **kwargs):
        super(AssayMethodRestrictedForm, self).__init__(*args, **kwargs)

        # Get target if possible
        # (It should always be possible, this form is only for editing)
        if self.instance and self.instance.id:
            self.fields['targets'].initial = (
                AssayTarget.objects.filter(
                    methods__id=self.instance.id
                )
            )

    def save(self, commit=True):
        new_method = super(AssayMethodRestrictedForm, self).save(commit)

        if commit:
            # In the restricted form, one is allowed to add targets ONLY
            for current_target in self.cleaned_data.get('targets', None):
                current_target.methods.add(self.instance)

        return new_method


class PhysicalUnitsForm(BootstrapForm):
    class Meta(object):
        model = PhysicalUnits
        exclude = tracking + ('availability',)

        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }


class AssayMeasurementTypeForm(BootstrapForm):
    class Meta(object):
        model = AssayMeasurementType
        exclude = tracking

        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }


class AssaySampleLocationForm(BootstrapForm):
    class Meta(object):
        model = AssaySampleLocation
        exclude = tracking

        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }


class AssaySettingForm(BootstrapForm):
    class Meta(object):
        model = AssaySetting
        exclude = tracking

        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }


class AssaySupplierForm(BootstrapForm):
    class Meta(object):
        model = AssaySupplier
        exclude = tracking

        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }


#####
# sck - ASSAY PLATE MAP START


# monkey patch to display method target and unit combo as needed in the assay plate map page
class AbstractClassAssayStudyAssay(AssayStudyAssay):
    class Meta:
        proxy = True

    def __str__(self):
        # return 'TARGET: {0}  METHOD: {1}  UNIT: {2}'.format(self.target, self.method, self.unit)
        return '{2}  --- TARGET: {0} by METHOD: {1}'.format(self.target, self.method, self.unit)


# Get info to populate pick lists; no qc needed on this form, just to use on webpage to allow user selections
class AssayPlateReadMapAdditionalInfoForm(forms.Form):
    """Form for Assay Plate Reader Map add/update/view extra info for dropdowns that are just used in GUI (not saved)."""

    def __init__(self, *args, **kwargs):
        study_id = kwargs.pop('study_id', None)
        self.user = kwargs.pop('user', None)
        super(AssayPlateReadMapAdditionalInfoForm, self).__init__(*args, **kwargs)
        # note that the non-selectized versions are manipulated in javascript to facilitate the plate map
        # they are not displayed to the user (they are hidden)
        # something did very early in development...probably would do differently now
        self.fields['se_matrix_item'].queryset = AssayMatrixItem.objects.filter(study_id=study_id).order_by('name',)
        self.fields['ns_matrix_item'].queryset = AssayMatrixItem.objects.filter(study_id=study_id).order_by('name',)
        self.fields['ns_matrix_item'].widget.attrs.update({'class': 'no-selectize'})
        self.fields['ns_location'].widget.attrs.update({'class': 'no-selectize'})
        self.fields['se_matrix'].queryset = AssayMatrix.objects.filter(
            study_id=study_id
        ).order_by('name',)
        self.fields['se_matrix'].widget.attrs.update({'class': ' required'})
        self.fields['se_platemap'].queryset = AssayPlateReaderMap.objects.filter(
            study_id=study_id
        ).order_by('name',)
        self.fields['se_platemap'].widget.attrs.update({'class': ' required'})

    # before got to development of calibration/processing the data
    ns_matrix_item = forms.ModelChoiceField(
        queryset=AssayMatrixItem.objects.none(),
        required=False,
    )
    se_matrix_item = forms.ModelChoiceField(
        queryset=AssayMatrixItem.objects.none(),
        required=False,
    )
    se_matrix = forms.ModelChoiceField(
        queryset=AssayMatrix.objects.none(),
        required=False,
    )
    se_platemap = forms.ModelChoiceField(
        queryset=AssayPlateReaderMap.objects.none(),
        required=False,
    )
    se_main_well_use = forms.ChoiceField(
        choices=assay_plate_reader_main_well_use_choices
    )
    se_blank_well_use = forms.ChoiceField(
        choices=assay_plate_reader_blank_well_use_choices
    )
    se_time_unit = forms.ChoiceField(
        choices=assay_plate_reader_time_unit_choices
    )
    se_location = forms.ModelChoiceField(
         queryset=AssaySampleLocation.objects.all().order_by(
             'name'
         ),
         required=False,
    )
    ns_location = forms.ModelChoiceField(
         queryset=AssaySampleLocation.objects.all(),
         required=False,
    )
    se_increment_operation = forms.ChoiceField(
        choices=(('divide', 'Divide'), ('multiply', 'Multiply'), ('subtract', 'Subtract'), ('add', 'Add'))
    )
    form_number_time = forms.DecimalField(
        required=False,
        initial=1,
    )
    form_number_time.widget.attrs.update({'class': 'form-control'})
    form_number_default_time = forms.DecimalField(
        required=False,
        initial=1,
    )
    form_number_default_time.widget.attrs.update({'class': 'form-control'})
    form_number_standard_value = forms.DecimalField(
        required=False,
        initial=0,
    )
    form_number_standard_value.widget.attrs.update({'class': 'form-control'})
    form_number_dilution_factor = forms.DecimalField(
        required=False,
        initial=1,
    )
    form_number_dilution_factor.widget.attrs.update({'class': 'form-control'})
    form_number_collection_volume = forms.DecimalField(
        required=False,
        initial=1,
    )
    form_number_collection_volume.widget.attrs.update({'class': 'form-control'})
    form_number_collection_time = forms.DecimalField(
        required=False,
        initial=1,
    )
    form_number_collection_time.widget.attrs.update({'class': 'form-control'})
    form_number_increment_value = forms.DecimalField(
        required=False,
        initial=1,
    )
    form_number_increment_value.widget.attrs.update({'class': 'form-control'})


# Parent for plate reader map page
class AssayPlateReaderMapForm(BootstrapForm):
    """Form for Assay Plate Reader Map"""

    class Meta(object):
        model = AssayPlateReaderMap
        fields = [
            # 'id', do not need in queryset
            'name',
            'description',
            'device',
            'study_assay',
            'time_unit',
            'volume_unit',
            'standard_unit',
            'cell_count',
            'standard_molecular_weight',
            'well_volume'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study', None)
        # self.user = kwargs.pop('user', None)
        super(AssayPlateReaderMapForm, self).__init__(*args, **kwargs)

        # need these or get blank study_assay in the update page (add page worked okay without)
        if not self.study and self.instance.study:
            self.study = self.instance.study
        if self.study:
            self.instance.study = self.study

        # plate map instance - note, based on model, this is the name, use .id for the pk
        my_instance = self.instance

        # note that, if leave selectize on, will need to change js file $("#id_device").val(matrix_size);
        # for tips on working with selectize, search in path for HANDY
        # self.fields['device'].widget.attrs['class'] += ' no-selectize'
        self.fields['name'].initial = "map-" + datetime.datetime.now().strftime("%Y%m%d")+"-"+datetime.datetime.now().strftime('%H:%M:%S')
        self.fields['name'].widget.attrs['class'] += ' required'
        self.fields['device'].widget.attrs['class'] += ' required'
        self.fields['time_unit'].widget.attrs['class'] += ' required'
        self.fields['standard_unit'].widget.attrs['class'] += ' required'
        self.fields['study_assay'].queryset = AbstractClassAssayStudyAssay.objects.filter(
            study_id=self.study
        ).prefetch_related(
            'target',
            'method',
            'unit',
        )
        self.fields['study_assay'].widget.attrs['class'] += ' required'
        # the selectize was causing PROBLEMS, I turned it off this field
        # HANDY - turn of selectize at the form level
        # self.fields['volume_unit'].widget.attrs.update({'class': 'no-selectize'})
        # self.fields['volume_unit'].widget.attrs['class'] += ' form-control'
        self.fields['standard_molecular_weight'].widget.attrs['class'] += ' form-control'

        ######
        # START section to deal with raw data showing in the plate map after file assignment
        # this will populate a dropdown that lets the user pick which file block to see on the page (map and calibrate)
        # For the dropdown, only look for those file blocks that have a populated file block id
        # get a record in the table with the plate index of 0 and that have a file block id
        as_value_formset_with_file_block = AssayPlateReaderMapItemValue.objects.filter(
            assayplatereadermap=my_instance.id
        ).prefetch_related(
            'assayplatereadermapitem',
        ).filter(
            assayplatereadermapitem__plate_index=0
        ).filter(
            assayplatereadermapdatafileblock__isnull=False
        ).order_by(
            'assayplatereadermapdatafileblock__id',
        )

        distinct_plate_map_with_select_string = []
        distinct_plate_map_with_block_pk = []
        number_filed_combos = len(as_value_formset_with_file_block)

        # print("print number of filed combos-forms.py: ", number_filed_combos)

        # queryset should have one record for each value SET that HAS a file-block associated to it
        # make a choice list/field for the file-block combos for this plate map
        if number_filed_combos > 0:
            i = 0
            for record in as_value_formset_with_file_block:
                short_file_name = os.path.basename(str(record.assayplatereadermapdatafile.plate_reader_file))
                data_block_label = str(record.assayplatereadermapdatafileblock.data_block)
                data_block_metadata = record.assayplatereadermapdatafileblock.data_block_metadata
                # data_file_id_str = str(record.assayplatereadermapdatafile.id)
                data_file_block_id_str = str(record.assayplatereadermapdatafileblock.id)
                # make a choice tuple list for showing selections and a choice tuple list of containing the file pk and block pk for javascript
                pick_value = str(i)
                pick_string = 'FILE: ' + short_file_name + ' BLOCK: ' + data_block_label + '  ' + data_block_metadata
                # pick_string_pk = data_file_id_str + '-' + data_file_block_id_str
                pick_string_block_pk = data_file_block_id_str
                distinct_plate_map_with_select_string.append((pick_value, pick_string))
                distinct_plate_map_with_block_pk.append((pick_value, pick_string_block_pk))
                # print("looking for unique blocks counter ", i)
                i = i + 1

        # self.fields['ns_file_pk_block_pk'].widget.attrs['class'] += ' no-selectize'
        self.fields['form_number_file_block_combos'].required = False
        self.fields['form_number_file_block_combos'].initial = number_filed_combos

        # file block options associated with a specific plate map
        self.fields['se_block_select_string'].required = False
        self.fields['se_block_select_string'].widget.attrs['class'] += ' required'
        self.fields['se_block_select_string'].choices = distinct_plate_map_with_select_string
        self.fields['ns_block_select_pk'].required = False
        self.fields['ns_block_select_pk'].widget.attrs.update({'class': 'no-selectize'})
        self.fields['ns_block_select_pk'].choices = distinct_plate_map_with_block_pk

        self.fields['se_form_calibration_curve'].widget.attrs.update({'class': ' required'})
        self.fields['form_make_mifc_on_submit'].widget.attrs.update({'class': ' big-checkbox'})
        self.fields['se_form_calibration_curve'].required = False
        self.fields['se_form_blank_handling'].required = False
        self.fields['radio_replicate_handling_average_or_not'].required = False

        # HANDY - save problems, this is likely the cause (required fields!)
        # self.fields['form_data_processing_multiplier_string'].required = False
        #
        # self.fields['form_data_processing_multiplier_string_short'].required = False
        # self.fields['form_data_processing_multiplier_value_short'].required = False

        # these multiplier fields were added to explain the multiplier in a table
        # the long string was unacceptable to the project PI
        # these really don't have to be form fields (not needed for data processing), but it was just easier/faster
        # self.fields['form_data_processing_multiplier_string1'].required = False
        # self.fields['form_data_processing_multiplier_string2'].required = False
        # self.fields['form_data_processing_multiplier_string3'].required = False
        # self.fields['form_data_processing_multiplier_string4'].required = False
        # self.fields['form_data_processing_multiplier_string5'].required = False
        # self.fields['form_data_processing_multiplier_string6'].required = False
        # self.fields['form_data_processing_multiplier_string7'].required = False
        # self.fields['form_data_processing_multiplier_string8'].required = False
        # self.fields['form_data_processing_multiplier_string9'].required = False

        # calibration fields - only a few are really needed as form fields (eg the calibration curve used, bounds)
        # many are not really needed in the data processing and could be handled differently
        self.fields['form_data_parsable_message'].required = False
        self.fields['form_calibration_curve_method_used'].required = False
        # self.fields['form_calibration_equation'].required = False
        # self.fields['form_calibration_rsquared'].required = False

        # self.fields['form_calibration_parameter_1_string'].required = False
        # self.fields['form_calibration_parameter_2_string'].required = False
        # self.fields['form_calibration_parameter_3_string'].required = False
        # self.fields['form_calibration_parameter_4_string'].required = False
        # self.fields['form_calibration_parameter_5_string'].required = False
        # self.fields['form_calibration_parameter_1_value'].required = False
        # self.fields['form_calibration_parameter_2_value'].required = False
        # self.fields['form_calibration_parameter_3_value'].required = False
        # self.fields['form_calibration_parameter_4_value'].required = False
        # self.fields['form_calibration_parameter_5_value'].required = False
        self.fields['form_calibration_standard_fitted_min_for_e'].required = False
        self.fields['form_calibration_standard_fitted_max_for_e'].required = False
        self.fields['form_calibration_sample_blank_average'].required = False
        self.fields['form_calibration_standard_standard0_average'].required = False
        self.fields['form_calibration_method'].required = False
        self.fields['form_calibration_target'].required = False
        self.fields['form_calibration_unit'].required = False
        self.fields['form_number_standards_this_plate'].required = False
        self.fields['form_hold_the_data_block_metadata_string'].required = False
        self.fields['form_hold_the_omits_string'].required = False
        self.fields['form_hold_the_notes_string'].required = False

        # Need a valid choice field.
        # When the selected plate map has standards, the user will never see this field and will not need it.
        # If the plate does not have standards, the user will need the option to pick to borrow standards from another plate.
        # Lab representative (ie Richard) indicated that standards, standard blanks, and sample blanks would all be borrowed from the same plate!

        # does this plate map have standards?
        does_this_plate_have_standards = AssayPlateReaderMapItem.objects.filter(
            assayplatereadermap=my_instance.id
        ).filter(
            well_use='standard'
        )
        number_standards_wells_on_plate = len(does_this_plate_have_standards)

        choiceBorrowData = (0, 'Select One'),
        choiceBorrowDataToPlateMap = (0, 0),

        if number_standards_wells_on_plate > 0:
            # left - file block pk in both
            # right is a string of the data block meta data for selection of data block pk (left)
            choiceBorrowData = choiceBorrowData
            # right is plate map pk
            choiceBorrowDataToPlateMap = choiceBorrowDataToPlateMap
        else:
            # if we have to borrow standards, need a list to pick from - add to choiceBorrowData
            # need to borrow standards from another plate
            # 20200510 - moving this to here from ajax call. Might move back depending on performance.
            # most users will not do it this way....
            as_value_formset_with_file_block_standard = AssayPlateReaderMapItemValue.objects.filter(
                study_id=self.study
            ).filter(
                assayplatereadermapdatafileblock__isnull=False
            ).prefetch_related(
                'assayplatereadermapdatafileblock',
                'assayplatereadermap',
                'assayplatereadermapitem',
            ).filter(
                assayplatereadermapitem__well_use='standard'
            ).order_by(
                'assayplatereadermapdatafileblock__id', 'assayplatereadermapitem__well_use'
            )

            # print('as_value_formset_with_file_block_standard')
            # print(as_value_formset_with_file_block_standard)

            prev_file = "none"
            prev_data_block_file_specific_pk = 0

            # queryset should have one record for each value SET that HAS a file-block and at least one standard associated to it
            if len(as_value_formset_with_file_block_standard) > 0:
                for record in as_value_formset_with_file_block_standard:

                    short_file_name = os.path.basename(str(record.assayplatereadermapdatafile.plate_reader_file))
                    # this is the data block of the file (for file 0 to something...)
                    data_block_file_specific_pk = record.assayplatereadermapdatafileblock.data_block

                    if prev_file == short_file_name and prev_data_block_file_specific_pk == data_block_file_specific_pk:
                        pass
                    else:
                        data_platemap_pk = record.assayplatereadermap_id
                        data_platemap_name = record.assayplatereadermap.name
                        data_block_metadata = record.assayplatereadermapdatafileblock.data_block_metadata
                        data_block_database_pk = record.assayplatereadermapdatafileblock.id

                        # make a choice tuple list for showing selections and a choice tuple list of containing the file pk and block pk for javascript
                        pick_string = 'PLATEMAP: ' + data_platemap_name + '  FILE: ' + short_file_name + '  BLOCK: ' + data_block_metadata + ' (' + str(
                            data_block_file_specific_pk) + ')'

                        addString1 = (data_block_database_pk, pick_string),
                        choiceBorrowData = choiceBorrowData + addString1
                        addString2 = (data_block_database_pk, data_platemap_pk),
                        choiceBorrowDataToPlateMap = choiceBorrowDataToPlateMap + (addString2)

                    prev_file = short_file_name
                    prev_data_block_file_specific_pk = data_block_file_specific_pk

        # print('choiceBorrowData')
        # print(choiceBorrowData)
        # print('choiceBorrowDataToPlateMap')
        # print(choiceBorrowDataToPlateMap)

        self.fields['se_block_standard_borrow_string'].choices = choiceBorrowData
        self.fields['ns_block_standard_borrow_string_to_block_pk_back_to_platemap_pk'].choices = choiceBorrowDataToPlateMap
        self.fields['ns_block_standard_borrow_string_to_block_pk_back_to_platemap_pk'].required = False
        self.fields['se_block_standard_borrow_string'].widget.attrs['class'] += ' required'
        self.fields['se_block_standard_borrow_string'].required = False

    # enable the selection of a plate to borrow standards from by letting the user see a string of info about the DATA BLOCK (not just the plate map!)
    se_block_standard_borrow_string = forms.ChoiceField()
    ns_block_standard_borrow_string_to_block_pk_back_to_platemap_pk = forms.ChoiceField()

    # pk of the file block borrowing when no standards on the current plate (store it here)
    form_block_standard_borrow_pk_single_for_storage = forms.IntegerField(
        required=False,
    )
    # pk of the plate map associated with the file block borrowing when no standards on the current plate (store it here)
    form_block_standard_borrow_pk_platemap_single_for_storage = forms.IntegerField(
        required=False,
    )
    # here here, remove these next two after checking other way works
    # form_hold_the_study_id = forms.IntegerField(
    #     required=False,
    # )
    # form_hold_the_platemap_id = forms.IntegerField(
    #     required=False,
    # )
    form_hold_the_data_block_metadata_string = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'initial': '-'})
    )
    form_hold_the_omits_string = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'initial': '-'})
    )
    form_hold_the_notes_string = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'initial': '-'})
    )
    form_block_file_data_block_selected_pk_for_storage = forms.IntegerField(
        required=False,
    )

    form_number_file_block_combos = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    # string of selected file block (selected in dropdown)
    se_block_select_string = forms.ChoiceField()
    # pk of selected file block (stays lined up with the string)
    ns_block_select_pk = forms.ChoiceField()

    # END section to deal with raw data showing in the plate map after file assignment and deal with standard in a different file block

    # print(calibration_choices)

    # processing the data fields added
    se_form_calibration_curve = forms.ChoiceField(
        choices=(
            calibration_choices
            # ('select_one', 'Select One'),
            # ('no_calibration', 'No Calibration'),
            # ('best_fit', 'Best Fit'),
            # ('logistic4', '4 Parameter Logistic w/fitted bounds'),
            # ('logistic4a0', '4 Parameter Logistic w/lower bound = 0'),
            # ('logistic4f', '4 Parameter Logistic w/user specified bound(s)'),
            # ('linear', 'Linear w/fitted intercept'),
            # ('linear0', 'Linear w/intercept = 0'),
            # ('log', 'Logarithmic'),
            # ('poly2', 'Quadratic Polynomial'),

            # ('select_one', 'Select One (n = standard concentration, s = signal)'),
            # ('no_calibration', 'No Calibration'),
            # ('best_fit', 'Best Fit'),
            # ('logistic4', '4 Parameter Logistic (s = ((A-D)/(1.0+((n/C)**B))) + D)'),
            # ('linear', 'Linear w/fitted intercept (s = B*n + A)'),
            # ('linear0', 'Linear w/intercept = 0 (s = B*n)'),
            # ('log', 'Logarithmic (s = B*ln(n) + A)'),
            # ('poly2', 'Polynomial (s = C*n**2 + B*n + A)'),

            )
    )

    # forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    # se_form_blank_handling = forms.ChoiceField(widget=forms.RadioSelect(attrs={'disabled': 'disabled'}),
    se_form_blank_handling = forms.ChoiceField(
        choices=(('subtracteachfromeach', 'Subtracting Average STANDARD Blanks from STANDARDS and Average SAMPLE Blanks from SAMPLES'),
                 ('subtractstandardfromstandard', 'Subtracting Average STANDARD Blanks from STANDARDS (ignore sample blanks)'),
                 ('subtractsamplefromsample', 'Subtracting Average SAMPLE Blanks from SAMPLES (ignore standard blanks)'),
                 ('subtractstandardfromall', 'Subtracting Average STANDARD Blanks from the STANDARDS and SAMPLES'),
                 ('subtractsamplefromall', 'Subtracting Average SAMPLE Blanks from the STANDARDS and SAMPLES'),
                 ('ignore', 'Ignoring the Blanks')), initial='subtracteachfromeach'
    )

    form_min_standard = forms.DecimalField(
        required=False,

    )
    form_min_standard.widget.attrs.update({'class': 'form-control'})

    form_max_standard = forms.DecimalField(
        required=False,

    )
    form_max_standard.widget.attrs.update({'class': 'form-control'})

    form_logistic4_A = forms.DecimalField(
        required=False,

    )
    form_logistic4_A.widget.attrs.update({'class': 'form-control'})

    form_logistic4_D = forms.DecimalField(
        required=False,
    )
    form_logistic4_D.widget.attrs.update({'class': 'form-control'})

    form_data_processing_multiplier = forms.DecimalField(
        required=False,
        initial=1,
    )
    form_data_processing_multiplier.widget.attrs.update({'class': 'form-control'})

    # works but only one line
    # form_data_processing_multiplier_string = forms.CharField(
    #     required=False,
    #     initial="",
    # )
    # works but only one line
    # form_data_processing_multiplier_string = forms.CharField()
    # form_data_processing_multiplier_string.widget.attrs.update({'required': False, 'initial': ""})

    # HANDY - how to make an extra field a widget so can manipulate it eg readonly
    # form_data_processing_multiplier_string = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 3, 'readonly': 'readonly', 'required': False})
    # )
    #
    # form_data_processing_multiplier_string_short = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 1, 'readonly': 'readonly'}))
    # form_data_processing_multiplier_value_short = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 1, 'readonly': 'readonly'}))
    #
    # form_data_processing_multiplier_string1 = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 2, 'readonly': 'readonly'}))
    # form_data_processing_multiplier_string2 = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 2, 'readonly': 'readonly'}))
    # form_data_processing_multiplier_string3 = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 2, 'readonly': 'readonly'}))
    # form_data_processing_multiplier_string4 = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 2, 'readonly': 'readonly'}))
    # form_data_processing_multiplier_string5 = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 2, 'readonly': 'readonly'}))
    # form_data_processing_multiplier_string6 = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 2, 'readonly': 'readonly'}))
    # form_data_processing_multiplier_string7 = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 2, 'readonly': 'readonly'}))
    # form_data_processing_multiplier_string8 = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 2, 'readonly': 'readonly'}))
    # form_data_processing_multiplier_string9 = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 2, 'readonly': 'readonly'}))

    form_data_parsable_message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'readonly': 'readonly', 'required': False})
    )

    form_calibration_curve_method_used = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'required': False, 'initial': '-'})
    )

    # form_calibration_equation = forms.CharField(
    #     widget=forms.TextInput(attrs={'readonly': 'readonly', 'required': False, 'initial': '-'})
    # )
    # form_calibration_rsquared = forms.CharField(
    #     widget=forms.TextInput(attrs={'readonly': 'readonly','initial': '-'})
    # )

    radio_replicate_handling_average_or_not = forms.ChoiceField(
        # widget=forms.RadioSelect(attrs={'id': 'value'}),
        widget=forms.RadioSelect,
        choices=[
            ('average', 'Show Averages the Replicate Samples'),
            ('each', 'Show Each Sample')])
            # ('average', 'Send the Average of the Replicates to the Study Summary'),
            # ('each', 'Send Each Replicates Value to the Study Summary')])
    radio_standard_option_use_or_not = forms.ChoiceField(
        required=False,
        widget=forms.RadioSelect,
        choices=[('no_calibration', 'No Calibration'), ('pick_block', 'Pick a Block of Data with Standards')])

    # going to need to pass some calibration parameters
    # think the max I will need is 5 for 5 parameter logistic
    # going to need to keep track of order
    # form_calibration_parameter_1_string = forms.CharField(
    #     widget=forms.TextInput(attrs={'readonly': 'readonly','initial': '-'})
    # )
    # form_calibration_parameter_2_string = forms.CharField(
    #     widget=forms.TextInput(attrs={'readonly': 'readonly', 'initial': '-'})
    # )
    # form_calibration_parameter_3_string = forms.CharField(
    #     widget=forms.TextInput(attrs={'readonly': 'readonly', 'initial': '-'})
    # )
    # form_calibration_parameter_4_string = forms.CharField(
    #     widget=forms.TextInput(attrs={'readonly': 'readonly', 'initial': '-'})
    # )
    # form_calibration_parameter_5_string = forms.CharField(
    #     widget=forms.TextInput(attrs={'readonly': 'readonly','initial': '-'})
    # )
    # form_calibration_parameter_1_value = forms.CharField(
    #     widget=forms.TextInput(attrs={'readonly': 'readonly','initial': '-'})
    # )
    # form_calibration_parameter_2_value = forms.CharField(
    #     widget=forms.TextInput(attrs={'readonly': 'readonly','initial': '-'})
    # )
    # form_calibration_parameter_3_value = forms.CharField(
    #     widget=forms.TextInput(attrs={'readonly': 'readonly','initial': '-'})
    # )
    # form_calibration_parameter_4_value = forms.CharField(
    #     widget=forms.TextInput(attrs={'readonly': 'readonly','initial': '-'})
    # )
    # form_calibration_parameter_5_value = forms.CharField(
    #     widget=forms.TextInput(attrs={'readonly': 'readonly','initial': '-'})
    # )
    form_calibration_standard_fitted_min_for_e = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly','initial': '-'})
    )
    form_calibration_standard_fitted_max_for_e = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly','initial': '-'})
    )
    form_calibration_sample_blank_average = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly','initial': '-'})
    )
    form_calibration_standard_standard0_average = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly','initial': '-'})
    )
    form_calibration_method = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'initial': '-'})
    )
    form_calibration_target = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'initial': '-'})
    )
    form_calibration_unit = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'initial': '-'})
    )
    form_number_standards_this_plate = forms.IntegerField(
        required=False,
        initial=1,
    )
    form_make_mifc_on_submit = forms.BooleanField(required=False)

    # Let them name the maps the same if they really want to. Does not really matter to me
    # def clean(self):
    #     # HANDY FORCE UNIQUE - this will return back to the form instead of showing the user an error
    #     cleaned_data = super(AssayPlateReaderMapForm, self).clean()
    #
    #     if AssayPlateReaderMap.objects.filter(
    #             study_id=self.instance.study.id,
    #             name=self.cleaned_data.get('name', '')
    #     ).exclude(pk=self.instance.pk).count():
    #         raise forms.ValidationError({'name': ['Plate Map name must be unique within study. This plate map is now corrupted. Go back to the Plate Map List and click to Add Plate Map and start again.']})
    #
    #     return cleaned_data

    def clean(self):
        # First thing in clean
        # Call super for data
        data = super(AssayPlateReaderMapForm, self).clean()
        # After initial stuff done
        self.process_file(save=False, calledme='clean')
        return data

    def save(self, commit=True):
                # First thing in save
        # Make sure to pass commit to the super call (don't want accidental saves)
        map = super(AssayPlateReaderMapForm, self).save(commit=commit)

        # Only save the file if commit is true
        if commit:
            self.process_file(save=True, calledme="save")
        return map

    def process_file(self, save=False, calledme="c"):
        #### START When saving AssayPlateReaderMapUpdate after a calibration
        # if user checked the box to send to study summary, make that happen

        data = self.cleaned_data
        # study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

        if data.get('form_make_mifc_on_submit'):
            # search term MIFC - if MIFC changes, this will need changed
            # make a list of column headers for the mifc file
            # could use COLUMN_HEADERS, but need to append one (What?! If you need to append a value, then use the existing variable and then append! Please adhere to DRY principles!)
            # column_table_headers_average = [
            #     'Chip ID',
            #     'Cross Reference',
            #     'Assay Plate ID',
            #     'Assay Well ID',
            #     'Day',

            #     'Hour',
            #     'Minute',
            #     'Target/Analyte',
            #     'Subtarget',
            #     'Method/Kit',

            #     'Sample Location',
            #     'Value',
            #     'Value Unit',
            #     'Replicate',
            #     'Caution Flag',

            #     'Exclude',
            #     'Notes',
            #     'Processing Details',
            # ]

            column_table_headers_average = list(COLUMN_HEADERS)
            column_table_headers_average.append('Processing Details')

            # Ought to be revised
            # search term MIFC - if MIFC changes, this will need changed
            # Make a dictionary of headers in utils and header needed in the mifc file
            utils_key_column_header = {
                'matrix_item_name': 'Chip ID or Well ID',
                'cross_reference': 'Cross Reference',
                'plate_name': 'Assay Plate ID',
                'well_name': 'Assay Well ID',
                'day': 'Day',
                'hour': 'Hour',
                'minute': 'Minute',
                'target': 'Target/Analyte',
                'subtarget': 'Subtarget',
                'method': 'Method/Kit',
                'location_name': 'Sample Location',
                'processed_value': 'Value',
                'unit': 'Value Unit',
                'replicate': 'Replicate',
                'caution_flag': 'Caution Flag',
                'exclude': 'Exclude',
                'notes': 'Notes',
                'sendmessage': 'Processing Details'
            }

            # print(".unit ",data.get('standard_unit').unit)
            # print(".id ", data.get('standard_unit').id)
            # .unit
            # µg / mL
            # .id
            # 6
            # print(".unit ",data.get('standard_unit').unit)
            # print(".id ", data.get('standard_unit').id)

            if data.get('form_block_standard_borrow_pk_single_for_storage') == None:
                borrowed_block_pk = -1
            else:
                borrowed_block_pk = data.get('form_block_standard_borrow_pk_single_for_storage')

            if data.get('form_block_standard_borrow_pk_platemap_single_for_storage') == None:
                borrowed_platemap_pk = -1
            else:
                borrowed_platemap_pk = data.get(
                    'form_block_standard_borrow_pk_platemap_single_for_storage')

            use_curve_long = data.get('form_calibration_curve_method_used')
            use_curve = find_a_key_by_value_in_dictionary(CALIBRATION_CURVE_MASTER_DICT, use_curve_long)
            if use_curve == 'select_one':
                use_curve = 'no_calibration'

            if len(use_curve.strip()) == 0:
                err_msg = "The calibration method " + use_curve_long + " was not found in the cross reference. This is a very bad error. It must be fixed"
                # print(err_msg)
                raise forms.ValidationError(err_msg)

            # form.instance.study
            # make a dictionary to send to the utils.py when call the function
            set_dict = {
                'called_from': 'form_save',
                'study': self.instance.study.id,
                'pk_platemap': self.instance.id,
                'pk_data_block': data.get('form_block_file_data_block_selected_pk_for_storage'),
                'plate_name': data.get('name'),
                'form_calibration_curve': use_curve,
                'multiplier': data.get('form_data_processing_multiplier'),
                'unit': data.get('form_calibration_unit'),
                'standard_unit': data.get('standard_unit').unit,
                'form_min_standard': data.get('form_calibration_standard_fitted_min_for_e'),
                'form_max_standard': data.get('form_calibration_standard_fitted_max_for_e'),
                'form_logistic4_A': data.get('form_logistic4_A'),
                'form_logistic4_D': data.get('form_logistic4_D'),
                'form_blank_handling': data.get('se_form_blank_handling'),
                'radio_standard_option_use_or_not': data.get('radio_standard_option_use_or_not'),
                'radio_replicate_handling_average_or_not_0': data.get(
                    'radio_replicate_handling_average_or_not'),
                'borrowed_block_pk': borrowed_block_pk,
                'borrowed_platemap_pk': borrowed_platemap_pk,
                'count_standards_current_plate': data.get('form_number_standards_this_plate'),
                'target': data.get('form_calibration_target'),
                'method': data.get('form_calibration_method'),
                'time_unit': data.get('time_unit'),
                'volume_unit': data.get('volume_unit'),
                'user_notes': data.get('form_hold_the_notes_string'),
                'user_omits': data.get('form_hold_the_omits_string'),
                'plate_size': data.get('device'),
            }

            # this function is in utils.py that returns data
            data_mover = plate_reader_data_file_process_data(set_dict)
            # what comes back is a dictionary of
            list_of_dicts = data_mover[9]
            list_of_lists_mifc_headers_row_0 = [None] * (len(list_of_dicts) + 1)
            list_of_lists_mifc_headers_row_0[0] = column_table_headers_average
            i = 1
            # print(" ")
            for each_dict_in_list in list_of_dicts:
                list_each_row = []
                for this_mifc_header in column_table_headers_average:
                    # print("this_mifc_header ", this_mifc_header)
                    # find the key in the dictionary that we need
                    utils_dict_header = find_a_key_by_value_in_dictionary(utils_key_column_header,
                                                                          this_mifc_header)
                    # print("utils_dict_header ", utils_dict_header)
                    # print("this_mifc_header ", this_mifc_header)
                    # get the value that is associated with this header in the dict
                    this_value = each_dict_in_list.get(utils_dict_header)
                    # print("this_value ", this_value)
                    # add the value to the list for this dict in the list of dicts
                    list_each_row.append(this_value)
                # when down with the dictionary, add the completely list for this row to the list of lists
                # print("list_each_row ", list_each_row)
                list_of_lists_mifc_headers_row_0[i] = list_each_row
                i = i + 1

            # First make a csv from the list_of_lists (using list_of_lists_mifc_headers_row_0)

            # or self.objects.study
            my_study = self.instance.study
            # my_user = self.request.user
            my_user = self.user
            my_platemap = self.instance
            my_data_block_pk = data.get('form_block_file_data_block_selected_pk_for_storage')

            platenamestring1 = str(my_platemap)
            metadatastring1 = str(data.get('form_hold_the_data_block_metadata_string'))

            # Specify the file for use with the file uploader class
            # some of these caused errors in the file name so remove them
            # Luke and Quinn voted for all the symbols out instead of a few

            platenamestring = re.sub('[^a-zA-Z0-9_]', '', platenamestring1)
            metadatastring = re.sub('[^a-zA-Z0-9_]', '', metadatastring1)

            name_the_file = 'PLATE-{}-{}--METADATA-{}-{}'.format(
                                my_platemap.id, platenamestring,
                                my_data_block_pk, metadatastring
                            )

            bulk_location = upload_file_location(
                my_study,
                name_the_file
            )

            # Make sure study has directories
            if not os.path.exists(MEDIA_ROOT + '/data_points/{}'.format(my_study.id)):
                os.makedirs(MEDIA_ROOT + '/data_points/{}'.format(my_study.id))

            # Need to import from models
            # Avoid magic string, use media location
            file_location = MEDIA_ROOT.replace('mps/../', '', 1) + '/' + bulk_location + '.csv'

            # Should make a csv writer to avoid repetition
            file_to_write = open(file_location, 'w')
            csv_writer = csv.writer(file_to_write, dialect=csv.excel)

            # Add the UTF-8 BOM
            list_of_lists_mifc_headers_row_0[0][0] = '\ufeff' + list_of_lists_mifc_headers_row_0[0][0]

            # Write the lines here here uncomment this
            for one_line_of_data in list_of_lists_mifc_headers_row_0:
                csv_writer.writerow(one_line_of_data)

            file_to_write.close()
            new_mifc_file = open(file_location, 'rb')

            file_processor = AssayFileProcessor(new_mifc_file,
                                                my_study,
                                                my_user, save=save,
                                                full_path='/media/' + bulk_location + '.csv')

            # Process the file
            file_processor.process_file()
        #### END When saving AssayPlateReaderMapUpdate after a calibration


# What is this? Can't you just write the dictionary in the other direction?
# this finds the key for the value provided as thisHeader
def find_a_key_by_value_in_dictionary(this_dict, this_header):
    """This is a function to find a key by value."""
    my_key = ''
    for key, value in this_dict.items():
        if value == this_header:
            my_key = key
            break
    return my_key

# There should be a complete set of items for each saved plate map (one for each well in the selected plate)
class AssayPlateReaderMapItemForm(forms.ModelForm):
    """Form for Assay Plate Reader Map Item"""

    class Meta(object):
        model = AssayPlateReaderMapItem
        # exclude = tracking + ('study',)
        fields = [
            # 'id', do not need
            'matrix_item',
            'location',
            'name',
            # 'row_index',
            # 'column_index',
            'plate_index',
            'standard_value',
            'dilution_factor',
            'collection_volume',
            'collection_time',
            'default_time',
            'well_use',
        ]

    # keep here for reference of what not to do if want form to be selectized
    # def __init__(self, *args, **kwargs):
    #     super(AssayPlateReaderMapItemForm, self).__init__(*args, **kwargs)
    #     self.fields['name'].widget.attrs.update({'class': ' no-selectize'})

    # # 20200428 for user entered information
    # # 20200609 these are adding too much overhead, and did not use in data process, so remove these
    # form_user_entered_notes = forms.CharField(
    #     initial='-',
    #     required=False,
    #     widget=forms.Textarea(attrs={'cols': 10, 'rows': 1}),
    # )
    # form_user_entered_omit_from_average = forms.BooleanField(required=False, )

###########
# 20200522 getting rid of the value form all together since not allowing editing after values attached to plate map.
# GET RID OF THIS
# # Item VALUES are sets that correspond to items. Each set should have a match to a well in the plate map.
# # If not file/blocks attached to plate map, will have one set of values (with one value for each item)
# # If one file/block attached to plate map, will have two sets of values (one for the file, one null file) etc.
# class AssayPlateReaderMapItemValueForm(forms.ModelForm):
#     """Form for Assay Plate Reader Map Item Value"""
#
#     # 20200113 - changing so this formset is only called when adding and when update or view when no data are yet attached
#
#     class Meta(object):
#         model = AssayPlateReaderMapItemValue
#         # it is worth noting that there is a nuance to excluding or setting fields
#         # exclude = tracking + ('study', )
#         fields = [
#             # 'id', do not need
#             # 'assayplatereadermapdatafile', do not need
#             # 'assayplatereadermapitem', do not need
#             # next item - can remove later - do not need since, if there are matches, this formset will not be called
#             # but check rest is working first since will also affect formset (the custom_fields)
#             # 'assayplatereadermapdatafileblock',
#             'plate_index',
#             'raw_value',
#             'time',
#             'well_use',
#         ]
###########


# Formset for items
# IMPORTANT - custom_fields remove the select options for all the formsets - saves ALOT of page load time is long lists
class AssayPlateReaderMapItemFormSet(BaseInlineFormSetForcedUniqueness):
    custom_fields = (
        'matrix_item',
        'location',
    )

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study', None)
        self.user = kwargs.pop('user', None)
        super(AssayPlateReaderMapItemFormSet, self).__init__(*args, **kwargs)

        if not self.study:
            self.study = self.instance.study

        # use the filter to get matrix items in this study ONLY - makes the dic much smaller
        # HANDY - this speed up the custom_fields
        filters = {'matrix_item': {'study_id': self.study.id}}
        self.dic = get_dic_for_custom_choice_field(self, filters=filters)
        for form in self.forms:
            for field in self.custom_fields:
                form.fields[field] = DicModelChoiceField(field, self.model, self.dic)

            if self.study:
                form.instance.study = self.study
            if form.instance.pk:
                form.instance.modified_by = self.user
            else:
                form.instance.created_by = self.user

###########
# 20200522 getting rid of the value form all together since not allowing editing after values attached to plate map.
# # GET RID OF THIS
# # Formset for item values
# class AssayPlateReaderMapItemValueFormSet(BaseInlineFormSetForcedUniqueness):
#     # changed way this worked on 20200114 and do not need this field any more
#     # custom_fields = (
#     #     'assayplatereadermapdatafileblock',
#     # )
#
#     def __init__(self, *args, **kwargs):
#         self.study = kwargs.pop('study', None)
#         self.user = kwargs.pop('user', None)
#         super(AssayPlateReaderMapItemValueFormSet, self).__init__(*args, **kwargs)
#
#         if not self.study:
#             self.study = self.instance.study
#
#         # changed way this worked on 20200114 and do not need this field any more - skip making the dic...
#         # # use the filter to get matrix items in this study ONLY - makes the dic much smaller
#         # # this speed up the custom_fields
#         # filters = {'assayplatereadermapdatafileblock': {'study_id': self.study.id}}
#         # self.dic = get_dic_for_custom_choice_field(self, filters=filters)
#         # # print(self.dic)
#         #
#         for form in self.forms:
#             # for field in self.custom_fields:
#             #     form.fields[field] = DicModelChoiceField(field, self.model, self.dic)
#
#             if self.study:
#                 form.instance.study = self.study
#             if form.instance.pk:
#                 form.instance.modified_by = self.user
#             else:
#                 form.instance.created_by = self.user
#
#         # HANDY had this up before the self.forms loop, but needed to move it down to work
#         # HANDY to know how to print a queryset to the console
#         # self.queryset = self.queryset.order_by('assayplatereadermapdatafile', 'assayplatereadermapdatafileblock', 'plate_index')
#         # https://stackoverflow.com/questions/13387446/changing-the-display-order-of-forms-in-a-formset
#         # print(self.queryset)
#         self.queryset = self.queryset.order_by('assayplatereadermapdatafileblock', 'plate_index')
#         # print(self.queryset)
###########


# Formset factory for item and value
# https://stackoverflow.com/questions/29881734/creating-django-form-from-more-than-two-models
AssayPlateReaderMapItemFormSetFactory = inlineformset_factory(
    AssayPlateReaderMap,
    AssayPlateReaderMapItem,
    formset=AssayPlateReaderMapItemFormSet,
    form=AssayPlateReaderMapItemForm,
    extra=1,
    exclude=tracking + ('study',),
)

###########
# 20200522 getting rid of the value form all together since not allowing editing after values attached to plate map.
# # GET RID OF THIS
# AssayPlateReaderMapItemValueFormSetFactory = inlineformset_factory(
#     AssayPlateReaderMap,
#     AssayPlateReaderMapItemValue,
#     formset=AssayPlateReaderMapItemValueFormSet,
#     form=AssayPlateReaderMapItemValueForm,
#     extra=1,
#     exclude=tracking + ('study',),
# )
##########


# end plate reader map page
#####


#####
# Start plate reader file page

# Add a plate reader file to the study (just add the file and check the file extension, no data processing)
class AssayPlateReaderMapDataFileAddForm(BootstrapForm):
    """Form for Plate Reader Data File Upload"""

    class Meta(object):
        model = AssayPlateReaderMapDataFile
        fields = ('plate_reader_file', )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.study = kwargs.pop('study', None)
        super(AssayPlateReaderMapDataFileAddForm, self).__init__(*args, **kwargs)

        # need or blank study_assay in the update page (add page worked okay)
        if not self.study and self.instance.study:
            self.study = self.instance.study
        if self.study:
            self.instance.study = self.study

    # check the file extension of the loaded file to make sure the user is not adding spreadsheet files
    # https://medium.com/@literallywords/server-side-file-extension-validation-in-django-2-1-b8c8bc3245a0
    def clean_plate_reader_file(self):
        data = self.cleaned_data['plate_reader_file']
        # Run file extension check
        file_extension = os.path.splitext(data.name)[1]
        if file_extension not in ['.csv', '.tsv', '.txt']:
            if '.xl' in file_extension or '.wk' in file_extension or '.12' in file_extension:
                raise ValidationError(
                     'This appears to be an spreadsheet file. To upload, export to a tab delimited file and try again.',
                     code='invalid'
                )
            else:
                raise ValidationError(
                     'Invalid file extension - must be in [.csv, .tsv, .txt]',
                     code='invalid'
                )
        return data

# UPDATE and VIEW (ADD is separate - above) - user routed here after adding a file to complete other needed info
class AssayPlateReaderMapDataFileForm(BootstrapForm):
    """Form for Assay Plate Reader Map Data File"""

    class Meta(object):
        model = AssayPlateReaderMapDataFile
        fields = ['id', 'description', 'file_delimiter', 'upload_plate_size', 'plate_reader_file', ]
        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
            'upload_plate_size': forms.TextInput(attrs={'readonly': 'readonly',
                                                 'style': 'border-style: none;',
                                                 'style': 'background-color: transparent;'
                                                        }),
        }

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study', None)
        # self.user = kwargs.pop('user', None)
        # # ??
        # filename_only = kwargs.pop('extra', 0)
        super(AssayPlateReaderMapDataFileForm, self).__init__(*args, **kwargs)

        # need this because, remember, the plate map doesn't come WITH a study, must tell it which
        if not self.study and self.instance.study:
            self.study = self.instance.study
        if self.study:
            self.instance.study = self.study

        my_instance = self.instance

        # to display the file name without the whole path
        form_filename_only = os.path.basename(str(my_instance.plate_reader_file))
        self.fields['form_filename_only'].initial = form_filename_only

    se_form_plate_size = forms.ChoiceField(
        required=False,
        choices=assay_plate_reader_map_info_plate_size_choices
    )
    form_number_blocks = forms.IntegerField(
        required=False,
        initial=1,
    )
    form_number_blank_columns = forms.IntegerField(
        required=False,
        initial=0,
    )
    form_number_blank_rows = forms.IntegerField(
        required=False,
        initial=0,
    )
    form_filename_only = forms.CharField(
        required=False,
    )
    # PI wants to select options for file processing
    # Currently, the choices for file formats are HARDCODED here
    # if we actually iron out the 'sanctioned' file formats, these could go into a table and be available in the admin
    # BUT, reading/processing of the format would still need to be build, so maybe better NOT to put in admin....

    se_file_format_select = forms.ChoiceField(
        required=False,
        initial=0,
        choices=(
            (0, 'COMPUTERS BEST GUESS'),
            (1, 'Softmax Pro 5.3 Molecular Devices M5 (UPDDI DoO)'),
            (10, 'Single data block with 1 column of row labels and 1 row of column headers'),

            # (96, 'One 96 plate (8 lines by 12 columns) starting at line 1 column 1 (CSV) - requested by Larry V.'),
            # (384, 'One 384 plate (16 lines by 24 columns) starting at line 1 column 1 (CSV) - requested by Larry V.'),
            # (2, 'Wallac EnVision Manager Version 1.12 (EnVision)'),
            (9999, 'USER CUSTOMIZES by Setting Format Information'),
        )
    )


class AssayPlateReaderMapDataFileBlockForm(forms.ModelForm):
    """Form for Assay Plate Reader Data File Block """

    class Meta(object):
        model = AssayPlateReaderMapDataFileBlock
        # fields = ('id', 'data_block', 'data_block_metadata', 'line_start', 'line_end', 'delimited_start', 'delimited_end', 'over_write_sample_time', 'assayplatereadermap'])
        exclude = tracking + ('study',)

        # this could go in AssayPlateReaderMapDataFileBlockForm or AssayPlateReaderMapFileBlockFormSet
        # but if do in formset, the widgets down get the form control!
        # fields = ('id', 'data_block', 'data_block_metadata', 'line_start', 'line_end', 'delimited_start', 'delimited_end', 'over_write_sample_time', 'assayplatereadermap')
        widgets = {
            # 'form_selected_plate_map_time_unit': forms.TextInput(attrs={'readonly': 'readonly',
            #                                                             'style': 'background-color: transparent;',
            #                                                             }),
            'data_block': forms.NumberInput(attrs={'readonly': 'readonly',
                                                   # 'style': 'box-shadow:inset 0px, 0px 0px ;',
                                                   # 'style': 'border-style: none;',
                                                   # 'style': 'border-width: 0;',
                                                   # 'style': 'border-color: transparent;',
                                                   'style': 'background-color: transparent;',
                                                   }),
            'line_start': forms.NumberInput(attrs={'class': 'form-control '}),
            'line_end': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'line_end': forms.NumberInput(attrs={'class': 'form-control required'}),
            # 'line_end': forms.NumberInput(attrs={'readonly': 'readonly',
            #                                      'style': 'background-color: transparent;',}),
            'delimited_start': forms.NumberInput(attrs={'class': 'form-control '}),
            'delimited_end': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'delimited_end': forms.NumberInput(attrs={'readonly': 'readonly',
            #                                           'style': 'background-color: transparent;',}),
            'over_write_sample_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'form_selected_plate_map_time_unit': forms.NumberInput(attrs={'readonly': 'readonly',
                                                                          'style': 'background-color: transparent;',}),
            'data_block_metadata': forms.Textarea(attrs={'cols': 80, 'rows': 1, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # Get the study
        self.study = kwargs.pop('study', None)
        self.user = kwargs.pop('user', None)
        super(AssayPlateReaderMapDataFileBlockForm, self).__init__(*args, **kwargs)

        # this made the dropdown behave when copied with the formset!
        # SUPER IMPORTANT and HANDY when need to copy formsets with dropdowns - if have selectized, it is a big mess
        self.fields['assayplatereadermap'].widget.attrs.update({'class': ' no-selectize required'})

    # not currently using to limit what is removed from the map item table - consider added this feature later
    form_changed_something_in_block = forms.IntegerField(
        initial=0,
        required=False,
    )
    form_selected_plate_map_time_unit = forms.CharField(
        required=False,
    )

# formsets
class AssayPlateReaderMapFileBlockFormSet(BaseInlineFormSetForcedUniqueness):
    custom_fields_for_limiting_list = (
        'assayplatereadermap',
    )

    # tried putting this in the Form, but had some issues
    # print(self.fields['assayplatereadermap'].queryset)
    # #
    # # next line makes it work
    # self.study = 293
    # print(self.study)
    # self.fields['assayplatereadermap'].queryset = AssayPlateReaderMap.objects.filter(
    #     study_id=self.study
    # )
    #
    # # print(self.fields['assayplatereadermap'].queryset)

    def __init__(self, *args, **kwargs):
        # Get the study
        self.study = kwargs.pop('study', None)
        self.user = kwargs.pop('user', None)
        super(AssayPlateReaderMapFileBlockFormSet, self).__init__(*args, **kwargs)

        if not self.study:
            self.study = self.instance.study

        idx = 0
        for formset in self.forms:
            for field in self.custom_fields_for_limiting_list:
                formset.fields[field].queryset = AssayPlateReaderMap.objects.filter(
                    study_id=self.study
                    # study_id=293
                )
            if self.study:
                formset.instance.study = self.study
            if formset.instance.pk:
                formset.instance.modified_by = self.user
            else:
                formset.instance.created_by = self.user
            idx = idx + 1


AssayPlateReaderMapDataFileBlockFormSetFactory = inlineformset_factory(
    AssayPlateReaderMapDataFile,
    AssayPlateReaderMapDataFileBlock,
    formset=AssayPlateReaderMapFileBlockFormSet,
    form=AssayPlateReaderMapDataFileBlockForm,
    extra=1,
    exclude=tracking + ('study',),
)


# ASSAY PLATE MAP END
#####

#####
# Start omics section

# use this to get the key from the value
# returned_key = find_a_key_by_value_in_dictionary(OMIC_COLUMN_HEADER_TO_TARGET_DICT, 'blah-baseMean')

class AssayOmicDataFileUploadForm(BootstrapForm):
    """Form Upload an AssayOmicDataFileUpload file and associated metadata """

    class Meta(object):
        model = AssayOmicDataFileUpload
        exclude = tracking + ('study',)

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study', None)
        super(AssayOmicDataFileUploadForm, self).__init__(*args, **kwargs)

        # # http://www.chidgilovitz.com/displaying-django-form-field-help-text-in-a-bootstrap-3-popover/
        # for field in self.fields:
        #     help_text = self.fields[field].help_text
        #     self.fields[field].help_text = None
        #     if help_text != '':
        #         self.fields[field].widget.attrs.update(
        #             {'class': 'has-popover',
        #              'data-content': help_text,
        #              'data-placement': 'right',
        #              # 'data-container': 'body'
        #              }
        #         )

        if not self.study and self.instance.study:
            self.study = self.instance.study
        if self.study:
            self.instance.study = self.study

        # for now, limit to the same study - we will need to revisit this when we think about
        # inter study and transitioning to treatment groups
        # data_groups_filtered = AssayOmicDataGroup.objects.filter(
        #     study_id=self.instance.study.id
        # )
        data_groups_filtered = AssayGroup.objects.filter(
            study_id=self.instance.study.id
        )
        # find the pk for the method tempo-seq
        obj = AssayMethod.objects.filter(name='TempO-Seq').first()
        if obj is not None:
            method_pk = obj.id
            self.fields['method'].initial = method_pk

        # HANDY to limit options in a dropdown on a model field in a form
        self.fields['group_1'].queryset = data_groups_filtered
        self.fields['group_2'].queryset = data_groups_filtered

        self.fields['group_2'].widget.attrs['class'] += ' required'

        if self.instance.time_1:
            time_1_instance = self.instance.time_1
            times_1 = get_split_times(time_1_instance)
            self.fields['time_1_day'].initial = times_1.get('day')
            self.fields['time_1_hour'].initial = times_1.get('hour')
            self.fields['time_1_minute'].initial = times_1.get('minute')

        if self.instance.time_2:
            time_2_instance = self.instance.time_2
            times_2 = get_split_times(time_2_instance)
            self.fields['time_2_day'].initial = times_2.get('day')
            self.fields['time_2_hour'].initial = times_2.get('hour')
            self.fields['time_2_minute'].initial = times_2.get('minute')

    time_1_day = forms.DecimalField(
        required=False,
        label='Day'
    )
    time_1_hour = forms.DecimalField(
        required=False,
        label='Hour'
    )
    time_1_minute = forms.DecimalField(
        required=False,
        label='Minute'
    )

    time_2_day = forms.DecimalField(
        required=False,
        label='Day'
    )
    time_2_hour = forms.DecimalField(
        required=False,
        label='Hour'
    )
    time_2_minute = forms.DecimalField(
        required=False,
        label='Minute'
    )
    filename_only = forms.CharField(
        required=False,
    )

    def clean(self):
        data = super(AssayOmicDataFileUploadForm, self).clean()
        self.process_file(save=False, calledme='clean')
        return data

    def save(self, commit=True):
        new_file = super(AssayOmicDataFileUploadForm, self).save(commit=commit)
        if commit:
            self.process_file(save=True, calledme='save')
        return new_file

    def process_file(self, save=False, calledme='c'):
        true_to_continue = True
        data = self.cleaned_data
        data['time_1'] = 0
        for time_unit, conversion in list(TIME_CONVERSIONS.items()):
            if data.get('time_1_' + time_unit) is not None:
                inttime = (data.get('time_1_' + time_unit))
                data.update({'time_1': data.get('time_1') + inttime * conversion,})

        data['time_2'] = 0
        for time_unit, conversion in list(TIME_CONVERSIONS.items()):
            if data.get('time_2_' + time_unit) is not None:
                inttime = data.get('time_2_' + time_unit)
                data.update({'time_2': data.get('time_2') + inttime * conversion,})

        file_extension = os.path.splitext(data.get('omic_data_file').name)[1]

        if 'omic_data_file' in self.changed_data or self.instance.id is None:
            # Run file extension check
            if file_extension in ['.csv', '.tsv', '.txt', '.xls', '.xlsx']:
                true_to_continue = True
            else:
                true_to_continue = False
                raise ValidationError(
                     'Invalid file extension - must be in csv, tsv, txt, xls, or xlsx',
                     code='invalid'
                )

        if true_to_continue:
            data_file_pk = self.instance.id
            data_type = data['data_type']
            pipeline = data['pipeline']

            # here here when decide on other data types
            if data_type == 'log2fc':
                # if 5==5:
                if calledme == 'clean':
                    # this function is in utils.py
                    # print('form clean')
                    data_file = data.get('omic_data_file')
                    amessage = omic_data_file_process_data(save, self.study.id, data_file_pk, data_file, file_extension, calledme, data_type, pipeline)
                    # print(amessage)
                else:
                    # print('form save')
                    queryset = AssayOmicDataFileUpload.objects.get(id=data_file_pk)
                    data_file = queryset.omic_data_file.open()
                    amessage = omic_data_file_process_data(save, self.study.id, data_file_pk, data_file, file_extension, calledme, data_type, pipeline)
                    # print(amessage)

        return data

#     End Omic Data File Upload Section
