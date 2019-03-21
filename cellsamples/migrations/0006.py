# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cellsamples', '0005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cellsample',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group (Level 0)', to='auth.Group', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='cellsample',
            name='restricted',
            field=models.BooleanField(default=True, help_text=b'Check box to restrict to selected group. Unchecked sends to Level 3'),
        ),
    ]
