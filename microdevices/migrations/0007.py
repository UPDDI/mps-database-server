# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('microdevices', '0006'),
    ]

    operations = [
        migrations.AddField(
            model_name='organmodel',
            name='tctc',
            field=models.BooleanField(default=False, help_text=b'Whether this compound is part of the TCTC project'),
        ),
    ]
