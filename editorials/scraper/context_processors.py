from .views import URL_ERRORS
from django.contrib.auth.models import User

def global_context(request):
    if request.user.is_superuser:
        user = User.objects.get(username=request.user.username)
        url_errors = URL_ERRORS[user.username+'url_errors'] if URL_ERRORS and URL_ERRORS[user.username+'url_errors'] else []
        url = ""
        
        if request.method == "GET":
            if URL_ERRORS:
                url= URL_ERRORS[user.username+'url']
            
                del URL_ERRORS[user.username+'url']
                del URL_ERRORS[user.username+'url_errors']
                
            return {'url': url, 'url_errors': url_errors}
    return {}