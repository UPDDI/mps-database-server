# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('microdevices', '0003'),
        ('assays', '0008'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assaychipsetup',
            name='device',
            field=models.ForeignKey(verbose_name=b'Organ Model Name', blank=True, to='microdevices.OrganModel', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.RenameField(
            model_name='assaychipsetup',
            old_name='device',
            new_name='organ_model'
        ),
        migrations.AddField(
            model_name='assaychipsetup',
            name='organ_model_protocol',
            field=models.ForeignKey(verbose_name=b'Organ Model Protocol', blank=True, to='microdevices.OrganModelProtocol', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychipsetup',
            name='device',
            field=models.ForeignKey(verbose_name=b'Device', to='microdevices.Microdevice', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assayrun',
            name='file',
            field=models.FileField(help_text=b'Protocol File for Study', upload_to=b'study_protocol', null=True, verbose_name=b'Protocol File', blank=True),
            preserve_default=True,
        ),
    ]
