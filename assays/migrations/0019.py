# -*- coding: utf-8 -*-


from django.db import migrations, models
import assays.models


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0018'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudySupportingData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(help_text=b'Describes the contents of the supporting data file', max_length=1000)),
                ('supporting_data', models.FileField(help_text=b'Supporting Data for Study', upload_to=assays.models.study_supporting_data_location)),
            ],
        ),
        migrations.RemoveField(
            model_name='assayrun',
            name='supporting_data',
        ),
        migrations.AddField(
            model_name='assayrun',
            name='use_in_calculations',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studysupportingdata',
            name='study',
            field=models.ForeignKey(to='assays.AssayRun', on_delete=models.CASCADE),
        ),
    ]
