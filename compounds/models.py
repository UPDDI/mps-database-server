from django.db import models
from mps.base.models import LockableModel, FrontEndModel

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


class Compound(FrontEndModel, LockableModel):

    class Meta(object):
        ordering = ('name',)
        verbose_name = 'Compound'

    # compound_id = AutoField(primary_key=True)
    # The name, rather than the chemblid and/or inchikey, is unique
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Preferred compound name.",
        verbose_name='Name'
    )
    synonyms = models.TextField(
        max_length=4000,
        default='',
        blank=True,
        verbose_name='synonyms'
    )
    # TODO DEPRECATED AND SUBJECT TO REMOVAL
    tags = models.TextField(
        default='',
        blank=True,
        help_text="Tags for the compound (EPA, NCATS, etc.)",
        verbose_name='Tags'
    )

    # External identifiers are checked for uniqueness in form's clean
    # Not optimal, but other solutions did not seem to work (editing save, so on)
    chemblid = models.CharField(
        max_length=20,
        default='',
        blank=True,
        help_text="Enter a ChEMBL id, e.g. CHEMBL25, and click Retrieve to "
            "get compound information automatically.",
        verbose_name='ChEMBL ID'
        )

    # Pubchem ID
    pubchemid = models.CharField(
        max_length=40,
        default='',
        blank=True,
        verbose_name='PubChem ID',
    )

    # DEPRECATED: SLATED FOR REMOVAL
    epa = models.BooleanField(
        default=False,
        help_text='Whether this compound is part of the EPA project',
        verbose_name='EPA'
    )
    mps = models.BooleanField(
        default=False,
        help_text='Whether this compound is part of the MPS project',
        verbose_name='MPS'
    )
    tctc = models.BooleanField(
        default=False,
        help_text='Whether this compound is part of the TCTC project',
        verbose_name='TCTC'
    )

    # standard names/identifiers
    inchikey = models.CharField(
        max_length=27,
        default='',
        blank=True,
        help_text="IUPAC standard InChI key for the compound",
        verbose_name='InChI Key'
    )
    smiles = models.CharField(
        max_length=1000,
        default='',
        blank=True,
        help_text="Canonical smiles, generated using pipeline pilot.",
        verbose_name='SMILES'
    )

    # molecular properties
    molecular_formula = models.CharField(
        max_length=40,
        default='',
        blank=True,
        help_text="Molecular formula of compound.",
        verbose_name='Molecular Formula'
    )
    molecular_weight = models.FloatField(
        null=True,
        blank=True,
        help_text="Molecular weight of the compound",
        verbose_name='Molecular Weight'
    )
    rotatable_bonds = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of rotatable bonds.",
        verbose_name='Rotatable Bonds'
    )

    # some calculated properties
    acidic_pka = models.FloatField(
        null=True,
        blank=True,
        help_text="The most acidic pKa calculated using ACDlabs.",
        verbose_name='Acidic pKa (ACD)'
    )
    basic_pka = models.FloatField(
        null=True,
        blank=True,
        help_text="The most basic pKa calculated using ACDlabs.",
        verbose_name='Basic pKa (ACD)'
    )
    logp = models.FloatField(
        null=True,
        blank=True,
        help_text="The calculated octanol/water partition coefficient using ACDlabs",
        verbose_name='LogP (ACD)'
    )
    logd = models.FloatField(
        null=True,
        blank=True,
        help_text="The calculated octanol/water distribution coefficient at pH7.4 using ACDlabs.",
        verbose_name='LogD (ACD)'
    )
    alogp = models.FloatField(
        null=True,
        blank=True,
        help_text="Calculated ALogP.",
        verbose_name='ALogP'
    )

    # drug related properties
    known_drug = models.BooleanField(
        default=False,
        verbose_name='Known Drug'
    )
    # This field is now deprecated
    # medchem_friendly = models.BooleanField(
    #     'Med Chem friendly?',
    #     default=False)
    medchem_alerts = models.BooleanField(
        help_text='Inicates whether structural alerts are listed for this compound',
        default=False,
        verbose_name='Medchem Alerts'
    )
    ro5_violations = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of properties defined in Lipinski's Rule of 5 (RO5) "
            "that the compound fails.",
        verbose_name='Rule of 5 Violations'
    )
    ro3_passes = models.BooleanField(
        default=False,
        help_text="Rule of 3 passes.  It is suggested "
            "that compounds that pass all these criteria are"
            "more likely to be hits in fragment screening.",
        verbose_name='Passes Rule of 3'
    )
    species = models.CharField(
        max_length=10,
        default='',
        blank=True,
        help_text="A description of the predominant species occurring at pH "
            "7.4 and can be acid, base, neutral or zwitterion.",
        verbose_name='Molecular Species'
    )

    last_update = models.DateField(
        blank=True,
        null=True,
        help_text="Last time when activities associated with the compound were"
                  " updated."
    )

    # DrugBank data
    drugbank_id = models.CharField(
        max_length=20,
        default='',
        blank=True,
        help_text="DrugBank ID",
        verbose_name='DrugBank ID'
    )
    # Listed as "Sub Class" in DrugBank
    drug_class = models.CharField(
        max_length=150,
        default='',
        blank=True,
        help_text="Drug Class from DrugBank",
        verbose_name='Drug Class'
    )
    # Percent value for protein_binding
    protein_binding = models.CharField(
        max_length=20,
        default='',
        blank=True,
        help_text="Protein Binding from DrugBank",
        verbose_name='Protein Binding'
    )
    # Drug's half life (may be a range)
    half_life = models.CharField(
        max_length=100,
        default='',
        blank=True,
        help_text="Half Life from DrugBank",
        verbose_name='Half Life'
    )
    # Description of clearance
    clearance = models.CharField(
        max_length=500,
        default='',
        blank=True,
        help_text="Clearance from DrugBank",
        verbose_name='Clearance'
    )
    # Percent value for drug bioavailability
    bioavailability = models.CharField(
        max_length=20,
        default='',
        blank=True,
        help_text="Bioavailability from DrugBank",
        verbose_name='Bioavailability (Fraction)'
    )
    # Test description of the drug's absorption
    absorption = models.CharField(
        max_length=1000,
        default='',
        blank=True,
        help_text="Absorption Description from DrugBank",
        verbose_name='Absorption'
    )
    # Summary of PK and Metabolism
    pk_metabolism = models.CharField(
        max_length=1000,
        default='',
        blank=True,
        help_text="Summary of pharmacokinetics and metabolism",
        verbose_name='PK/Metabolism'
    )
    # Summary of pre-clinical trial data
    preclinical = models.CharField(
        max_length=1000,
        default='',
        blank=True,
        help_text="Summary of pre-clinical findings",
        verbose_name='Pre-clinical Findings'
    )
    # Summary of clinical trial data
    clinical = models.CharField(
        max_length=1000,
        default='',
        blank=True,
        help_text="Summary of clinical findings",
        verbose_name='Clinical Findings'
    )
    post_marketing = models.CharField(
        max_length=1000,
        default='',
        blank=True,
        help_text="Summary of post-marketing findings",
        verbose_name='Post-marketing'
    )

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


# TODO THIS MODEL IS DEPRECATED
class SummaryType(LockableModel):
    class Meta(object):
        verbose_name = 'Summary Type'
        verbose_name_plural = 'Summary Types'

    name = models.CharField(
        max_length=100,
        verbose_name='Name'
    )
    description = models.CharField(
        max_length=500,
        default='',
        verbose_name='Description'
    )

    def __str__(self):
        return str(self.name)


# TODO THIS MODEL IS DEPRECATED
class PropertyType(LockableModel):
    class Meta(object):
        verbose_name = 'Compound Property Type'

    name = models.CharField(
        max_length=100,
        verbose_name='Name'
    )
    description = models.CharField(
        max_length=500,
        default='',
        verbose_name='Description'
    )

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

    compound = models.ForeignKey(
        Compound,
        on_delete=models.CASCADE,
        verbose_name='Compound'
    )
    summary_type = models.ForeignKey(
        SummaryType,
        on_delete=models.CASCADE,
        verbose_name='Summary Type'
    )
    summary = models.CharField(
        max_length=500,
        verbose_name='Summary'
    )
    source = models.CharField(
        max_length=250,
        verbose_name='Source'
    )

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

    compound = models.ForeignKey(
        Compound,
        on_delete=models.CASCADE,
        verbose_name='Compound'
    )
    property_type = models.ForeignKey(
        PropertyType,
        on_delete=models.CASCADE,
        verbose_name='Property Type'
    )
    # After some amount of debate, it was decided a float field should be sufficient for out purposes
    value = models.FloatField(verbose_name='Value')
    source = models.CharField(
        max_length=250,
        verbose_name='Source'
    )

    def __str__(self):
        return str(self.value)


# Should these be treated separately from bioactivity targets?
# Whatever the case, the following information was requested:
class CompoundTarget(models.Model):
    # Must link back to a compound
    compound = models.ForeignKey(
        Compound,
        on_delete=models.CASCADE,
        verbose_name='Compound'
    )

    name = models.CharField(
        max_length=150,
        verbose_name='Name'
    )
    # May not be present
    uniprot_id = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='UniProt ID'
    )
    action = models.CharField(
        max_length=75,
        blank=True,
        default='',
        verbose_name='Action'
    )
    pharmacological_action = models.CharField(
        max_length=20,
        verbose_name='Pharmacological Action'
    )
    organism = models.CharField(
        max_length=150,
        verbose_name='Organism'
    )
    type = models.CharField(
        max_length=30,
        verbose_name='Type'
    )


# Should this be trackable?
class CompoundSupplier(LockableModel):
    """Compound suppliers so that we can track where compounds come from"""
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Name'
    )

    def __str__(self):
        return str(self.name)


# TODO Add uniqueness contraints
class CompoundInstance(LockableModel):
    """An instance of a compound that includes its supplier and lot number"""
    class Meta(object):
        unique_together = [('compound', 'supplier', 'lot', 'receipt_date')]

    compound = models.ForeignKey(
        Compound,
        on_delete=models.CASCADE,
        verbose_name='Compound'
    )
    # Required, though N/A should be an option
    supplier = models.ForeignKey(
        CompoundSupplier,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='Supplier'
    )
    # Required, though N/A should be an option
    # It is possible that the lot_number will not be solely numeric
    lot = models.CharField(
        max_length=255,
        verbose_name='Lot'
    )
    # Receipt date
    receipt_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Receipt Date'
    )

    def __str__(self):
        items = [
            str(self.compound), str(self.supplier), str(self.lot), str(self.receipt_date)
        ]
        return ' '.join(items)
