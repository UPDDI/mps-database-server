# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compounds', '0007'),
    ]

    operations = [
        migrations.AddField(
            model_name='compound',
            name='tctc',
            field=models.BooleanField(default=False, help_text=b'Whether this compound is part of the TCTC project'),
        ),
    ]
