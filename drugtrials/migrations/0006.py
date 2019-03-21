# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drugtrials', '0005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drugtrial',
            name='age_unit',
            field=models.CharField(default=b'Y', max_length=1, blank=True, choices=[(b'M', b'months'), (b'Y', b'years')]),
        ),
        migrations.AlterField(
            model_name='drugtrial',
            name='condition',
            field=models.CharField(default=b'', max_length=1400, blank=True),
        ),
        migrations.AlterField(
            model_name='drugtrial',
            name='gender',
            field=models.CharField(default=b'U', max_length=1, blank=True, choices=[(b'F', b'female'), (b'M', b'male'), (b'X', b'mixed'), (b'U', b'unknown or unspecified')]),
        ),
        migrations.AlterField(
            model_name='drugtrial',
            name='population_size',
            field=models.CharField(default=b'1', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='drugtrial',
            name='references',
            field=models.CharField(default=b'', max_length=400, verbose_name=b'Trial ID/Reference'),
        ),
        migrations.AlterField(
            model_name='drugtrial',
            name='title',
            field=models.CharField(default=b'', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='drugtrial',
            name='weight_unit',
            field=models.CharField(default=b'L', max_length=1, blank=True, choices=[(b'K', b'kilograms'), (b'L', b'pounds')]),
        ),
        migrations.AlterField(
            model_name='findingresult',
            name='frequency',
            field=models.CharField(default=b'', max_length=25, blank=True, choices=[(b'>= 10%', b'>= 10% : Very Common'), (b'1 - < 10%', b'1 - < 10% : Common'), (b'0.1 - < 1%', b'0.1 - < 1% : Uncommon'), (b'0.01 - < 0.1%', b'0.01 - < 0.1% : Rare'), (b'< 0.01%', b'< 0.01% : Very Rare')]),
        ),
        migrations.AlterField(
            model_name='openfdacompound',
            name='nonclinical_toxicology',
            field=models.TextField(default=b'', blank=True),
        ),
    ]
