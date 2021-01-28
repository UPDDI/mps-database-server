from django.contrib import admin
from .models import Disease, DiseaseComponent

from mps.base.admin import LockableAdmin


class DiseaseAdmin(LockableAdmin):
    model = Disease

admin.site.register(Disease, DiseaseAdmin)


class DiseaseComponentAdmin(LockableAdmin):
    model = DiseaseComponent

admin.site.register(DiseaseComponent, DiseaseComponentAdmin)
