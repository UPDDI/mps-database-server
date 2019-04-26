from django.contrib import admin
from django.conf.urls import url, include
import debug_toolbar

from mps import settings

# from .views import CustomSearch
# from .views import *
# from .forms import *
import mps.views
import mps.ajax
import mps.forms
import django.views
import mps.management

# For registration
from django_registration.backends.activation.views import ActivationView, RegistrationView
from django.contrib.auth import views as auth_views

from django.conf.urls.static import static

admin.autodiscover()

urlpatterns = [
    url(r'^$', mps.views.main),

    # user auth urls
    url(
        r'^accounts/login/$',
        # Deprecated
        # auth_views.login,
        # {'template_name': 'login.html'},
        auth_views.LoginView.as_view(
            template_name='login.html'
        ),
        name='auth_login'
    ),
    url(
        r'^accounts/logout/$',
        # Deprecated
        # auth_views.logout,
        # {'template_name': 'logout.html'},
        auth_views.LogoutView.as_view(
            template_name='logout.html'
        ),
        name='auth_logout'
    ),
    url(r'^accounts/loggedin/$', mps.views.loggedin, name='auth_loggedin'),
    url(
        r'^password_change/$',
        auth_views.PasswordChangeView.as_view(
            template_name='password_change.html'
        ),
        name='password_change'
    ),
    url(
        r'^password_change_done/$',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='password_change_done.html'
        ),
        name="password_change_done"
    ),

    # Registration
    url(
        r'^activate/complete/$',
        mps.views.TemplateView.as_view(
            template_name='django_registration/activation_complete.html'
        ),
        name='django_registration_activation_complete'
    ),
    # The activation key can make use of any character from the
    # URL-safe base64 alphabet, plus the colon as a separator.
    url(
        r'^activate/(?P<activation_key>[-:\w]+)/$',
        ActivationView.as_view(),
        name='django_registration_activate'
    ),
    url(
        r'^register/$',
        RegistrationView.as_view(
            form_class=mps.forms.CaptchaRegistrationForm
        ),
        name='django_registration_register'
    ),
    url(
        r'^register/complete/$',
        mps.views.TemplateView.as_view(
            template_name='django_registration/registration_complete.html'
        ),
        name='django_registration_complete'
    ),
    url(
        r'^register/closed/$',
        mps.views.TemplateView.as_view(
            template_name='django_registration/registration_closed.html'
        ),
        name='django_registration_disallowed'
    ),

    # Password Reset
    url(
        r'^password/reset/$',
        auth_views.PasswordResetView.as_view(
            success_url='/password/reset/done/',
            email_template_name='django_registration/password_reset_email.txt',
            subject_template_name='django_registration/password_reset_subject.txt',
            template_name='django_registration/password_reset_form.html',
            form_class=mps.forms.CaptchaResetForm,
        ),
        name='auth_password_reset'
    ),
    url(
        r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/'
        r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(
            success_url='/password/reset/complete/',
            template_name='django_registration/password_reset_confirm.html'
        ),
        name='auth_password_reset_confirm'
    ),
    url(
        r'^password/reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='django_registration/password_reset_complete.html'
        ),
        name='auth_password_reset_complete'
    ),
    url(
        r'^password/reset/done/$',
        auth_views.PasswordResetDoneView.as_view(
            template_name='django_registration/password_reset_done.html'
        ),
        name='auth_password_reset_done'
    ),

    # Captchas
    url(r'^captcha/', include('captcha.urls')),

    # Help
    url(r'^help/', mps.views.mps_help),

    # Djangovoice for feedback
    url(r'^comments/', include('django_comments.urls')),
    url(r'^feedback/', include('djangovoice.urls')),

    # The frontend
    url(r'^', include('bioactivities.urls')),
    url(r'^', include('assays.urls')),
    url(r'^', include('compounds.urls')),
    url(r'^', include('microdevices.urls')),
    url(r'^', include('drugtrials.urls')),
    url(r'^', include('cellsamples.urls')),
    url(r'^', include('diseases.urls')),

    # Default search via haystack/whoosh
    url(r'^haystack/', include('haystack.urls')),
    # Testing custom search (same as default currently)
    # (r'^search/', CustomSearch()),
    url(r'^search/', mps.views.custom_search),


    # BEGIN old-style API
    # TODO THESE SHOULD BE IN THEIR RESPECTIVE APPS
    url(r'^search_ajax/$', mps.ajax.ajax),
    # url(r'^assays_ajax/$', 'assays.ajax.ajax'),
    # url(r'^compounds_ajax/$', 'compounds.ajax.ajax'),
    # url(r'^cellsamples_ajax/$', 'cellsamples.ajax.ajax'),
    # END old-style API

    # Under construction message
    url(r'^under_construction/$', mps.views.UnderConstruction.as_view()),

    url(
        r'^admin/doc/',
        include('django.contrib.admindocs.urls')
    ),
    url(r'^admin/', admin.site.urls),

    url(r'^webhook$', mps.management.webhook),
    url(r'^database$', mps.management.database),

    # url(
    #     r'^media/(?P<path>.*)$',
    #     django.views.static.serve,
    #     {'document_root': settings.MEDIA_ROOT}
    # ),
    url('__debug__/', include(debug_toolbar.urls)),
]

# Note that the URL path can be whatever you want, but you must include
# rest_framework.urls' with the 'rest_framework' namespace.

# urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
