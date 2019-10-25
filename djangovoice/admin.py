from django.contrib import admin
from djangovoice.models import Feedback, Status, Type

from import_export.admin import ImportExportModelAdmin


class SlugFieldAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}


class FeedbackAdmin(ImportExportModelAdmin):
    list_display = [
        '__str__',
        'type',
        'status',
        # 'duplicate',
        # 'anonymous',
        'private',
        'user',
        'description',
        # 'email'
    ]
    list_filter = ['type', 'status', 'private']
    list_editable = ['type', 'status', 'private']
    # REVISED
    # list_display = [
    #     '__str__', 'type', 'status', 'duplicate', 'anonymous', 'private',
    #     'user', 'email']
    # list_filter = ['type', 'status', 'anonymous', 'private']
    # list_editable = ['type', 'status', 'anonymous', 'private']


admin.site.register(Feedback, FeedbackAdmin)
admin.site.register([Status, Type], SlugFieldAdmin)
