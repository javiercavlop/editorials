from .views import URL_ERRORS
from django.contrib.auth.models import User
from app.models import Category

def global_context(request):
    categories = None
    user_categories = None
    
    if request.user.is_authenticated:
        categories = Category.objects.all()
        user_categories = Category.objects.filter(usercategory__users=request.user)
    
    if request.user.is_superuser:
        user = User.objects.get(username=request.user.username)
        url_errors = URL_ERRORS[user.username+'url_errors'] if URL_ERRORS and URL_ERRORS[user.username+'url_errors'] else []
        url = ""
        
        if request.method == "GET":
            if URL_ERRORS:
                url= URL_ERRORS[user.username+'url']
            
                del URL_ERRORS[user.username+'url']
                del URL_ERRORS[user.username+'url_errors']
                
            return {'url': url, 'url_errors': url_errors, 'categories': categories, 'user_categories': user_categories}
    
    if request.user.is_authenticated and request.method == "GET":
        return {'categories_form': categories, 'user_categories_form': user_categories}
        
    return {}