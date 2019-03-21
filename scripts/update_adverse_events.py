from compounds.models import Compound
from drugtrials.models import OpenFDACompound, CompoundAdverseEvent, AdverseEvent
from cellsamples.models import Organ

import time
import ujson as json

from mps.settings import PROJECT_ROOT

import urllib.request, urllib.parse, urllib.error
import urllib3
import certifi

try:
    from additional_credentials import openfda_api_key as api_key
except:
    api_key = ''

http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',  # Force certificate check.
    ca_certs=certifi.where(),  # Path to the Certifi bundle.
)

SCRIPTS_ROOT = PROJECT_ROOT[:-4] + '/scripts/'

# Call this with the command: ./manage.py runscript update_adverse_events

# This blacklist is a crude way of preventing some compounds from being erroneously listed as having black box warnings

# Potential additions (not listed on ChEMBL as Black Box)
# Apparently Acetaminophen actually does have a Black Box warning now (it is a leading cause of acute liver failure)
# ACETAMINOPHEN
# ALOGLIPTIN
# ELVITEGRAVIR

blacklist = {
    'CAFFEINE': 'mislabel for boxed_warning',
    'ASPIRIN': 'mislabel for boxed_warning',
    'ALOGLIPTIN': 'miscategorized',
    'ELVITEGRAVIR': 'miscategorized',
}


def get_label_field(generic_name, field):
    # WILL NEED TO CHANGE WITH PYTHON 3
    generic_name = urllib.parse.quote_plus(generic_name)

    try:
        # Arbitrary limit of 100 might not be sufficient to ensure grabbing the correct entry
        if api_key:
            url = 'https://api.fda.gov/drug/label.json?api_key=' + api_key + '&search=_exists_:{}+AND+openfda.generic_name:"{}"&limit=100'.format(field, generic_name)
        else:
            url = 'https://api.fda.gov/drug/label.json?search=_exists_:{}+AND+openfda.generic_name:"{}"&limit=100'.format(field, generic_name)
        response = http.request('GET', url)
        data = json.loads(response.data)
        for drug in data['results'][:-1]:
            # generic_name is a list initially, convert it to be a string
            if str(drug['openfda']['generic_name'][0]) == generic_name:
                ret = '\n'.join(drug[field])
                return (ret, True)

        ret = '\n'.join(data['results'][-1][field])
        return (ret, False)
    except:
        return ''


def get_event_frequency(generic_name, organs):
    # WILL NEED TO CHANGE WITH PYTHON 3
    generic_name = urllib.parse.quote_plus(generic_name)

    # Reset organ highest and count
    for key, organ in list(organs.items()):
        organ.update({'highest': 0})
        organ.update({'events': 0})

    normal_events = 0
    events = []
    try:
        if api_key:
            url = 'https://api.fda.gov/drug/event.json?api_key=' + api_key + '&search=patient.drug.openfda.generic_name:"{}"&count=patient.reaction.reactionmeddrapt.exact&limit=1000'.format(generic_name)
        else:
            url = 'https://api.fda.gov/drug/event.json?search=patient.drug.openfda.generic_name:"{}"&count=patient.reaction.reactionmeddrapt.exact&limit=1000'.format(generic_name)
        response = http.request('GET', url)
        data = json.loads(response.data)

        # Automatically take the first result, if it exists
        if data.get('results', ''):
            first = data.get('results')[0]
            term = first.get('term')
            count = first.get('count')

            first_in_organ = False

            for key, organ in list(organs.items()):
                organ_terms = organ.get('terms')
                organ_highest = organ.get('highest')
                organ_events = organ.get('events')
                if term in organ_terms:
                    events.append((term, count))
                    organ.update({'highest': count})
                    organ.update({'events': organ_events+1})
                    first_in_organ = True
            if not first_in_organ:
                events.append((term, count))
                normal_events += 1

            highest_count = count
        else:
            return []

        data_after_first = data.get('results', '')[1:]

        for event in data_after_first:
            term = event.get('term')
            count = event.get('count')

            found_in_organ = False

            for key, organ in list(organs.items()):
                organ_terms = organ.get('terms')
                organ_highest = organ.get('highest')
                organ_events = organ.get('events')
                if term in organ_terms and (count >= organ_highest*0.50 or organ_events < 5):
                    events.append((term, count))
                    organ.update({'events': organ_events+1})
                    if count > organ_highest:
                        organ.update({'highest': count})
                    found_in_organ = True
            # Only take the most frequent event and every event that is at least 50% the frequency
            # Take a minimum of FIVE (5) events
            if not found_in_organ and (count >= highest_count*0.50 or normal_events < 5):
                events.append((term, count))
                normal_events += 1
            # End if the event count is smaller (data should be in order)
            # else:
            #     return events

        # In the off chance that all of the events are at least 50%
        return events

    except:
        return []


def run():
    organs = {
        'Liver': {
                'model': Organ.objects.get(organ_name='Liver'),
                'terms': {},
                'file': SCRIPTS_ROOT + 'Liver.tsv',
                'events': 0,
                'highest': 0
        },
        'Kidney': {
                'model': Organ.objects.get(organ_name='Kidney'),
                'terms': {},
                'file': SCRIPTS_ROOT + 'Kidney.tsv',
                'events': 0,
                'highest': 0
        },
        'Intestine': {
            'model': Organ.objects.get(organ_name='Intestine'),
            'terms': {},
            'file': SCRIPTS_ROOT + 'Intestine.tsv',
            'events': 0,
            'highest': 0
        },
        'Skeletal Muscle': {
            'model': Organ.objects.get(organ_name='Skeletal Muscle'),
            'terms': {},
            'file': SCRIPTS_ROOT + 'Skeletal Muscle.tsv',
            'events': 0,
            'highest': 0
        },
        'Brain': {
            'model': Organ.objects.get(organ_name='Brain'),
            'terms': {},
            'file': SCRIPTS_ROOT + 'Brain.tsv',
            'events': 0,
            'highest': 0
        },
        'Heart': {
            'model': Organ.objects.get(organ_name='Heart'),
            'terms': {},
            'file': SCRIPTS_ROOT + 'Heart.tsv',
            'events': 0,
            'highest': 0
        }
    }

    # liver_model = Organ.objects.get(organ_name='Liver')

    # liver = {}
    # liver_file = open('/home/developer/github/mps-database-server/scripts/Liver.tsv', 'r')

    for key, organ in list(organs.items()):
        organ_file = open(organ.get('file'))
        for line in organ_file:
            line = line.strip().split('\t')
            organ.get('terms').update({line[1].upper(): True})

        organ_file.close()

    # Delete all old adverse events
    CompoundAdverseEvent.objects.all().delete()

    for compound in Compound.objects.all():
        print(compound)
        # TODO CHANGE TO ACCOMODATE ALL ORGANS
        events = get_event_frequency(compound.name, organs)
        print((len(events)))
        time.sleep(0.2)

        if events:
            # Test to see if model already exists
            try:
                compound_model = OpenFDACompound.objects.get(compound=compound)

            # Make a new OpenFDACompound model if it does not already exist
            except:
                compound_model = OpenFDACompound(compound=compound)
                compound_model.save()

            for event in events:
                # Replace ^ with '
                adverse_event = event[0].replace('^', "'")
                frequency = event[1]

                # Get adverse event if possible
                try:
                    adverse_event_model = AdverseEvent.objects.get(event=adverse_event)

                    for key, organ in list(organs.items()):
                        organ_model = organ.get('model')
                        organ_terms = organ.get('terms')
                        if adverse_event in organ_terms:
                            adverse_event_model.organ = organ_model
                            adverse_event_model.save()

                # if adverse_event does not exist
                except:
                    for key, organ in list(organs.items()):
                        organ_model = organ.get('model')
                        organ_terms = organ.get('terms')
                        if adverse_event in organ_terms:
                            adverse_event_model = AdverseEvent(
                                event=adverse_event,
                                organ=organ_model
                            )
                    else:
                        adverse_event_model = AdverseEvent(event=adverse_event)
                    adverse_event_model.save()

                try:
                    adverse_event_model = CompoundAdverseEvent(
                        compound=compound_model,
                        event=adverse_event_model,
                        frequency=frequency
                    )
                    adverse_event_model.save()
                    # print "Success!"
                except:
                    print("Fail...")

    print("Finished Adverse Events")

    time.sleep(30)

    for compound in OpenFDACompound.objects.all():
        time.sleep(1)

        if not compound.warnings and not compound.nonclinical_toxicology:
            try:
                # Warning and boxed warning are tuples: (warning, True/False for if exact match)
                warning = get_label_field(compound.compound.name, 'warnings')
                nonclinical_toxicology = get_label_field(compound.compound.name, 'nonclinical_toxicology')

                if nonclinical_toxicology:
                    nonclinical_toxicology = nonclinical_toxicology[0]

                if compound.compound.name not in blacklist:
                    boxed_warning = get_label_field(compound.compound.name, 'boxed_warning')
                else:
                    boxed_warning = None

                if boxed_warning and (boxed_warning[1] or not(warning)):
                    compound.warnings = boxed_warning[0]
                    compound.black_box = True
                    compound.nonclinical_toxicology = nonclinical_toxicology
                    compound.save()
                    print("Black Box Warning found")

                elif warning:
                    compound.warnings = warning[0]
                    compound.nonclinical_toxicology = nonclinical_toxicology
                    compound.save()
                    print("Warning found")

                else:
                    warnings_and_precautions = get_label_field(compound.compound.name, 'warnings_and_precautions')

                    if warnings_and_precautions:
                        warnings_and_precautions = warnings_and_precautions[0]

                    compound.warnings = warnings_and_precautions
                    compound.nonclinical_toxicology = nonclinical_toxicology
                    compound.save()
                    print("Attempted to find warning in warnings_and precautions")
            except:
                print("An error occurred")
