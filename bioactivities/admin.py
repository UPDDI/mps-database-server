from django.contrib import admin
# from django.contrib import messages
from django import forms
# from django.shortcuts import render_to_response
# from django.template import RequestContext
# from django.http import HttpResponseRedirect
from django.forms import Textarea
from django.db import models

from bioactivities.resource import BioactivityTypeResource
from mps.base.admin import LockableAdmin
from .models import (
    Target,
    Assay,
    Bioactivity,
    BioactivityType,
    PubChemBioactivity
)
from bioactivities.forms import AssayForm
from bioactivities.forms import TargetsForm

from django.utils.safestring import mark_safe

# TODO TODO TODO allow_tags attribute has been removed


class TargetAdmin(LockableAdmin):
    """Admin for Bioactivity Target"""
    # class Media(object):
    #     js = ('bioactivities/customize_admin.js',)

    form = TargetsForm

    # class AddMultiForm(forms.Form):
    #
    #     chemblids = forms.CharField(
    #         required=True,
    #         label='ChEMBL IDs',
    #         widget=forms.Textarea(),
    #         help_text='<br>ChEMBL IDs separated by a space or a new line.'
    #     )

    save_on_top = True
    list_per_page = 300
    list_display = ('name', 'organism', 'target_type', 'chembl_link', 'GI', 'locked')
    list_filter = ('target_type', 'organism')
    search_fields = ['name', 'organism', 'synonyms', '=chemblid', 'GI']
    actions = ['update_fields']
    readonly_fields = ('last_update', 'created_by', 'created_on',
                       'modified_by', 'modified_on')

    fieldsets = (
        (
            None, {
                'fields': (
                    'name',
                    'synonyms',
                    'chemblid',
                    'description',
                    'gene_names',
                    'organism',
                    'uniprot_accession',
                    'target_type',
                    'GI',
                    'last_update',
                )
            }
        ),
        (
            'Change Tracking', {
                'fields': (
                    # 'locked',
                    ('created_by', 'created_on'),
                    ('modified_by', 'modified_on'),
                    ('signed_off_by', 'signed_off_date'),
                )
            }
        ),
    )

    # REMOVED FOR NOW
    # def get_urls(self):
    #
    #     return patterns(
    #         '',
    #         (r'^add_multi/$', self.admin_site.admin_view(self.add_targets))
    #     ) + super(TargetAdmin, self).get_urls()
    #
    # def add_targets(self, request):
    #
    #     if '_add' in request.POST:
    #         form = self.AddMultiForm(request.POST)
    #         if form.is_valid():
    #             chemblids = form.cleaned_data['chemblids']
    #             counter = skipped = invalid = notfound = 0
    #             chemblids = chemblids.split()
    #             for chemblid in chemblids:
    #                 if not chemblid.startswith('CHEMBL'):
    #                     invalid += 1
    #                     continue
    #                 if Target.objects.filter(chemblid=chemblid):
    #                     skipped += 1
    #                     continue
    #                 try:
    #                     data = chembl_target(chemblid)
    #                 except Exception:
    #                     notfound += 1
    #                 else:
    #                     if data:
    #                         data['locked'] = True
    #                         counter += 1
    #                         Target.objects.create(**data)
    #
    #             if counter:
    #                 self.message_user(request,
    #                                   'Successfully added {} target{}.'
    #                                   .format(counter,
    #                                           '' if counter == 1 else 's'))
    #             if skipped:
    #                 self.message_user(request, 'Skipped {} target{} that '
    #                                            '{} already in the database.'
    #                                   .format(skipped,
    #                                           '' if skipped == 1 else 's',
    #                                           'is' if skipped == 1 else 'are'),
    #                                   level=messages.WARNING)
    #             if invalid:
    #                 self.message_user(request, 'Skipped {} invalid '
    #                                            'identifier{}.'
    #                                   .format(invalid,
    #                                           '' if invalid == 1 else 's'),
    #                                   level=messages.WARNING)
    #             if notfound:
    #                 self.message_user(request,
    #                                   'Could not find {} identifier{} in '
    #                                   'ChEMBL database.'
    #                                   .format(notfound,
    #                                           '' if notfound == 1 else 's'),
    #                                   level=messages.WARNING)
    #
    #             return HttpResponseRedirect(request.get_full_path())
    #     else:
    #         form = self.AddMultiForm()
    #
    #     return render_to_response('bioactivities/add_multi.html', {
    #         'title': 'Add multiple targets',
    #         'opts': self.model._meta,
    #         'form': form,
    #         'what': 'target',
    #         # 'root_path': self.admin_site.root_path,
    #     }, context_instance=RequestContext(request))


admin.site.register(Target, TargetAdmin)


class AssayAdmin(LockableAdmin):
    """Admin for Bioactivity Assay (not to be confused with models of the Assay App)"""
    form = AssayForm

    class Media(object):
        js = ('bioactivities/customize_admin.js',)

    class AddMultiForm(forms.Form):

        chemblids = forms.CharField(required=True, label='ChEMBL IDs',
                                    widget=forms.Textarea(),
                                    help_text='<br>ChEMBL IDs separated by a '
                                              'space or a new line.')

    save_on_top = True
    list_per_page = 300
    list_display = (
        'description', 'chembl_link', 'pubchem_id', 'organism', 'target', 'assay_type', 'locked')
    list_filter = ('assay_type',)
    search_fields = ['description', '=chemblid', 'pubchem_id']
    actions = ['update_fields']
    readonly_fields = ('last_update', 'created_by', 'created_on',
                       'modified_by', 'modified_on')

    fieldsets = (
        (
            None, {
                'fields': (
                    'chemblid',
                    'pubchem_id',
                    ('source', 'source_id',),
                    'name',
                    'target',
                    'description',
                    'assay_type',
                    'organism',
                    'strain',
                    'journal',
                    'last_update',
                )
            }
        ),
        (
            'Change Tracking', {
                'fields': (
                    # 'locked',
                    ('created_by', 'created_on'),
                    ('modified_by', 'modified_on'),
                    ('signed_off_by', 'signed_off_date'),
                )
            }
        ),
    )

    # Removed for now
    # def get_urls(self):
    #
    #     return patterns(
    #         '',
    #         (r'^add_multi/$', self.admin_site.admin_view(self.add_assays))
    #     ) + super(AssayAdmin, self).get_urls()
    #
    # def add_assays(self, request):
    #
    #     if '_add' in request.POST:
    #         form = self.AddMultiForm(request.POST)
    #         if form.is_valid():
    #             chemblids = form.cleaned_data['chemblids']
    #             counter = skipped = invalid = notfound = 0
    #             chemblids = chemblids.split()
    #             for chemblid in chemblids:
    #                 if not chemblid.startswith('CHEMBL'):
    #                     invalid += 1
    #                     continue
    #                 if Assay.objects.filter(chemblid=chemblid):
    #                     skipped += 1
    #                     continue
    #                 try:
    #                     data = chembl_assay(chemblid)
    #                 except Exception:
    #                     notfound += 1
    #                 else:
    #                     if data:
    #                         data['locked'] = True
    #                         counter += 1
    #                         Assay.objects.create(**data)
    #
    #             if counter:
    #                 self.message_user(request,
    #                                   'Successfully added {} assay{}.'
    #                                   .format(counter,
    #                                           '' if counter == 1 else 's'))
    #             if skipped:
    #                 self.message_user(request, 'Skipped {} assay{} that '
    #                                            '{} already in the database.'
    #                                   .format(skipped,
    #                                           '' if skipped == 1 else 's',
    #                                           'is' if skipped == 1 else 'are'),
    #                                   level=messages.WARNING)
    #             if invalid:
    #                 self.message_user(request, 'Skipped {} invalid '
    #                                            'identifier{}.'
    #                                   .format(invalid,
    #                                           '' if invalid == 1 else 's'),
    #                                   level=messages.WARNING)
    #             if notfound:
    #                 self.message_user(request,
    #                                   'Could not find {} identifier{} in '
    #                                   'ChEMBL database.'
    #                                   .format(notfound,
    #                                           '' if notfound == 1 else 's'),
    #                                   level=messages.WARNING)
    #
    #             return HttpResponseRedirect(request.get_full_path())
    #     else:
    #         form = self.AddMultiForm()
    #
    #     return render_to_response('bioactivities/add_multi.html', {
    #         'title': 'Add multiple assays',
    #         'opts': self.model._meta,
    #         'form': form,
    #         'what': 'assay',
    #         # 'root_path': self.admin_site.root_path,
    #     }, context_instance=RequestContext(request))


admin.site.register(Assay, AssayAdmin)


class BioactivityAdmin(LockableAdmin):
    """Admin for an individual Bioactivity"""
    save_on_top = True
    list_per_page = 50
    ordering = ('compound', 'standard_name')
    raw_id_fields = ('compound', 'target', 'assay',)

    @mark_safe
    def chembl_link(self, obj):
        return obj.assay.chembl_link()

    chembl_link.allow_tags = True
    chembl_link.short_description = 'CHEMBL Links'

    @mark_safe
    def bioactivity_display(self, obj):

        if obj.compound.chemblid:
            url = ('https://www.ebi.ac.uk/chembldb/compound/'
                   'displayimage/' + obj.compound.chemblid)
            return '<img src="%s">' % \
                url
        else:
            return ''

    bioactivity_display.allow_tags = True
    bioactivity_display.short_description = 'Structure'

    list_display = (
        'compound',
        'target',
        'organism',
        'standard_name',
        'operator',
        'standardized_value',
        'standardized_units',
        'chembl_link',
        'bioactivity_type',
        'value',
        'units',
        # 'locked',
    )
    search_fields = ['compound__name', 'target__name', 'bioactivity_type']
    readonly_fields = ['created_by', 'created_on', 'modified_by',
                       'modified_on', 'bioactivity_display']
    actions = ['update_fields']

    fieldsets = (
        (None, {
            'fields': (('compound', 'assay'), 'bioactivity_display', ('target', 'target_confidence'),
                       ('bioactivity_type', 'value', 'units'),
                       ('standard_name', 'standardized_value', 'standardized_units'),
                       ('activity_comment', 'reference', 'name_in_reference'),
                       ('notes', 'data_validity'),
                       # 'locked',
                       ('created_by', 'created_on'), ('modified_by', 'modified_on'),
                       ('signed_off_by', 'signed_off_date'),)
        }),
    )

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 20})}
    }


admin.site.register(Bioactivity, BioactivityAdmin)


class BioactivityTypeAdmin(LockableAdmin):
    """Admin for Bioactivty Type (for consolidating units and so on)"""
    resource_class = BioactivityTypeResource
    save_on_top = True
    list_per_page = 50
    list_max_show_all = 2000
    list_display = (
        'chembl_bioactivity',
        'standard_name',
        'chembl_unit',
        'scale_factor',
        'standard_unit',
        'mass_flag',
        'description'
    )
    search_fields = ['chembl_bioactivity', 'standard_name', 'chembl_unit', 'standard_unit']
    list_filter = ['standard_unit', ]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 30})}
    }
    readonly_fields = ['created_by', 'created_on', 'modified_by',
                       'modified_on', 'chembl_bioactivity', 'chembl_unit']

    fieldsets = (
        (
            None, {
                'fields': (
                    ('chembl_bioactivity', 'chembl_unit'),
                    ('scale_factor', 'mass_flag'),
                    'description',
                    ('standard_name', 'standard_unit'),
                )
            }
        ),
        (
            'Change Tracking', {
                'fields': (
                    # 'locked',
                    ('created_by', 'created_on'),
                    ('modified_by', 'modified_on'),
                    ('signed_off_by', 'signed_off_date'),
                )
            }
        ),
    )


admin.site.register(BioactivityType, BioactivityTypeAdmin)


class PubChemBioactivityAdmin(LockableAdmin):
    """Admin for a PubChem Bioactivity"""
    search_fields = ['compound__name', 'activity_name', 'target__name', 'outcome']
    list_filter = ['compound', ]

    raw_id_fields = ('target', 'assay')

    save_on_top = True
    list_per_page = 50

    list_display = (
        'compound',
        'activity_name',
        'value',
        'outcome',
        'normalized_value',
        'assay'
    )

    fieldsets = (
        (None, {
            'fields': (
                'compound',
                'target',
                'value',
                'outcome',
                'normalized_value',
                'activity_name',
                'assay',
                ('notes', 'data_validity'),
            )
        }),
    )


admin.site.register(PubChemBioactivity, PubChemBioactivityAdmin)


# DEPRECATED
#class PubChemTargetAdmin(LockableAdmin):
#    search_fields = ['name', 'organism', 'GI']
#
#    save_on_top = True
#    list_per_page = 50
#
#    list_display = (
#        'name',
#        'organism',
#        'GI',
#    )
#
#    fieldsets = (
#        (None, {
#            'fields': (
#                'name',
#                'organism',
#                'GI',
#            )
#        }),
#    )
#
#
#admin.site.register(PubChemTarget, PubChemTargetAdmin)


#class PubChemAssayAdmin(LockableAdmin):
#    search_fields = ['aid', 'name', 'source']
#
#    save_on_top = True
#    list_per_page = 50
#
#    list_display = (
#        'aid',
#        'name',
#        'target_type',
#        'organism',
#        'source',
#        'source_id'
#    )
#
#    fieldsets = (
#        (None, {
#            'fields': (
#                'aid',
#                'name',
#                'target_type',
#                'organism',
#                'source',
#                'description',
#                'source_id'
#            )
#        }),
#    )
#
#
#admin.site.register(PubChemAssay, PubChemAssayAdmin)
