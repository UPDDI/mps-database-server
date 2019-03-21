from django.db import models
from mps.base.models import LockableModel


class Disease(LockableModel):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(default='', blank=True)

    # Everything necessary for the Overview Page
    overview_state_blurb = models.TextField(
        default='',
        blank=True,
        help_text="NOTE: Use HTML tags to create lists."
    )
    overview_state_image = models.ImageField(
        upload_to='disease_images',
        null=True,
        blank=True
    )

    # Everything necessary for the Biology Page
    biology_blurb = models.TextField(
        default='',
        blank=True,
        help_text="NOTE: Use HTML tags to create lists."
    )
    biology_image = models.ImageField(
        upload_to='disease_images',
        null=True,
        blank=True
    )
    biology_kegg_pathway_map = models.ImageField(
        upload_to='disease_images',
        null=True, blank=True,
        help_text="NOTE: Save and upload the KEGG Pathway Map."
    )
    biology_kegg_pathway_url = models.CharField(
        max_length=400,
        default="https://www.genome.jp/kegg/",
        help_text="Example: http://www.genome.jp/kegg-bin/show_pathway?hsa04932 (Direct link to KEGG Pathway Map)"
    )
    biology_kegg_url = models.CharField(
        max_length=400,
        default="https://www.genome.jp/kegg/",
        help_text="Example: https://www.genome.jp/dbget-bin/www_bget?ds:H01333 (Link to KEGG Disease Entry)"
    )

    biology_genomic_geo_url = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )
    biology_genomic_omim_url = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="NOTE: On the OMIM result page for this disease, click the blue 'Gene Map Table' button before copying the URL."
    )
    biology_genomic_exsnp_url = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )
    biology_genomic_diseasesorg_url = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    # Everything necessary for the Clinical Data Page
    clinicaldata_blurb = models.TextField(
        default='',
        blank=True,
        help_text="NOTE: Use HTML tags to create lists."
    )
    clinicaldata_image = models.ImageField(
        upload_to='disease_images',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name
