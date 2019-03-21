from django.db import models
from django.utils.translation import pgettext
from django.utils.translation import ugettext_lazy as _

from django.dispatch import receiver

from django.template.loader import render_to_string

# from django.conf import settings
# try:
#     from django.contrib.auth import get_user_model
#     User = settings.AUTH_USER_MODEL
# except ImportError:
#     from django.contrib.auth.models import User

# I am just using the default User anyway
from django.contrib.auth.models import User

from qhonuskan_votes.models import VotesField
from qhonuskan_votes.models import ObjectsWithScoresManager

from mps.settings import DEFAULT_FROM_EMAIL

from django.urls import reverse

STATUS_CHOICES = (
    ('open', pgettext('status', "Open")),
    ('closed', pgettext('status', "Closed")),
)


class Status(models.Model):
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500)
    default = models.BooleanField(
        blank=True,
        help_text=_("New feedback will have this status"),
        default=False)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])

    def save(self, **kwargs):
        if self.default:
            try:
                default_project = Status.objects.get(default=True)
                default_project.default = False
                default_project.save()

            except Status.DoesNotExist:
                pass

        super(Status, self).save(**kwargs)

    def __str__(self):
        return str(self.title)

    class Meta:
        verbose_name = _("status")
        verbose_name_plural = _("statuses")


class Type(models.Model):
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500)

    def __str__(self):
        return self.title


class Feedback(models.Model):
    title = models.CharField(max_length=500, verbose_name=_("Title"))
    description = models.TextField(
        blank=True, verbose_name=_("Description"),
        help_text=_(
            "This will be viewable by other people - do not include any "
            "private details such as passwords or phone numbers here."))
    type = models.ForeignKey(Type, verbose_name=_("Type"), on_delete=models.CASCADE)
    anonymous = models.BooleanField(
        blank=True, verbose_name=_("Anonymous"),
        help_text=_("Do not show who sent this"),
        default=False)
    private = models.BooleanField(
        verbose_name=_("Private"), blank=True,
        help_text=_(
            "Hide from public pages. Only site administrators will be able to "
            "view and respond to this"),
        default=False)
    user = models.ForeignKey(User, blank=True, null=True, verbose_name=_("User"), on_delete=models.CASCADE)
    email = models.EmailField(
        blank=True, null=True, verbose_name=_('E-mail'),
        help_text=_(
            "You must provide your e-mail so we can answer you. "
            "Alternatively you can bookmark next page and check out for an "
            "answer later."))
    slug = models.SlugField(max_length=10, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    status = models.ForeignKey(Status, verbose_name=_('Status'), on_delete=models.CASCADE)
    duplicate = models.ForeignKey('self', null=True, blank=True, verbose_name=_("Duplicate"), on_delete=models.CASCADE)
    votes = VotesField()
    objects = ObjectsWithScoresManager()

    def save(self, **kwargs):
        try:
            self.status

        except Status.DoesNotExist:
            try:
                default = Status.objects.get(default=True)

            except Status.DoesNotExist:
                default = Status.objects.all()[0]

            self.status = default

        super(Feedback, self).save(**kwargs)

    def get_absolute_url(self):
        return reverse('djangovoice_item', args=[self.id])

    def __str__(self):
        return str(self.title)

    class Meta:
        verbose_name = _("feedback")
        verbose_name_plural = _("feedback")
        ordering = ('-created',)
        get_latest_by = 'created'


@receiver(models.signals.post_save, sender=Feedback)
def admin_email_alert_for_new_feedback(sender, **kwargs):
    current_instance = kwargs.get('instance', None)
    created = kwargs.get('created', False)
    if current_instance and created:
        superusers_to_be_alerted = User.objects.filter(is_superuser=True, is_active=True)
        # Magic strings are in poor taste, should use a template instead
        superuser_subject = 'New Feedback: {0}'.format(current_instance.title)
        superuser_message = render_to_string(
            'djangovoice/email/superuser_new_feedback_alert.txt',
            {
                'feedback': current_instance
            }
        )

        for user_to_be_alerted in superusers_to_be_alerted:
            user_to_be_alerted.email_user(superuser_subject, superuser_message, DEFAULT_FROM_EMAIL)
