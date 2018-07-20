from .models import FindingResult,  DrugTrial, AdverseEvent, OpenFDACompound, CompoundAdverseEvent

from django.views.generic import ListView, DetailView, TemplateView
# from django.shortcuts import render_to_response
# from django.template import RequestContext


class DrugTrialList(ListView):
    """Displays a list of Drug Trials"""
    # model = FindingResult
    template_name = 'drugtrials/drugtrial_list.html'

    def get_queryset(self):
        queryset = FindingResult.objects.prefetch_related(
            'descriptor',
            'value_units',
            'drug_trial__compound',
            'drug_trial__species',
            'finding_name__organ',
            'finding_name__finding_type',
            'findingtreatment_set__compound',
            'findingtreatment_set__concentration_unit',
        ).all()

        return queryset


class DrugTrialDetail(DetailView):
    """Details for a Drug Trial

    Contains next and previous buttons
    """
    model = DrugTrial
    template_name = 'drugtrials/drugtrial_detail.html'

    def get_context_data(self, **kwargs):
        context = super(DrugTrialDetail, self).get_context_data(**kwargs)

        results = FindingResult.objects.filter(
            drug_trial=self.object
        ).prefetch_related(
            'descriptor',
            'value_units',
            'drug_trial__compound',
            'drug_trial__species',
            'finding_name__organ',
            'finding_name__finding_type',
            'findingtreatment_set__compound',
            'findingtreatment_set__concentration_unit',
        )

        # Get the unique compounds in the results
        treatments_dic = {}
        treatments = []
        for finding in results:
            for treatment in finding.findingtreatment_set.all():
                treatment_tuple = (
                    treatment.compound_id,
                    treatment.concentration_unit_id,
                    treatment.concentration
                )
                if not treatments_dic.get(treatment_tuple, ''):
                    treatments_dic.update({
                        treatment_tuple: True
                    })
                    treatments.append(treatment)

        self.object.unique_treatments = treatments

        # Can no longer *really* order by compound (there may be more than one!)
        # This may lead to a bit of confusion, but then again that would be true if the user changed the sorting...
        trials = list(DrugTrial.objects.all().order_by('compound', 'id').values_list('id', flat=True))
        current = trials.index(self.object.id)

        if current == 0:
            previous_trial = trials[-1]
        else:
            previous_trial = trials[current - 1]
        if current == len(trials)-1:
            next_trial = trials[0]
        else:
            next_trial = trials[current + 1]

        context.update({
            'results': results,
            'previous': previous_trial,
            'next': next_trial,
        })

        return context


class AdverseEventsList(TemplateView):
    """Displays a list of Compound Adverse Events"""
    template_name = 'drugtrials/adverse_events_list.html'


class AdverseEventDetail(DetailView):
    """Details for an Adverse Event (includes a time plot)

    Contains next and previous buttons
    """
    model = OpenFDACompound
    template_name = 'drugtrials/adverse_events_detail.html'

    def get_context_data(self, **kwargs):
        context = super(AdverseEventDetail, self).get_context_data(**kwargs)

        events = CompoundAdverseEvent.objects.filter(
            compound_id=self.object.id
        ).prefetch_related(
            'event__organ',
            'compound'
        ).order_by('-frequency')

        for ae in events:
            if ae.compound.estimated_usage:
                ae.normalized_reports = float(ae.frequency) / ae.compound.estimated_usage * 10000
            else:
                ae.normalized_reports = None

        compounds = list(OpenFDACompound.objects.all().order_by('compound').values_list('id', flat=True))
        current = compounds.index(self.object.id)

        if current == 0:
            previous_events = compounds[-1]
        else:
            previous_events = compounds[current - 1]
        if current == len(compounds)-1:
            next_events = compounds[0]
        else:
            next_events = compounds[current + 1]

        context.update({
            'events': events,
            'previous': previous_events,
            'next': next_events,
        })

        return context

class AutoDrugTrials(TemplateView):
    """Displays a list auto curated drug trials"""
    template_name = 'drugtrials/auto_drug_trials.html'

class AutoDrugTrialsForm(TemplateView):
    """Precursor to Auto Drug Trials, Input Disease"""
    template_name = 'drugtrials/auto_drug_trials_form.html'

class CompareAdverseEvents(TemplateView):
    template_name = 'drugtrials/compare_adverse_events.html'

# PROBABLY SHOULD JUST BE A CBV TemplateView
# def compare_adverse_events(request):
#     """Adverse event rates for the given adverse event"""
#
#     c = RequestContext(request)
#
#     compounds = OpenFDACompound.objects.all().prefetch_related(
#         'compound'
#     )
#
#     # Alternative call
#     # compounds = Compound.objects.filter(compoundadverseevent_set__isnull=False)
#
#     adverse_events = AdverseEvent.objects.all().prefetch_related(
#         'organ'
#     )
#
#     compound_frequency = {}
#     adverse_event_frequency = {}
#
#     for adverse_event in CompoundAdverseEvent.objects.all().prefetch_related('compound', 'event'):
#         compound_frequency.setdefault(adverse_event.compound_id, []).append(adverse_event.frequency)
#         adverse_event_frequency.setdefault(adverse_event.event_id, []).append(adverse_event.frequency)
#
#     for adverse_event in adverse_events:
#         adverse_event.frequency = sum(adverse_event_frequency.get(adverse_event.id, [0]))
#
#     for compound in compounds:
#         compound.frequency = sum(compound_frequency.get(compound.id, [0]))
#
#     # Should I even bother putting events (perhaps even compounds) into the context?
#     c.update({
#         'compounds': compounds,
#         'adverse_events': adverse_events
#     })
#
#     # What to name template?
#     return render_to_response('drugtrials/compare_adverse_events.html', c)
