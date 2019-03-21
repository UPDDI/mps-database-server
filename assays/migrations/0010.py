# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


def fix_setups_and_devices(apps, schema_editor):
    AssayChipSetup = apps.get_model("assays", "AssayChipSetup")
    for setup in AssayChipSetup.objects.all():
        setup.device = setup.organ_model.device
        setup.save()

    Microdevice = apps.get_model("microdevices", "Microdevice")
    for device in Microdevice.objects.all():
        if device.row_labels:
            device.device_type = 'plate'
        else:
            device.device_type = 'chip'

        device.save()


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0009'),
    ]

    operations = [
        migrations.RunPython(
            fix_setups_and_devices
        ),
    ]
