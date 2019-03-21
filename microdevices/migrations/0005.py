# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('microdevices', '0004'),
    ]

    operations = [
        migrations.AddField(
            model_name='organmodel',
            name='epa',
            field=models.BooleanField(default=False, help_text=b'Whether this compound is part of the EPA project'),
        ),
        migrations.AddField(
            model_name='organmodel',
            name='mps',
            field=models.BooleanField(default=False, help_text=b'Whether this compound is part of the MPS project'),
        ),
    ]
