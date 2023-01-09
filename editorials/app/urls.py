from django.urls import path
from . import views

app_name = "app"
urlpatterns = [
    path('', views.index, name="index"),
    path('book/<int:book_id>', views.book_details, name='show_book'),
    path("comments/add/<int:book_id>", views.add_comment, name="add_comment"),
    path("ratings/add/<int:book_id>", views.add_rating, name="add_rating"),
    path("signin", views.signin, name="signin"),
    path("signup", views.signup, name="signup"),
    path("login", views.login, name="login"),
    path("signout", views.signout, name="signout"),
    path("profile", views.edit_user, name="profile"),
    path("categories", views.categories, name="categories"),
]
