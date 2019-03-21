# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Definition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(unique=True, max_length=60)),
                ('definition', models.CharField(default=b'', max_length=200)),
                ('reference', models.URLField(default=b'', blank=True)),
            ],
        ),
    ]
