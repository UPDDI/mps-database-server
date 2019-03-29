from django.contrib import admin
from django.contrib.admin.widgets import AdminURLFieldWidget
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from django.db.models import URLField
from django.utils.safestring import mark_safe

from mps.base.admin import LockableAdmin
from drugtrials.models import (
    Species,
    TrialSource,
    FindingResult,
    FindingTreatment,
    FindingType,
    ResultDescriptor,
    Finding,
    AdverseEvent,
    OpenFDACompound,
    DrugTrial
)
from drugtrials.resource import DrugTrialResource
from .forms import (
    FindingResultForm,
    DrugTrialForm,
    FindingForm
)

from import_export.admin import ImportExportModelAdmin

from django.utils.safestring import mark_safe


class URLFieldWidget(AdminURLFieldWidget):
    """Widget for displaying URLs in Admin"""
    def render(self, name, value, attrs=None):
        """Return the safe HTML"""
        widget = super(URLFieldWidget, self).render(name, value, attrs)

        # u'<input type="button" ' \
        # u'value="Click here to open the URL in a new window." ' \
        # u'style="float: right; clear: both;" ' \
        # u'onclick="window.' \
        # u'open(document.getElementById(\'{1}\')' \
        # u'.value)" />' \

        html = \
            '<div style="width: 55em; height: 4em;">' \
            '<div>' \
            '{0}' \
            '</div>' \
            '<div style="float: right; z-index: 10;' \
            ' margin-top: -3em; margin-right: -25em;">' \
            '<button type="button" onclick="window.open(document.getElementById(\'{1}\').value, \'_newtab\');" ' \
            '>Open Link in New Tab</button>' \
            '<button type="button" onclick="window.open(document.getElementById(\'{1}\').value, \'win\', ' \
            '\'toolbars=0,width=800,height=800,left=200,top=200,scrollbars=1,resizable=1\');" ' \
            '>Open Link in New Window</button>' \
            '</div>' \
            '</div>'.format(widget, attrs['id'])

        return mark_safe(html)


class SpeciesAdmin(LockableAdmin):
    """Admin for Species"""
    list_per_page = 300
    save_on_top = True
    fieldsets = (
        (
            None, {
                'fields': (
                    'species_name',
                )
            }
        ),
        ('Change Tracking', {
            'fields': (
                'locked',
                ('created_by', 'created_on'),
                ('modified_by', 'modified_on'),
                ('signed_off_by', 'signed_off_date'),
            )
        }
        ),
    )

admin.site.register(Species, SpeciesAdmin)

# Participants information is now part of DrugTrials model
# instead of a seperate entity


class TrialSourceAdmin(LockableAdmin):
    """Admin for Trial Source"""
    save_on_top = True
    list_per_page = 300
    list_display = ('source_name', 'source_site', 'description')
    fieldsets = (
        (
            None, {
                'fields': (
                    'source_name',
                    'source_website',
                    'description',
                )
            }
        ),
        (
            'Change Tracking', {
                'fields': (
                    'locked',
                    ('created_by', 'created_on'),
                    ('modified_by', 'modified_on'),
                    ('signed_off_by', 'signed_off_date'),
                )
            }
        ),
    )
    actions = ['update_fields']

    @mark_safe
    def source_site(self, obj):
        return '<a href="%s" target="_blank">%s</a>' % (obj.source_website, obj.source_website)

    source_site.allow_tags = True

admin.site.register(TrialSource, TrialSourceAdmin)


class FindingResultInline(admin.TabularInline):
    """Admin for Finding Result Inlines"""
    model = FindingResult
    form = FindingResultForm
    raw_id_fields = ('finding_name',)
    verbose_name = 'Organ Finding'
    verbose_name_plural = 'Organ Findings'
    fields = ('finding_name', 'get_edit_link', 'descriptor', 'finding_time', 'time_units',
              'result', 'severity', 'frequency', 'value', 'value_units', 'notes')
    readonly_fields = ['get_edit_link']
    extra = 0

    @mark_safe
    def get_edit_link(self, obj=None):
        if obj.pk:  # if object has already been saved and has a primary key, show link to it
            url = reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=[force_text(obj.pk)])
            return """<a href="{url}">{text}</a>""".format(
                url=url,
                text=_("Edit this %s separately") % obj._meta.verbose_name,
            )
        return _("(save and continue editing to create a link)")
    get_edit_link.short_description = _("Edit link")
    get_edit_link.allow_tags = True

    class Media(object):
        css = {"all": ("css/hide_admin_original.css",)}


class FindingTreatmentInline(admin.StackedInline):
    """Admin for Finding Treatment Inlines"""
    model = FindingTreatment
    verbose_name = 'Finding Treatments'
    fields = ('compound', 'concentration', 'concentration_unit')
    extra = 0


class FindingResultAdmin(admin.ModelAdmin):
    """Admin for Finding Result"""
    model = FindingResult
    fields = ('finding_name', 'descriptor', 'finding_time', 'time_units',
              'result', 'severity', 'frequency', 'value', 'value_units',)
    inlines = [FindingTreatmentInline]

admin.site.register(FindingResult, FindingResultAdmin)


class DrugTrialAdmin(LockableAdmin):
    """Admin for Drug Trials"""
    form = DrugTrialForm

    class Media(object):
        js = ('js/inline_fix.js',)

    resource_class = DrugTrialResource

    formfield_overrides = {
        URLField: {'widget': URLFieldWidget},
    }

    save_on_top = True
    list_per_page = 300
    list_display = (
        'compound', 'species', 'trial_type', 'trial_sub_type',
        'source_page', 'start_date', 'locked')
    list_filter = ['trial_type', ]
    search_fields = [
        'compound__name', 'species__species_name']
    actions = ['update_fields']
    raw_id_fields = ('compound',)
    readonly_fields = ['created_on', 'created_by', 'modified_by',
                       'modified_on', 'drug_display', 'figure1_display', 'figure2_display']

    # Display figures
    @mark_safe
    def figure1_display(self, obj):
        if obj.id and obj.figure1:
            return '<img src="%s">' % \
                   obj.figure1.url
        return ''

    @mark_safe
    def figure2_display(self, obj):
        if obj.id and obj.figure2:
            return '<img src="%s">' % \
                   obj.figure2.url
        return ''
    figure1_display.allow_tags = True
    figure2_display.allow_tags = True

    @mark_safe
    def drug_display(self, obj):

        if obj.compound.chemblid:
            url = ('https://www.ebi.ac.uk/chembldb/compound/'
                   'displayimage/' + obj.compound.chemblid)
            return '<img src="%s">' % \
                url
        else:
            return ''

    drug_display.allow_tags = True
    drug_display.short_description = 'Structure'

    filter_horizontal = ('disease',)
    fieldsets = (
        (None, {
            'fields': (('compound', 'title'),
                       ('drug_display', 'figure1_display', 'figure2_display',),
                       ('trial_type', 'trial_sub_type'),
                       ('start_date', 'end_date', 'publish_date'),
                       ('disease'),
                       ('condition', 'description',),
                       ('figure1', 'figure2',),)
        }),
        ('Participants', {
            'fields': (
                ('species', 'gender', 'population_size',),
                ('age_min', 'age_max', 'age_average', 'age_unit',),
                ('weight_min', 'weight_max', 'weight_average', 'weight_unit'),
            )
        }),
        ('References', {
            'fields': (('source', 'references', 'source_link'),)
        }),
        ('Change Tracking', {
            'fields': (
                'locked',
                ('created_by', 'created_on'),
                ('modified_by', 'modified_on'),
                ('signed_off_by', 'signed_off_date'),
            )
        }
        ),
    )
    inlines = [FindingResultInline]

    @mark_safe
    def source_page(self, obj):
        return '<a href="%s" target="_blank">%s</a>' % (obj.source_link, obj.source_link)
    source_page.allow_tags = True

admin.site.register(DrugTrial, DrugTrialAdmin)


class FindingTypeAdmin(LockableAdmin):
    """Admin for Finding Types"""
    list_per_page = 300
    save_on_top = True
    list_display = ('finding_type', 'description')
    fieldsets = (
        (
            None, {
                'fields': (
                    'finding_type',
                    'description',
                )
            }
        ),
        ('Change Tracking', {
            'fields': (
                'locked',
                ('created_by', 'created_on'),
                ('modified_by', 'modified_on'),
                ('signed_off_by', 'signed_off_date'),
            )
        }
        ),
    )

admin.site.register(FindingType, FindingTypeAdmin)


class ResultDescriptorAdmin(LockableAdmin):
    """Admin for Result Descriptors"""
    list_per_page = 300
    save_on_top = True
    fieldsets = (
        (
            None, {
                'fields': (
                    'result_descriptor',
                )
            }
        ),
        (
            'Change Tracking', {
                'fields': (
                    'locked',
                    ('created_by', 'created_on'),
                    ('modified_by', 'modified_on'),
                    ('signed_off_by', 'signed_off_date'),
                )
            }
        ),
    )


admin.site.register(ResultDescriptor, ResultDescriptorAdmin)


class FindingAdmin(LockableAdmin):
    """Admin for Findings"""
    form = FindingForm

    save_on_top = True
    list_per_page = 300
    list_display = ('organ', 'finding_type', 'finding_name', 'optional_link')
    list_display_links = ('organ', 'finding_name', 'finding_type')
    list_filter = sorted(['finding_type'])
    search_fields = ['finding_name', ]
    fieldsets = (
        (
            None, {
                'fields': (
                    'finding_name',
                    'finding_type',
                    'organ',
                    'description',
                )
            }
        ),
        (
            'Change Tracking', {
                'fields': (
                    'locked',
                    ('created_by', 'created_on'),
                    ('modified_by', 'modified_on'),
                    ('signed_off_by', 'signed_off_date'),
                )
            }
        ),
    )
    actions = ['update_fields']

    @mark_safe
    def optional_link(self, obj):
        words = obj.description.split()
        sentence = ''
        for thing in words:
            if thing.startswith("http://"):
                link = '<a href="%s" target="_blank">%s</a>' % (thing, thing)
                sentence += (' ' + link)
            else:
                sentence += (' ' + thing)
        return sentence
    optional_link.allow_tags = True
    optional_link.short_description = "Description"


admin.site.register(Finding, FindingAdmin)


class AdverseEventAdmin(ImportExportModelAdmin):
    """Admin for Adverse Events"""
    save_on_top = True
    list_per_page = 300
    list_display = ('event', 'organ')
    fieldsets = (
        (
            None, {
                'fields': (
                    'event',
                    'organ',
                )
            }
        ),
    )


admin.site.register(AdverseEvent, AdverseEventAdmin)


class OpenFDACompoundAdmin(ImportExportModelAdmin):
    """Admin for OpenFDA Compounds"""
    save_on_top = True
    list_per_page = 300
    list_display = ('compound', 'black_box')
    fieldsets = (
        (
            None, {
                'fields': (
                    'compound',
                    'black_box',
                    'warnings',
                    'nonclinical_toxicology',
                )
            }
        ),
    )


admin.site.register(OpenFDACompound, OpenFDACompoundAdmin)
