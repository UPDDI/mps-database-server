from django.urls import reverse
from django.test import Client, TestCase
from django.contrib.auth.models import User
from djangovoice.models import Status, Type, Feedback


class ViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_feedback_list_page(self):
        # user is not logged in, but it can see feedback list:
        response = self.client.get(reverse('djangovoice_home'))
        self.assertEqual(response.status_code, 200)


class StatusTestCase(TestCase):
    def setUp(self):
        self.in_progress = Status.objects.create(
            title='In progress', slug='in_progress', default=False)
        self.need_to_test = Status.objects.create(
            title='Need to test', slug='need_to_test', default=True)

    def testSpeaking(self):
        self.assertEqual(self.in_progress.status, 'open')
        self.assertEqual(self.need_to_test.default, True)


class TypeTestCase(TestCase):
    def setUp(self):
        self.bug = Type.objects.create(title='Bug', slug='bug')
        self.betterment = Type.objects.create(title='Betterment',
                                              slug='betterment')

    def testSpeaking(self):
        self.assertEqual(self.bug.slug, 'bug')
        self.assertEqual(self.betterment.title, 'Betterment')


class FeedbackTestCase(TestCase):
    def setUp(self):
        feedback_type = Type.objects.create(title='Bug', slug='bug')
        feedback_user = User.objects.create_user(
            username='djangovoice', email='django@voice.com')
        self.login_form_does_not_work = Feedback.objects.create(
            type=feedback_type,
            title='Login form does not work.',
            # XD
            description='What a superb test...',
            anonymous=False,
            private=True,
            user=feedback_user)

    def testSpeaking(self):
        default_status = Status.objects.get(default=True)
        self.assertEqual(self.login_form_does_not_work.status, default_status)
