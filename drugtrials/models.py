from django.db import models

from mps.base.models import LockableModel
from microdevices.models import OrganModel
from cellsamples.models import Organ
from diseases.models import Disease

from assays.models import PhysicalUnits

from django.core.exceptions import ValidationError


class Species(LockableModel):
    """A Species defines a particular species"""
    class Meta(object):
        verbose_name_plural = 'Species'
        ordering = ('species_name', )

    species_name = models.CharField(
        max_length=40,
        unique=True,
        verbose_name='Species'
    )

    def __str__(self):
        return self.species_name


PARTICIPANTTYPES = (
    ('I', 'Individual'),
    ('P', 'Population'),
)

TRIALSUBTYPES = (
    ('C', 'Case Report'),
    ('P', 'Population Report'),
    ('U', 'Unknown / Unspecified'),
)

# Participants information is now part of DrugTrials model
# instead of a seperate entity


class TrialSource(LockableModel):
    """A Trial Source indicates where a trial came from and provides some information"""
    class Meta(object):
        ordering = ('source_name', )
    source_name = models.CharField(max_length=40, unique=True)
    source_website = models.URLField(blank=True, null=True)
    description = models.CharField(max_length=400, blank=True, default='')

    def __str__(self):
        return self.source_name


TRIALTYPES = (
    ('S', 'Microphysiology'),
    ('P', 'Preclinical'),
    ('C', 'Clinical'),
    ('M', 'Post-marketing'),
    ('B', 'Combined Clinical-Post Market'),
    ('U', 'Unknown / Unspecified'),
)


class DrugTrial(LockableModel):
    """A Drug Trial describes the participants and high-level data of a drug trial"""
    class Meta(object):
        verbose_name = 'Drug Trial'
        ordering = ('compound', 'species', )

    # title = models.CharField(max_length=2000, unique=True)
    title = models.CharField(max_length=2000)
    condition = models.CharField(max_length=1400, blank=True, default='')
    source = models.ForeignKey(TrialSource, on_delete=models.CASCADE)
    compound = models.ForeignKey('compounds.Compound', blank=True, null=True, on_delete=models.CASCADE)

    # Figures
    figure1 = models.ImageField(upload_to='figures', null=True, blank=True)
    figure2 = models.ImageField(upload_to='figures', null=True, blank=True)

    # Participant Information

    species = models.ForeignKey(
        Species,
        default='1',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    gender = models.CharField(max_length=1,
                              choices=(
                                  ('F', 'female'), ('M', 'male'),
                                  ('X', 'mixed'),
                                  ('U', 'unknown or unspecified'),
                              ),
                              default='U',
                              blank=True)

    population_size = models.CharField(max_length=50,
                                       default='1',
                                       blank=True)

    age_average = models.FloatField(blank=True, null=True)

    age_max = models.FloatField(blank=True, null=True)

    age_min = models.FloatField(blank=True, null=True)

    age_unit = models.CharField(max_length=1,
                                blank=True,
                                choices=(
                                    ('M', 'months'), ('Y', 'years')
                                ),
                                default='Y')

    weight_average = models.FloatField(blank=True, null=True)
    weight_max = models.FloatField(blank=True, null=True)
    weight_min = models.FloatField(blank=True, null=True)
    weight_unit = models.CharField(max_length=1, blank=True,
                                   choices=(
                                       ('K', 'kilograms'), ('L', 'pounds'),
                                   ),
                                   default='L')

    # End of Participant Information

    disease = models.ManyToManyField(Disease, blank=True)
    trial_type = models.CharField(max_length=1, choices=TRIALTYPES)
    trial_sub_type = models.CharField(max_length=1,
                                      choices=TRIALSUBTYPES, default='C')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    publish_date = models.DateField(blank=True, null=True)
    description = models.CharField(max_length=1400, blank=True, default='')
    source_link = models.URLField(blank=True, null=True)
    references = models.CharField(max_length=400, default='',
                                  verbose_name='Trial ID/Reference')

    def __str__(self):
        return '{} from {}'.format(dict(TRIALTYPES)[self.trial_type],
                                           self.source.source_name)

    def get_absolute_url(self):
        return "/drugtrials/{}/".format(self.id)


# DEPRECATED AND SUBJECT TO REMOVAL
class TestType(LockableModel):
    """A Test Type describes what sort of test was performed

    THIS MODEL HAS BEEN DEPRECATED IN FAVOR OF FINDINGTYPE
    """
    class Meta(object):
        ordering = ('test_type',)
    test_type = models.CharField(max_length=60, unique=True)
    description = models.CharField(max_length=200, blank=True, default='')

    def __str__(self):
        return self.test_type


# DEPRECATED AND SUBJECT TO REMOVAL
# The only difference between Test and Finding is the ability to select and organ model
# However, it was decided to use DrugTrials for EXTERNAL data only
class Test(LockableModel):
    """A Test describes and instance of a test performed

    THIS MODEL HAS BEEN DEPRECATED IN FAVOR OF FINDING
    """
    class Meta(object):
        unique_together = [('test_type', 'test_name')]
        ordering = ('test_name', 'organ', 'test_type', )

    organ_model = models.ForeignKey(
        OrganModel,
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    test_type = models.ForeignKey(TestType, on_delete=models.CASCADE)
    test_name = models.CharField(max_length=40,
                                 verbose_name='Organ Function Test')
    test_unit = models.CharField(max_length=40, blank=True, default='')
    organ = models.ForeignKey(Organ, blank=True, null=True, on_delete=models.CASCADE)
    description = models.CharField(max_length=400, blank=True, default='')

    def __str__(self):
        return '{} :: {} :: {}'.format(
            self.organ,
            self.test_type,
            self.test_name
        )


class FindingType(LockableModel):
    """Finding Type describes a type of finding (e.g. biopsy)"""
    class Meta(object):
        ordering = ('finding_type', )

    finding_type = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True, default='')

    def __str__(self):
        return self.finding_type


class Finding(LockableModel):
    """Finding describes a finding relative to what organ (e.g. liver biopsy)"""
    class Meta(object):
        unique_together = [('organ', 'finding_name')]
        ordering = ('organ', 'finding_type', 'finding_name', )

    finding_type = models.ForeignKey(FindingType, on_delete=models.CASCADE)
    finding_name = models.CharField(max_length=100)
    finding_unit = models.CharField(max_length=40, blank=True, default='')
    organ = models.ForeignKey(
        Organ,
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    # Subject to removal?
    description = models.CharField(max_length=400, blank=True, default='')

    def __str__(self):
        return '{} :: {} :: {}'.format(self.organ, self.finding_type, self.finding_name)


class ResultDescriptor(LockableModel):
    """A Result Descriptor adds detail to a Finding (e.g. increased, female only, etc."""
    class Meta(object):
        ordering = ('result_descriptor', )
    result_descriptor = models.CharField(max_length=40, unique=True)

    def __str__(self):
        return self.result_descriptor


SEVERITY_SCORE = (
    ('-1', 'UNKNOWN'), ('0', 'NEGATIVE'), ('1', '+'), ('2', '+ +'),
    ('3', '+ + +'), ('4', '+ + + +'), ('5', '+ + + + +')
)

# DEPRECATED
TIME_UNITS = (
    ('u', 'unknown'), ('h', 'hours'), ('d', 'days'),
    ('w', 'weeks'), ('m', 'months'), ('y', 'years')
)

POSNEG = (
    ('0', 'Neg'), ('1', 'Pos')
)

RESULT_TYPE = (
    ('B', 'Biopsy'), ('R', 'Report'), ('M', 'Mechanism'), ('I', 'Information')
)


# DEPRECATED AND SUBJECT TO REMOVAL
class TestResult(models.Model):
    """A Test Result describes a specific discovery from a organ model test

    THIS MODEL IS DEPRECATED
    """
    drug_trial = models.ForeignKey(DrugTrial, on_delete=models.CASCADE)

    test_name = models.ForeignKey(
        Test,
        verbose_name='Test',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    test_time = models.FloatField(verbose_name='Time', blank=True, null=True)

    time_units = models.ForeignKey(
        PhysicalUnits,
        blank=True,
        null=True,
        related_name='test_time_units',
        on_delete=models.CASCADE
    )

    result = models.CharField(default='1',
                              max_length=8,
                              choices=POSNEG,
                              verbose_name='Pos/Neg?',
                              blank=True)

    severity = models.CharField(default='-1',
                                max_length=5,
                                choices=SEVERITY_SCORE,
                                verbose_name='Severity',
                                blank=True)

    percent_min = models.FloatField(blank=True,
                                    null=True,
                                    verbose_name='Min Affected (% Population)')

    percent_max = models.FloatField(blank=True,
                                    null=True,
                                    verbose_name='Max Affected (% Population)')

    descriptor = models.ForeignKey(ResultDescriptor, blank=True, null=True, on_delete=models.CASCADE)

    value = models.FloatField(blank=True, null=True)

    value_units = models.ForeignKey(PhysicalUnits, blank=True, null=True, related_name='test_value_units', on_delete=models.CASCADE)

    def clean(self):
        """Require units to be specified if a value is present"""

        if self.value or self.value_units:
            if not (self.drug_trial.source and self.drug_trial.source_link
                    and self.value_units and self.value):
                raise ValidationError(
                    "Values and units must have a defined source "
                    "and source link"
                )

        if self.value:
            if not self.value_units:
                raise ValidationError(
                    "You must specify valid units "
                    "for the value you entered"
                )

        if not self.value:
            if self.value_units:
                raise ValidationError("You forgot to enter a value!")

    def __str__(self):
        return ''

FREQUENCIES = (
    ('>= 10%', '>= 10% : Very Common'), ('1 - < 10%', '1 - < 10% : Common'),
    ('0.1 - < 1%', '0.1 - < 1% : Uncommon'), ('0.01 - < 0.1%', '0.01 - < 0.1% : Rare'),
    ('< 0.01%', '< 0.01% : Very Rare')
)


class FindingResult(models.Model):
    """A Finding Result describes in detail a single finding from a Drug Trial"""

    class Meta(object):
        verbose_name = 'Drug Trial Result'

    drug_trial = models.ForeignKey(DrugTrial, on_delete=models.CASCADE)

    finding_name = models.ForeignKey(
        Finding,
        verbose_name='Finding',
        on_delete=models.CASCADE
    )

    finding_time = models.FloatField(verbose_name='Time', blank=True, null=True)

    time_units = models.ForeignKey(PhysicalUnits, blank=True, null=True, related_name='finding_time_units', on_delete=models.CASCADE)

    result = models.CharField(default='1',
                              max_length=8,
                              choices=POSNEG,
                              verbose_name='Pos/Neg?')

    severity = models.CharField(default='-1',
                                max_length=5,
                                choices=SEVERITY_SCORE,
                                verbose_name='Severity',
                                blank=True)

    # May drop percent_min later, hide for now
    percent_min = models.FloatField(blank=True,
                                    null=True,
                                    verbose_name='Min Affected (% Population)')

    # May drop percent_max later, hide for now
    percent_max = models.FloatField(blank=True,
                                    null=True,
                                    verbose_name='Max Affected (% Population)')

    frequency = models.CharField(choices=FREQUENCIES,
                                 max_length=25,
                                 blank=True,
                                 default='')

    descriptor = models.ForeignKey(ResultDescriptor, blank=True, null=True, on_delete=models.CASCADE)

    value = models.FloatField(blank=True, null=True)

    value_units = models.ForeignKey(PhysicalUnits, blank=True, null=True, related_name='finding_value_units', on_delete=models.CASCADE)

    notes = models.CharField(max_length=2048, blank=True, default='')

    def get_absolute_url(self):
        return self.drug_trial.get_absolute_url()

    def __str__(self):
        treatments = []

        for treatment in self.findingtreatment_set.all():
            treatments.append(str(treatment))

        treatments = '; '.join(treatments)

        return '{}: {} for {}'.format(str(self.drug_trial), str(self.finding_name), treatments)


class FindingTreatment(models.Model):
    """Finding Treatments are tied to Findings, and elaborate on the compounds and concentrations involved therein"""
    compound = models.ForeignKey('compounds.Compound', on_delete=models.CASCADE)
    finding_result = models.ForeignKey(FindingResult, on_delete=models.CASCADE)
    concentration = models.FloatField(blank=True, null=True)
    concentration_unit = models.ForeignKey(
        'assays.PhysicalUnits',
        blank=True,
        null=True,
        verbose_name='Concentration Unit',
        on_delete=models.CASCADE
    )

    def __str__(self):
        if self.concentration:
            return '{} {} {}'.format(self.compound, self.concentration, self.concentration_unit)
        else:
            return '{}'.format(self.compound)


class AdverseEvent(models.Model):
    """An Adverse Event describes an adverse event and what organ it affects"""
    event = models.CharField(max_length=100)
    organ = models.ForeignKey(Organ, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return '{}'.format(self.event)


# TODO think of a better name
# TODO what other fields should be placed here?
# Theoretically, we would place usage information here, but that is difficult to acquire
# If we can't think of anything, scrap this model before you put it on production
class OpenFDACompound(LockableModel):
    """An OpenFDACompound describes a compound with some data from OpenFDA"""
    class Meta(object):
        verbose_name = 'OpenFDA Report'

    compound = models.ForeignKey('compounds.Compound', on_delete=models.CASCADE)
    warnings = models.TextField(blank=True, default='')
    black_box = models.BooleanField(default=False)

    # Insights into non-human toxicology (can be useful)
    nonclinical_toxicology = models.TextField(blank=True, default='')

    # Deemed less than useful
    # clinical_studies = models.TextField(blank=True, default='')
    # Deemed less than useful
    # laboratory_tests = models.TextField(blank=True, default='')

    # For normalizing data, may change
    estimated_usage = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.compound.name)

    def get_absolute_url(self):
        return "/adverse_events/{}/".format(self.id)


class CompoundAdverseEvent(models.Model):
    """A Compound Adverse Event describes an adverse event's frequency as brought on by a compound"""
    # CompoundAdverseEvents are inlines in OpenFDACompound (name subject to change)
    compound = models.ForeignKey('OpenFDACompound', on_delete=models.CASCADE)
    event = models.ForeignKey(AdverseEvent, on_delete=models.CASCADE)
    frequency = models.IntegerField()

    def __str__(self):
        return '{}:{}'.format(self.compound, self.event)
