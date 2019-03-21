# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings

from assays.models import PHYSICAL_UNIT_TYPES

def fix_unit_types(apps, schema_editor):
    UnitType = apps.get_model("assays", "UnitType")
    PhysicalUnits = apps.get_model("assays", "PhysicalUnits")
        
    for abbreviation, unit_type in PHYSICAL_UNIT_TYPES:
        new_unit_type = UnitType(unit_type=unit_type,description=abbreviation)
        new_unit_type.save()
        
    for unit in PhysicalUnits.objects.all():
        current = unit.unit_type
        unit.unit_type_fk = UnitType.objects.filter(description=current)[0]
        unit.save()


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0012'),
    ]

    operations = [
        migrations.RunPython(
            fix_unit_types
        ),
    ]
