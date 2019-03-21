# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0027'),
        ('microdevices', '0011'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganModelLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('notes', models.CharField(max_length=1024)),
            ],
        ),
        migrations.AlterModelOptions(
            name='manufacturer',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='microdevice',
            options={'ordering': ('name', 'organ')},
        ),
        migrations.AlterModelOptions(
            name='microphysiologycenter',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='organmodel',
            options={'ordering': ('name', 'organ'), 'verbose_name': 'Organ Model'},
        ),
        migrations.RenameField(
            model_name='manufacturer',
            old_name='manufacturer_name',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='manufacturer',
            old_name='Manufacturer_website',
            new_name='website',
        ),
        migrations.RenameField(
            model_name='microdevice',
            old_name='device_name',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='microphysiologycenter',
            old_name='center_name',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='microphysiologycenter',
            old_name='center_website',
            new_name='website',
        ),
        migrations.RenameField(
            model_name='organmodel',
            old_name='model_name',
            new_name='name',
        ),
        migrations.AddField(
            model_name='organmodellocation',
            name='organ_model',
            field=models.ForeignKey(to='microdevices.OrganModel', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='organmodellocation',
            name='sample_location',
            field=models.ForeignKey(to='assays.AssaySampleLocation', on_delete=models.CASCADE),
        ),
    ]
