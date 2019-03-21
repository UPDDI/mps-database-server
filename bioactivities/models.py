from django.db import models
from mps.base.models import LockableModel

CHEMBL = None
FIELDS = {
    'chemblId': 'chemblid',
    'description': 'description',
    'geneNames': 'gene_names',
    'preferredName': 'name',
    'proteinAccession': 'uniprot_accession',
    'organism': 'organism',
    'targetType': 'target_type',
    'synonyms': 'synonyms',
    'assayOrganism': 'organism',
    'assayStrain': 'strain',
    'assayType': 'assay_type',
    'journal': 'journal',
    'assayDescription': 'description',
}


def chembl_target(chemblid):
    """Access ChEMBL to get information for related targets"""
    global CHEMBL
    if CHEMBL is None:
        from bioservices import ChEMBL as ChEMBLdb

        CHEMBL = ChEMBLdb()

    data = CHEMBL.get_target_by_chemblId(str(chemblid))['target']

    return {FIELDS[key]: value for key, value in list(data.items())
            if key in FIELDS}


def chembl_assay(chemblid):
    """Access ChEMBL to get information for related assays"""
    global CHEMBL
    if CHEMBL is None:
        from bioservices import ChEMBL as ChEMBLdb

        CHEMBL = ChEMBLdb()

    data = CHEMBL.get_assays_by_chemblId(str(chemblid))['assay']

    return {FIELDS[key]: value for key, value in list(data.items())
            if key in FIELDS}


class Target(LockableModel):
    """Information for a Bioactivity Target (usually a protein)"""
    name = models.TextField(help_text="Preferred target name.")
    synonyms = models.TextField(default='', blank=True)

    # external identifiers, not unique because does go with null on SQL server
    chemblid = models.TextField('ChEMBL ID',
                                default='', blank=True,
                                help_text="Enter a ChEMBL id, e.g. CHEMBL260, "
                                          "and click Retrieve to get target "
                                          "information automatically.")

    description = models.TextField(default='', blank=True)

    gene_names = models.TextField(default='', blank=True)

    organism = models.TextField(default='', blank=True)

    uniprot_accession = models.TextField(default='', blank=True)

    target_type = models.TextField(default='', blank=True)

    # NCBI identifier for protein/gene targets
    GI = models.TextField('NCBI GI',
                          default='', blank=True)

    last_update = models.DateField(blank=True, null=True,
                                   help_text="Last time when activities "
                                             "associated with the target "
                                             "were updated.")

    class Meta(object):
        ordering = ('name', )

    def __str__(self):

        return self.name

    def chembl_link(self):

        if self.chemblid:
            return ('<a href="https://www.ebi.ac.uk/chembl/target/inspect/'
                    '{0}" target="_blank">{0}</a>').format(self.chemblid)
        else:
            return ''

    chembl_link.allow_tags = True
    chembl_link.short_description = 'ChEMBL ID'


ASSAYTYPES = (('B', 'Binding'), ('F', 'Functional'), ('A', 'ADMET'), ('P', 'Physicochemical'), ('U', 'Unknown'))


class Assay(LockableModel):
    """Information for a Bioactivity Assay (not to be mistaken for models of Assays app)"""
    # external identifiers, not unique because does go with null on SQL server
    chemblid = models.TextField('ChEMBL ID',
                                default='', blank=True,
                                help_text="Enter a ChEMBL id, e.g. "
                                          "CHEMBL1217643, and click Retrieve "
                                          "to get target information "
                                          "automatically.")

    description = models.TextField(default='', blank=True,)
    organism = models.TextField(default='', blank=True,)
    assay_type = models.CharField(max_length=1, choices=ASSAYTYPES, default='U')
    journal = models.TextField(default='', blank=True,)
    strain = models.TextField(default='', blank=True,)

    pubchem_id = models.TextField('PubChem ID', default='', blank=True)
    source = models.TextField(default='', blank=True)
    source_id = models.TextField(default='', blank=True)
    name = models.TextField(default='', blank=True, verbose_name="Assay Name")

    target = models.ForeignKey('Target', default=None, verbose_name="Target", null=True, blank=True, on_delete=models.CASCADE)

    last_update = models.DateField(blank=True, null=True,
                                   help_text="Last time when activities "
                                             "associated with the assay were "
                                             "updated.")

    class Meta(object):
        ordering = ('chemblid', )

    def __str__(self):

        return self.chemblid

    def chembl_link(self):

        if self.chemblid:
            return ('<a href="https://www.ebi.ac.uk/chembl/assay/inspect/'
                    '{0}" target="_blank">{0}</a>').format(self.chemblid)
        else:
            return ''

    chembl_link.allow_tags = True
    chembl_link.short_description = 'ChEMBL ID'

DATA_VALIDITY_ANNOTATIONS = (('R', 'Outside typical range'), ('T', 'Potential transcription error'), ('O', 'Other'))


class Bioactivity(LockableModel):
    """A Bioactivity detailing the compound, target, assay, and pertinent values"""
    class Meta(object):
        verbose_name_plural = 'bioactivities'
        unique_together = ('assay', 'target', 'compound')
        ordering = ('compound', 'bioactivity_type',)

    assay = models.ForeignKey(Assay, on_delete=models.CASCADE)
    compound = models.ForeignKey(
        'compounds.Compound',
        related_name='bioactivity_compound',
        on_delete=models.CASCADE
    )
    parent_compound = models.ForeignKey(
        'compounds.Compound',
        related_name='bioactivity_parent',
        on_delete=models.CASCADE
    )

    # TODO NOTE THAT THIS TARGET IS MORE ACCURATE THAN ASSAY TARGET FOR CHEMBL
    target = models.ForeignKey(Target, on_delete=models.CASCADE)
    target_confidence = models.IntegerField(blank=True, null=True)

    bioactivity_type = models.TextField(verbose_name="name", default='', blank=True)

    standard_name = models.TextField(default='', blank=True)
    operator = models.TextField(default='', blank=True)

    units = models.TextField(default='', blank=True)
    value = models.FloatField(blank=True, null=True)

    standardized_units = models.TextField(verbose_name="std units",
                                          default='', blank=True)
    standardized_value = models.FloatField(verbose_name="std vals",
                                           blank=True,
                                           null=True)

    activity_comment = models.TextField(default='', blank=True)
    reference = models.TextField(default='', blank=True)
    name_in_reference = models.TextField(default='', blank=True)

    normalized_value = models.FloatField(blank=True,
                                         null=True,
                                         verbose_name="Normalized Value")

    # Column for notes
    notes = models.TextField(default='', blank=True)

    # Indicates the validity of the entry: empty string is valid other choices show questionable
    data_validity = models.CharField(max_length=1, choices=DATA_VALIDITY_ANNOTATIONS, default='', blank=True)

    # Use ChEMBL Assay Type to clarify unclear names like "Activity"
    # Removed for now
    # chembl_assay_type = models.TextField(blank=True, null=True, default='', blank=True)

    def organism(self):
        return self.target.organism

    def __str__(self):
        return '{}: {} {}'.format(
            self.compound,
            self.bioactivity_type,
            self.target.name
        )


class BioactivityType(LockableModel):
    """A unified Bioactivity unit with conversion"""
    class Meta(object):
        ordering = ('chembl_bioactivity', 'chembl_unit', )
    chembl_bioactivity = models.TextField(default='', blank=True)
    chembl_unit = models.TextField(default='', blank=True)
    scale_factor = models.FloatField(default=1, blank=True, null=True)
    mass_flag = models.CharField(
        max_length=8, default='N',
        choices=(('Y', 'Yes'), ('N', 'No'))
    )
    standard_name = models.TextField(default='', blank=True)
    description = models.TextField(default='', blank=True)
    standard_unit = models.TextField(default='', blank=True)

    def __str__(self):
        return str(self.standard_name)


class PubChemBioactivity(LockableModel):
    """A Bioactivity from PubChem (Bioactivity is from ChEMBL)"""
    # TextFields and CharFields have no performace benefits over eachother, but may want to use CharFields for clarity
    assay = models.ForeignKey('Assay', blank=True, null=True, on_delete=models.CASCADE)

    # It makes sense just to add the PubChem CID to the compound then just use a FK
    #compound_id = models.TextField(verbose_name="Compound ID")
    compound = models.ForeignKey('compounds.Compound', on_delete=models.CASCADE)

    # TODO SHOULD PULL TARGET FROM ASSAY IF THIS IS NONE (IF TO BE KEPT)
    target = models.ForeignKey('Target', verbose_name="Target", null=True, blank=True, on_delete=models.CASCADE)

    # Value is required
    value = models.FloatField(verbose_name="Value (uM)")

    outcome = models.TextField(default='', blank=True, verbose_name="Bioactivity Outcome")

    # Not required?
    # TODO Consider making this a FK to bioactivity types
    # TODO Or, perhaps we should make another table for PubChem types?
    activity_name = models.TextField(default='', blank=True, verbose_name="Activity Name")

    # Normalized value for visualization and so on
    # Be sure to normalize on bioactivity-target pair across the entire database
    normalized_value = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Normalized Value"
    )

    # Column for notes
    notes = models.TextField(default='', blank=True)

    # Indicates the validity of the entry: empty string is valid other choices show questionable
    data_validity = models.CharField(max_length=1, choices=DATA_VALIDITY_ANNOTATIONS, default='', blank=True)

# TODO PubChem Bioactivity Type? and PubChem targets
# To following table may eventually be merged into the existing bioactivty type table
# Deliberating, is it really worthwhile to make a model with only one field?
#class PubChemBioactivityType(LockableModel):
#    name = models.TextField(default='', blank=True)


# DEPRECATED
# TODO PubChemTarget model is slated for removal
class PubChemTarget(LockableModel):
    name = models.TextField(default='', blank=True, help_text="Preferred target name.")

    # May be difficult to acquire
    #synonyms = models.TextField(null=True, blank=True)

    # The GI is what is given by a PubChem assay
    # Optional, not all targets will have this
    GI = models.TextField('NCBI GI',
                          default='',
                          blank=True)

    # Target type is not always listed: not required
    target_type = models.TextField(default='', blank=True)

    # Organism is not always listed: not required
    organism = models.TextField(default='', blank=True)

    def __str__(self):
        return str(self.name)


# DEPRECATED
# TODO PubChemAssay model is slated for removal
class PubChemAssay(LockableModel):
    # Source is an optional field showing where PubChem pulled their data
    source = models.TextField(default='', blank=True)

    source_id = models.TextField(default='', blank=True)

    # PubChem ID
    aid = models.TextField(verbose_name="Assay ID")

    # Not required?
    name = models.TextField(default='', blank=True, verbose_name="Assay Name")

    description = models.TextField(default='', blank=True)

    def __str__(self):
        return str(self.aid)
