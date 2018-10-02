# coding=utf-8

"""Base Models"""

from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords
# from django.shortcuts import redirect, get_object_or_404


# TODO THIS WILL HAVE TO BE CHANGED IF WE WANT TO HAVE A RECORD FOR EVERY MODIFIER
class TrackableModel(models.Model):
    """The base model for Trackable models

    NOTE: the "read-only" configuration method resides in base/admin.py
    """

    class Meta(object):
        abstract = True

    # CREATION DATA #

    created_by = models.ForeignKey('auth.User',
                                   related_name='%(class)s_created_by',
                                   blank=True,
                                   null=True)

    created_on = models.DateTimeField(auto_now_add=True,
                                      blank=True,
                                      null=True)

    # MODIFICATION DATA #

    modified_by = models.ForeignKey('auth.User',
                                    related_name='%(class)s_modified_by',
                                    blank=True,
                                    null=True)

    modified_on = models.DateTimeField(auto_now=True,
                                       blank=True,
                                       null=True)

    signed_off_by = models.ForeignKey('auth.User',
                                      related_name='%(class)s_signed_off_by',
                                      blank=True,
                                      null=True)

    signed_off_date = models.DateTimeField(blank=True,
                                           null=True)

    # Using django-simplehistory
    history = HistoricalRecords(inherit=True)

    # May be useful... however might be better to just add as needed
    # sign_off_notes = models.CharField(max_length=255, blank=True, default='')

    def full_creator(self):
        if self.created_by:
            return self.created_by.first_name + ' ' + self.created_by.last_name
        else:
            return 'Admin'

    def full_modifier(self):
        if self.modified_by:
            return self.modified_by.first_name + ' ' + self.modified_by.last_name
        else:
            return 'Admin'

    def full_reviewer(self):
        if self.signed_off_by:
            return self.signed_off_by.first_name + ' ' + self.signed_off_by.last_name
        else:
            return 'Admin'

    # @property
    # def _history_user(self):
    #     return self.modified_by
    #
    # @_history_user.setter
    # def _history_user(self, value):
    #     self.modified_by = value


class LockableModel(TrackableModel):
    """The base model for Lockable models"""

    locked = models.BooleanField(default=False,
                                 help_text='Check the box and save to lock the entry. '
                                 'Uncheck and save to enable editing.')

    class Meta(object):
        abstract = True


# DEPRECATED
# AT THE MOMENT, THESE FIELDS ARE NOT VERY MEANINGFULLY USED
# TODO WE WILL HAVE TO BE SURE TO CHANGE ANY LOGIC THAT RELIES ON GROUP AND RESTRICTED
class RestrictedModel(LockableModel):
    """The base model for Restricted models"""

    # It is mandatory to bind a group to a restricted model
    group = models.ForeignKey('auth.Group',
                              help_text='Bind to a group (Level 0)')

    # DEPRECATED
    # We seem to have decided to handle this differently
    restricted = models.BooleanField(default=True,
                                     help_text='Check box to restrict to selected group. Unchecked sends to Level 3')

    class Meta(object):
        abstract = True


class FlaggableModel(LockableModel):
    """The base model for flaggable models"""

    flagged = models.BooleanField(default=False,
                                  help_text='Check box to flag for review')

    reason_for_flag = models.CharField(max_length=300,
                                       help_text='Reason for why this entry was flagged', blank=True, default='')

    class Meta(object):
        abstract = True


# FOR COMPATIBILITY
class FlaggableRestrictedModel(RestrictedModel):
    """The base model for flaggable models"""

    flagged = models.BooleanField(default=False,
                                  help_text='Check box to flag for review')

    reason_for_flag = models.CharField(max_length=300,
                                       help_text='Reason for why this entry was flagged', blank=True, default='')

    class Meta(object):
        abstract = True


def save_forms_with_tracking(self, form, formset=None, update=False):
    """Save tracking data
    Params:
    self -- the view in question (passed as self)
    form -- the form for the view
    formset -- the formset for the view
    update -- whether this is an update to an existing instance
    """
    if form:
        data = form.cleaned_data

        # TODO SUBJECT TO REVISION
        # Only update review if the entry has not already been reviewed
        if not form.instance.signed_off_by and data.get('signed_off', ''):
            form.instance.signed_off_by = self.request.user
            form.instance.signed_off_date = timezone.now()
        # Remove sign off if necessary
        elif form.instance.signed_off_by and not data.get('signed_off', 'NOT_IN_FORM'):
            form.instance.signed_off_by = None
            form.instance.signed_off_date = None

        self.object = form.save(commit=False)

        # Else if Add
        if not update:
            self.object.modified_by = self.object.created_by = self.request.user
        else:
            self.object.modified_by = self.request.user

        self.object.save()

    if formset:
        formset_has_changed = False

        # If a list of formsets, save each
        if type(formset) == list:
            for current_formset in formset:
                if current_formset.has_changed():
                    current_formset.save()
                    formset_has_changed = True

        # Otherwise, just save the one
        elif formset.has_changed():
            formset.save()
            formset_has_changed = True

        if update and formset_has_changed:
            self.object.modified_by = self.request.user
            self.object.save()
