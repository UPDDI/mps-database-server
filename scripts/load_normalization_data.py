from drugtrials.models import OpenFDACompound
import ujson as json
from mps.settings import PROJECT_ROOT

def run():
    normalize_file = open(PROJECT_ROOT[:-4] + '/scripts/NAMCS_NHAMCS_combined_data.json', 'r')
    normalize = json.loads(normalize_file.read())
    normalize_file.close()

    failed = []

    for compound in OpenFDACompound.objects.all().prefetch_related('compound'):
        compound_name = compound.compound.name
        if compound_name in normalize:
            compound.estimated_usage = normalize.get(compound_name)
        else:
            failed.append(compound)
        compound.save()

    keys = list(normalize.keys())

    for compound in failed:
        compound_name = compound.compound.name
        found = False
        found_key = ''
        for key in keys:
            if compound_name in key:
                found = True
                found_key = key
        if found:
            compound.estimated_usage = normalize.get(found_key)
            compound.save()
