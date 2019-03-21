import sys
import os
sys.path.append('/home/mps/mps-database-server')
os.environ['DJANGO_SETTINGS_MODULE'] = 'mps.settings'
#from django.conf import settings
import datetime

from compounds.models import Compound, CompoundTarget
from compounds.ajax import get_chembl_compound_data, get_drugbank_data_from_chembl_id
from bioactivities.models import Assay, Target, Bioactivity
from bioactivities.models import chembl_target, chembl_assay

from bioservices import ChEMBL as ChEMBLdb
from bioservices.services import BioServicesError

from django.db import connection

import numpy as np

FIELDS = {
    'reference': 'reference',
    'target_chemblid': 'target',
    'bioactivity_type': 'bioactivity_type',
    'ingredient_cmpd_chemblid': 'compound',
    'value': 'value',
    'units': 'units',
    'assay_chemblid': 'assay',
    'parent_cmpd_chemblid': 'parent_compound',
    'operator': 'operator',
    'activity_comment': 'activity_comment',
    'name_in_reference': 'name_in_reference',
    'target_confidence': 'target_confidence'
}


def run(days=180):
    """Run as::

      $ python manage.py runscript update_activities

    By default, updates bioactivities of compounds that were never updated
    or updates 180 days ago.

    To force updating bioactivities for all compounds, give 0 days argument
    as follows::

        $ python manage.py runscript update_activities --script-args=0

    """

    try:
        days = int(days)
    except ValueError:
        days = 180

    chembl = ChEMBLdb()

    #for table, func in [
    #    (Compound, chembl.get_compounds_activities),
    #    (Target, chembl.get_target_bioactivities),
    #    (Assay, chembl.get_assay_bioactivities), ]:
    count = skip = error = ncomp = 0
    # will iterate over all compounds one-by-one
    for compound in Compound.objects.all():

        # if no updates were made, last_update is None
        if (compound.last_update is None or
                (datetime.date.today() - compound.last_update) >= datetime.timedelta(days)):
            ncomp += 1

            try:
                acts = chembl.get_compounds_activities(str(compound.chemblid))
            except BioServicesError:
                continue

            try:
                for act in acts['bioactivities']:
                    act = {FIELDS[key]: value for key, value in list(act.items()) if key in FIELDS}

                    tid, aid, cid, pid = (
                        act['target'], act['assay'], act['compound'], act['parent_compound']
                    )
                    try:
                        parent = Compound.objects.get(chemblid=pid)
                    except Compound.DoesNotExist:
                        try:
                            # Uses implemented methods in lieu of Bioservices
                            parent_compound_data = get_chembl_compound_data(pid)
                            parent_compound_data.update(get_drugbank_data_from_chembl_id(pid))

                            parent_compound_targets = parent_compound_data.get('targets', [])
                            del parent_compound_data['targets']

                            parent = Compound.objects.create(locked=True, **parent_compound_data)

                            for target in parent_compound_targets:
                                CompoundTarget.objects.create(compound=parent, **target)
                            print(("Added Compound:", parent.name))
                        except ValueError:
                            error += 1
                            continue

                    try:
                        target = Target.objects.get(chemblid=tid)
                    except Target.DoesNotExist:
                        try:
                            target = Target.objects.create(locked=True, **chembl_target(tid))
                        except ValueError:
                            error += 1
                            continue

                    try:
                        assay = Assay.objects.get(chemblid=aid)
                    except Assay.DoesNotExist:
                        try:
                            assay = Assay.objects.create(locked=True, **chembl_assay(aid))
                        except ValueError:
                            error += 1
                            continue

                    try:
                        activity = Bioactivity.objects.get(
                            target=target, assay=assay, compound=compound)
                    except Bioactivity.DoesNotExist:

                        (act['target'], act['assay'], act['compound'], act['parent_compound']) = (
                            target, assay, compound, parent
                        )

                        try:
                            ba = Bioactivity.objects.create(locked=True, **act)
                        except ValueError:
                            error += 1
                        except Exception as err:
                            for key, val in list(act.items()):
                                if isinstance(val, str):
                                    print(('{}: ({}) {}'.format(key, len(val), val)))
                            raise err
                        else:
                            count += 1
                    else:
                        skip += 1
            except:
                print(("An error occured:", compound.name, acts))

            compound.last_update = datetime.date.today()
            compound.save()

    print(('{} bioactivities were added, {} were found in the database, and '
          '{} failed due to value errors.'.format(count, skip, error)))

    print('Updating bioactivity units...')
    cursor = connection.cursor()

    cursor.execute(
        '''
        UPDATE bioactivities_bioactivity
        SET standardized_units = '',
            standard_name = '',
            standardized_value = NULL;

        --no mass is needed in data conversion
        UPDATE public.bioactivities_bioactivity as v
        SET standard_name = s.standard_name,
        standardized_units=s.standard_unit,
            standardized_value=value*scale_factor
        FROM public.bioactivities_bioactivitytype as s
        WHERE v.bioactivity_type = s.chembl_bioactivity and
        v.units=s.chembl_unit and s.mass_flag='N';

        --mass is needed in data conversion
        UPDATE public.bioactivities_bioactivity as v
        SET standard_name = s.standard_name,
        standardized_units=s.standard_unit,
            standardized_value=value*scale_factor/c.molecular_weight
        FROM public.bioactivities_bioactivitytype as s,
        public.compounds_compound as c
        WHERE v.bioactivity_type = s.chembl_bioactivity and
        v.units=s.chembl_unit and v.compound_id =c.id and s.mass_flag='Y';
        '''
    )

    print('Units updated')

    print('Normalizing values')

    bio_types = {bio.standard_name: True for bio in Bioactivity.objects.all()}

    for bio_type in bio_types:
        targets = {
            bio.target: True for bio in Bioactivity.objects.filter(
                standard_name=bio_type
            ).prefetch_related('target')
        }
        for target in targets:
            current_bio = Bioactivity.objects.filter(
                standard_name=bio_type,
                target=target,
                standardized_value__isnull=False
            ).prefetch_related('target')

            bio_pk = [bio.id for bio in current_bio]
            bio_value = np.array([bio.standardized_value for bio in current_bio])
            if len(bio_pk) > 0 and len(bio_value) > 0:
                bio_value /= np.max(np.abs(bio_value), axis=0)
                for index, pk in enumerate(bio_pk):
                    try:
                        Bioactivity.objects.filter(pk=pk).update(
                            normalized_value=bio_value[index]
                        )
                    except:
                        print(('Update of bioactivity {} failed'.format(pk)))

    # Flag questionable entries
    print('Flagging questionable entries...')

    # Remove old flags in case they have become outdated (medians change and so on)
    Bioactivity.objects.all().update(data_validity='')

    total = 0

    all_chembl = Bioactivity.objects.all().prefetch_related('compound', 'target').filter(
        standardized_value__isnull=False
    )

    bio_types = {bio.standard_name: True for bio in all_chembl}
    bio_compounds = {bio.compound: True for bio in all_chembl}
    bio_targets = {bio.target: True for bio in all_chembl}

    chembl_entries = {}

    for entry in all_chembl:
        if entry.target:
            key = '|'.join([entry.standard_name, str(entry.compound.id), str(entry.target.id)])
        else:
            key = '|'.join([entry.standard_name, str(entry.compound.id), 'None'])

        chembl_entries.setdefault(key, []).append(entry)

    # ChEMBL contains negative values!
    # TODO Needs revision
    for bio_type in bio_types:
        for target in bio_targets:
            for compound in bio_compounds:
                if bio_type and target and compound:
                    if target:
                        current_bio = chembl_entries.get('|'.join([bio_type, str(compound.id), str(target.id)]), [])
                    else:
                        current_bio = chembl_entries.get('|'.join([bio_type, str(compound.id), 'None']), [])

                    bio_pk = [bio.id for bio in current_bio]
                    bio_value = np.array([bio.standardized_value for bio in current_bio])

                    if len(bio_value) > 0:
                        # Shift values by the minimum to avoid problems with negative values
                        bio_value = np.array(bio_value) + np.abs(np.min(bio_value)) + 1

                    if len(bio_pk) > 0 and len(bio_value) > 0:
                        bio_median = np.median(bio_value)
                        flag_threshold = bio_median * 100

                        for index, pk in enumerate(bio_pk):
                            if bio_value[index] > flag_threshold:
                                this_bio = Bioactivity.objects.get(pk=bio_pk[index])
                                #this_bio.notes = 'Flagged'
                                # Flag data validity for "Out of Range"
                                this_bio.data_validity = 'R'
                                this_bio.save()
                                print((bio_pk[index], bio_value[index], 'vs', bio_median))
                                total += 1

                        # Check for possible transcription errors (1000-fold error mistaking uM for nM)
                        for index, pk in enumerate(bio_pk):
                            thousand_fold = np.where(bio_value == bio_value[index] * 1000)[0]
                            if len(thousand_fold) > 0:
                                for error_index in thousand_fold:
                                    this_bio = Bioactivity.objects.get(pk=bio_pk[error_index])
                                    if not this_bio.data_validity:
                                        total += 1
                                    this_bio.data_validity = 'T'
                                    this_bio.save()
                                    print((bio_pk[error_index], bio_value[error_index], 'thousand fold'))

    print(total)

# A second run is useful to catch newly added compounds,
# but just calling run is somewhat inefficient (it would run through every compound again)
#run(0)
