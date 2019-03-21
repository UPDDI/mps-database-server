# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bioactivities', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PubChemAssay',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('source', models.TextField(default=b'', null=True, blank=True)),
                ('source_id', models.TextField(default=b'', null=True, blank=True)),
                ('target_type', models.TextField(default=b'', null=True, blank=True)),
                ('organism', models.TextField(default=b'', null=True, blank=True)),
                ('aid', models.TextField(verbose_name=b'Assay ID')),
                ('name', models.TextField(default=b'', null=True, verbose_name=b'Assay Name', blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='pubchemassay_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='pubchemassay_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='pubchemassay_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='pubchembioactivity',
            name='assay_id',
        ),
        migrations.RemoveField(
            model_name='pubchembioactivity',
            name='assay_name',
        ),
        migrations.RemoveField(
            model_name='pubchembioactivity',
            name='source',
        ),
        migrations.AddField(
            model_name='pubchembioactivity',
            name='assay',
            field=models.ForeignKey(blank=True, to='bioactivities.PubChemAssay', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
