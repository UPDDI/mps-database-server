from haystack import indexes
from .models import Definition


class DefinitionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.NgramField(document=True, use_template=True)

    rendered = indexes.CharField(use_template=True, indexed=False)

    def get_model(self):
        return Definition

    def index_queryset(self, using=None):
        # FILTER FOR ONLY GLOSSARY DISPLAY
        return self.get_model().objects.filter(glossary_display=True)
