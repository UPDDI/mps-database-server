from django.db import models
from mps.base.models import LockableModel

from django.utils.safestring import mark_safe

CHEMBL = None


def get_chembl_handle():
    """Returns the bioservice wrapper for ChEMBL"""
    from bioservices import ChEMBL as ChEMBLdb
    global CHEMBL
    if CHEMBL is None:
        CHEMBL = ChEMBLdb()
    return CHEMBL

FIELDS = {
    'acdAcidicPka': 'acidic_pka',
    'acdBasicPka': 'basic_pka',
    'acdLogd': 'logd',
    'acdLogp': 'logp',
    'alogp': 'alogp',
    'chemblId': 'chemblid',
    'knownDrug': 'known_drug',
    # Deprecated
    # 'medChemFriendly': 'medchem_friendly',
    'molecularFormula': 'molecular_formula',
    'molecularWeight': 'molecular_weight',
    'numRo5Violations': 'ro5_violations',
    'passesRuleOfThree': 'ro3_passes',
    'preferredCompoundName': 'name',
    'rotatableBonds': 'rotatable_bonds',
    'smiles': 'smiles',
    'species': 'species',
    'stdInChiKey': 'inchikey',
    'synonyms': 'synonyms'
}


def chembl_compound(chemblid):
    """Get a ChEMBL compound from bioservices and return it as a dictionary"""
    chembl = get_chembl_handle()
    data = chembl.get_compounds_by_chemblId(str(chemblid))['compound']
    return {
        FIELDS[key]: value for key, value in list(data.items())
        if key in FIELDS
    }


class Compound(LockableModel):
    # compound_id = AutoField(primary_key=True)
    # The name, rather than the chemblid and/or inchikey, is unique
    name = models.CharField(
        max_length=200, unique=True,
        help_text="Preferred compound name.")
    synonyms = models.TextField(
        max_length=4000,
        default='', blank=True)
    # TODO DEPRECATED AND SUBJECT TO REMOVAL
    tags = models.TextField(
        default='', blank=True,
        help_text="Tags for the compound (EPA, NCATS, etc.)")

    # External identifiers are checked for uniqueness in form's clean
    # Not optimal, but other solutions did not seem to work (editing save, so on)
    chemblid = models.CharField(
        'ChEMBL ID', max_length=20,
        default='', blank=True,
        help_text="Enter a ChEMBL id, e.g. CHEMBL25, and click Retrieve to "
                  "get compound information automatically.")

    # Pubchem ID
    pubchemid = models.CharField(verbose_name='PubChem ID', max_length=40, default='', blank=True)

    epa = models.BooleanField(
        default=False,
        help_text='Whether this compound is part of the EPA project'
    )
    mps = models.BooleanField(
        default=False,
        help_text='Whether this compound is part of the MPS project'
    )
    tctc = models.BooleanField(
        default=False,
        help_text='Whether this compound is part of the TCTC project'
    )

    # standard names/identifiers
    inchikey = models.CharField(
        'InChI key', max_length=27,
        default='', blank=True,
        help_text="IUPAC standard InChI key for the compound")
    smiles = models.CharField(
        max_length=1000,
        default='', blank=True,
        help_text="Canonical smiles, generated using pipeline pilot.")

    # molecular properties
    molecular_formula = models.CharField(
        max_length=40,
        default='', blank=True,
        help_text="Molecular formula of compound.")
    molecular_weight = models.FloatField(
        null=True, blank=True,
        help_text="Molecular weight of the compound")
    rotatable_bonds = models.IntegerField(
        null=True, blank=True,
        help_text="Number of rotatable bonds.")

    # some calculated properties
    acidic_pka = models.FloatField(
        "Acidic pKa (ACD)",
        null=True, blank=True,
        help_text="The most acidic pKa calculated using ACDlabs.")
    basic_pka = models.FloatField(
        "Basic pKa (ACD)",
        null=True, blank=True,
        help_text="The most basic pKa calculated using ACDlabs.")
    logp = models.FloatField(
        "LogP (ACD)",
        null=True, blank=True,
        help_text="The calculated octanol/water partition coefficient using "
                  "ACDlabs")
    logd = models.FloatField(
        "LogD (ACD)",
        null=True, blank=True,
        help_text="The calculated octanol/water distribution "
                  "coefficient at pH7.4 using ACDlabs.")
    alogp = models.FloatField(
        'ALogP',
        null=True, blank=True,
        help_text="Calculated ALogP.")

    # drug related properties
    known_drug = models.BooleanField(
        'Known drug?',
        default=False)
    # This field is now deprecated
    # medchem_friendly = models.BooleanField(
    #     'Med Chem friendly?',
    #     default=False)
    medchem_alerts = models.BooleanField(
        'Inicates whether structural alerts are listed for this compound',
        default=False)
    ro5_violations = models.IntegerField(
        'Rule of 5 violations',
        null=True, blank=True,
        help_text="Number of properties defined in Lipinski's Rule of 5 (RO5) "
                  "that the compound fails.")
    ro3_passes = models.BooleanField(
        'Passes rule of 3?',
        default=False,
        help_text="Rule of 3 passes.  It is suggested "
                  "that compounds that pass all these criteria are"
                  "more likely to be hits in fragment screening.")
    species = models.CharField(
        'Molecular species', max_length=10,
        default='', blank=True,
        help_text="A description of the predominant species occurring at pH "
                  "7.4 and can be acid, base, neutral or zwitterion.")

    last_update = models.DateField(
        blank=True, null=True,
        help_text="Last time when activities associated with the compound were"
                  " updated.")

    # DrugBank data
    drugbank_id = models.CharField(
        'DrugBank ID', max_length=20,
        default='', blank=True,
        help_text="DrugBank ID")
    # Listed as "Sub Class" in DrugBank
    drug_class = models.CharField(
        'Class', max_length=150,
        default='', blank=True,
        help_text="Drug Class from DrugBank")
    # Percent value for protein_binding
    protein_binding = models.CharField(
        'Protein Binding', max_length=20,
        default='', blank=True,
        help_text="Protein Binding from DrugBank")
    # Drug's half life (may be a range)
    half_life = models.CharField(
        'Half Life', max_length=100,
        default='', blank=True,
        help_text="Half Life from DrugBank")
    # Description of clearance
    clearance = models.CharField(
        'Clearance', max_length=500,
        default='', blank=True,
        help_text="Clearance from DrugBank")
    # Percent value for drug bioavailability
    bioavailability = models.CharField(
        'Bioavailability', max_length=20,
        default='', blank=True,
        help_text="Bioavailability from DrugBank")
    # Test description of the drug's absorption
    absorption = models.CharField(
        'Absorption', max_length=1000,
        default='', blank=True,
        help_text="Absorption Description from DrugBank")
    # Summary of PK and Metabolism
    pk_metabolism = models.CharField(
        'PK/Metabolism', max_length=1000,
        default='', blank=True,
        help_text="Summary of pharmacokinetics and metabolism")
    # Summary of pre-clinical trial data
    preclinical = models.CharField(
        'Pre-clinical Findings', max_length=1000,
        default='', blank=True,
        help_text="Summary of pre-clinical findings")
    # Summary of clinical trial data
    clinical = models.CharField(
        'Clinical Findings', max_length=1000,
        default='', blank=True,
        help_text="Summary of clinical findings")
    post_marketing = models.CharField(
        'Post-marketing', max_length=1000,
        default='', blank=True,
        help_text="Summary of post-marketing findings")

    class Meta(object):
        ordering = ('name',)

    def __str__(self):
        return '{0}'.format(self.name)

    @mark_safe
    def chembl_link(self):
        if self.chemblid:
            return ('<a href="https://www.ebi.ac.uk/chembl/compound/inspect/'
                    '{0}" target="_blank">{0}</a>').format(self.chemblid)
        else:
            return ''

    chembl_link.allow_tags = True
    chembl_link.short_description = 'ChEMBL ID'

    @mark_safe
    def thumb_src(self):
        if self.chemblid:
            return ('https://www.ebi.ac.uk/chembldb/compound/'
                    'displayimage/' + self.chemblid)
        else:
            return ''

    @mark_safe
    def thumb(self):
        url = self.thumb_src()
        if url:
            return '<img src="{}" />'.format(url)
        else:
            return ''

    thumb.allow_tags = True
    thumb.short_description = 'Thumbnail'

    def image(self):
        url = self.image_src()
        if url:
            return '<img src="{}" />'.format(url)
        else:
            return ''

    def image_src(self):
        if self.chemblid:
            return ('https://www.ebi.ac.uk/chembldb/compound/'
                    'displayimage_large/' + self.chemblid)
        else:
            return ''

    image.allow_tags = True
    image.short_description = 'Image'

    def get_absolute_url(self):
        return "/compounds/{}/".format(self.id)

    def get_post_submission_url(self):
        return "/compounds/"


# TODO THIS MODEL IS DEPRECATED
class SummaryType(LockableModel):
    class Meta(object):
        verbose_name = 'Summary Type'
        verbose_name_plural = 'Summary Types'

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500, default='')

    def __str__(self):
        return str(self.name)


# TODO THIS MODEL IS DEPRECATED
class PropertyType(LockableModel):
    class Meta(object):
        verbose_name = 'Compound Property Type'

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500, default='')

    def __str__(self):
        return str(self.name)


# TODO THIS MODEL IS DEPRECATED
# At worst, I suppose I can merge these together or even add them as fields in Compound
# It would be useful to have a model that catalogues COMPOUND SUMMARIES such as non-clinical/clinical toxicology
class CompoundSummary(models.Model):
    class Meta(object):
        unique_together = [('compound', 'summary_type')]
        verbose_name = 'Compound Summary'
        verbose_name_plural = 'Compound Summaries'

    compound = models.ForeignKey(Compound, on_delete=models.CASCADE)
    summary_type = models.ForeignKey(SummaryType, on_delete=models.CASCADE)
    summary = models.CharField(max_length=500)
    source = models.CharField(max_length=250)

    def __str__(self):
        return str(self.summary)


# TODO THIS MODEL IS DEPRECATED
# It would be useful to have a model that catalogues COMPOUND PROPERTIES such as cmax and clogp
class CompoundProperty(models.Model):
    class Meta(object):
        # Remove restriction
        # unique_together = [('compound', 'property_type')]
        verbose_name = 'Compound Property'
        verbose_name_plural = 'Compound Properties'

    compound = models.ForeignKey(Compound, on_delete=models.CASCADE)
    property_type = models.ForeignKey(PropertyType, on_delete=models.CASCADE)
    # After some amount of debate, it was decided a float field should be sufficient for out purposes
    value = models.FloatField()
    source = models.CharField(max_length=250)

    def __str__(self):
        return str(self.value)


# Should these be treated separately from bioactivity targets?
# Whatever the case, the following information was requested:
class CompoundTarget(models.Model):
    # Must link back to a compound
    compound = models.ForeignKey(Compound, on_delete=models.CASCADE)

    name = models.CharField(max_length=150)
    # May not be present
    uniprot_id = models.CharField(max_length=20, blank=True, default='')
    action = models.CharField(max_length=75, blank=True, default='')
    pharmacological_action = models.CharField(max_length=20)
    organism = models.CharField(max_length=150)
    type = models.CharField(max_length=30)


# Should this be trackable?
class CompoundSupplier(LockableModel):
    """Compound suppliers so that we can track where compounds come from"""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.name)


# TODO Add uniqueness contraints
class CompoundInstance(LockableModel):
    """An instance of a compound that includes its supplier and lot number"""
    class Meta(object):
        unique_together = [('compound', 'supplier', 'lot', 'receipt_date')]

    compound = models.ForeignKey(Compound, on_delete=models.CASCADE)
    # Required, though N/A should be an option
    supplier = models.ForeignKey(CompoundSupplier, blank=True, on_delete=models.CASCADE)
    # Required, though N/A should be an option
    # It is possible that the lot_number will not be solely numeric
    lot = models.CharField(max_length=255)
    # Receipt date
    receipt_date = models.DateField(null=True, blank=True)

    def __str__(self):
        items = [
            str(self.compound), str(self.supplier), str(self.lot), str(self.receipt_date)
        ]
        return ' '.join(items)
