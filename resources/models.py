from django.db import models
from mps.base.models import LockableModel
from django.utils.html import format_html


class ResourceSubtype(LockableModel):
    """A Resource Subtype specifies a category (e.g. supplier, database, etc.

    PLEASE NOTE: Subtype is referred to as a 'Category' typically
    """
    class Meta(object):
        verbose_name = 'Resource category'
        verbose_name_plural = 'Resource categories'
        ordering = ['name']

    name = models.TextField(max_length=40, unique=True, verbose_name='Category')
    description = models.TextField(max_length=400, blank=True, default='')

    def __str__(self):
        return self.name


class ResourceType(LockableModel):
    """A Resource Type specifies what a resource specializes in (e.g. images, cells, etc.)"""
    class Meta(object):
        ordering = ['resource_subtype', 'resource_type_name']

    resource_type_name = models.CharField(max_length=40, unique=True, verbose_name="Type")
    description = models.CharField(max_length=400, blank=True, default='')
    resource_subtype = models.ForeignKey(ResourceSubtype, verbose_name="Category", on_delete=models.CASCADE)

    def __str__(self):
        return '{} ({})'.format(self.resource_subtype,
                                 self.resource_type_name)


class Resource(LockableModel):
    """A Resource is a specific website or location to learn more of something"""
    class Meta(object):
        ordering = ['type', 'resource_name']

    resource_name = models.CharField(max_length=60, unique=True, verbose_name="Name")
    resource_website = models.URLField(blank=True, null=True)
    description = models.CharField(max_length=400, blank=True, default='')
    type = models.ForeignKey(ResourceType, on_delete=models.CASCADE)

    def __str__(self):
        return self.resource_name

    def subtype(self):
        return self.type.resource_subtype.name


class Definition(LockableModel):
    """A Definition is a definition for the glossary found in Help"""
    term = models.CharField(max_length=60, unique=True)
    definition = models.CharField(max_length=2500, default='')
    reference = models.URLField(default='', blank=True)

    def __str__(self):
        return self.term

    def show_url(self):
        if self.reference:
            return format_html(
                "<a target='_blank' href='{url}'><span title='{url}' class='glyphicon glyphicon-link'></span></a>", url=self.reference
            )
        else:
            return ""

    show_url.short_description = "Ref URL"
    show_url.allow_tags = True
