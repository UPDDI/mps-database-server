# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('compounds', '0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cellsamples', '0002'),
        ('microdevices', '0002'),
        ('assays', '0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssayChipResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('result', models.CharField(default=b'1', max_length=8, verbose_name=b'Pos/Neg?', choices=[(b'0', b'Negative'), (b'1', b'Positive'), (b'x', b'Failed')])),
                ('severity', models.CharField(default=b'-1', choices=[(b'-1', b'UNKNOWN'), (b'0', b'NEGATIVE'), (b'1', b'+'), (b'2', b'+ +'), (b'3', b'+ + +'), (b'4', b'+ + + +'), (b'5', b'+ + + + +')], max_length=5, blank=True, null=True, verbose_name=b'Severity')),
                ('value', models.FloatField(null=True, blank=True)),
                ('assay_name', models.ForeignKey(verbose_name=b'Assay', to='assays.AssayChipReadoutAssay', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayChipTestResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('restricted', models.BooleanField(default=True, help_text=b'Check box to restrict to selected group')),
                ('flagged', models.BooleanField(default=False, help_text=b'Check box to flag for review')),
                ('reason_for_flag', models.CharField(help_text=b'Reason for why this entry was flagged', max_length=300, null=True, blank=True)),
                ('chip_readout', models.ForeignKey(verbose_name=b'Chip Readout', to='assays.AssayChipReadout', on_delete=models.CASCADE)),
                ('created_by', models.ForeignKey(related_name='assaychiptestresult_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('group', models.ForeignKey(help_text=b'Bind to a group', to='auth.Group', on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='assaychiptestresult_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='assaychiptestresult_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Chip Result',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayPlateCells',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cellsample_density', models.FloatField(default=0, verbose_name=b'density')),
                ('cellsample_density_unit', models.CharField(default=b'WE', max_length=8, verbose_name=b'Unit', choices=[(b'WE', b'cells / well'), (b'ML', b'cells / mL'), (b'MM', b'cells / mm^2')])),
                ('cell_passage', models.CharField(default=b'-', max_length=16, verbose_name=b'Passage#')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayPlateReadout',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('restricted', models.BooleanField(default=True, help_text=b'Check box to restrict to selected group')),
                ('flagged', models.BooleanField(default=False, help_text=b'Check box to flag for review')),
                ('reason_for_flag', models.CharField(help_text=b'Reason for why this entry was flagged', max_length=300, null=True, blank=True)),
                ('treatment_time_length', models.FloatField(null=True, verbose_name=b'Treatment Duration', blank=True)),
                ('readout_start_time', models.DateField(help_text=b'YYYY-MM-DD', verbose_name=b'Readout Date')),
                ('notebook', models.CharField(max_length=256, null=True, blank=True)),
                ('notebook_page', models.IntegerField(null=True, blank=True)),
                ('notes', models.CharField(max_length=2048, null=True, blank=True)),
                ('scientist', models.CharField(max_length=100, null=True, blank=True)),
                ('file', models.FileField(upload_to=b'csv', null=True, verbose_name=b'Data File', blank=True)),
                ('created_by', models.ForeignKey(related_name='assayplatereadout_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('group', models.ForeignKey(help_text=b'Bind to a group', to='auth.Group', on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='assayplatereadout_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Plate Readout',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayPlateReadoutAssay',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('feature', models.CharField(max_length=150)),
                ('assay_id', models.ForeignKey(verbose_name=b'Assay', to='assays.AssayModel', null=True, on_delete=models.CASCADE)),
                ('reader_id', models.ForeignKey(verbose_name=b'Reader', to='assays.AssayReader', on_delete=models.CASCADE)),
                ('readout_id', models.ForeignKey(verbose_name=b'Readout', to='assays.AssayPlateReadout', on_delete=models.CASCADE)),
                ('readout_unit', models.ForeignKey(to='assays.ReadoutUnit', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayPlateResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('result', models.CharField(default=b'1', max_length=8, verbose_name=b'Result', choices=[(b'0', b'Negative'), (b'1', b'Positive'), (b'x', b'Failed')])),
                ('severity', models.CharField(default=b'-1', choices=[(b'-1', b'UNKNOWN'), (b'0', b'NEGATIVE'), (b'1', b'+'), (b'2', b'+ +'), (b'3', b'+ + +'), (b'4', b'+ + + +'), (b'5', b'+ + + + +')], max_length=5, blank=True, null=True, verbose_name=b'Severity')),
                ('value', models.FloatField(null=True, blank=True)),
                ('assay_name', models.ForeignKey(verbose_name=b'Assay', to='assays.AssayPlateReadoutAssay', on_delete=models.CASCADE)),
                ('assay_result', models.ForeignKey(to='assays.AssayPlateTestResult', on_delete=models.CASCADE)),
                ('result_function', models.ForeignKey(verbose_name=b'Function', blank=True, to='assays.AssayResultFunction', null=True, on_delete=models.CASCADE)),
                ('result_type', models.ForeignKey(verbose_name=b'Measure', blank=True, to='assays.AssayResultType', null=True, on_delete=models.CASCADE)),
                ('test_unit', models.ForeignKey(blank=True, to='assays.PhysicalUnits', null=True, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayPlateSetup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('restricted', models.BooleanField(default=True, help_text=b'Check box to restrict to selected group')),
                ('flagged', models.BooleanField(default=False, help_text=b'Check box to flag for review')),
                ('reason_for_flag', models.CharField(help_text=b'Reason for why this entry was flagged', max_length=300, null=True, blank=True)),
                ('setup_date', models.DateField(help_text=b'YYYY-MM-DD')),
                ('assay_plate_id', models.CharField(max_length=512, verbose_name=b'Plate ID/ Barcode')),
                ('scientist', models.CharField(max_length=100, null=True, blank=True)),
                ('notebook', models.CharField(max_length=256, null=True, blank=True)),
                ('notebook_page', models.IntegerField(null=True, blank=True)),
                ('notes', models.CharField(max_length=2048, null=True, blank=True)),
                ('assay_layout', models.ForeignKey(verbose_name=b'Assay Layout', to='assays.AssayLayout', on_delete=models.CASCADE)),
                ('assay_run_id', models.ForeignKey(verbose_name=b'Study', to='assays.AssayRun', on_delete=models.CASCADE)),
                ('created_by', models.ForeignKey(related_name='assayplatesetup_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('group', models.ForeignKey(help_text=b'Bind to a group', to='auth.Group', on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='assayplatesetup_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='assayplatesetup_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Plate Setup',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayWellCompound',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('concentration', models.FloatField(default=0)),
                ('row', models.CharField(max_length=25)),
                ('column', models.CharField(max_length=25)),
                ('assay_layout', models.ForeignKey(to='assays.AssayLayout', on_delete=models.CASCADE)),
                ('compound', models.ForeignKey(to='compounds.Compound', on_delete=models.CASCADE)),
                ('concentration_unit', models.ForeignKey(to='assays.PhysicalUnits', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayWellLabel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=150)),
                ('row', models.CharField(max_length=25)),
                ('column', models.CharField(max_length=25)),
                ('assay_layout', models.ForeignKey(to='assays.AssayLayout', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayWellTimepoint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timepoint', models.FloatField(default=0)),
                ('row', models.CharField(max_length=25)),
                ('column', models.CharField(max_length=25)),
                ('assay_layout', models.ForeignKey(to='assays.AssayLayout', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='assaybaselayout',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='assaybaselayout',
            name='layout_format',
        ),
        migrations.RemoveField(
            model_name='assaybaselayout',
            name='modified_by',
        ),
        migrations.RemoveField(
            model_name='assaybaselayout',
            name='signed_off_by',
        ),
        migrations.RemoveField(
            model_name='assaycompound',
            name='assay_layout',
        ),
        migrations.RemoveField(
            model_name='assaycompound',
            name='compound',
        ),
        migrations.DeleteModel(
            name='AssayCompound',
        ),
        migrations.RemoveField(
            model_name='assaydevicereadout',
            name='assay_layout',
        ),
        migrations.RemoveField(
            model_name='assaydevicereadout',
            name='assay_name',
        ),
        migrations.RemoveField(
            model_name='assaydevicereadout',
            name='cell_sample',
        ),
        migrations.RemoveField(
            model_name='assaydevicereadout',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='assaydevicereadout',
            name='modified_by',
        ),
        migrations.RemoveField(
            model_name='assaydevicereadout',
            name='reader_name',
        ),
        migrations.RemoveField(
            model_name='assaydevicereadout',
            name='readout_unit',
        ),
        migrations.RemoveField(
            model_name='assaydevicereadout',
            name='signed_off_by',
        ),
        migrations.RemoveField(
            model_name='assaydevicereadout',
            name='timeunit',
        ),
        migrations.RemoveField(
            model_name='assaylayoutformat',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='assaylayoutformat',
            name='device',
        ),
        migrations.RemoveField(
            model_name='assaylayoutformat',
            name='modified_by',
        ),
        migrations.RemoveField(
            model_name='assaylayoutformat',
            name='signed_off_by',
        ),
        migrations.DeleteModel(
            name='AssayLayoutFormat',
        ),
        migrations.RemoveField(
            model_name='assayresult',
            name='assay_name',
        ),
        migrations.RemoveField(
            model_name='assayresult',
            name='assay_result',
        ),
        migrations.RemoveField(
            model_name='assayresult',
            name='result_function',
        ),
        migrations.RemoveField(
            model_name='assayresult',
            name='result_type',
        ),
        migrations.RemoveField(
            model_name='assayresult',
            name='test_unit',
        ),
        migrations.DeleteModel(
            name='AssayResult',
        ),
        migrations.RemoveField(
            model_name='assaytestresult',
            name='assay_device_readout',
        ),
        migrations.RemoveField(
            model_name='assaytestresult',
            name='chip_setup',
        ),
        migrations.RemoveField(
            model_name='assaytestresult',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='assaytestresult',
            name='group',
        ),
        migrations.RemoveField(
            model_name='assaytestresult',
            name='modified_by',
        ),
        migrations.RemoveField(
            model_name='assaytestresult',
            name='signed_off_by',
        ),
        migrations.DeleteModel(
            name='AssayTestResult',
        ),
        migrations.RemoveField(
            model_name='assaytimepoint',
            name='assay_layout',
        ),
        migrations.DeleteModel(
            name='AssayTimepoint',
        ),
        migrations.AlterUniqueTogether(
            name='assayplatereadoutassay',
            unique_together=set([('readout_id', 'assay_id')]),
        ),
        migrations.AddField(
            model_name='assayplatereadout',
            name='setup',
            field=models.ForeignKey(to='assays.AssayPlateSetup', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatereadout',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assayplatereadout_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatereadout',
            name='timeunit',
            field=models.ForeignKey(default=23, to='assays.PhysicalUnits', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatecells',
            name='assay_plate',
            field=models.ForeignKey(to='assays.AssayPlateSetup', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatecells',
            name='cell_biosensor',
            field=models.ForeignKey(blank=True, to='cellsamples.Biosensor', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatecells',
            name='cell_sample',
            field=models.ForeignKey(to='cellsamples.CellSample', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipresult',
            name='assay_result',
            field=models.ForeignKey(to='assays.AssayChipTestResult', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipresult',
            name='result_function',
            field=models.ForeignKey(verbose_name=b'Function', blank=True, to='assays.AssayResultFunction', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipresult',
            name='result_type',
            field=models.ForeignKey(verbose_name=b'Measure', blank=True, to='assays.AssayResultType', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipresult',
            name='test_unit',
            field=models.ForeignKey(blank=True, to='assays.PhysicalUnits', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterModelOptions(
            name='assaylayout',
            options={'ordering': ('layout_name',), 'verbose_name': 'Assay Layout'},
        ),
        migrations.AlterModelOptions(
            name='assayplatetestresult',
            options={'verbose_name': 'Plate Result'},
        ),
        migrations.AlterModelOptions(
            name='assayrun',
            options={'ordering': ('assay_run_id',), 'verbose_name': 'Study', 'verbose_name_plural': 'Studies'},
        ),
        migrations.AlterModelOptions(
            name='studyconfiguration',
            options={'verbose_name': 'Study Configuration'},
        ),
        migrations.RemoveField(
            model_name='assaylayout',
            name='base_layout',
        ),
        migrations.RemoveField(
            model_name='assayplatetestresult',
            name='assay_device_id',
        ),
        migrations.RemoveField(
            model_name='assayplatetestresult',
            name='assay_test_time',
        ),
        migrations.RemoveField(
            model_name='assayplatetestresult',
            name='result',
        ),
        migrations.RemoveField(
            model_name='assayplatetestresult',
            name='severity',
        ),
        migrations.RemoveField(
            model_name='assayplatetestresult',
            name='time_units',
        ),
        migrations.RemoveField(
            model_name='assayplatetestresult',
            name='value',
        ),
        migrations.RemoveField(
            model_name='assayplatetestresult',
            name='value_units',
        ),
        migrations.AddField(
            model_name='assaylayout',
            name='device',
            field=models.ForeignKey(default=1, to='microdevices.Microdevice', on_delete=models.CASCADE),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='assaylayout',
            name='flagged',
            field=models.BooleanField(default=False, help_text=b'Check box to flag for review'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaylayout',
            name='group',
            field=models.ForeignKey(default=1, to='auth.Group', help_text=b'Bind to a group', on_delete=models.CASCADE),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='assaylayout',
            name='reason_for_flag',
            field=models.CharField(help_text=b'Reason for why this entry was flagged', max_length=300, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaylayout',
            name='restricted',
            field=models.BooleanField(default=True, help_text=b'Check box to restrict to selected group'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatetestresult',
            name='flagged',
            field=models.BooleanField(default=False, help_text=b'Check box to flag for review'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatetestresult',
            name='group',
            field=models.ForeignKey(default=1, to='auth.Group', help_text=b'Bind to a group', on_delete=models.CASCADE),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='assayplatetestresult',
            name='readout',
            field=models.ForeignKey(default=1, verbose_name=b'Plate ID/ Barcode', to='assays.AssayPlateReadout', on_delete=models.CASCADE),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='assayplatetestresult',
            name='reason_for_flag',
            field=models.CharField(help_text=b'Reason for why this entry was flagged', max_length=300, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatetestresult',
            name='restricted',
            field=models.BooleanField(default=True, help_text=b'Check box to restrict to selected group'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayreadout',
            name='assay',
            field=models.ForeignKey(default=1, to='assays.AssayPlateReadoutAssay', on_delete=models.CASCADE),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='assaywell',
            name='assay_layout',
            field=models.ForeignKey(default=1, to='assays.AssayLayout', on_delete=models.CASCADE),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='assaychipreadout',
            name='timeunit',
            field=models.ForeignKey(default=23, to='assays.PhysicalUnits', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assaychipreadoutassay',
            name='object_type',
            field=models.CharField(default=b'F', max_length=6, verbose_name=b'Object of Interest', choices=[(b'F', b'Field'), (b'C', b'Colony'), (b'M', b'Media'), (b'X', b'Other')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assaychipsetup',
            name='assay_run_id',
            field=models.ForeignKey(verbose_name=b'Study', to='assays.AssayRun', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assayreadout',
            name='assay_device_readout',
            field=models.ForeignKey(to='assays.AssayPlateReadout', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.DeleteModel(
            name='AssayDeviceReadout',
        ),
        migrations.AlterUniqueTogether(
            name='assaywell',
            unique_together=set([('assay_layout', 'row', 'column')]),
        ),
        migrations.RemoveField(
            model_name='assaywell',
            name='signed_off_date',
        ),
        migrations.RemoveField(
            model_name='assaywell',
            name='signed_off_by',
        ),
        migrations.RemoveField(
            model_name='assaywell',
            name='modified_on',
        ),
        migrations.RemoveField(
            model_name='assaywell',
            name='modified_by',
        ),
        migrations.RemoveField(
            model_name='assaywell',
            name='locked',
        ),
        migrations.RemoveField(
            model_name='assaywell',
            name='created_on',
        ),
        migrations.RemoveField(
            model_name='assaywell',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='assaywell',
            name='base_layout',
        ),
        migrations.DeleteModel(
            name='AssayBaseLayout',
        ),
    ]
