# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('resource_name', models.CharField(unique=True, max_length=60, verbose_name=b'Name')),
                ('resource_website', models.URLField(null=True, blank=True)),
                ('description', models.CharField(max_length=400, null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='resource_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='resource_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='resource_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['type', 'resource_name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResourceSubtype',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('name', models.TextField(unique=True, max_length=40, verbose_name=b'Category')),
                ('description', models.TextField(max_length=400, null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='resourcesubtype_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='resourcesubtype_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='resourcesubtype_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Resource category',
                'verbose_name_plural': 'Resource categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResourceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('resource_type_name', models.CharField(unique=True, max_length=40, verbose_name=b'Type')),
                ('description', models.CharField(max_length=400, null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='resourcetype_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='resourcetype_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('resource_subtype', models.ForeignKey(verbose_name=b'Category', to='resources.ResourceSubtype', on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='resourcetype_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['resource_subtype', 'resource_type_name'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='resource',
            name='type',
            field=models.ForeignKey(to='resources.ResourceType', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
