from django.contrib.auth.models import User
from rest_framework.authentication import BaseAuthentication

DEV_USERNAME = "dev"


class AutoLoginDevAuthentication(BaseAuthentication):
    """Dev-only DRF authenticator: treats every request as a fixed local user.

    Only wired in via REST_FRAMEWORK settings when DEBUG is True; never used
    in production, so this bypasses token auth exclusively in local dev.
    """

    def authenticate(self, request):
        user, _ = User.objects.get_or_create(username=DEV_USERNAME)
        return (user, None)