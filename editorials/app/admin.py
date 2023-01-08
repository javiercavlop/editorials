from django.contrib import admin
from .models import Category, Collection, Book, Rating, Comment, ProfilePicture

admin.site.register(Category)
admin.site.register(Collection)
admin.site.register(Book)
admin.site.register(Rating)
admin.site.register(Comment)
admin.site.register(ProfilePicture)
