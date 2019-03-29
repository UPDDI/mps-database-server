from compounds.models import Compound
from bioactivities.models import PubChemBioactivity, Target, Assay

from bs4 import BeautifulSoup
import urllib.request, urllib.parse, urllib.error
import requests
import ujson as json

import numpy as np

# Call this with the command: ./manage.py runscript update_pubchem

# 0.)AID    1.)AID Version    2.)AID Revision    3.)Panel Member ID    4.)SID
# 5.)CID    6.)Bioactivity Outcome    7.)Target GI    8.)Activity Value [uM]
# 9.)Activity Name    10.)Assay Name 11.)Bioassay Type 12.)PubMed ID
# 13.)RNAi 14.)Gene Target if RNAi

# TODO REPLACE PUBCHEM TARGET AND PUBCHEM ASSAY


def get_chembl_target(target):
    data = {}

    try:
        # Get URL of target for scrape
        url = "https://www.ebi.ac.uk/chembl/target/inspect/{}/".format(target)
        # Make the http request
        response = requests.get(url)
        # Get the webpage as text
        stuff = response.text
        # Make a BeatifulSoup object
        soup = BeautifulSoup(stuff)

        table = soup.find('table', class_='contenttable_lmenu')
        rows = table.findAll('td')

        chemblid = ''
        target_type = ''
        name = ''
        synonyms = ''
        organism = ''

        for index in range(len(rows)):
            contents = rows[index].text

            if contents == 'Target ID':
                chemblid = rows[index+1].text.strip()

            elif contents == 'Target Type':
                target_type = rows[index+1].text.strip()

            elif contents == 'Preferred Name':
                name = rows[index+1].text.strip()

            elif contents == 'Synonyms':
                synonyms = rows[index+1].text.strip()

            elif contents == 'Organism':
                organism = rows[index+1].text.strip()

        data.update({
            'chemblid': chemblid,
            'target_type': target_type,
            'name': name,
            'organism': organism,
            'synonyms': synonyms,
        })
    except:
        print(('Failed target {}'.format(target)))

    return data

    #print 'id:', chemblid, 'type:', target_type, 'name:', name, 'organism:', organism


def get_chembl_assay(assay):
    data = {}

    try:
        # Get URL of target for scrape
        url = "https://www.ebi.ac.uk/chembl/assay/inspect/{}/".format(assay)
        # Make the http request
        response = requests.get(url)
        # Get the webpage as text
        stuff = response.text
        # Make a BeatifulSoup object
        soup = BeautifulSoup(stuff)

        table = soup.find('table', class_='contenttable_lmenu')
        rows = table.findAll('td')

        # Try to get chemblid, description, organism, assay_type, journal, strain
        chemblid = rows[1].text.strip()
        # NOTE THAT ONLY THE FIRST UPPER CASE LETTER IS TAKEN
        assay_type = rows[3].text.strip().upper()[0]
        description = rows[5].text.strip()
        journal = rows[9].text.strip()
        organism = rows[11].text.strip()
        strain = rows[13].text.strip()

        target_table = soup.find(id='bioactSummary')
        link = target_table.find('a')

        # Try to get the target ID
        target = link['href'].split('/')[-1]

        if target:
            target_data = get_chembl_target(target)
            existing = Target.objects.filter(chemblid=target_data.get('chemblid'))
            # If not existing, make the entry
            if not existing:
                try:
                    new_target = Target.objects.create(**target_data)
                    data.update({'target_id': new_target.id})
                except:
                    print(('Failed creating target {}'.format(target)))
            else:
                existing_assay = existing[0]
                data.update({'target_id': existing_assay.id})
                existing.update(**target_data)

        data.update({
            'chemblid': chemblid,
            'assay_type': assay_type,
            'description': description,
            'journal': journal,
            'organism': organism,
            'strain': strain,
        })
    except Exception as e:
        print(('Failed assay {}'.format(assay)))
        print(e)

    return data


def get_pubchem_target(target):
    final_target = None

    if target:
        # If the target is in the database
        try:
            final_target = Target.objects.get(GI=target)
            #print "Found target!"
        # If the target is not in the database, create it
        except:

            try:
                # Get URL of target organism for scrape
                url = "http://togows.dbcls.jp/entry/protein/{}/organism".format(target)
                # Make the http request
                response = urllib.request.urlopen(url)
                # Get the webpage as text
                data = response.read()

                organism = data.strip().strip('.')

                # Get URL of target definition for scrape
                url = "http://togows.dbcls.jp/entry/protein/{}/definition".format(target)
                # Make the http request
                response  = urllib.request.urlopen(url)
                # Get the webpage as text
                data = response.read()

                # If the entry is annoying
                if 'RecName: Full=' in data:
                    full = data.split(';')[0]
                    full = full.replace('RecName: Full=', '')
                    name = full.strip().strip('.')
                else:
                    name = data.strip().strip('.')

                # Remove superfluous organism in name (if it is already listed separately, what is the point?)
                if '[{}]'.format(organism) in name:
                    name = name.replace('[{}]'.format(organism), '').strip()

                entry = {
                    'name': name,
                    'organism': organism,
                    'GI': target,
                    'target_type': 'SINGLE PROTEIN'
                }

                target_model = Target.objects.create(locked=True, **entry)
                final_target = target_model
                #print "Created target!"

            except:

                entry = {
                    'name': name,
                    'organism': organism,
                    'GI': target,
                    'target_type': 'SINGLE PROTEIN'
                }

                target_model = Target.objects.create(locked=True, **entry)
                final_target = target_model

                print(("Error processing target:", target))

    return final_target


def get_cid(param, string):
    """
    Acquires PubChem CID if compound does not currently have a CID associated with it
    """
    url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/{}/{}/json'.format(param, string)
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())

    data = data.get('PC_Compounds', '[{}]')

    data = data[0]

    try:
        cid = data.get('id', '').get('id', '').get('cid', '')
        return cid

    except:
        return ''


def get_bioactivities(cid):
    # Using the inchikey has the consequence of failing when PubChem "doesn't like" the inchikey
    # or the inchikey does not exist to begin with
    # Likewise, using the name can cause collisions between similar names (eg. ZIMELDINE AND ZIMELDINE HYDROCHLORIDE)
    url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{}/assaysummary/json'.format(cid)
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())

    data = data.get('Table', '')

    if not data:
        return []

    activities = []
    assays = {}

    if data.get('Row', ''):
        for entry in data.get('Row'):
            entry = entry.get('Cell', '')

            if entry:
                AID = entry[0]
                CID = entry[5]
                outcome = entry[6]
                # The target is only sometimes listed
                target = entry[7]
                value = entry[9]
                # Please note that specifying the units as micromolar is superfluous and thus these strings are removed
                activity_name = entry[10].replace(' (uM)', '').replace('_uM', '').replace('_MICROM', '')

                # TODO Insert code to add/handle Bioactivity Types?
                # Do not add outcome to returned data, assumed to be active
                if AID and CID and outcome and value and activity_name:

                    if not AID in assays:
                        assays.update({AID: [len(activities)]})
                    else:
                        assays.get(AID).append(len(activities))

                    activities.append({
                        'compound_id': CID,
                        'value': value,
                        'activity_name': activity_name,
                        'outcome': outcome,
                    })

        # Some entries might be empty thus check for assays
        if assays:

            all_assays = [x for x in assays]
            flat_assays = []

            # Need to split into a series of queries due to the limit on URL length
            for i in range(0, len(all_assays),500):
                batch = ','.join(all_assays[i:i+500])
                flat_assays.append(batch)

            for assay in flat_assays:
                assay_url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/{}/summary/json'.format(assay)
                assay_response = urllib.request.urlopen(assay_url)
                assay_data = json.loads(assay_response.read())
                assay_data = assay_data.get('AssaySummaries').get('AssaySummary')

                for assay in assay_data:
                    aid = str(assay.get('AID'))

                    if 'Target' in assay:
                        target = str(assay.get('Target')[0].get('GI', ''))

                    comment = assay.get('Comment', '')

                    target_type = ''
                    organism = ''

                    for entry in comment:
                        if entry.startswith('Target Type'):
                            target_type = entry.split(': ')[-1].strip()
                        elif entry.startswith('Organism'):
                            organism = entry.split(': ')[-1].strip()

                    # Try to get an assay with this AID from the database
                    try:
                        assay_model = Assay.objects.get(pubchem_id=aid)
                        # Add the GI to the target if necessary
                        if assay_model.target:
                            target_model = assay_model.target
                            if not target_model.GI:
                                target_model.GI = target
                                target_model.save()
                            if not target_model.target_type:
                                target_model.target_type = target_type
                                target_model.save()
                        #print "Found assay!"

                    except:
                        source = assay.get('SourceName')
                        source_id = assay.get('SourceID')
                        name = assay.get('Name')
                        description = '\n'.join(assay.get('Description')).strip()

                        entry = {
                            'pubchem_id': aid,
                            'source': source,
                            'source_id': source_id,
                            'name': name,
                            'description': description,
                            'organism': organism,
                            'chemblid': '',
                            'assay_type': 'U',
                            'journal': 'strain',
                        }

                        # If this is NOT a ChEMBL assay, then also get the target and add it
                        # If it is, that should be caught later
                        if source != 'ChEMBL':
                            entry.update({'target': get_pubchem_target(target)})

                        assay_model = Assay.objects.create(locked=True, **entry)
                        #print "Created assay!"

                    activities_to_change = assays.get(aid)

                    for index in activities_to_change:
                        activities[index].update({'assay': assay_model})

        return activities

    else:
        return []


def delete_from_activity_name(string):
    """Remove undesired portion of activity name"""
    for bio in PubChemBioactivity.objects.filter(activity_name__contains=string):
        # print 'Removing {0} from {1}'.format(string, bio.activity_name)
        bio.activity_name = bio.activity_name.replace(string, '')
        bio.save()


def replace_with_activity_name(original, new):
    """Replace undesired portion of activity namea"""
    for bio in PubChemBioactivity.objects.filter(activity_name__contains=original):
        # print 'Replacing {0} with {1}'.format(original, new)
        bio.activity_name = bio.activity_name.replace(original, new)
        bio.save()


def purify_activity_name(string):
    """Completely overwrite activity names containing the string of interest"""
    for bio in PubChemBioactivity.objects.filter(activity_name__contains=string):
        # print 'Purifying {}'.format(bio.activity_name)
        bio.activity_name = string
        bio.save()


def run():
    # Remove all old bioactivities
    PubChemBioactivity.objects.all().delete()

    success = 0
    fail_bioactivity = 0
    fail_compound = 0

    # TODO make pubchem bioactivity entries for each activity
    for compound in Compound.objects.all():
        if not compound.pubchemid:
            # Prefer search by name, as inchikeys from ChEMBL are not always the best
            cid = get_cid('name', compound.name)

            # If the search by name failed, use the inchikey
            if not cid:
                cid = get_cid('inchikey', compound.inchikey)

            if cid:
                compound.pubchemid = cid
                compound.save()

        if compound.pubchemid:
            activities = get_bioactivities(compound.pubchemid)
            if activities:
                # Add CID to compound
                # add back in later, need to potentially rectify some CID
                # if not compound.pubchemid:
                # cid = activities[0].get('compound_id')
                # compound.pubchemid = cid
                # compound.save()

                for activity in activities:
                    # Add the bioactivity
                    entry = {
                        'outcome': activity.get('outcome'),
                        'assay': activity.get('assay'),
                        'compound': compound,
                        'target': activity.get('target'),
                        'value': activity.get('value'),
                        'activity_name': activity.get('activity_name')
                    }
                    try:
                        PubChemBioactivity.objects.create(locked=True, **entry)
                        # print "Success!"
                        success += 1
                    except:
                        print("Failed bioactivity...")
                        fail_bioactivity += 1
        else:
            print(("Failed compound: {}...".format(compound.name)))
            fail_compound += 1

    print(("Compound Failures:{}".format(fail_compound)))
    print(("Bioactivity Failures:{}".format(fail_bioactivity)))
    print(("Success:{}".format(success)))

    print("Cleaning up activity names...")

    delete_from_activity_name('-Replicate_1')
    delete_from_activity_name('um_Run1')
    delete_from_activity_name(' 1')
    delete_from_activity_name(' #1')
    delete_from_activity_name('uM_Run1')

    replace_with_activity_name('Ac50', 'AC50')

    purify_activity_name('IC50')

    print('Cleaning up assays and targets...')

    # TODO NEEDS REVISIONS
    # Check failures

    initial_bio = PubChemBioactivity.objects.all().count()

    updates = 0
    replaces = 0

    failed_updates = 0
    failed_replaces = 0

    for assay in Assay.objects.filter(chemblid='', source='ChEMBL'):
        # If ChEMBL is the source
        # if assay.source == u'ChEMBL' and not assay.chemblid:
        data = get_chembl_assay(assay.source_id)
        if data:
            chembl_assay = Assay.objects.filter(chemblid=data.get('chemblid'))
            # Update the pubchem assay with info from chembl
            if not chembl_assay:
                try:
                    assay_query = Assay.objects.filter(pk=assay.id)
                    #print 'Updating', data.get('chemblid')
                    assay_query.update(**data)
                    updates += 1
                except Exception as e:
                    failed_updates += 1
                    print(('Failed updating assay {}'.format(assay.source_id)))
                    print(e)
            # Update the chembl assay with pubchem data then delete the old assay
            else:
                try:
                    #print 'Replacing', chembl_assay[0].chemblid
                    chembl_assay.update(**data)
                    chembl_assay.update(**{
                        'pubchem_id': assay.pubchem_id,
                        'source': assay.source,
                        'source_id': assay.source_id
                    })
                    # Switch bioactivities to the correct assay
                    for bio in PubChemBioactivity.objects.filter(assay_id=assay.id):
                        bio.assay_id = chembl_assay[0].id
                        bio.save()
                    # Delete the old pubchem assay
                    assay.delete()
                    replaces += 1
                except Exception as e:
                    failed_replaces += 1
                    print(('Failed replacing assay {}'.format(assay.source_id)))
                    print(e)
        else:
            print(('Scrape for {} failed'.format(assay.source_id)))

    print(('Failed updates:', failed_updates))
    print(('Failed replaces:', failed_replaces))

    print(('Successful updates:', updates))
    print(('Successful replaces:', replaces))

    if initial_bio == PubChemBioactivity.objects.all().count():
        print('Bio number has not changed.')

    else:
        print('!!!!! Bio number has changed !!!!!')

    print('Normalizing values')

    bio_types = {bio.activity_name: True for bio in PubChemBioactivity.objects.all()}

    for bio_type in bio_types:
        targets = {
            bio.assay.target: True for bio in PubChemBioactivity.objects.filter(
                activity_name=bio_type
            ).prefetch_related('assay__target')
        }
        for target in targets:
            current_bio = PubChemBioactivity.objects.filter(
                activity_name=bio_type,
                assay__target_id=target.id
            ).prefetch_related('assay__target')

            bio_pk = [bio.id for bio in current_bio]
            bio_value = np.array([bio.value for bio in current_bio])
            if len(bio_pk) > 0 and len(bio_value) > 0:
                bio_value /= np.max(np.abs(bio_value), axis=0)
                for index, pk in enumerate(bio_pk):
                    try:
                        PubChemBioactivity.objects.filter(pk=pk).update(
                            normalized_value=bio_value[index]
                        )
                    except:
                        print(('Update of bioactivity {} failed'.format(pk)))

    print('Adding SINGLE PROTEIN to NCBI target entries')

    no_type = Target.objects.filter(target_type='')

    for target in no_type.exclude(GI=''):
        target.target_type = 'SINGLE PROTEIN'
        target.save()

    # Flag questionable entries
    print('Flagging questionable entries...')

    all_pubchem = PubChemBioactivity.objects.all().prefetch_related('compound', 'assay__target')

    bio_types = {bio.activity_name: True for bio in all_pubchem}
    bio_compounds = {bio.compound: True for bio in all_pubchem}
    bio_targets = {bio.assay.target: True for bio in all_pubchem}

    pubchem_entries = {}

    for entry in all_pubchem:
        if entry.assay.target:
            key = '|'.join([entry.activity_name, str(entry.compound.id), str(entry.assay.target.id)])

        else:
            key = '|'.join([entry.activity_name, str(entry.compound.id), 'None'])

        pubchem_entries.setdefault(key, []).append(entry)

    # Remove old flags in case they have become outdated (medians change and so on)
    PubChemBioactivity.objects.all().update(data_validity='')

    total = 0

    for bio_type in bio_types:
        for target in bio_targets:
            for compound in bio_compounds:
                if bio_type and target and compound:
                    if target:
                        current_bio = pubchem_entries.get('|'.join([bio_type, str(compound.id), str(target.id)]), [])
                    else:
                        current_bio = pubchem_entries.get('|'.join([bio_type, str(compound.id), 'None']), [])

                    bio_pk = [bio.id for bio in current_bio]
                    bio_value = np.array([bio.value for bio in current_bio])

                    if len(bio_pk) > 0 and len(bio_value) > 0:
                        bio_median = np.median(bio_value)
                        flag_threshold = bio_median * 100

                        # Check for out of range
                        for index, pk in enumerate(bio_pk):
                            if bio_value[index] > flag_threshold:
                                this_bio = PubChemBioactivity.objects.get(pk=bio_pk[index])
                                pubchem_id = this_bio.assay.pubchem_id
                                #this_bio.notes = 'Flagged'
                                # Flag data validity for "Out of Range"
                                this_bio.data_validity = 'R'
                                this_bio.save()
                                print((bio_pk[index], bio_value[index], 'vs', bio_median))
                                #print pubchem_id
                                #print 'https://pubchem.ncbi.nlm.nih.gov/bioassay/' + pubchem_id
                                total += 1

                        # Check for possible transcription errors (1000-fold error mistaking uM for nM)
                        for index, pk in enumerate(bio_pk):
                            thousand_fold = np.where(bio_value==bio_value[index] * 1000)[0]
                            if len(thousand_fold) > 0:
                                for error_index in thousand_fold:
                                    this_bio = PubChemBioactivity.objects.get(pk=bio_pk[error_index])
                                    if not this_bio.data_validity:
                                        total += 1
                                    this_bio.data_validity = 'T'
                                    this_bio.save()
                                    print((bio_pk[error_index], bio_value[error_index], 'thousand fold'))

    print(total)

    print('Finished')
