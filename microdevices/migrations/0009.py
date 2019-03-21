# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('microdevices', '0008'),
    ]

    operations = [
        migrations.AlterField(
            model_name='microdevice',
            name='number_of_columns',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='microdevice',
            name='number_of_rows',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(100)]),
        ),
    ]
