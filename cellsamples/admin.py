# coding=utf-8

"""CellSamples Admin"""

from django.contrib import admin
from cellsamples.resource import CellSampleResource
from mps.base.admin import LockableAdmin
from cellsamples.models import (
    CellType,
    Organ,
    CellSubtype,
    CellSample,
    Biosensor,
    Supplier
)


class CellTypeAdmin(LockableAdmin):
    """Admin for Cell Type"""
    save_on_top = True
    list_display = ('organ', 'cell_type', 'species')

    fieldsets = (
        (
            None, {
                'fields': (
                    'cell_type',
                    'species',
                    'organ',
                )
            }
        ),
        ('Change Tracking', {
            'fields': (
                # 'locked',
                ('created_by', 'created_on'),
                ('modified_by', 'modified_on'),
                ('signed_off_by', 'signed_off_date'),
            )
        }
        ),
    )


admin.site.register(CellType, CellTypeAdmin)


class CellTypeInline(admin.TabularInline):
    """Admin Inline for Cell Type

    May be subject to deprecation
    """
    model = CellType

    fields = (('cell_type', 'species', 'locked'),)
    extra = 0

    class Media(object):
        css = {"all": ("css/hide_admin_original.css",)}


class OrganAdmin(LockableAdmin):
    """Admin for Organs"""

    class Media(object):
        js = ('js/inline_fix.js',)

    save_as = True
    save_on_top = True
    fieldsets = (
        (
            None, {
                'fields': (
                    'organ_name',
                )
            }
        ),
        ('Change Tracking', {
            'fields': (
                # 'locked',
                ('created_by', 'created_on'),
                ('modified_by', 'modified_on'),
                ('signed_off_by', 'signed_off_date'),
            )
        }
        ),
    )
    # May be deprecated in the future; seldom used
    inlines = [CellTypeInline]


admin.site.register(Organ, OrganAdmin)


class CellSubtypeAdmin(LockableAdmin):
    """Admin for Cell Subtypes"""
    save_on_top = True

    list_display = ('cell_subtype', 'cell_type')

    fieldsets = (
        (
            None, {
                'fields': (
                    'cell_subtype',
                    'cell_type'
                )
            }
        ),
        ('Change Tracking', {
            'fields': (
                # 'locked',
                ('created_by', 'created_on'),
                ('modified_by', 'modified_on'),
                ('signed_off_by', 'signed_off_date'),
            )
        }
        ),
    )


admin.site.register(CellSubtype, CellSubtypeAdmin)


class CellSampleAdmin(LockableAdmin):
    """Admin for Cell Samples"""
    resource_class = CellSampleResource
    date_hierarchy = 'receipt_date'

    save_on_top = True
    list_per_page = 300
    list_display = ('receipt_date', 'barcode', 'cell_type', 'cell_subtype',
                    'supplier',
                    'locked')

    search_fields = ['cell_type__cell_type',
                     'cell_subtype__cell_subtype',
                     'supplier__name',
                     'barcode',
                     'product_id']
    save_as = True
    fieldsets = (
        (None, {
            'fields': (
                ('cell_type', 'cell_subtype'),
                ('receipt_date'),
            )
        }),
        ('Supplier Information', {
            'fields': (
                ('supplier', 'product_id', 'barcode'),
                'cell_image',
                'notes',
            )
        }),
        ('Isolation Information', {
            'fields': ('isolation_datetime', ('isolation_method',
                       'isolation_notes'),)
        }),
        ('Patient Information', {
            'fields': (('patient_age', 'patient_gender',
                       'patient_condition'),)
        }),
        ('Cell Viability', {
            'fields': (('viable_count',
                       'percent_viability'),)
        }),
        ('Change Tracking', {
            'fields': (
                # 'locked',
                ('created_by', 'created_on'),
                ('modified_by', 'modified_on'),
                ('signed_off_by', 'signed_off_date'), )
        }),
        (
            'Flag for Review', {
                'fields': (
                    ('flagged', 'reason_for_flag',)
                )
            }
        ),
        (
            'Group Access', {
                'fields': (
                    'group',
                ),
            }
        ),
    )


admin.site.register(CellSample, CellSampleAdmin)


class BiosensorAdmin(LockableAdmin):
    """Admin for Biosensors"""
    save_on_top = True
    list_display = ('name', 'supplier',
                    'lot_number', 'product_id', 'description')
    list_per_page = 300
    fieldsets = (
        (
            None, {
                'fields': (
                    ('name', 'supplier', ),
                    ('product_id', 'lot_number', 'description',),
                )
            }
        ),
        ('Change Tracking', {
            'fields': (
                # 'locked',
                ('created_by', 'created_on'),
                ('modified_by', 'modified_on'),
                ('signed_off_by', 'signed_off_date'),
            )
        }
        ),
    )

admin.site.register(Biosensor, BiosensorAdmin)


class SupplierAdmin(LockableAdmin):
    """Admin for Cell Suppliers"""
    save_on_top = True
    list_display = ('name', 'phone', 'address')
    list_per_page = 300
    fieldsets = (
        (
            None, {
                'fields': (
                    'name',
                    'phone',
                    'address',
                )
            }
        ),
        ('Change Tracking', {
            'fields': (
                # 'locked',
                ('created_by', 'created_on'),
                ('modified_by', 'modified_on'),
                ('signed_off_by', 'signed_off_date'),
            )
        }
        ),
    )

admin.site.register(Supplier, SupplierAdmin)
