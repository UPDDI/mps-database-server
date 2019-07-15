"""
    This script finds studies that either have been released to Level 2
    (either because they have no stakeholders or every stakeholder approved)
    and moves them to the public automatically after approximately one year's time
"""
from assays.models import AssayStudy, AssayStudyStakeholder
from datetime import datetime, timedelta
import pytz

from django.contrib.auth.models import User, Group

from django.template.loader import render_to_string, TemplateDoesNotExist
from mps.settings import DEFAULT_FROM_EMAIL

from mps.templatetags.custom_filters import (
    ADMIN_SUFFIX,
    VIEWER_SUFFIX
)


def run():
    """Main function that runs the script"""
    # Superusers to alert
    superusers_to_be_alerted = User.objects.filter(is_superuser=True, is_active=True)

    # Needed to make minimum timezone aware
    minimum_datetime = datetime.min.replace(tzinfo=pytz.UTC)
    datetime_now = datetime.now().replace(tzinfo=pytz.UTC)

    # Local datetime
    tz = pytz.timezone('US/Eastern')
    datetime_now_local = datetime.now(tz)

    signed_off_restricted_studies = AssayStudy.objects.filter(
        restricted=True,
        # PLEASE NOTE: Locking a study will prevent this script from interacting with it
        locked=False,
        # DO NOT RELEASE ARCHIVED
        archived=False
    ).exclude(
        signed_off_by_id=None
    )

    # Just make me the auto-approver for now
    auto_approval_user = User.objects.get(pk=20)

    # Now check to see if any stakeholders need to be auto-approved!
    for study in signed_off_restricted_studies:
        # NOTE: This uses the study's last update data, NOT the time it was signed off
        # Check if 17 days since last update
        # Really, this should be in the queryset filter
        seventeen_days_since_update = study.modified_on < datetime_now - timedelta(days=17)

        # Force approval of all stakeholders
        if seventeen_days_since_update:
            current_stakeholders = AssayStudyStakeholder.objects.filter(
                # signed_off_by=None,
                study_id=study.id
            )

            current_unapproved_stakeholders = current_stakeholders.filter(
                signed_off_by_id=None
            )

            if current_unapproved_stakeholders:
                current_unapproved_stakeholders.update(
                    signed_off_by=auto_approval_user,
                    signed_off_date=datetime_now_local,
                    signed_off_notes="Expiration of two week period"
                )

                # Send emails
                # TODO, THESE EMAILS ARE NOT DRY, THEY SHOULD BE IN CONSOLIDATED FUNCTIONS/METHODS OR SOMETHING
                access_group_names = {group.name: group.id for group in study.access_groups.all()}
                matching_groups = list(set([
                    group.id for group in Group.objects.all() if
                    group.name.replace(ADMIN_SUFFIX, '').replace(VIEWER_SUFFIX, '') in access_group_names
                ]))

                stakeholder_group_names = {stakeholder.group.name: stakeholder.group.id for stakeholder in current_stakeholders}
                exclude_groups = list(set([
                    group.id for group in Group.objects.all() if
                    group.name.replace(ADMIN_SUFFIX, '').replace(VIEWER_SUFFIX, '') in stakeholder_group_names
                ]))

                viewer_subject = 'Study {0} Now Available for Viewing'.format(study)

                # Just in case, exclude stakeholders to prevent double messages
                viewers_to_be_alerted = User.objects.filter(
                    groups__id__in=matching_groups, is_active=True
                ).exclude(
                    groups__id__in=exclude_groups
                ).distinct()

                for user_to_be_alerted in viewers_to_be_alerted:
                    viewer_message = render_to_string(
                        'assays/email/viewer_alert.txt',
                        {
                            'user': user_to_be_alerted,
                            'study': study
                        }
                    )

                    user_to_be_alerted.email_user(
                        viewer_subject,
                        viewer_message,
                        DEFAULT_FROM_EMAIL
                    )

                # Magic strings are in poor taste, should use a template instead
                superuser_subject = 'Study Released to Next Level: {0}'.format(study)
                superuser_message = render_to_string(
                    'assays/email/superuser_viewer_release_alert.txt',
                    {
                        'study': study,
                        'auto_approval': True
                    }
                )

                for user_to_be_alerted in superusers_to_be_alerted:
                    user_to_be_alerted.email_user(
                        superuser_subject,
                        superuser_message,
                        DEFAULT_FROM_EMAIL
                    )

    # Indicates whether there are required stakeholders that have not approved
    required_stakeholder_map = {}

    relevant_required_stakeholders_without_approval = AssayStudyStakeholder.objects.filter(
        sign_off_required=True,
        signed_off_by_id=None,
        study__id__in=signed_off_restricted_studies
    ).prefetch_related(
        'study'
    )

    for stakeholder in relevant_required_stakeholders_without_approval:
        required_stakeholder_map.update({
            stakeholder.study_id: True
        })

    # Contains as a datetime the lastest approval for a study
    latest_approval = {}

    approved_stakeholders = AssayStudyStakeholder.objects.filter(
        sign_off_required=True,
        study__id__in=signed_off_restricted_studies
    ).exclude(
        signed_off_by_id=None
    )

    for stakeholder in approved_stakeholders:
        # Compare to minimum if no date at the moment
        if stakeholder.signed_off_date > latest_approval.get(stakeholder.study_id, minimum_datetime):
            latest_approval.update({
                stakeholder.study_id: stakeholder.signed_off_date
            })

    for study in signed_off_restricted_studies:
        # If there are no stakeholders, just use the sign off date
        if study.id not in latest_approval:
            # Days are approximated for a year
            greater_than_a_year_ago = study.signed_off_date < datetime_now - timedelta(days=365.2425)
        else:
            # Days are approximated for a year
            greater_than_a_year_ago = latest_approval.get(study.id) < datetime_now - timedelta(days=365.2425)

        stakeholders_without_approval = required_stakeholder_map.get(study.id, False)

        # Publish the study if no stakeholders without approval AND it was sent to Level to greater than a year ago
        if not stakeholders_without_approval and greater_than_a_year_ago:
            # print study, 'has been published'
            study.restricted = False
            study.save()

            # Magic strings are in poor taste, should use a template instead
            superuser_subject = 'Study Automatically Made Public: {0}'.format(study)
            superuser_message = render_to_string(
                'assays/email/superuser_study_made_public_alert.txt',
                {
                    'study': study,
                }
            )

            for user_to_be_alerted in superusers_to_be_alerted:
                user_to_be_alerted.email_user(superuser_subject, superuser_message, DEFAULT_FROM_EMAIL)
