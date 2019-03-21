import urllib.request, urllib.parse, urllib.error
from django import VERSION as DJANGO_VERSION
from django.conf import settings
from hashlib import md5

if 'gravatar' in settings.INSTALLED_APPS:
    from gravatar.templatetags.gravatar_tags import gravatar_for_user

else:
    # Just use a glyphicon for users
    def gravatar_for_user(user, size=80):
        url = '/static/img/glyphicons-user.png'

        return url
