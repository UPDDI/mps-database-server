# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0017'),
    ]

    operations = [
        migrations.RenameField(
            model_name='assayrun',
            old_name='file',
            new_name='protocol',
        ),
        migrations.RemoveField(
            model_name='studyconfiguration',
            name='study_format',
        ),
        migrations.AddField(
            model_name='assayrun',
            name='supporting_data',
            field=models.FileField(help_text=b'Supporting Data for Study', null=True, upload_to=b'supporting_data', blank=True),
        ),
        migrations.AlterField(
            model_name='assaychipsetup',
            name='chip_test_type',
            field=models.CharField(default=b'control', max_length=8, choices=[(b'control', b'Control'), (b'compound', b'Compound')]),
        ),
        migrations.AlterField(
            model_name='studymodel',
            name='integration_mode',
            field=models.CharField(default=b'1', max_length=13, choices=[(b'0', b'Functional'), (b'1', b'Physical')]),
        ),
    ]
