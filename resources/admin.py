from django.contrib import admin
# from django.contrib.admin.widgets import AdminURLFieldWidget
# from django.db.models import URLField
# from django.utils.safestring import mark_safe

from mps.base.admin import LockableAdmin
from resources.models import (
    Resource,
    ResourceType,
    ResourceSubtype,
    Definition
)
from resources.forms import (
    ResourceForm,
    ResourceTypeForm,
    ResourceSubtypeForm,
    DefinitionForm
)

from django.utils.safestring import mark_safe


class ResourceAdmin(LockableAdmin):
    """Admin for Resource"""
    form = ResourceForm
    save_on_top = True
    list_per_page = 300
    search_fields = ['resource_name']
    readonly_fields = ('created_by', 'created_on',
                       'modified_by', 'modified_on',)
    list_display = ('resource_name', 'type',
                    'resource_site', 'description',)
    fieldsets = (
        (
            None, {
                'fields': (
                    'type',
                    'resource_name',
                    'resource_website',
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
    def resource_site(self, obj):
        return '<a href="%s" target="_blank">%s</a>' % (obj.resource_website, obj.resource_website)
    resource_site.allow_tags = True


admin.site.register(Resource, ResourceAdmin)


class ResourceTypeAdmin(LockableAdmin):
    """Admin for Resource Type"""
    form = ResourceTypeForm
    save_on_top = True
    list_per_page = 300
    list_display = ('resource_subtype', 'resource_type_name', 'description')

    fieldsets = (
        (
            None, {
                'fields': (
                    'resource_subtype',
                    'resource_type_name',
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


admin.site.register(ResourceType, ResourceTypeAdmin)


class ResourceSubtypeAdmin(LockableAdmin):
    """Admin for Resource Subtype"""
    form = ResourceSubtypeForm
    save_on_top = True
    list_per_page = 300
    list_display = ('name', 'description')

    fieldsets = (
        (
            None, {
                'fields': (
                    'name',
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


admin.site.register(ResourceSubtype, ResourceSubtypeAdmin)


class DefinitionAdmin(LockableAdmin):
    """Admin for Definitions"""
    form = DefinitionForm
    save_on_top = True
    list_per_page = 300
    list_display = (
        'term',
        'definition',
        'show_url',
        'created_on',
        'modified_on'
    )
    search_fields = ['term', 'definition', 'reference']

    fieldsets = (
        (
            None, {
                'fields': (
                    'term',
                    'definition',
                    'reference',
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
        )
    )
    actions = ['update_fields']


admin.site.register(Definition, DefinitionAdmin)
