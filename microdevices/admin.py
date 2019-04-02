# coding=utf-8

from django.contrib import admin
from mps.base.admin import LockableAdmin, TrackableAdmin
from .models import (
    MicrophysiologyCenter,
    Manufacturer,
    Microdevice,
    OrganModel,
    ValidatedAssay,
    OrganModelProtocol,
    GroupDeferral
)
from.forms import MicrophysiologyCenterForm, GroupDeferralForm
from django.urls import resolve
from django.db.models.fields.files import FieldFile

from django.utils.safestring import mark_safe


class MicrophysiologyCenterAdmin(LockableAdmin):
    """Admin for Microphysiology Centers"""
    form = MicrophysiologyCenterForm
    save_on_top = True
    list_display = (
        'name', 'center_id', 'institution', 'description', 'pi', 'contact_person', 'center_site'
    )
    list_per_page = 300
    filter_horizontal = ('groups',)
    fieldsets = (
        (
            None, {
                'fields': (
                    'name',
                    'center_id',
                    'institution',
                    'description',
                    'contact_person',
                    'contact_email',
                    'contact_web_page',
                    'pi',
                    'pi_email',
                    'pi_web_page',
                    'website',
                    'groups',
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

    @mark_safe
    def center_site(self, obj):
        return '<a href="%s" target="_blank">%s</a>' % (obj.website, obj.website)
    center_site.allow_tags = True

admin.site.register(MicrophysiologyCenter, MicrophysiologyCenterAdmin)


class ManufacturerAdmin(LockableAdmin):
    """Admin for Manufacturers"""
    save_on_top = True
    list_per_page = 300
    list_display = ['name', 'contact_person', 'manufacturer_site']
    fieldsets = (
        (
            None, {
                'fields': (
                'name',
                'contact_person',
                'website',
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

    @mark_safe
    def manufacturer_site(self, obj):
        return '<a href="%s" target="_blank">%s</a>' % (obj.website, obj.website)
    manufacturer_site.allow_tags = True

admin.site.register(Manufacturer, ManufacturerAdmin)


class MicrodeviceAdmin(LockableAdmin):
    """Admin for Microdevices"""
    class Media(object):
        js = ('microdevices/layout.js',)
        css = {'all': ('assays/customize_admin.css',)}

    @mark_safe
    def device_image_display(self, obj):
        if obj.id and obj.device_image:
            return '<img src="%s">' % \
                   obj.device_image.url
        return ''

    @mark_safe
    def device_cross_section_image_display(self, obj):
        if obj.id and obj.device_cross_section_image:
            return '<img src="%s">' % \
                   obj.device_cross_section_image.url
        return ''

    device_image_display.allow_tags = True
    device_cross_section_image_display.allow_tags = True

    save_as = True
    save_on_top = True
    list_per_page = 300
    list_display = ('name', 'organ', 'center', 'manufacturer',
                    'description')
    # TODO REVISE ORGAN_NAME
    search_fields = ['name', 'organ__organ_name', 'center__name',  'description']
    list_filter = ['organ', 'center', ]

    fieldsets = (
        (
            None, {
                'fields': (
                    (
                        'device_type'
                    ),
                    (
                        'center', 'manufacturer',
                    ),
                    (
                        'name', 'organ',
                    ),
                    (
                        'description', 'barcode',
                    ),
                    (
                        'device_image_display',
                        'device_cross_section_image_display',
                    ),
                    (
                        'references'
                    )
                )
            }
        ),
        (
            'Dimensions', {
                'fields': (
                    (
                        'device_width', 'device_length', 'device_thickness',
                    ),
                    (
                        'device_fluid_volume',
                    ),
                    (
                        'substrate_material', 'substrate_thickness',
                    ),
                    (
                        'device_image', 'device_cross_section_image',
                    ),
                )
            }
        ),
        (
            'Layout', {
                'fields': (
                    (
                        'number_of_rows', 'number_of_columns',
                    ),
                    (
                        'row_labels', 'column_labels',
                    ),
                )
            }
        ),
        (
            None, {
                'fields': (
                    'locked',
                    'created_by',
                    'modified_by',
                    ('signed_off_by', 'signed_off_date'),
                )
            }
        ),
    )
    actions = ['update_fields']

    readonly_fields = (
        'device_image_display', 'device_cross_section_image_display',
    )

    def save_model(self, request, obj, form, change):
        # Django always sends this when "Save as new is clicked"
        if '_saveasnew' in request.POST:
            # Get the ID from the admin URL
            original_pk = resolve(request.path).args[0]
            # Get the original object
            original_obj = obj._meta.concrete_model.objects.get(id=original_pk)

            # Iterate through all it's properties
            for prop, value in list(vars(original_obj).items()):
                # if the property is an Image (don't forget to import ImageFieldFile!)
                if isinstance(getattr(original_obj, prop), FieldFile):
                    # Copy it!
                    setattr(obj, prop, getattr(original_obj, prop))
        obj.save()

admin.site.register(Microdevice, MicrodeviceAdmin)


class OrganModelProtocolInline(admin.TabularInline):
    """Admin Inline for Organ Model Protocols"""
    model = OrganModelProtocol
    fields = ('version', 'file')
    extra = 1

    class Media(object):
        css = {"all": ("css/hide_admin_original.css",)}


class ValidatedAssayInline(admin.TabularInline):
    """Admin Inline for Validated Assays"""
    # Results calculated from CHIP READOUTS
    model = ValidatedAssay
    verbose_name = 'Validated Assay'
    verbose_name_plural = 'Validated Assays'
    fields = ('assay',)
    extra = 0

    class Media(object):
        css = {"all": ("css/hide_admin_original.css",)}


class OrganModelAdmin(LockableAdmin):
    """Admin for Organ Models"""
    class Media(object):
        js = ('js/inline_fix.js',)

    list_per_page = 300
    list_display = (
        'name',
        'center',
        'base_model',
        'organ',
        'device',
        'disease',
        'description',
        'alt_name',
        'model_type',
        'disease_trigger',
    )
    search_fields = [
        'name', 'organ__organ_name', 'device__name', 'center__name', 'description']
    readonly_fields = ['created_by', 'created_on',
                       'modified_by', 'modified_on']

    # fieldsets = (
    #     (
    #         None, {
    #             'fields': (
    #                 (
    #                     'name', 'organ', 'alt_name', 'base_model', 'model_type'
    #                 ),
    #                 (
    #                     'disease', 'disease_trigger'
    #                 ),
    #                 (
    #                     'device', 'description',
    #                 ),
    #                 (
    #                     'mps', 'epa', 'tctc'
    #                 ),
    #                 (
    #                     'model_image'
    #                 ),
    #                 (
    #                     'references'
    #                 )
    #             )
    #         }
    #     ),
    #     (
    #         'Change Tracking', {
    #             'fields': (
    #                 'locked',
    #                 ('created_by', 'created_on'),
    #                 ('modified_by', 'modified_on'),
    #                 ('signed_off_by', 'signed_off_date'),
    #             )
    #         }
    #     )
    # )

    actions = ['update_fields']
    save_on_top = True
    inlines = [ValidatedAssayInline, OrganModelProtocolInline]

admin.site.register(OrganModel, OrganModelAdmin)


class GroupDeferralAdmin(TrackableAdmin):
    """Admin for Manufacturers"""
    form = GroupDeferralForm
    save_on_top = True
    list_per_page = 300
    list_display = ['group', 'approval_file', 'notes']
    fieldsets = (
        (
            None, {
                'fields': (
                'group',
                'approval_file',
                'notes',
                )
            }
        ),
        (
            'Change Tracking', {
                'fields': (
                    ('created_by', 'created_on'),
                    ('modified_by', 'modified_on'),
                    ('signed_off_by', 'signed_off_date'),
                )
            }
        ),
    )

admin.site.register(GroupDeferral, GroupDeferralAdmin)
