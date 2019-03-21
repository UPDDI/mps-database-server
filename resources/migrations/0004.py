# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('resources', '0003'),
    ]

    operations = [
        migrations.AddField(
            model_name='definition',
            name='created_by',
            field=models.ForeignKey(related_name='definition_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='definition',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='definition',
            name='locked',
            field=models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.'),
        ),
        migrations.AddField(
            model_name='definition',
            name='modified_by',
            field=models.ForeignKey(related_name='definition_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='definition',
            name='modified_on',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='definition',
            name='signed_off_by',
            field=models.ForeignKey(related_name='definition_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='definition',
            name='signed_off_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='definition',
            name='definition',
            field=models.CharField(default=b'', max_length=2500),
        ),
    ]
