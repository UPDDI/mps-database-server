from haystack import indexes
from .models import OpenFDACompound, DrugTrial, FindingResult


class OpenFDACompoundIndex(indexes.SearchIndex, indexes.Indexable):
    """Search index for OpenFDA Compounds"""
    text = indexes.NgramField(document=True, use_template=True)
    rendered = indexes.CharField(use_template=True, indexed=False)

    def get_model(self):
        return OpenFDACompound


# Deprecated
# class DrugTrialIndex(indexes.SearchIndex, indexes.Indexable):
#     """Search index for Drug Trials"""
#     text = indexes.NgramField(document=True, use_template=True)
#     rendered = indexes.CharField(use_template=True, indexed=False)
#
#     def get_model(self):
#         return DrugTrial


class FindingResultIndex(indexes.SearchIndex, indexes.Indexable):
    """Search index for Drug Trials"""
    text = indexes.NgramField(document=True, use_template=True)
    rendered = indexes.CharField(use_template=True, indexed=False)

    def get_model(self):
        return FindingResult
