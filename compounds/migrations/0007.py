# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compounds', '0006'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='compound',
            name='medchem_friendly',
        ),
    ]
