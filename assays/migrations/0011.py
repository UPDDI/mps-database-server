# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assays', '0010'),
    ]

    operations = [
        # Make devices required
        migrations.AlterField(
            model_name='assaychipsetup',
            name='device',
            field=models.ForeignKey(verbose_name=b'Device', to='microdevices.Microdevice', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        # Remove restriction on replicates in chip readout data
        migrations.AlterUniqueTogether(
            name='assaychiprawdata',
            unique_together=set([]),
        ),
        # Create Unit Type model
        migrations.CreateModel(
            name='UnitType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('unit_type', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=256, null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='unittype_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='unittype_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='unittype_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
