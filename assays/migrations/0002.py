# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('microdevices', '0001_initial'),
        ('cellsamples', '0001_initial'),
        ('compounds', '0001_initial'),
        ('auth', '0001_initial'),
        ('assays', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='studymodel',
            name='organ',
            field=models.ForeignKey(to='microdevices.OrganModel'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='studymodel',
            name='study_configuration',
            field=models.ForeignKey(to='assays.StudyConfiguration'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='studyconfiguration',
            name='created_by',
            field=models.ForeignKey(related_name='studyconfiguration_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='studyconfiguration',
            name='modified_by',
            field=models.ForeignKey(related_name='studyconfiguration_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='studyconfiguration',
            name='signed_off_by',
            field=models.ForeignKey(related_name='studyconfiguration_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='readoutunit',
            name='created_by',
            field=models.ForeignKey(related_name='readoutunit_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='readoutunit',
            name='modified_by',
            field=models.ForeignKey(related_name='readoutunit_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='readoutunit',
            name='signed_off_by',
            field=models.ForeignKey(related_name='readoutunit_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='physicalunits',
            name='created_by',
            field=models.ForeignKey(related_name='physicalunits_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='physicalunits',
            name='modified_by',
            field=models.ForeignKey(related_name='physicalunits_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='physicalunits',
            name='signed_off_by',
            field=models.ForeignKey(related_name='physicalunits_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaywelltype',
            name='created_by',
            field=models.ForeignKey(related_name='assaywelltype_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaywelltype',
            name='modified_by',
            field=models.ForeignKey(related_name='assaywelltype_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaywelltype',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assaywelltype_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaywell',
            name='base_layout',
            field=models.ForeignKey(to='assays.AssayBaseLayout'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaywell',
            name='created_by',
            field=models.ForeignKey(related_name='assaywell_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaywell',
            name='modified_by',
            field=models.ForeignKey(related_name='assaywell_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaywell',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assaywell_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaywell',
            name='well_type',
            field=models.ForeignKey(to='assays.AssayWellType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='assaywell',
            unique_together=set([('base_layout', 'row', 'column')]),
        ),
        migrations.AddField(
            model_name='assaytimepoint',
            name='assay_layout',
            field=models.ForeignKey(to='assays.AssayLayout'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaytestresult',
            name='assay_device_readout',
            field=models.ForeignKey(verbose_name=b'Organ Chip Study', to='assays.AssayRun'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaytestresult',
            name='chip_setup',
            field=models.ForeignKey(verbose_name=b'Chip Setup', to='assays.AssayChipSetup', unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaytestresult',
            name='created_by',
            field=models.ForeignKey(related_name='assaytestresult_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaytestresult',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group', to='auth.Group'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaytestresult',
            name='modified_by',
            field=models.ForeignKey(related_name='assaytestresult_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaytestresult',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assaytestresult_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayrun',
            name='created_by',
            field=models.ForeignKey(related_name='assayrun_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayrun',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group', to='auth.Group'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayrun',
            name='modified_by',
            field=models.ForeignKey(related_name='assayrun_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayrun',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assayrun_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayrun',
            name='study_configuration',
            field=models.ForeignKey(blank=True, to='assays.StudyConfiguration', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayresulttype',
            name='created_by',
            field=models.ForeignKey(related_name='assayresulttype_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayresulttype',
            name='modified_by',
            field=models.ForeignKey(related_name='assayresulttype_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayresulttype',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assayresulttype_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayresultfunction',
            name='created_by',
            field=models.ForeignKey(related_name='assayresultfunction_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayresultfunction',
            name='modified_by',
            field=models.ForeignKey(related_name='assayresultfunction_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayresultfunction',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assayresultfunction_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayresult',
            name='assay_name',
            field=models.ForeignKey(verbose_name=b'Assay', to='assays.AssayChipReadoutAssay'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayresult',
            name='assay_result',
            field=models.ForeignKey(to='assays.AssayTestResult'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayresult',
            name='result_function',
            field=models.ForeignKey(verbose_name=b'Function', blank=True, to='assays.AssayResultFunction', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayresult',
            name='result_type',
            field=models.ForeignKey(verbose_name=b'Measure', blank=True, to='assays.AssayResultType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayresult',
            name='test_unit',
            field=models.ForeignKey(blank=True, to='assays.PhysicalUnits', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayreadout',
            name='assay_device_readout',
            field=models.ForeignKey(to='assays.AssayDeviceReadout'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayreader',
            name='created_by',
            field=models.ForeignKey(related_name='assayreader_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayreader',
            name='modified_by',
            field=models.ForeignKey(related_name='assayreader_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayreader',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assayreader_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatetestresult',
            name='assay_device_id',
            field=models.ForeignKey(verbose_name=b'Plate ID/ Barcode', to='assays.AssayDeviceReadout'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatetestresult',
            name='created_by',
            field=models.ForeignKey(related_name='assayplatetestresult_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatetestresult',
            name='modified_by',
            field=models.ForeignKey(related_name='assayplatetestresult_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatetestresult',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assayplatetestresult_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatetestresult',
            name='time_units',
            field=models.ForeignKey(blank=True, to='assays.TimeUnits', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatetestresult',
            name='value_units',
            field=models.ForeignKey(blank=True, to='assays.PhysicalUnits', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaymodeltype',
            name='created_by',
            field=models.ForeignKey(related_name='assaymodeltype_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaymodeltype',
            name='modified_by',
            field=models.ForeignKey(related_name='assaymodeltype_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaymodeltype',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assaymodeltype_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaymodel',
            name='assay_type',
            field=models.ForeignKey(to='assays.AssayModelType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaymodel',
            name='created_by',
            field=models.ForeignKey(related_name='assaymodel_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaymodel',
            name='modified_by',
            field=models.ForeignKey(related_name='assaymodel_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaymodel',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assaymodel_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaylayoutformat',
            name='created_by',
            field=models.ForeignKey(related_name='assaylayoutformat_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaylayoutformat',
            name='device',
            field=models.ForeignKey(to='microdevices.Microdevice'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaylayoutformat',
            name='modified_by',
            field=models.ForeignKey(related_name='assaylayoutformat_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaylayoutformat',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assaylayoutformat_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaylayout',
            name='base_layout',
            field=models.ForeignKey(to='assays.AssayBaseLayout'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaylayout',
            name='created_by',
            field=models.ForeignKey(related_name='assaylayout_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaylayout',
            name='modified_by',
            field=models.ForeignKey(related_name='assaylayout_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaylayout',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assaylayout_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaydevicereadout',
            name='assay_layout',
            field=models.ForeignKey(to='assays.AssayLayout'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaydevicereadout',
            name='assay_name',
            field=models.ForeignKey(verbose_name=b'Assay', to='assays.AssayModel', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaydevicereadout',
            name='cell_sample',
            field=models.ForeignKey(to='cellsamples.CellSample'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaydevicereadout',
            name='created_by',
            field=models.ForeignKey(related_name='assaydevicereadout_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaydevicereadout',
            name='modified_by',
            field=models.ForeignKey(related_name='assaydevicereadout_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaydevicereadout',
            name='reader_name',
            field=models.ForeignKey(verbose_name=b'Reader', to='assays.AssayReader'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaydevicereadout',
            name='readout_unit',
            field=models.ForeignKey(to='assays.ReadoutUnit'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaydevicereadout',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assaydevicereadout_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaydevicereadout',
            name='timeunit',
            field=models.ForeignKey(to='assays.TimeUnits'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaycompound',
            name='assay_layout',
            field=models.ForeignKey(to='assays.AssayLayout'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaycompound',
            name='compound',
            field=models.ForeignKey(to='compounds.Compound'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipsetup',
            name='assay_run_id',
            field=models.ForeignKey(verbose_name=b'Organ Chip Study', to='assays.AssayRun'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipsetup',
            name='compound',
            field=models.ForeignKey(blank=True, to='compounds.Compound', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipsetup',
            name='created_by',
            field=models.ForeignKey(related_name='assaychipsetup_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipsetup',
            name='device',
            field=models.ForeignKey(verbose_name=b'Organ Model Name', to='microdevices.OrganModel'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipsetup',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group', to='auth.Group'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipsetup',
            name='modified_by',
            field=models.ForeignKey(related_name='assaychipsetup_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipsetup',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assaychipsetup_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipsetup',
            name='unit',
            field=models.ForeignKey(default=4, blank=True, to='assays.PhysicalUnits', null=True, verbose_name=b'conc. Unit'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipreadoutassay',
            name='assay_id',
            field=models.ForeignKey(verbose_name=b'Assay', to='assays.AssayModel', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipreadoutassay',
            name='reader_id',
            field=models.ForeignKey(verbose_name=b'Reader', to='assays.AssayReader'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipreadoutassay',
            name='readout_id',
            field=models.ForeignKey(verbose_name=b'Readout', to='assays.AssayChipReadout'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipreadoutassay',
            name='readout_unit',
            field=models.ForeignKey(to='assays.ReadoutUnit'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='assaychipreadoutassay',
            unique_together=set([('readout_id', 'assay_id')]),
        ),
        migrations.AddField(
            model_name='assaychipreadout',
            name='chip_setup',
            field=models.ForeignKey(null=True, to='assays.AssayChipSetup', unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipreadout',
            name='created_by',
            field=models.ForeignKey(related_name='assaychipreadout_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipreadout',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group', to='auth.Group'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipreadout',
            name='modified_by',
            field=models.ForeignKey(related_name='assaychipreadout_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipreadout',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assaychipreadout_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipreadout',
            name='timeunit',
            field=models.ForeignKey(default=3, to='assays.TimeUnits'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychiprawdata',
            name='assay_chip_id',
            field=models.ForeignKey(to='assays.AssayChipReadout'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychiprawdata',
            name='assay_id',
            field=models.ForeignKey(to='assays.AssayChipReadoutAssay'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='assaychiprawdata',
            unique_together=set([('assay_chip_id', 'assay_id', 'field_id', 'elapsed_time')]),
        ),
        migrations.AddField(
            model_name='assaychipcells',
            name='assay_chip',
            field=models.ForeignKey(to='assays.AssayChipSetup'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipcells',
            name='cell_biosensor',
            field=models.ForeignKey(blank=True, to='cellsamples.Biosensor', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipcells',
            name='cell_sample',
            field=models.ForeignKey(to='cellsamples.CellSample'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaybaselayout',
            name='created_by',
            field=models.ForeignKey(related_name='assaybaselayout_created-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaybaselayout',
            name='layout_format',
            field=models.ForeignKey(to='assays.AssayLayoutFormat'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaybaselayout',
            name='modified_by',
            field=models.ForeignKey(related_name='assaybaselayout_modified-by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaybaselayout',
            name='signed_off_by',
            field=models.ForeignKey(related_name='assaybaselayout_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
