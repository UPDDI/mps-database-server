# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('microdevices', '0001_initial'),
        ('drugtrials', '0001_initial'),
        ('cellsamples', '0001_initial'),
        ('compounds', '0001_initial'),
        ('assays', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='test',
            name='organ_model',
            field=models.ForeignKey(blank=True, to='microdevices.OrganModel', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='test',
            name='signed_off_by',
            field=models.ForeignKey(related_name='test_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='test',
            name='test_type',
            field=models.ForeignKey(to='drugtrials.TestType', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='test',
            unique_together=set([('test_type', 'test_name')]),
        ),
        migrations.AddField(
            model_name='species',
            name='created_by',
            field=models.ForeignKey(related_name='species_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='species',
            name='modified_by',
            field=models.ForeignKey(related_name='species_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='species',
            name='signed_off_by',
            field=models.ForeignKey(related_name='species_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resultdescriptor',
            name='created_by',
            field=models.ForeignKey(related_name='resultdescriptor_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resultdescriptor',
            name='modified_by',
            field=models.ForeignKey(related_name='resultdescriptor_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resultdescriptor',
            name='signed_off_by',
            field=models.ForeignKey(related_name='resultdescriptor_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='openfdacompound',
            name='compound',
            field=models.ForeignKey(to='compounds.Compound', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='openfdacompound',
            name='created_by',
            field=models.ForeignKey(related_name='openfdacompound_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='openfdacompound',
            name='modified_by',
            field=models.ForeignKey(related_name='openfdacompound_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='openfdacompound',
            name='signed_off_by',
            field=models.ForeignKey(related_name='openfdacompound_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='findingtype',
            name='created_by',
            field=models.ForeignKey(related_name='findingtype_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='findingtype',
            name='modified_by',
            field=models.ForeignKey(related_name='findingtype_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='findingtype',
            name='signed_off_by',
            field=models.ForeignKey(related_name='findingtype_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='findingresult',
            name='descriptor',
            field=models.ForeignKey(blank=True, to='drugtrials.ResultDescriptor', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='findingresult',
            name='drug_trial',
            field=models.ForeignKey(to='drugtrials.DrugTrial', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='findingresult',
            name='finding_name',
            field=models.ForeignKey(verbose_name=b'Finding', to='drugtrials.Finding', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='findingresult',
            name='time_units',
            field=models.ForeignKey(blank=True, to='assays.TimeUnits', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='findingresult',
            name='value_units',
            field=models.ForeignKey(blank=True, to='assays.PhysicalUnits', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='finding',
            name='created_by',
            field=models.ForeignKey(related_name='finding_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='finding',
            name='finding_type',
            field=models.ForeignKey(to='drugtrials.FindingType', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='finding',
            name='modified_by',
            field=models.ForeignKey(related_name='finding_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='finding',
            name='organ',
            field=models.ForeignKey(blank=True, to='cellsamples.Organ', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='finding',
            name='signed_off_by',
            field=models.ForeignKey(related_name='finding_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='finding',
            unique_together=set([('organ', 'finding_name')]),
        ),
        migrations.AddField(
            model_name='drugtrial',
            name='compound',
            field=models.ForeignKey(to='compounds.Compound', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='drugtrial',
            name='created_by',
            field=models.ForeignKey(related_name='drugtrial_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='drugtrial',
            name='modified_by',
            field=models.ForeignKey(related_name='drugtrial_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='drugtrial',
            name='signed_off_by',
            field=models.ForeignKey(related_name='drugtrial_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='drugtrial',
            name='source',
            field=models.ForeignKey(to='drugtrials.TrialSource', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='drugtrial',
            name='species',
            field=models.ForeignKey(default=b'1', blank=True, to='drugtrials.Species', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='compoundadverseevent',
            name='compound',
            field=models.ForeignKey(to='drugtrials.OpenFDACompound', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='compoundadverseevent',
            name='event',
            field=models.ForeignKey(to='drugtrials.AdverseEvent', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adverseevent',
            name='organ',
            field=models.ForeignKey(blank=True, to='cellsamples.Organ', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
