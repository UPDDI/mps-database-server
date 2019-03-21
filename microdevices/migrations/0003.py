# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('microdevices', '0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganModelProtocol',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.CharField(max_length=20)),
                ('file', models.FileField(upload_to=b'protocols', verbose_name=b'Protocol File')),
                ('organ_model', models.ForeignKey(verbose_name=b'Organ Model', to='microdevices.OrganModel', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='organmodel',
            name='protocol',
        ),
        migrations.AlterField(
            model_name='organmodel',
            name='device',
            field=models.ForeignKey(to='microdevices.Microdevice', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='microdevice',
            name='device_fluid_volume_unit',
        ),
        migrations.AlterField(
            model_name='microdevice',
            name='device_fluid_volume',
            field=models.FloatField(null=True, verbose_name=b'device fluid volume (uL)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='organmodelprotocol',
            unique_together=set([('version', 'organ_model')]),
        ),
    ]
