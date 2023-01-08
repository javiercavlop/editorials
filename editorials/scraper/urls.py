from django.urls import path
from . import views

app_name = "scraper"
urlpatterns = [
    path('populate/all', views.populate_all, name='populate'),
    path('populate/planeta', views.populate_planeta, name='populate_planeta'),
    path('populate/penguin', views.populate_penguin, name='populate_penguin'),
    path('populate/sm', views.populate_sm, name='populate_sm'),
    path('populate/alianza', views.populate_alianza, name='populate_alianza'),
    path('clear', views.clear_db, name='clear'),
    path('search', views.search, name='search'),
    path('populate/one', views.populate_one, name='populate_one'),
]
