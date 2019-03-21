# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compounds', '0004'),
    ]

    operations = [
        migrations.AddField(
            model_name='compound',
            name='epa',
            field=models.BooleanField(default=False, help_text=b'Whether this compound is part of the EPA project'),
        ),
        migrations.AddField(
            model_name='compound',
            name='medchem_alerts',
            field=models.BooleanField(default=False, verbose_name=b'Inicates whether structural alerts are listed for this compound'),
        ),
        migrations.AddField(
            model_name='compound',
            name='mps',
            field=models.BooleanField(default=False, help_text=b'Whether this compound is part of the MPS project'),
        ),
    ]
