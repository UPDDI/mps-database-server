from django import forms
from captcha.fields import CaptchaField
from django_registration.forms import RegistrationFormUniqueEmail
from django.contrib.auth.forms import PasswordResetForm, UserChangeForm
from django.contrib.auth.models import User
from mps.settings import DEFAULT_FROM_EMAIL

from django.template.loader import render_to_string

# SHOULD BE IN ALL CAPS
tracking = ('created_by', 'created_on', 'modified_on', 'modified_by', 'signed_off_by', 'signed_off_date', 'locked')

WIDGETS_TO_ADD_FORM_CONTROL_TO = {
    "<class 'django.forms.widgets.TextInput'>": True,
    "<class 'django.forms.widgets.Textarea'>": True,
    "<class 'django.forms.widgets.DateInput'>": True,
    "<class 'django.forms.widgets.Select'>": True,
    "<class 'django.forms.widgets.NumberInput'>": True
}

DATE_INPUT_WIDGET = "<class 'django.forms.widgets.DateInput'>"

FILE_INPUT_WIDGET = "<class 'django.forms.widgets.ClearableFileInput'>"

WIDGETS_WITH_AUTOCOMPLETE_OFF = {
    "<class 'django.forms.widgets.DateInput'>": True,
}

class BootstrapForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', '')
        super(BootstrapForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            widget_type = str(type(self.fields[field].widget))

            if widget_type in WIDGETS_TO_ADD_FORM_CONTROL_TO:
                self.fields[field].widget.attrs['class'] = 'form-control'
            if widget_type in WIDGETS_WITH_AUTOCOMPLETE_OFF:
                self.fields[field].widget.attrs['autocomplete'] = 'off'
            if widget_type == DATE_INPUT_WIDGET:
                self.fields[field].widget.attrs['class'] += ' datepicker-input'
            if widget_type == FILE_INPUT_WIDGET:
                # Sloppy (doubly strange)
                if getattr(self.fields[field], 'required', False):
                    self.fields[field].widget.attrs['class'] = 'btn btn-lg'
                else:
                    self.fields[field].widget.attrs['class'] = 'btn btn-default btn-lg'

            # CRUDE WAY TO INDICATE REQUIRED FIELDS
            if getattr(self.fields[field], 'required', False):
                # SLOPPY
                if self.fields[field].widget.attrs.get('class', ''):
                    self.fields[field].widget.attrs['class'] += ' required'
                else:
                    self.fields[field].widget.attrs['class'] = 'required'

            # Not really a good idea to use "private" attributes...
            if hasattr(self.fields[field], '_queryset'):
                if hasattr(self.fields[field]._queryset, 'model'):
                    self.fields[field].widget.attrs['data-app'] = self.fields[field]._queryset.model._meta.app_label
                    self.fields[field].widget.attrs['data-model'] = self.fields[field]._queryset.model._meta.object_name



class SignOffMixin(BootstrapForm):
    def __init__(self, *args, **kwargs):
        super(SignOffMixin, self).__init__(*args, **kwargs)

        instance = kwargs.get('instance', None)

        if instance and instance.signed_off_by:
            self.fields['signed_off'].initial = True

    signed_off = forms.BooleanField(required=False)


class SearchForm(forms.Form):
    """Form for Global/Bioactivity searches"""
    app = forms.CharField(max_length=50)
    compound = forms.CharField(max_length=100, required=False)
    target = forms.CharField(max_length=100, required=False)
    name = forms.CharField(max_length=100, required=False)
    pubchem = forms.BooleanField(required=False)
    exclude_targetless = forms.BooleanField(required=False)
    exclude_organismless = forms.BooleanField(required=False)
    search_term = forms.CharField(max_length=500, required=False)

    def clean(self):
        super(SearchForm, self).clean()

        app = self.cleaned_data.get('app', '')
        compound = self.cleaned_data.get('compound', '')
        target = self.cleaned_data.get('target', '')
        name = self.cleaned_data.get('name', '')

        if app == "Bioactivities" and not any([compound, target, name]):
            raise forms.ValidationError(
                'You must have at least one search term'
            )

        return self.cleaned_data


# Add captcha to registration form
class CaptchaRegistrationForm(RegistrationFormUniqueEmail):
    """Extended Registration Form with Captcha"""
    captcha = CaptchaField()
    first_name = forms.CharField(initial='')
    last_name = forms.CharField(initial='')

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()[:30].strip()

        return username

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '').strip()[:30]

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '').strip()[:30]

        return last_name

    def clean(self):
        cleaned_data = super(CaptchaRegistrationForm, self).clean()
        username = cleaned_data.get('username')
        if username and User.objects.filter(username__iexact=username).exists():
            self.add_error('username', 'A user with that username already exists.')
        return cleaned_data

    def save(self, commit=True):
        new_user = super(CaptchaRegistrationForm, self).save()
        new_user.first_name = self.cleaned_data.get('first_name')
        new_user.last_name = self.cleaned_data.get('last_name')
        new_user.save()

        # Magic strings are in poor taste, should use a template instead
        subject = 'New User: {0} {1}'.format(new_user.first_name, new_user.last_name)
        message = render_to_string(
            'django_registration/superuser_new_user_alert.txt',
            {
                'user': new_user
            }
        )

        users_to_be_alerted = User.objects.filter(is_superuser=True, is_active=True)

        for user_to_be_alerted in users_to_be_alerted:
            user_to_be_alerted.email_user(subject, message, DEFAULT_FROM_EMAIL)

        return new_user


# Add captcha to reset form
class CaptchaResetForm(PasswordResetForm):
    """Extended Password Reset form with Captcha"""
    captcha = CaptchaField()

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("There is no user registered with the specified email address!")

        return email


class MyUserChangeForm(UserChangeForm):
    # Very sloppy use of inheritance
    class Meta(UserChangeForm.Meta):
        help_texts = {
            'groups':   '***Assign permissions as follows:***<br>'
                        'data group viewer: {{ data group }} Viewer<br>'
                        'data group editor: {{ data group }}<br>'
                        'data group admin (can sign off): {{ data group }} Admin<br>'
                        'stakeholder group admin (can approve): {{ access group }} Admin<br>'
                        'stakeholder/access group viewer: {{ access group }} Viewer<br><br>'
                        '***NOTE THAT EDITORS ARE ALSO VIEWERS AND ADMINS ARE EDITORS AND VIEWERS***<br><br>',
            'user_permissions': '***THIS IS FOR THE ADMIN INTERFACE ONLY***<br>',
        }

    def clean(self):
        cleaned_data = super(MyUserChangeForm, self).clean()
        username = cleaned_data.get('username')
        if username and User.objects.filter(username__iexact=username).exclude(id=self.instance.id).exists():
            self.add_error('username', 'A user with that username already exists.')
        return cleaned_data
