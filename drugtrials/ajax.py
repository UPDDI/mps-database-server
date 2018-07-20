# coding=utf-8

from django.http import HttpResponse, HttpResponseServerError
from .models import CompoundAdverseEvent, OpenFDACompound, AdverseEvent
import ujson as json
# TODO TODO TODO REVISE IN PYTHON 3
import cgi

# imports by Dale
import urllib2
import psycopg2
import psycopg2.extras

import mps_AATCcredentials


def main(request):
    """Default to Server Error"""
    return HttpResponseServerError()

def fetch_auto_drug_trial_data(request):
    # This should be replaced by query in the future, testing purposes only
    if(request.POST.get('disease', None) is not None):
        disease = request.POST.get('disease')
    else:
        disease = "nafld"

# https://clinicaltrials.gov/ct2/results?cond=&term=&type=Intr&rslt=With&recrs=e&age_v=&gndr=&intr=&titles=&outc=&spons=&lead=&id=&cntry=US&state=&city=&dist=&locn=&strd_s=&strd_e=&prcd_s=&prcd_e=&sfpd_s=&sfpd_e=&lupd_s=&lupd_e=
    url = "https://clinicaltrials.gov/ct2/results/download_fields?cond=" + disease + "&term=&type=Intr&rslt=With&recrs=e&age_v=&gndr=&intr=&titles=&outc=&spons=&lead=&id=&cntry=US&state=&city=&dist=&locn=&strd_s=&strd_e=&prcd_s=&prcd_e=&sfpd_s=&sfpd_e=&lupd_s=&lupd_e=&down_count=10000&down_fmt=plain"
    file = urllib2.urlopen(url)
    studyIDs = []
    link = "https://ClinicalTrials.gov/show/"
    for line in file:
        if link in line:
            ID = line[line.find(link)+len(link):line.find(link)+len(link)+11]
            studyIDs.append(ID)

    def lst2pgarr(alist):
        return '{' + ','.join(alist) + '}'

    studyIDs = (lst2pgarr(studyIDs))

    userName = mps_AATCcredentials.userid
    passWord = mps_AATCcredentials.pw

    try:
        conn = psycopg2.connect(dbname="aact", host="aact-db.ctti-clinicaltrials.org", user=userName, password=passWord, port=5432)
    except Exception, e:
        print "Cannot connect to database"
        print e

    del userName
    del passWord

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT nct_id,last_update_posted_date,start_date,completion_date,target_duration, \
                study_type,brief_title,official_title,overall_status,phase,results_first_posted_date, \
                source,why_stopped FROM studies WHERE nct_id = ANY(%s)",(studyIDs,))
    studies = cur.fetchall()
    cur.execute("SELECT nct_id,description FROM brief_summaries WHERE nct_id = ANY(%s)",(studyIDs,))
    brief_summaries = cur.fetchall()
    cur.execute("SELECT nct_id,name,downcase_name FROM conditions WHERE nct_id = ANY(%s)",(studyIDs,))
    conditions = cur.fetchall()
    cur.execute("SELECT nct_id,agency_class,lead_or_collaborator,name FROM sponsors WHERE nct_id = ANY(%s)",(studyIDs,))
    sponsors = cur.fetchall()
    cur.execute("SELECT nct_id,description FROM detailed_descriptions WHERE nct_id = ANY(%s)",(studyIDs,))
    detailed_descriptions = cur.fetchall()
    cur.execute("SELECT nct_id,group_type,title,description FROM design_groups WHERE nct_id = ANY(%s)",(studyIDs,))
    design_groups = cur.fetchall()
    cur.execute("SELECT nct_id,intervention_type,name,description FROM interventions WHERE \
                nct_id = ANY(%s)",(studyIDs,))  # (SELECT nct_id FROM conditions WHERE downcase_name= %s )", [condition])
    interventions = cur.fetchall()
    drugs = []
    for i in range(0,len(interventions)):
        if interventions[i]['intervention_type']=='Drug':
            drugs.append(interventions[i])
    cur.execute("SELECT nct_id,outcome_type,measure,time_frame,population,description \
                FROM design_outcomes WHERE nct_id = ANY(%s)",(studyIDs,))
    design_outcomes = cur.fetchall()
    cur.execute("SELECT nct_id,gender,minimum_age,maximum_age,population,criteria FROM eligibilities WHERE \
                nct_id = ANY(%s)",(studyIDs,))  # (SELECT nct_id FROM conditions WHERE downcase_name= %s )", [condition])
    eligibilities = cur.fetchall()
    cur.execute("SELECT nct_id,url,description FROM links WHERE nct_id = ANY(%s)",(studyIDs,))
    links = cur.fetchall()
    cur.execute("SELECT nct_id,pmid,reference_type FROM study_references WHERE nct_id = ANY(%s)",(studyIDs,))
    study_references = cur.fetchall()
    cur.execute("SELECT nct_id,result_group_id,time_frame,event_type,description,event_count, \
                organ_system,adverse_event_term,frequency_threshold FROM reported_events WHERE nct_id = ANY(%s)",(studyIDs,))
    reported_events = cur.fetchall()
    cur.execute("SELECT id,nct_id,result_type,title,description FROM result_groups \
                WHERE nct_id = ANY(%s)",(studyIDs,)) # IN (SELECT nct_id FROM conditions WHERE downcase_name= %s )", [condition])
    result_groups = cur.fetchall()
    cur.execute("SELECT nct_id,outcome_id,result_group_id,classification,category,title, \
                description,units,param_type,param_value,param_value_num, dispersion_value_num, \
                explanation_of_na FROM outcome_measurements WHERE nct_id = ANY(%s)",(studyIDs,))
    outcome_measurements = cur.fetchall()
    cur.execute("SELECT nct_id,outcome_id,param_type,param_value,p_value_modifier,p_value, \
                method,method_description,groups_description FROM outcome_analyses WHERE nct_id = ANY(%s)",(studyIDs,))
    outcome_analyses = cur.fetchall()
    cur.execute("SELECT id,nct_id,outcome_type,title,description,time_frame,population,units, \
                units_analyzed FROM outcomes WHERE nct_id = ANY(%s)",(studyIDs,))
    outcomes = cur.fetchall()

    cur.close()
    conn.close()

    def rList(nct_id,key):
        l = [d for d in key if d['nct_id'] == nct_id]

        if len(l) < 1:
            return None
        # elif len(l) == 1:
        #     return (item for item in key if item["nct_id"] == nct_id).next()
        else:
            return l

    studiesWithResults = []
    for i in range(0,len(studies)):
        #if studies[i]['results_first_posted_date'] is not None:
            #studiesWithResults.append(studies[i]['nct_id'])
            nct_id = studies[i]['nct_id']
            study = {'brief_summaries': (item for item in brief_summaries if item["nct_id"] == nct_id).next(), \
                     'conditions': rList(nct_id,conditions), \
                     'design_groups': rList(nct_id,design_groups), \
                     'design_outcomes': rList(nct_id,design_outcomes), \
                     'detailed_descriptions': rList(nct_id,detailed_descriptions), \
                     'drugs': rList(nct_id,drugs), \
                     'eligibilities': (item for item in eligibilities if item["nct_id"] == nct_id).next(), \
                     'interventions': rList(nct_id,interventions), \
                     'links': rList(nct_id,links), \
                     'outcome_analyses': rList(nct_id,outcome_analyses), \
                     'outcome_measurements': rList(nct_id,outcome_measurements), \
                     'outcomes': rList(nct_id,outcomes), \
                     'reported_events': rList(nct_id,reported_events), \
                     'result_groups': rList(nct_id,result_groups), \
                     'sponsors': rList(nct_id,sponsors), \
                     'studies': (item for item in studies if item["nct_id"] == nct_id).next(), \
                     'study_references': rList(nct_id,study_references), \
                     'nct_id': nct_id #?
                    }
            studiesWithResults.append(study)

    studyData = { 'data' : studiesWithResults }

    return HttpResponse(
        json.dumps(studyData),
        content_type="application/json"
    )

def fetch_adverse_events_data(request):
    ae_data = list(CompoundAdverseEvent.objects.prefetch_related(
        'compound__compound',
        'event__organ'
    ).all().values(
        'compound_id',
        'compound__compound__name',
        'compound__compound_id',
        # Probably should be, you know, NAME
        'event__event',
        'frequency',
        'compound__estimated_usage',
        # WHY ISN'T THIS JUST NAME??
        'event__organ__organ_name',
        # Add logp
        'compound__compound__logp',
        'compound__compound__alogp',
        'compound__black_box',
        # SUBJECT TO CHANGE
        'compound__compound__tctc',
        'compound__compound__mps',
        'compound__compound__epa'
    ))

    data = []

    # A serializer would probably better serve us here...
    for ae in ae_data:
        project = ''

        if ae.get('compound__compound__tctc'):
            project += 'TCTC'

        if ae.get('compound__compound__epa'):
            project += 'EPA'

        if ae.get('compound__compound__mps'):
            project += 'MPS'

        if not project:
            project = 'Unassigned'

        organ_name = ''

        if ae.get('event__organ__organ_name'):
            organ_name = ae.get('event__organ__organ_name')

        black_box_warning = False

        if ae.get('compound__black_box'):
            black_box_warning = True

        normalized_reports = ''
        estimated_usage = ''

        if ae.get('compound__estimated_usage'):
            normalized_reports = '{:,.2f}'.format(
                float(ae.get('frequency')) / ae.get('compound__estimated_usage') * 10000
            )
            estimated_usage = '{:,}'.format(ae.get('compound__estimated_usage'))

        data.append(
            {
                'view': ae.get('compound_id'),
                'compound': {
                    'id': ae.get('compound__compound_id'),
                    'name': cgi.escape(ae.get('compound__compound__name'))
                },
                'event': {
                    'lower': cgi.escape(ae.get('event__event').lower()),
                    'name': cgi.escape(ae.get('event__event'))
                },
                'number_of_reports': '{:,}'.format(
                    ae.get('frequency')
                ),
                'normalized_reports': normalized_reports,
                'estimated_usage': estimated_usage,
                'organ': organ_name,
                'black_box_warning': black_box_warning,
                'project': project,
                'logp': ae.get('compound__compound__logp'),
                'alogp': ae.get('compound__compound__alogp')
            }
        )

    all_data = {
        'data': data
    }

    return HttpResponse(
        json.dumps(all_data),
        content_type="application/json"
    )


def fetch_aggregate_ae_by_compound(request):
    compounds = OpenFDACompound.objects.all().prefetch_related(
        'compound'
    )

    compound_frequency = {}
    ae_to_compound = {}

    for adverse_event in CompoundAdverseEvent.objects.all().prefetch_related('event', 'compound__compound'):
        compound_frequency.setdefault(adverse_event.compound_id, []).append(adverse_event.frequency)
        ae_to_compound.setdefault(adverse_event.event.event, {}).update({
            adverse_event.compound.compound.name: True
        })

    data = []

    for compound in compounds:
        estimated_usage = ''

        if compound.estimated_usage:
            estimated_usage = '{:,}'.format(compound.estimated_usage)

        checkbox = '<input class="checkbox big-checkbox compound" type="checkbox" value="{}">'.format(compound.compound.name)

        data.append({
            # 'checkbox': cgi.escape(compound.compound.name),
            'checkbox': cgi.escape(checkbox),
            'compound': compound.compound.name,
            'estimated_usage': estimated_usage,
            'frequency': '{:,}'.format(sum(compound_frequency.get(compound.id, [0])))
        })

    all_data = {
        'data': data,
        'ae_to_compound': ae_to_compound
    }

    return HttpResponse(
        json.dumps(all_data),
        content_type="application/json"
    )


def fetch_aggregate_ae_by_event(request):
    adverse_events = AdverseEvent.objects.all().prefetch_related(
        'organ'
    )

    adverse_event_frequency = {}

    for adverse_event in CompoundAdverseEvent.objects.all():
        adverse_event_frequency.setdefault(adverse_event.event_id, []).append(adverse_event.frequency)

    data = []

    for adverse_event in adverse_events:
        frequency = sum(adverse_event_frequency.get(adverse_event.id, [0]))
        organ_name = ''

        if adverse_event.organ:
            organ_name = adverse_event.organ.organ_name

        checkbox = '<input class="checkbox big-checkbox adverse-event" type="checkbox" value="{}">'.format(adverse_event.event)

        if frequency:
            data.append({
                # 'checkbox': cgi.escape(adverse_event.event),
                'checkbox': cgi.escape(checkbox),
                'event': adverse_event.event,
                'organ': organ_name,
                'frequency': '{:,}'.format(frequency)
            })

    all_data = {
        'data': data
    }

    return HttpResponse(
        json.dumps(all_data),
        content_type="application/json"
    )

switch = {
    'fetch_adverse_events_data': fetch_adverse_events_data,
    'fetch_aggregate_ae_by_event': fetch_aggregate_ae_by_event,
    'fetch_aggregate_ae_by_compound': fetch_aggregate_ae_by_compound,
    'fetch_auto_drug_trial_data': fetch_auto_drug_trial_data
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
