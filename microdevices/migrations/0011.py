# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
        ('microdevices', '0010'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupDeferral',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('notes', models.CharField(max_length=1024)),
                ('approval_file', models.FileField(null=True, upload_to=b'deferral', blank=True)),
                ('created_by', models.ForeignKey(related_name='groupdeferral_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('group', models.ForeignKey(to='auth.Group', on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='groupdeferral_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='groupdeferral_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='microdevice',
            name='references',
            field=models.CharField(default=b'', max_length=2000, blank=True),
        ),
        migrations.AddField(
            model_name='organmodel',
            name='references',
            field=models.CharField(default=b'', max_length=2000, blank=True),
        ),
        migrations.AlterField(
            model_name='manufacturer',
            name='manufacturer_name',
            field=models.CharField(unique=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='microdevice',
            name='description',
            field=models.CharField(default=b'', max_length=4000, blank=True),
        ),
        migrations.AlterField(
            model_name='microdevice',
            name='device_name',
            field=models.CharField(unique=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='microphysiologycenter',
            name='center_id',
            field=models.CharField(unique=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='microphysiologycenter',
            name='center_name',
            field=models.CharField(unique=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='microphysiologycenter',
            name='description',
            field=models.CharField(default=b'', max_length=4000, blank=True),
        ),
        migrations.AlterField(
            model_name='microphysiologycenter',
            name='groups',
            field=models.ManyToManyField(help_text=b'***PLEASE DO NOT INCLUDE "Admin" OR "Viewer": ONLY SELECT THE BASE GROUP (ie "Taylor_MPS" NOT "Taylor_MPS Admin")***<br>', to='auth.Group', blank=True),
        ),
        migrations.AlterField(
            model_name='organmodel',
            name='description',
            field=models.CharField(default=b'', max_length=4000, blank=True),
        ),
        migrations.AlterField(
            model_name='organmodel',
            name='model_name',
            field=models.CharField(unique=True, max_length=200),
        ),
    ]
