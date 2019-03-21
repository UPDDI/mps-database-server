# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0013'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='physicalunits',
            name='unit_type',
        ),
        migrations.RenameField(
            model_name='physicalunits',
            old_name='unit_type_fk',
            new_name='unit_type'
        ),
    ]
