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
    AssayPlateReaderMap,
    AssayPlateReaderMapItem,
    AssayPlateReaderMapItemValue,
    AssayPlateReaderMapDataFile,
    AssayPlateReaderMapDataFileBlock,
    #AssayPlateReaderMapDataFileLine,
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
    PlateReaderMapDataFileAdd,
    get_user_accessible_studies,
)
from django.utils import timezone

from mps.templatetags.custom_filters import is_group_admin, filter_groups, ADMIN_SUFFIX

from django.core.exceptions import NON_FIELD_ERRORS

import ujson as json

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
            if self.fields.get('duration', None):
                self.fields['duration_' + time_unit] = forms.FloatField(
                    initial=0,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'style': 'width:75px;'
                    })
                )

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
        "Check to see if the provided value is a valid choice"
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

        unit_queryset = PhysicalUnits.objects.filter(
            availability__icontains='readout'
        ).order_by('unit_type__unit_type', 'base_unit__unit', 'scale_factor')

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

    class Meta(object):
        model = AssayStudy
        widgets = {
            'assay_run_id': forms.Textarea(attrs={'rows': 1}),
            'name': forms.Textarea(attrs={'rows': 1}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 100}),
        }
        exclude = tracking + restricted + ('access_groups', 'signed_off_notes', 'bulk_file', 'collaborator_groups', 'archived')

    def clean(self):
        """Checks for at least one study type"""
        # clean the form data, before validation
        data = super(AssayStudyForm, self).clean()

        if not any([data['toxicity'], data['efficacy'], data['disease'], data['cell_characterization']]):
            raise forms.ValidationError('Please select at least one study type')


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

    def clean(self):
        # clean the form data, before validation
        data = super(AssayStudyFormAdmin, self).clean()

        if not any([data['toxicity'], data['efficacy'], data['disease'], data['cell_characterization']]):
            raise forms.ValidationError('Please select at least one study type')


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


class SetupFormsMixin(BootstrapForm):
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

    cell_addition_location = forms.ModelChoiceField(queryset=AssaySampleLocation.objects.all().order_by('name'), required=False)

    ### ?ADDING SETUP SETTINGS
    setting_setting = forms.ModelChoiceField(queryset=AssaySetting.objects.all().order_by('name'), required=False)
    setting_unit = forms.ModelChoiceField(queryset=PhysicalUnits.objects.all().order_by('base_unit','scale_factor'), required=False)

    setting_value = forms.CharField(required=False)

    setting_addition_location = forms.ModelChoiceField(
        queryset=AssaySampleLocation.objects.all().order_by('name'),
        required=False
    )

    ### ADDING COMPOUNDS
    compound_compound = forms.ModelChoiceField(queryset=Compound.objects.all().order_by('name'), required=False)
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
        queryset=AssaySampleLocation.objects.all().order_by('name'),
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
        self.user = kwargs.pop('user', None)
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
    compound_concentration_increment_type = forms.ChoiceField(choices=(
        ('/', 'Divide'),
        ('*', 'Multiply'),
        ('+', 'Add'),
        ('-', 'Subtract')
    ), required=False)
    compound_concentration_increment_direction = forms.ChoiceField(choices=(
        ('lrd', 'Left to Right and Down'),
        ('rlu', 'Right to Left and Up')
    ), required=False)

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


class AssayMatrixItemForm(forms.ModelForm):
    class Meta(object):
        model = AssayMatrixItem
        exclude = ('study', 'matrix') + tracking


# TODO NEED TO TEST
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
    form=AssayMatrixItemForm,
    extra=1,
    exclude=('study',) + tracking
)


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

    query_term = forms.CharField(initial='', required=False)

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
def process_error_for_study_new(prefix, row, column, full_error):
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


# Perhaps it would have been more intelligent to leverage the forms in the add
# There would have been different consquences for doing so, but consistency
class AssayStudyFormNew(SetupFormsMixin, SignOffMixin, BootstrapForm):
    setup_data = forms.CharField(required=False)
    processed_setup_data = forms.CharField(required=False)
    number_of_items = forms.CharField(required=False)
    test_type = forms.ChoiceField(
        initial='control',
        choices=TEST_TYPE_CHOICES,
        required=False
    )

    def __init__(self, *args, **kwargs):
        """Init the Study Form

        Kwargs:
        groups -- a queryset of groups (allows us to avoid N+1 problem)
        """
        super(AssayStudyFormNew, self).__init__(*args, **kwargs)
        self.fields['group'].queryset = filter_groups(self.user)

        # Make sure there are only organ models with versions
        # Removed for now
        # self.fields['organ_model'].queryset = OrganModel.objects.filter(
        #     organmodelprotocol__isnull=False
        # ).distinct()

        # SLOPPY
        self.fields['test_type'].widget.attrs['class'] += ' no-selectize test-type required'
        # Bad
        self.fields['test_type'].widget.attrs['style'] = 'width:100px;'
        self.fields['number_of_items'].widget.attrs['class'] = 'form-control number-of-items required'
        # Bad
        # self.fields['number_of_items'].widget.attrs['style'] = 'margin-top:10px;'

    class Meta(object):
        model = AssayStudy
        widgets = {
            'assay_run_id': forms.Textarea(attrs={'rows': 1}),
            'name': forms.Textarea(attrs={'rows': 1}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 100}),
        }
        exclude = tracking + restricted + ('access_groups', 'signed_off_notes', 'bulk_file')

    def clean(self):
        """Checks for at least one study type"""
        # clean the form data, before validation
        data = super(AssayStudyFormNew, self).clean()

        if not any([data['toxicity'], data['efficacy'], data['disease'], data['cell_characterization']]):
            raise forms.ValidationError('Please select at least one study type')

        # SLOPPY NOT DRY
        new_setup_data = {}
        new_matrix = None
        new_items = None
        new_related = None

        errors = {'organ_model': [], 'setup_data': []}
        current_errors = errors.get('setup_data')

        # study = super(AssayStudyFormNew, self).save(commit=False)

        if self.cleaned_data.get('setup_data', None):
            all_setup_data = json.loads(self.cleaned_data.get('setup_data', '[]'))
        else:
            all_setup_data = []

        # Never consider if no model
        if not self.cleaned_data.get('organ_model', None):
            all_setup_data = []

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

            current_item_number = 1

            # CRUDE: JUST MAKE ONE LARGE ROW?
            # number_of_items = 0
            #
            # for setup_group in all_setup_data:
            #     number_of_items += int(setup_group.get('number_of_items', '0'))

            # Find max for number of columns
            number_of_columns = 0
            for setup_group in all_setup_data:
                if int(setup_group.get('number_of_items', '0')) > number_of_columns:
                    number_of_columns = int(setup_group.get('number_of_items', '0'))

            new_matrix = AssayMatrix(
                name=data.get('name', ''),
                # Does not work with plates at the moment
                representation='chips',
                # study=self.instance,
                device=None,
                number_of_rows=len(all_setup_data),
                number_of_columns=number_of_columns,
                # number_of_rows=1,
                # number_of_columns=number_of_items,
                created_by=created_by,
                created_on=created_on,
                modified_by=created_by,
                modified_on=created_on,
            )

            try:
                new_matrix.full_clean(exclude=['study'])
            except forms.ValidationError as e:
                errors.get('organ_model').append(e.values())

            # new_matrix.save()

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

            new_items = []
            new_related = {}

            # NOTE: ROW IS DERIVED FROM THE GROUP IN QUESTION
            # ALL ITEMS IN THE GROUP ARE IN THE COLUMNS OF SAID ROW
            for setup_row, setup_group in enumerate(all_setup_data):
                items_in_group = int(setup_group.pop('number_of_items', '0'))
                test_type = setup_group.get('test_type', '')

                # To break out to prevent repeat errors
                group_has_error = False

                for iteration in range(items_in_group):
                    new_item = AssayMatrixItem(
                        # study=study,
                        # matrix=new_matrix,
                        name=str(current_item_number),
                        # JUST MAKE SETUP DATE THE STUDY DATE FOR NOW
                        setup_date=data.get('start_date', ''),
                        row_index=setup_row,
                        column_index=iteration,
                        # column_index=current_item_number-1,
                        # device=study.organ_model.device,
                        # organ_model=study.organ_model,
                        # organ_model_protocol=study.organ_model_protocol,
                        test_type=test_type,
                        created_by=created_by,
                        created_on=created_on,
                        modified_by=created_by,
                        modified_on=created_on,
                    )

                    try:
                        new_item.full_clean(exclude=[
                            'study',
                            'matrix',
                            'device',
                            'organ_model',
                            'organ_model_protocol',
                        ])
                        new_items.append(new_item)

                    except forms.ValidationError as e:
                        # raise forms.ValidationError(e)
                        errors.get('organ_model').append(e.values())
                        group_has_error = True

                    current_related_list = new_related.setdefault(
                        str(len(new_items)), []
                    )

                    # new_item.save()
                    for prefix, current_objects in setup_group.items():
                        for setup_column, current_object in enumerate(current_objects):
                            if prefix in ['cell', 'compound', 'setting'] and current_object:
                                current_object.update({
                                    'matrix_item': new_item,
                                })
                                if prefix == 'cell':
                                    new_cell = AssaySetupCell(**current_object)

                                    try:
                                        new_cell.full_clean(exclude=['matrix_item'])
                                        current_related_list.append(new_cell)
                                    except forms.ValidationError as e:
                                        # raise forms.ValidationError(e)
                                        current_errors.append(
                                            process_error_for_study_new(
                                                prefix,
                                                setup_row,
                                                setup_column,
                                                e
                                            )
                                        )
                                        group_has_error = True

                                    # new_cell.save()
                                elif prefix == 'setting':
                                    new_setting = AssaySetupSetting(**current_object)
                                    try:
                                        new_setting.full_clean(exclude=['matrix_item'])
                                        current_related_list.append(new_setting)
                                    except forms.ValidationError as e:
                                        # raise forms.ValidationError(e)
                                        current_errors.append(
                                            process_error_for_study_new(
                                                prefix,
                                                setup_row,
                                                setup_column,
                                                e
                                            )
                                        )
                                        group_has_error = True

                                    # new_setting.save()
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
                                    concentration_unit_id = int(current_object.get('concentration_unit_id', '0'))
                                    addition_location_id = int(current_object.get('addition_location_id', '0'))

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
                                            # raise forms.ValidationError(e)
                                            current_errors.append(
                                                process_error_for_study_new(
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
                                            # raise forms.ValidationError(e)
                                            current_errors.append(
                                                process_error_for_study_new(
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
                                            # new_item.id,
                                            current_item_number,
                                            compound_instance.id,
                                            concentration,
                                            concentration_unit_id,
                                            addition_time,
                                            duration,
                                            addition_location_id
                                        ), None
                                    )
                                    if not conflicting_assay_compound_instance:
                                        new_compound = AssaySetupCompound(
                                            # matrix_item_id=new_item.id,
                                            compound_instance_id=compound_instance.id,
                                            concentration=concentration,
                                            concentration_unit_id=concentration_unit_id,
                                            addition_time=addition_time,
                                            duration=duration,
                                            addition_location_id=addition_location_id
                                        )

                                        try:
                                            new_compound.full_clean(exclude=['matrix_item'])
                                            current_related_list.append(new_compound)
                                        except forms.ValidationError as e:
                                            # raise forms.ValidationError(e)
                                            current_errors.append(
                                                process_error_for_study_new(
                                                    prefix,
                                                    setup_row,
                                                    setup_column,
                                                    e
                                                )
                                            )
                                            group_has_error = True

                                        # new_compound.save()

                                    assay_compound_instances.update({
                                        (
                                            # new_item.id,
                                            current_item_number,
                                            compound_instance.id,
                                            concentration,
                                            concentration_unit_id,
                                            addition_time,
                                            duration,
                                            addition_location_id
                                        ): True
                                    })

                    current_item_number += 1

                    # Don't keep iterating through this group if there is a problem
                    if group_has_error:
                        break

        if current_errors:
            errors.get('organ_model').append(['Please review the table below for errors.'])
            raise forms.ValidationError(errors)

        new_setup_data.update({
            'new_matrix': new_matrix,
            'new_items': new_items,
            'new_related': new_related,
        })

        data.update({
            'processed_setup_data': new_setup_data
        })

        return data

    def save(self, commit=True):
        # PLEASE SEE BASE MODELS
        # study = super(AssayStudyFormNew, self).save(commit)
        study = super(AssayStudyFormNew, self).save()

        # VERY SLOPPY
        created_by = self.user
        created_on = timezone.now()

        study.created_by = created_by
        study.created_on = created_on
        study.modified_by = created_by
        study.modified_on = created_on

        study.save()
        # SLOPPY: REVISE

        study_id = study.id

        if study.organ_model_id:
            device_id = study.organ_model.device_id
        else:
            device_id = None

        organ_model_id = study.organ_model_id
        organ_model_protocol_id = study.organ_model_protocol_id

        all_setup_data = self.cleaned_data.get('processed_setup_data', None)

        if all_setup_data:
            new_matrix = all_setup_data.get('new_matrix', None)
            new_items = all_setup_data.get('new_items', None)
            new_related = all_setup_data.get('new_related', None)

            if new_matrix:
                new_matrix.study_id = study_id
                new_matrix.save()
                new_matrix_id = new_matrix.id

                new_item_ids = {}

                for new_item in new_items:
                    # ADD MATRIX and tracking
                    new_item.matrix_id = new_matrix_id
                    new_item.study_id = study_id
                    new_item.device_id = device_id
                    new_item.organ_model_id = organ_model_id
                    new_item.organ_model_protocol_id = organ_model_protocol_id
                    new_item.save()

                    new_item_ids.update({
                        new_item.name: new_item.id
                    })

                for current_item_name, new_related_data_set in new_related.items():
                    new_item_id = new_item_ids.get(current_item_name, None)

                    if new_item_id:
                        for new_related_data in new_related_data_set:
                            # ADD MATRIX ITEM
                            new_related_data.matrix_item_id = new_item_id
                            new_related_data.save()

        return study


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
        self.user = kwargs.pop('user', None)
        super(AssayMatrixFormNew, self).__init__(*args, **kwargs)

        # SLOPPY
        self.fields['test_type'].widget.attrs['class'] += ' no-selectize test-type'
        # Bad
        self.fields['test_type'].widget.attrs['style'] = 'width:100px;'


class AssayTargetForm(BootstrapForm):
    class Meta(object):
        model = AssayTarget
        exclude = tracking

        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }


class AssayMethodForm(BootstrapForm):
    class Meta(object):
        model = AssayMethod
        exclude = tracking

        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }


class PhysicalUnitsForm(BootstrapForm):
    class Meta(object):
        model = PhysicalUnits
        exclude = tracking

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


### ASSAY PLATE MAP START
##### monkey patch to display method target and unit combo as needed in the assay plate map page
class AbstractClassAssayStudyAssay(AssayStudyAssay):
    class Meta:
        proxy = True

    def __str__(self):
        return '{0} by {1} ({2})'.format(self.target, self.method, self.unit)


##### Get info to populate pick lists; no qc needed on this form, just to use on webpage
class AssayPlateReadMapAdditionalInfoForm(forms.Form):
    """Form for Assay Plate Reader Map add extra info for dropdown"""
    #initilize with the study_id as a kwarg
    def __init__(self, *args, **kwargs):
        study_id = kwargs.pop('study_id', None)
        self.user = kwargs.pop('user', None)
        super(AssayPlateReadMapAdditionalInfoForm, self).__init__(*args, **kwargs)
        # note that the non-selectized versions are manipulated in javascript, they are not displayed to the user
        self.fields['se_matrix_item'].queryset = AssayMatrixItem.objects.filter(study_id=study_id).order_by('name',)
        self.fields['ns_matrix_item'].queryset = AssayMatrixItem.objects.filter(study_id=study_id).order_by('name',)
        self.fields['ns_matrix_item'].widget.attrs.update({'class': 'no-selectize'})
        self.fields['ns_location'].widget.attrs.update({'class': 'no-selectize'})
        self.fields['se_matrix'].queryset = AssayMatrix.objects.filter(
            study_id=study_id
        ).order_by('name',)
        #self.fields['se_matrix'].widget.attrs.update({'class': 'no-selectize'})
        self.fields['se_matrix'].widget.attrs.update({'class': ' required'})

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
    se_well_use = forms.ChoiceField(
        choices=(('empty', 'Empty/Unused'), ('sample', 'Sample'), ('standard', 'Standard'), ('blank', 'Blank'))
    )
    se_time_unit = forms.ChoiceField(
        choices=(('day', 'Day'), ('hour', 'Hour'), ('minute', 'Minute'))
    )
    se_location = forms.ModelChoiceField(
         queryset=AssaySampleLocation.objects.all(),
         required=False,
    )
    ns_location = forms.ModelChoiceField(
         queryset=AssaySampleLocation.objects.all(),
         required=False,
    )
    se_increment_operation = forms.ChoiceField(
        choices=(('divide', 'Divide'), ('multiply', 'Multiply'), ('subtract', 'Subtract'), ('add', 'Add'))
    )

    se_time = forms.DecimalField(
        required=False,
        initial=1,
    )
    se_time.widget.attrs.update({'class': 'form-control'})

    se_standard_value = forms.DecimalField(
        required=False,
        initial=0,
    )
    se_standard_value.widget.attrs.update({'class': 'form-control'})

    se_increment_value = forms.DecimalField(
        required=False,
        initial=0,
    )
    se_increment_value.widget.attrs.update({'class': 'form-control'})


##### Parent for plate reader map page
class AssayPlateReaderMapForm(BootstrapForm):
    """Form for Assay Plate Reader Map"""

    class Meta(object):
        model = AssayPlateReaderMap
        fields = ['id', 'name', 'description', 'device', 'study_assay', 'time_unit', 'plate_reader_unit']
        widgets = {
            'description': forms.Textarea(attrs={'cols': 50, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        my_test = kwargs.pop('extra', 0)
        se_file_block = kwargs.pop('extra', 0)
        ns_file_pk_block_pk = kwargs.pop('extra', 0)
        # TODO sck note to self: still need to decide if will keep a template plate map
        #  (where a set of items and values have NO file/block), or assign during first file upload
        number_file_block_combos = kwargs.pop('extra', 0)
        self.study = kwargs.pop('study', None)
        self.user = kwargs.pop('user', None)
        super(AssayPlateReaderMapForm, self).__init__(*args, **kwargs)

        # need this because, remember, the plate map doesn't come WITH a study, must tell it which
        # not having this caused blank study_assay in the update page (add page worked okay)
        if not self.study and self.instance.study:
            self.study = self.instance.study

        if self.study:
            self.instance.study = self.study

        my_instance = self.instance
        self.fields['device'].widget.attrs['class'] += ' no-selectize'
        self.fields['ns_file_pk_block_pk'].widget.attrs['class'] += ' no-selectize'
        self.fields['name'].initial = "map-" + datetime.datetime.now().strftime ("%Y%m%d")+"-"+ datetime.datetime.now().strftime('%H:%M:%S')

        #may need to revisit this later, do for now so ADD will work
        self.fields['se_file_block'].required = False
        self.fields['ns_file_pk_block_pk'].required = False
        self.fields['number_file_block_combos'].required = False
        self.fields['my_test'].required = False

        self.fields['study_assay'].queryset = AbstractClassAssayStudyAssay.objects.filter(
            study_id=self.study
        ).prefetch_related(
            'target',
            'method',
            'unit',
        )

        ######
        # this will populate a dropdown that lets the user pick which file block to see on the page
        # note that, if one or more file blocks must be attached to the plate map to return something
        # might revisit this if decide to handle empty templates. Here, they would just be ignored if they exist.
        as_value_formset = AssayPlateReaderMapItemValue.objects.filter(
            assayplatereadermap=my_instance.id
        ).filter(
            plate_index=0
        ).filter(
            assayplatereadermapdatafileblock__isnull=False
        )
        number_value_sets = len(as_value_formset)
        self.fields['number_file_block_combos'].initial = number_value_sets

        distinct_plate_map = []
        distinct_plate_map_pk = []

        # queryset should have one record for each value set that HAS a file-block associated to it
        i = 0
        for record in as_value_formset:
            pick_value = str(i)
            pick_string = record.assayplatereadermapdatafile.name + '-' + record.assayplatereadermapdatafileblock.name
            pick_string_pk = str(record.assayplatereadermapdatafile.id) + '-' + str(record.assayplatereadermapdatafileblock.id)
            distinct_plate_map.append((pick_value, pick_string))
            distinct_plate_map_pk.append((pick_value, pick_string_pk))
            i = i+1

        self.fields['se_file_block'].choices = distinct_plate_map
        self.fields['ns_file_pk_block_pk'].choices = distinct_plate_map_pk
        self.fields['my_test'].initial = distinct_plate_map_pk
        self.fields['device'].widget.attrs['class'] += ' required'
        self.fields['name'].widget.attrs['class'] += ' required'
        self.fields['time_unit'].widget.attrs['class'] += ' required'
        self.fields['plate_reader_unit'].widget.attrs['class'] += ' required'

    se_file_block = forms.ChoiceField()
    ns_file_pk_block_pk = forms.ChoiceField()
    my_test = forms.CharField(widget=forms.TextInput())
    number_file_block_combos = forms.CharField(widget=forms.TextInput())


##### There should be a complete set of items for each saved plate map (one for each well in the selected plate)
class AssayPlateReaderMapItemForm(forms.ModelForm):
    """Form for Assay Plate Reader Map Item"""

    class Meta(object):
        model = AssayPlateReaderMapItem
        exclude = tracking + ('study',)

    # doing this here made the formsets selectized (override something of base formatting)...don't do it this way
    # keep here for reference
    # def __init__(self, *args, **kwargs):
    #     super(AssayPlateReaderMapItemForm, self).__init__(*args, **kwargs)
    #     self.fields['name'].widget.attrs.update({'class': ' no-selectize'})


##### Item values are sets that correspond to items. Each set should have a match to a well in the plate map.
class AssayPlateReaderMapItemValueForm(forms.ModelForm):
    """Form for Assay Plate Reader Map Item Value"""
    class Meta(object):
        model = AssayPlateReaderMapItemValue
        #exclude = tracking + ('study', )
        fields = ['id', 'assayplatereadermapdatafile', 'assayplatereadermapdatafileblock', 'plate_index',
                  'value', 'time', 'well_use', ]


##### Formset for items (custom_fields remove the select options for all the formsets - saves page load time)
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


##### Formset for item values (custom_fields remove the select options for all the formsets - saves page load time)
class AssayPlateReaderMapItemValueFormSet(BaseInlineFormSetForcedUniqueness):
    # FUTURE PERFORMANCE NOTE: may need to add the file and block if performance gets slow because there are many in the database
    custom_fields = (
        #'matrix_item',
        'assayplatereadermapdatafile', 'assayplatereadermapdatafileblock',
    )

    def __init__(self, *args, **kwargs):
        # Get the study
        self.study = kwargs.pop('study', None)
        self.user = kwargs.pop('user', None)
        super(AssayPlateReaderMapItemValueFormSet, self).__init__(*args, **kwargs)
        self.queryset = self.queryset.order_by('assayplatereadermapdatafile', 'assayplatereadermapdatafileblock', 'plate_index')
        #https://stackoverflow.com/questions/13387446/changing-the-display-order-of-forms-in-a-formset

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

##### Formset factory for item and value
#https://stackoverflow.com/questions/29881734/creating-django-form-from-more-than-two-models
AssayPlateReaderMapItemFormSetFactory = inlineformset_factory(
    AssayPlateReaderMap,
    AssayPlateReaderMapItem,
    formset=AssayPlateReaderMapItemFormSet,
    form=AssayPlateReaderMapItemForm,
    extra=1,
    #study is not needed and it adds overhead on load and save if included
    exclude=tracking + ('study',),
)
AssayPlateReaderMapItemValueFormSetFactory = inlineformset_factory(
    AssayPlateReaderMap,
    AssayPlateReaderMapItemValue,
    formset=AssayPlateReaderMapItemValueFormSet,
    form=AssayPlateReaderMapItemValueForm,
    extra=1,
    #study is not needed and it adds overhead on load and save if included
    exclude=tracking + ('study',),
)
##### end plate reader map page

##### Start plate reader file page

##### Add a plate reader file to the study - in process
class AssayPlateReaderMapDataFileAddForm(BootstrapForm):
    """Form for Plate Reader Data File Upload"""
    pass

##### Parent for plate reader file page - not using yet - still in process
class AssayPlateReaderMapDataFileUpdateForm(BootstrapForm):
    """Form for Assay Plate Reader Map Data File """
    pass

### ASSAY PLATE MAP END
