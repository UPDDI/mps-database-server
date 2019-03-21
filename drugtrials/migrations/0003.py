# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('drugtrials', '0002'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='drugtrial',
            options={'ordering': ('compound', 'species'), 'verbose_name': 'Drug Trial'},
        ),
        migrations.AlterModelOptions(
            name='openfdacompound',
            options={'verbose_name': 'OpenFDA Report'},
        ),
        migrations.AlterField(
            model_name='findingresult',
            name='time_units',
            field=models.ForeignKey(related_name='finding_time_units', blank=True, to='assays.PhysicalUnits', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='findingresult',
            name='value_units',
            field=models.ForeignKey(related_name='finding_value_units', blank=True, to='assays.PhysicalUnits', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='testresult',
            name='time_units',
            field=models.ForeignKey(related_name='test_time_units', blank=True, to='assays.PhysicalUnits', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='testresult',
            name='value_units',
            field=models.ForeignKey(related_name='test_value_units', blank=True, to='assays.PhysicalUnits', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
