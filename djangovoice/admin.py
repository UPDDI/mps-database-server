from django.contrib import admin
from djangovoice.models import Feedback, Status, Type

from import_export.admin import ImportExportModelAdmin
from import_export import resources


class SlugFieldAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}


class FeedbackResource(resources.ModelResource):
    class Meta:
        model = Feedback
        fields = (
            'title',
            'type__title',
            'status__title',
            # 'duplicate',
            # 'anonymous',
            'private',
            'user__username',
            'description',
            # 'email'
        )


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

    resource_class = FeedbackResource

    def get_queryset(self, request):
        queryset = super(FeedbackAdmin, self).get_queryset(request)
        return queryset.prefetch_related('user')


admin.site.register(Feedback, FeedbackAdmin)
admin.site.register([Status, Type], SlugFieldAdmin)
