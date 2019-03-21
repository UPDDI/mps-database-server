# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('compounds', '0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompoundProperty',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.FloatField()),
                ('source', models.CharField(max_length=250)),
                ('compound', models.ForeignKey(to='compounds.Compound', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Compound Property',
                'verbose_name_plural': 'Compound Properties',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CompoundSummary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('summary', models.CharField(max_length=500)),
                ('source', models.CharField(max_length=250)),
                ('compound', models.ForeignKey(to='compounds.Compound', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Compound Summary',
                'verbose_name_plural': 'Compound Summaries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PropertyType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(default=b'', max_length=500)),
                ('created_by', models.ForeignKey(related_name='propertytype_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='propertytype_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='propertytype_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Compound Property Type',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SummaryType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(default=b'', max_length=500)),
                ('created_by', models.ForeignKey(related_name='summarytype_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='summarytype_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='summarytype_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Summary Type',
                'verbose_name_plural': 'Summary Types',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='compoundsummary',
            name='summary_type',
            field=models.ForeignKey(to='compounds.SummaryType', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='compoundsummary',
            unique_together=set([('compound', 'summary_type')]),
        ),
        migrations.AddField(
            model_name='compoundproperty',
            name='property_type',
            field=models.ForeignKey(to='compounds.PropertyType', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='compoundproperty',
            unique_together=set([('compound', 'property_type')]),
        ),
    ]
