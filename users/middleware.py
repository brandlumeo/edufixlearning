from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from .utils import decode_token

User = get_user_model()

class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # We only authenticate if the user is not already authenticated by session
        if not request.user.is_authenticated:
            token = request.COOKIES.get('access_token')
            if token:
                payload = decode_token(token)
                if payload:
                    user_id = payload.get('user_id')
                    try:
                        user = User.objects.get(id=user_id)
                        # We don't use login(request, user) here to avoid session overhead
                        # if the requirement is strictly JWT.
                        # Instead, we just attach the user to the request.
                        request.user = user
                    except User.DoesNotExist:
                        pass
        return None
