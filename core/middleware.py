from django.shortcuts import render


class MaintenanceModeMiddleware:
    """
    When SiteConfiguration.maintenance_mode is on, shows a maintenance page to
    everyone except staff/admins, so staff can still log in (via /admin/ or
    /accounts/login/) and turn it back off.
    """

    ALWAYS_ALLOWED_PREFIXES = (
        '/admin/',
        '/accounts/login/',
        '/accounts/logout/',
        '/static/',
        '/media/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .models import SiteConfiguration

        try:
            config = SiteConfiguration.get()
        except Exception:
            return self.get_response(request)

        if config.maintenance_mode:
            if request.path.startswith(self.ALWAYS_ALLOWED_PREFIXES):
                return self.get_response(request)
            user = getattr(request, 'user', None)
            if user is not None and user.is_authenticated and user.is_staff:
                return self.get_response(request)
            return render(
                request,
                'maintenance.html',
                {'message': config.maintenance_message},
                status=503,
            )

        return self.get_response(request)
