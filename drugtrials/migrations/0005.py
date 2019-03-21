# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drugtrials', '0004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drugtrial',
            name='description',
            field=models.CharField(default=b'', max_length=1400, blank=True),
        ),
        migrations.AlterField(
            model_name='finding',
            name='description',
            field=models.CharField(default=b'', max_length=400, blank=True),
        ),
        migrations.AlterField(
            model_name='finding',
            name='finding_unit',
            field=models.CharField(default=b'', max_length=40, blank=True),
        ),
        migrations.AlterField(
            model_name='findingresult',
            name='severity',
            field=models.CharField(default=b'-1', max_length=5, verbose_name=b'Severity', blank=True, choices=[(b'-1', b'UNKNOWN'), (b'0', b'NEGATIVE'), (b'1', b'+'), (b'2', b'+ +'), (b'3', b'+ + +'), (b'4', b'+ + + +'), (b'5', b'+ + + + +')]),
        ),
        migrations.AlterField(
            model_name='findingtype',
            name='description',
            field=models.CharField(default=b'', max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='openfdacompound',
            name='warnings',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='test',
            name='description',
            field=models.CharField(default=b'', max_length=400, blank=True),
        ),
        migrations.AlterField(
            model_name='test',
            name='test_unit',
            field=models.CharField(default=b'', max_length=40, blank=True),
        ),
        migrations.AlterField(
            model_name='testresult',
            name='result',
            field=models.CharField(default=b'1', max_length=8, verbose_name=b'Pos/Neg?', blank=True, choices=[(b'0', b'Neg'), (b'1', b'Pos')]),
        ),
        migrations.AlterField(
            model_name='testresult',
            name='severity',
            field=models.CharField(default=b'-1', max_length=5, verbose_name=b'Severity', blank=True, choices=[(b'-1', b'UNKNOWN'), (b'0', b'NEGATIVE'), (b'1', b'+'), (b'2', b'+ +'), (b'3', b'+ + +'), (b'4', b'+ + + +'), (b'5', b'+ + + + +')]),
        ),
        migrations.AlterField(
            model_name='testtype',
            name='description',
            field=models.CharField(default=b'', max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='trialsource',
            name='description',
            field=models.CharField(default=b'', max_length=400, blank=True),
        ),
    ]
