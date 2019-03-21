# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0016'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assaychipcells',
            name='cell_passage',
            field=models.CharField(default=b'', max_length=16, verbose_name=b'Passage#', blank=True),
        ),
        migrations.AlterField(
            model_name='assaychipreadout',
            name='notebook',
            field=models.CharField(default=b'', max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='assaychipreadout',
            name='notes',
            field=models.CharField(default=b'', max_length=2048, blank=True),
        ),
        migrations.AlterField(
            model_name='assaychipreadout',
            name='reason_for_flag',
            field=models.CharField(default=b'', help_text=b'Reason for why this entry was flagged', max_length=300, blank=True),
        ),
        migrations.AlterField(
            model_name='assaychipreadout',
            name='scientist',
            field=models.CharField(default=b'', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='assaychipresult',
            name='severity',
            field=models.CharField(default=b'-1', max_length=5, verbose_name=b'Severity', blank=True, choices=[(b'-1', b'UNKNOWN'), (b'0', b'NEGATIVE'), (b'1', b'+'), (b'2', b'+ +'), (b'3', b'+ + +'), (b'4', b'+ + + +'), (b'5', b'+ + + + +')]),
        ),
        migrations.AlterField(
            model_name='assaychipsetup',
            name='notebook',
            field=models.CharField(default=b'', max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='assaychipsetup',
            name='notes',
            field=models.CharField(default=b'', max_length=2048, blank=True),
        ),
        migrations.AlterField(
            model_name='assaychipsetup',
            name='reason_for_flag',
            field=models.CharField(default=b'', help_text=b'Reason for why this entry was flagged', max_length=300, blank=True),
        ),
        migrations.AlterField(
            model_name='assaychipsetup',
            name='scientist',
            field=models.CharField(default=b'', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='assaychipsetup',
            name='variance',
            field=models.CharField(default=b'', max_length=3000, verbose_name=b'Variance from Protocol', blank=True),
        ),
        migrations.AlterField(
            model_name='assaychiptestresult',
            name='reason_for_flag',
            field=models.CharField(default=b'', help_text=b'Reason for why this entry was flagged', max_length=300, blank=True),
        ),
        migrations.AlterField(
            model_name='assaylayout',
            name='reason_for_flag',
            field=models.CharField(default=b'', help_text=b'Reason for why this entry was flagged', max_length=300, blank=True),
        ),
        migrations.AlterField(
            model_name='assaymodel',
            name='assay_description',
            field=models.TextField(default=b'', verbose_name=b'Description', blank=True),
        ),
        migrations.AlterField(
            model_name='assaymodel',
            name='assay_short_name',
            field=models.CharField(default=b'', unique=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='assaymodel',
            name='version_number',
            field=models.CharField(default=b'', max_length=200, verbose_name=b'Version', blank=True),
        ),
        migrations.AlterField(
            model_name='assaymodeltype',
            name='assay_type_description',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='assayplatecells',
            name='cell_passage',
            field=models.CharField(default=b'', max_length=16, verbose_name=b'Passage#', blank=True),
        ),
        migrations.AlterField(
            model_name='assayplatereadout',
            name='notebook',
            field=models.CharField(default=b'', max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='assayplatereadout',
            name='notes',
            field=models.CharField(default=b'', max_length=2048, blank=True),
        ),
        migrations.AlterField(
            model_name='assayplatereadout',
            name='reason_for_flag',
            field=models.CharField(default=b'', help_text=b'Reason for why this entry was flagged', max_length=300, blank=True),
        ),
        migrations.AlterField(
            model_name='assayplatereadout',
            name='scientist',
            field=models.CharField(default=b'', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='assayplateresult',
            name='severity',
            field=models.CharField(default=b'-1', max_length=5, verbose_name=b'Severity', blank=True, choices=[(b'-1', b'UNKNOWN'), (b'0', b'NEGATIVE'), (b'1', b'+'), (b'2', b'+ +'), (b'3', b'+ + +'), (b'4', b'+ + + +'), (b'5', b'+ + + + +')]),
        ),
        migrations.AlterField(
            model_name='assayplatesetup',
            name='notebook',
            field=models.CharField(default=b'', max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='assayplatesetup',
            name='notes',
            field=models.CharField(default=b'', max_length=2048, blank=True),
        ),
        migrations.AlterField(
            model_name='assayplatesetup',
            name='reason_for_flag',
            field=models.CharField(default=b'', help_text=b'Reason for why this entry was flagged', max_length=300, blank=True),
        ),
        migrations.AlterField(
            model_name='assayplatesetup',
            name='scientist',
            field=models.CharField(default=b'', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='assayplatetestresult',
            name='reason_for_flag',
            field=models.CharField(default=b'', help_text=b'Reason for why this entry was flagged', max_length=300, blank=True),
        ),
        migrations.AlterField(
            model_name='assayresultfunction',
            name='description',
            field=models.CharField(default=b'', max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='assayresultfunction',
            name='function_results',
            field=models.CharField(default=b'', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='assayresulttype',
            name='description',
            field=models.CharField(default=b'', max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='assayrun',
            name='description',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='assaywelltype',
            name='well_description',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='physicalunits',
            name='availability',
            field=models.CharField(default=b'', help_text='Type a series of strings for indicating where this unit should be listed:\ntest = test results\nreadouts = readouts', max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='physicalunits',
            name='description',
            field=models.CharField(default=b'', max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='studyconfiguration',
            name='hardware_description',
            field=models.CharField(default=b'', max_length=1000, blank=True),
        ),
        migrations.AlterField(
            model_name='studyconfiguration',
            name='media_composition',
            field=models.CharField(default=b'', max_length=1000, blank=True),
        ),
        migrations.AlterField(
            model_name='studymodel',
            name='output',
            field=models.CharField(default=b'', max_length=20, blank=True),
        ),
        migrations.AlterField(
            model_name='unittype',
            name='description',
            field=models.CharField(default=b'', max_length=256, blank=True),
        ),
    ]
