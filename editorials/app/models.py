from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

class Category(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False, unique=True)
    
    def __str__(self):
        return f"Category[name={self.name}]"

class Collection(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False, unique=True)
    
    def __str__(self):
        return f"Collection[name={self.name}]"

class Book(models.Model):
    title = models.CharField(max_length=128, default="Sin título", null=False, blank=False)
    author = models.CharField(max_length=256, null=False, default="Anónimo", blank=False)
    description = models.TextField(null=True)
    collection = models.ForeignKey(Collection, null=True, on_delete=models.CASCADE)
    pages = models.PositiveIntegerField(null=True, blank=True, default=0)
    editorial = models.CharField(max_length=64, null=True)
    categories = models.ManyToManyField(Category, related_name='categories')
    cover = models.URLField(null=True)
    url = models.URLField(null=False, blank=False, unique=True)
    
    def __str__(self):
        return f"Book[title={self.title}, author={self.author}, url={self.url}]"

class Rating(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('book', 'user')
    
    def __str__(self):
        return f"Rating[book={self.book}, rating={self.rating}, user={self.user}]"
    
class Comment(models.Model):
    text = models.CharField(max_length=2000)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Comment[text={self.text}, date={self.date}, user={self.user}, book={self.book}]"
    
class ProfilePicture(models.Model):
    image = models.ImageField(upload_to='profile_pictures', null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"ProfilePicture[image={self.image}, user={self.user}]"
    
class UserCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    users = models.ManyToManyField(User, related_name='users')
    
    def __str__(self):
        return f"UserCategory[category={self.category}, user={self.users}]"