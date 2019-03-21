# coding=utf-8

from django.http import HttpResponse, HttpResponseServerError
import ujson as json
from .models import Compound, CompoundInstance, CompoundSupplier
# from assays.utils import CHIP_DATA_PREFETCH
# from assays.models import AssayChipRawData, AssayCompoundInstance, AssayChipSetup
from assays.models import AssayDataPoint, AssaySetupCompound, AssayMatrixItem

from bioservices import ChEMBL as ChEMBLdb

# from bioactivities.models import Assay, Target

from bs4 import BeautifulSoup
import requests
import re

import numpy as np

# Calling main is and always will be indicative of an error condition.
# ajax.py is strictly for AJAX requests

# Ajax requests are sent to ajax(request) and funneled into the correct
# handler function using a simulated Python switch routing function


def main(request):
    """Default to Server Error"""
    return HttpResponseServerError()


def fetch_compound_name(request):
    """Return a compound name from a pk in JSON

    Receives the following from POST:
    compound_id -- the pk of the requested compound
    """
    data = {}

    compound = Compound.objects.filter(id=request.POST.get('compound_id', ''))

    if compound:
        data.update({'name': compound.name})
    else:
        data.update({'name': ''})

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def chembl_error(error):
    """Returns an error from ChEMBL in JSON"""
    data = {}
    data.update({'error': error})

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


# Virtually deprecated (gives incorrect values for things like known drug. Sad!
def fetch_chemblid_data(request):
    """Uses Bioservices to acquire data from ChEMBL

    Receives the following from POST:
    chemblid -- the ChEMBL ID for the desired entry
    selctor -- specifies whether the data is for a compound, assay, or target
    """
    chemblid = request.POST.get('chemblid', '')
    selector = request.POST.get('selector', '')

    if not chemblid or not selector:
        return main(request)

    if chemblid.startswith('CHEMBL') and chemblid[6:].isdigit():
        try:
            if 'compound' == selector:
                data = ChEMBLdb().get_compounds_by_chemblId(str(chemblid))
            elif 'assay' == selector:
                data = ChEMBLdb().get_assay_by_chemblId(str(chemblid))
            elif 'target' == selector:
                data = ChEMBLdb().get_target_by_chemblId(str(chemblid))

        except Exception:
            return chembl_error(
                '"{}" did not match any compound records.'.format(chemblid)
            )

    else:
        return chembl_error(
            '"{}" is not a valid ChEMBL id.'.format(chemblid)
        )

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def get_chembl_compound_data(chemblid):
    """Returns a dictionary of ChEMBL data given a chemblid"""
    data = {}

    url = 'https://www.ebi.ac.uk/chembl/api/data/molecule/{}.json'.format(chemblid)
    response = requests.get(url)
    initial_data = json.loads(response.text)

    if initial_data:
        molecular_structures = initial_data.get('molecule_structures', {})

        if molecular_structures:
            data['name'] = initial_data.get('pref_name', '')
            data['inchikey'] = molecular_structures.get('standard_inchi_key', '')
            data['smiles'] = molecular_structures.get('canonical_smiles', '')

        # Start known drug as False
        data['known_drug'] = False
        # Get synonyms and check if it is a drug too
        synonyms = []
        for entry in initial_data.get('molecule_synonyms', []):
            synonym = entry.get('synonyms', '')
            syn_type = entry.get('syn_type', '')
            if synonym and synonym not in synonyms:
                synonyms.append(synonym)
            # Check whether the synonym is a International, FDA, British Approved, or US Adopted Name
            # This technique includes pesticides, however they are *usually* also used topically, and thus drugs
            if syn_type in ['INN', 'FDA', 'BAN', 'USAN', 'JAN']:
                data['known_drug'] = True
        data['synonyms'] = ', '.join(synonyms)

        molecular_properties = initial_data.get('molecule_properties', {})

        if molecular_properties:
            data['chemblid'] = chemblid
            data['molecular_formula'] = molecular_properties.get('full_molformula', '')
            data['molecular_weight'] = molecular_properties.get('full_mwt', '')
            data['rotatable_bonds'] = molecular_properties.get('rtb', '')
            data['acidic_pka'] = molecular_properties.get('acd_most_apka', '')
            data['basic_pka'] = molecular_properties.get('acd_most_bpka', '')
            data['logp'] = molecular_properties.get('acd_logp', '')
            data['logd'] = molecular_properties.get('acd_logd', '')
            data['alogp'] = molecular_properties.get('alogp', '')
            data['species'] = molecular_properties.get('molecular_species', '')
            data['ro5_violations'] = molecular_properties.get('num_ro5_violations', '')

            if molecular_properties.get('ro3_pass', 'N') == 'Y':
                data['ro3_passes'] = True
            else:
                data['ro3_passes'] = False

        # Get medchem alerts
        medchem_alerts = False
        # Get URL of target for scrape
        url = "https://www.ebi.ac.uk/chembl/compound/structural_alerts/{}".format(chemblid)
        # Make the http request
        response = requests.get(url)
        # Get the webpage as text
        stuff = response.text
        # Make a BeatifulSoup object
        soup = BeautifulSoup(stuff, 'html5lib')

        # Get all tables
        table = soup.find(id="structural_wedding")
        # If there is a table and it contains alerts
        if table and table.tbody.text.strip():
            medchem_alerts = True

        data['medchem_alerts'] = medchem_alerts

    return data


def fetch_chembl_compound_data(request):
    """Returns ChEMBL data in JSON

    Receives the following from POST:
    chemblid -- the chemblid of the desired compound
    """
    chemblid = request.POST.get('chemblid', '')

    data = get_chembl_compound_data(chemblid)

    return HttpResponse(json.dumps(data),
                        content_type='application/json')


# TODO TODO TODO TODO TODO
def fetch_compound_report(request):
    """Return in JSON the data required to make a compound report

    Receives the following from POST:
    compounds -- the names of the desired ChEMBL ids
    """

    # Should "compounds" be pk's instead of names?
    compounds_request = json.loads(request.POST.get('compounds', []))

    data = {}

    # TODO WHY IS COMPOUND PASSED AS A NAME?
    compounds = Compound.objects.filter(name__in=compounds_request)

    for compound in compounds:
        data.update(
            {compound.name: {
                'table': {
                    'id': compound.id,
                    'preclinical': compound.preclinical,
                    'clinical': compound.clinical,
                    'pk_metabolism': compound.pk_metabolism,
                    'post_marketing': compound.post_marketing,
                    'logP': compound.logp,
                    'max_time': {}
                },
                'plot': {}
            }}
        )

    setup_compounds = AssaySetupCompound.objects.filter(
        compound_instance__compound__name__in=compounds_request
    ).prefetch_related(
        'compound_instance__compound',
        'concentration_unit'
    )

    matrix_item_id_to_compounds_map = {}

    for setup_compound in setup_compounds:
        matrix_item_id_to_compounds_map.setdefault(
            setup_compound.matrix_item_id, []
        ).append(setup_compound)

    studies = AssayMatrixItem.objects.filter(
        id__in=matrix_item_id_to_compounds_map
    ).values_list('study_id', flat=True)

    control_data_points = AssayDataPoint.objects.filter(
        replaced=False,
        excluded=False,
        study__use_in_calculations=True,
        study_id__in=studies,
        matrix_item__assaysetupcompound__isnull=True
    ).prefetch_related(
        # TODO
        'study',
        'study_assay__target'
    )
    initial_control_data = {}
    control_data = {}

    for data_point in control_data_points:
        if data_point.value:
            initial_control_data.setdefault(
                data_point.study_id, {}
            ).setdefault(
                data_point.study_assay.target.short_name, {}
            ).setdefault(
                data_point.time, []
            ).append(data_point.value)

    for study_id, studies in list(initial_control_data.items()):
        for assay, assays in list(studies.items()):
            for time, times in list(assays.items()):
                control_data.update({
                    (study_id, assay, time): np.average(times)
                })

    data_points = AssayDataPoint.objects.filter(
        replaced=False,
        excluded=False,
        study__use_in_calculations=True,
        matrix_item_id__in=matrix_item_id_to_compounds_map
    ).prefetch_related(
        'study',
        'study_assay__target'
    )

    for data_point in data_points:
        study_id = data_point.study_id
        assay = data_point.study_assay.target.short_name
        time = data_point.time
        value = data_point.value

        if control_data.get((study_id, assay, time)) and value:
            for setup_compound in matrix_item_id_to_compounds_map.get(
                    data_point.matrix_item_id
            ):
                if setup_compound.addition_time <= time:
                    data.get(
                        setup_compound.compound_instance.compound.name, {}
                    ).get(
                        'plot'
                    ).setdefault(
                        assay, {}
                    ).setdefault(
                        '{0:.2f}_{1}'.format(
                            setup_compound.concentration,
                            setup_compound.concentration_unit.unit
                        ), {}
                    ).setdefault(
                        '{0:.2f}'.format(time / 1440), []
                    ).append(
                        value / control_data.get(
                            (study_id, assay, time)
                        )
                    )

    # Average out the values
    for compound in data:
        plot = data.get(compound).get('plot')
        for assay in plot:
            for concentration in plot[assay]:
                entry = plot[assay][concentration]
                averaged_plot = {}
                for time, values in list(entry.items()):
                    averaged_plot.update({time: np.average(values)})
                # Add maximum
                times = [float(t) for t in list(entry.keys())]
                if assay not in data[compound]['table']['max_time'] or \
                        max(times) > data[compound]['table']['max_time'][assay]:
                    data[compound]['table']['max_time'].update({assay: max(times)})
                # Add arbitrary 0 as necessary (won't make a line otherwise
                if len(averaged_plot) == 1:
                    averaged_plot.update({'0': 0})
                # Switch to averaged values
                plot[assay][concentration] = averaged_plot

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def fetch_compound_list(request):
    """This function just gets a list of compounds and returns it in JSON"""
    # Why does this function exist? To have compound search suggestions without violating SOC
    data = [compound.name for compound in Compound.objects.all()]
    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def get_drugbank_target_information(data, type_of_target):
    """Return a dictionary of DrugBank data

    Parameters:
    data -- raw html for the target
    type_of_target -- the type of target (e.g. 'Transporter')
    """
    target = {
        'name': '',
        # May not be present
        'uniprot_id': '',
        'action': '',
        'pharmacological_action': '',
        'organism': '',
        'type': type_of_target
    }

    try:
        # Get name from header (table may not be present?)
        name = data.findChildren('strong')[0].findChildren('a')[0].text
    except:
        name_text = data.findChildren('strong')[0].text.split('.')[1:]
        name = ''.join(name_text).strip()

    if len(name) > 150:
        name = name[:145] + '...'

    target['name'] = name

    headers = data.findChildren('dt')
    values = data.findChildren('dd')

    for index, dt in enumerate(headers):
        dd = values[index]
        if dt.text == 'Organism':
            organism = dd.text.strip()

            if len(organism) > 150:
                organism = organism[:145] + '...'

            target['organism'] = organism

        elif dt.text == 'Pharmacological action':
            # Badges are used to show pharmacological action
            label = dd.findChildren('div', class_='badge')

            if label:
                target['pharmacological_action'] = label[0].text.strip()

        elif dt.text == 'Actions':
            # Badges contain actions
            badges = dd.findChildren('div', class_='badge')
            actions = []

            for badge in badges:
                actions.append(badge.text.strip())

            target['action'] = ', '.join(actions)

        elif dt.text == 'Uniprot ID':
            uniprot = dd.findChildren('a')

            if uniprot:
                if 'www.uniprot.org' in uniprot[0]['href']:
                    target['uniprot_id'] = uniprot[0].text.strip()

    return target


def get_drugbank_data_from_chembl_id(chembl_id):
    """Returns a dictionary of data acquired from DrugBank and PubChem"""
    # Values found in table
    data = {
        'drugbank_id': '',
        'pubchemid': '',
        'drug_class': '',
        'protein_binding': '',
        'half_life': '',
        'clearance': '',
        'bioavailability': '',
        'absorption': '',
    }

    # Get drugbank_id or fail
    url = 'https://www.ebi.ac.uk/unichem/rest/src_compound_id/{}/1/2'.format(chembl_id)
    # Make the http request
    response = requests.get(url)
    # Get the webpage in JSON
    json_data = json.loads(response.text)

    if json_data and 'error' not in json_data:
        # Get drugbank_id
        drugbank_id = json_data[0].get('src_compound_id')
        # Assign drugbank id right away
        data['drugbank_id'] = drugbank_id

        # Get URL of target for scrape
        url = "http://www.drugbank.ca/drugs/{}".format(drugbank_id)
        # Make the http request
        response = requests.get(url)
        # Get the webpage as text
        stuff = response.text
        # Make a BeatifulSoup object
        soup = BeautifulSoup(stuff, 'html5lib')

        # Get all tables
        tables = soup.findChildren('dl')

        # Regex for extracting percentages
        percent_extractor = re.compile(r'<?\>?\d*\.?\d+%')

        # Units for half life
        units = ['week', 'day', 'hour', 'minute', 'second']

        # Regex for extracting SPECIFICALLY floats
        # float_extractor = re.compile(r'\d+\.\d+')
        # Regex for extracting ints (ignores anything with periods)
        # integer_extractor = re.compile(r'(?<!\.)(?<!\d)\d+(?!\.)')
        # Regex for extracting ints or floats
        integer_and_float_extractor = re.compile(r'\d*\.?\d+')

        # Loop through every dl
        for dl in tables:
            dts = dl.findChildren('dt')
            dds = dl.findChildren('dd')

            for index, dt in enumerate(dts):
                header = dt.text
                dd = dds[index]

                # Handled earlier, skip
                # if header == 'Accession Number':
                #     data['drugbank_id'] = dd.text

                # TODO MAKE A NEW FIELD FOR CLASS AND RENAME SUB CLASS
                if header == 'Sub Class':
                    # The sub class is in the text of a link
                    # There might not be a sub class
                    if dd.findChildren('a'):
                        drug_class = dd.findChildren('a')[0].text.rstrip()

                        if len(drug_class) > 150:
                            drug_class = drug_class[:145] + '...'

                        data['drug_class'] = drug_class

                elif header == 'Protein binding':
                    # Trim protein binding to get just the percentage
                    # There might not be protein binding
                    if dd.findChildren('p'):
                        protein_binding_initial = dd.findChildren('p')[0].text
                        protein_binding_processed = re.findall(percent_extractor, protein_binding_initial)
                        # If there are multiple, which do I take?
                        # Taking first percent for now
                        if protein_binding_processed:
                            data['protein_binding'] = protein_binding_processed[0]

                        # If regex has failed and 'percent' is in the strings
                        elif 'percent' in protein_binding_initial:
                            protein_binding_processed = re.findall(
                                re.compile(r'<?\>?\d*\.?\d+\spercent'),
                                protein_binding_initial
                            )
                            if protein_binding_processed:
                                data['protein_binding'] = protein_binding_processed[0]

                        # If +/- is in the string, the percent is likely the deviation
                        if '+/-' in protein_binding_initial:
                            protein_binding_processed = protein_binding_initial.split('+/-')
                            protein_binding_processed = re.findall(
                                integer_and_float_extractor,
                                protein_binding_processed[0]
                            )
                            if protein_binding_processed:
                                data['protein_binding'] = protein_binding_processed[0]

                        if '±' in protein_binding_initial:
                            protein_binding_processed = protein_binding_initial.split('±')
                            protein_binding_processed = re.findall(
                                integer_and_float_extractor,
                                protein_binding_processed[0]
                            )
                            if protein_binding_processed:
                                data['protein_binding'] = protein_binding_processed[0]

                # NOT GUARANTEED TO BE 100% ACCURATE
                elif header == 'Half life':
                    # Take full string
                    # Might not exist
                    # Be sure to decode for unicode comparisons
                    if dd.findChildren('p'):
                        life = dd.findChildren('p')[0].text

                        # Remove 't1/2' to eliminate confusion for the parser
                        life = life.replace('t1/2', '')

                        unit = ''
                        for possible_unit in units:
                            if not unit and possible_unit in life:
                                unit = possible_unit
                            # If a unit has already been selected, trim life to remove distracting units
                            elif unit and possible_unit in life:
                                life = life[life.index(possible_unit):]

                        # Special exception for min (abbreviation of minutes)
                        if not unit and 'min' in life:
                            unit = 'min'

                        if unit:
                            trimmed_life = life[:life.index(unit)]
                            found_numbers = re.findall(integer_and_float_extractor, trimmed_life)

                            # Make sure the numbers aren't jumbled (float came second and integer came first)
                            found_numbers.sort(key=float)

                            # If it is plus or minus
                            if '+/-' in trimmed_life or '±' in trimmed_life:
                                found_numbers = [
                                    str(float(found_numbers[-1])-float(found_numbers[0])),
                                    str(float(found_numbers[-1])+float(found_numbers[0]))
                                ]

                            # Take first two
                            data['half_life'] = '-'.join(found_numbers[:2]) + ' ' + unit + 's'.lstrip()

                # THIS IS NOW A UL
                # Be sure to trim
                elif header == 'Clearance':
                    # Might not exist
                    # Get rid of bullets with lstrip
                    clearance = []
                    clearance_lis = dd.findChildren('li')

                    for li in clearance_lis:
                        clearance.append(li.text.lstrip())

                    clearance = '\n'.join(clearance)

                    if len(clearance) > 500:
                        clearance = clearance[:495] + '...'

                    data['clearance'] = clearance

                # Be sure to trim
                elif header == 'Absorption':
                    # Might not exist
                    if dd.findChildren('p'):
                        absorption_initial = dd.findChildren('p')[0].text

                        # Absorption is just the full text
                        absorption = absorption_initial
                        if len(absorption) > 1000:
                            absorption = absorption[:995] + '...'
                        data['absorption'] = absorption

                        # Find percent for bioavailability
                        bioavailability_initial = re.findall(percent_extractor, absorption_initial)
                        # If there are multiple, which do I take?
                        # Taking first percent for now
                        if bioavailability_initial:
                            data['bioavailability'] = bioavailability_initial[0]

        # Convert Not Available to None (for clarity)
        for key, value in list(data.items()):
            if value == 'Not Available':
                data.update({key: ''})

        # Array of targets
        targets = []

        classes = {
            'targets': 'Target',
            'enzymes': 'Enzyme',
            'carriers': 'Carrier',
            'transporters': 'Transporter',
        }

        # Loop through all target cards
        for class_name, full_name in list(classes.items()):
            listed_targets = soup.findChildren('div', class_=class_name)

            if listed_targets:
                listed_targets = listed_targets[0].findChildren('div', class_='bond')

                for target in listed_targets:
                    to_add = get_drugbank_target_information(target, full_name)
                    if to_add.get('name', ''):
                        targets.append(to_add)

        # Remember that targets is a list!
        data.update({'targets': targets})

    # YES, I know that the function title is deceiving in that this is actually a PubChem ID
    # Get pubchemid from unichem too
    url = 'https://www.ebi.ac.uk/unichem/rest/src_compound_id/{}/1/22'.format(chembl_id)
    # Make the http request
    response = requests.get(url)
    # Get the webpage in JSON
    json_data = json.loads(response.text)

    if json_data and 'error' not in json_data:
        # Extract ID
        pubchemid = json_data[0].get('src_compound_id')
        data.update({'pubchemid': pubchemid})

    return data


def fetch_drugbank_data(request):
    """Get DrugBank and PubChem data and return it as JSON

    Receives the following from POST:
    chembl_id -- the ChEMBL ID for the desired compound
    """
    chembl_id = request.POST.get('chembl_id', '')

    data = get_drugbank_data_from_chembl_id(chembl_id)

    return HttpResponse(json.dumps(data),
                        content_type='application/json')


def fetch_chembl_search_results(request):
    """Returns ChEMBL search results as JSON

    Receives the following from POST:
    query -- the query for ChEMBL
    """
    query = request.POST.get('query', '')

    url = 'https://www.ebi.ac.uk/chembl/api/data/chembl_id_lookup/search.json?q={}'.format(query)
    # Make the http request
    response = requests.get(url)
    # Get the webpage in JSON
    json_data = json.loads(response.text)

    lookups = json_data.get('chembl_id_lookups', [])

    results = []
    for lookup in lookups:
        if lookup.get('entity_type', '') == 'COMPOUND' and lookup.get('status', '') == 'ACTIVE':
            additional_data = {}
            chembl_id = lookup.get('chembl_id', '')

            url = 'https://www.ebi.ac.uk/chembl/api/data/molecule/{}.json'.format(chembl_id)
            # Make the http request
            response = requests.get(url)
            # Get the webpage in JSON
            json_data = json.loads(response.text)

            additional_data.update({'name': json_data.get('pref_name', '')})

            synonyms = []
            for entry in json_data.get('molecule_synonyms', []):
                synonym = entry.get('synonyms', '')
                if synonym and synonym not in synonyms:
                    synonyms.append(synonym)

            synonyms = ', '.join(synonyms)
            additional_data.update({'synonyms': synonyms})

            lookup.update(additional_data)
            results.append(lookup)

    return HttpResponse(json.dumps(results),
                        content_type="application/json")


# TODO this function should initially split the date in lieu of doing that in JS
def fetch_compound_instances(request):
    """Returns all compound instances as JSON"""
    data = {
        'suppliers': [],
        'instances': []
    }

    for compound_instance in CompoundInstance.objects.all().prefetch_related(
        'compound',
        'supplier'
    ):
        data.get('instances').append({
            'id': compound_instance.id,
            'compound_id': compound_instance.compound.id,
            'supplier_name': compound_instance.supplier.name,
            'lot': compound_instance.lot,
            'receipt_date': compound_instance.receipt_date
        })

    for supplier in CompoundSupplier.objects.all():
        data.get('suppliers').append({
            'id': supplier.id,
            'name': supplier.name
        })

    return HttpResponse(json.dumps(data),
                        content_type="application/json")

switch = {
    'fetch_compound_name': fetch_compound_name,
    'fetch_chemblid_data': fetch_chemblid_data,
    'fetch_compound_report': fetch_compound_report,
    'fetch_compound_list': fetch_compound_list,
    'fetch_drugbank_data': fetch_drugbank_data,
    'fetch_chembl_search_results': fetch_chembl_search_results,
    'fetch_chembl_compound_data': fetch_chembl_compound_data,
    'fetch_compound_instances': fetch_compound_instances
}


# Should probably consolidate these (DRY)
def ajax(request):
    """Switch to correct function given POST call

    Receives the following from POST:
    call -- What function to redirect to
    """
    post_call = request.POST.get('call', '')

    # Abort if there is no valid call sent to us from Javascript
    if not post_call:
        return main(request)

    # Route the request to the correct handler function
    # and pass request to the functions
    try:
        # select the function from the dictionary
        procedure = switch[post_call]

    # If all else fails, handle the error message
    except KeyError:
        return main(request)

    else:
        # execute the function
        return procedure(request)
