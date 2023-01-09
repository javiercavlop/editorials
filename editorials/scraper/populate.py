from django.contrib.auth.models import User
from app.models import Rating, Comment, UserCategory, Book, Category, Collection
from .utils.Timer import Timer
import random, shutil, os
from django.conf import settings
from random_username.generate import generate_username
from .whoosh_lib import new_comment


def populate():
    timer = Timer()
    timer.start()
    print("----------------------POPULATE DATABASE-----------------------")
    
    create_superuser()
    
    users = []
    books = Book.objects.all()
    max_books = books.count()-1
    
    for username in generate_username(int(max_books/10)):
        user = create_user(username=username)
        if user:
            users.append(user)
    
    max_users = len(users)-1
    print("%f Users fueron creados" % (max_users+1))
    
    for _ in range(int(max_books*2)):
        random_user_index = random.randint(0, max_users)
        random_user = users[random_user_index]
        random_book_index = random.randint(0, max_books)
        random_book = books[random_book_index]
        create_rating(random_user, random_book)
        
    print("Aprox %f Ratings fueron creados" % (int(max_books*2)))
    
    categories = Category.objects.all()
    max_categories = categories.count()-1
    
    for _ in range(int(max_users*0.75)):
        random_category_index = random.randint(0, max_categories)
        random_category = categories[random_category_index]
        random_users = set([users[random.randint(0, max_users)] for _ in range(0, random.randint(1,15))])
        create_user_category(random_users, random_category)
    
    print("Aprox %f UserCategories fueron creadas" % (int(max_users*0.75)))
    
    create_comment(users[0], books[0], "Probando a escribir un comentario")
    create_comment(users[0], books[0], "Es una novela que no decepciona")
    create_comment(users[0], books[1], "Muy guay el libro")
    create_comment(users[0], books[2], "¡Me encanta!")
    create_comment(users[1], books[0], "No me gusta este")
    create_comment(users[1], books[1], "JAJAJAJAJAJA")
    create_comment(users[1], books[2], "El autor nos manda un mensaje precioso a través de este libro")
    create_comment(users[1], books[3], "Muy buena encuadernación")
    create_comment(users[0], books[4], "Es un libro que recomiendo a todo el mundo")
    create_comment(users[2], books[5], "Deseando seguir leyendo más libros de este gran autor")
    
    print("10 Comments fueron creados")
        
    timer.stop()
    print("El tiempo de ejecución ha sido de %f milisegundos" % (timer.get_time()))

def clean():
    timer = Timer()
    timer.start()
    print("----------------------CLEAN DATABASE-----------------------")
    
    User.objects.all().delete()
    Rating.objects.all().delete()
    Comment.objects.all().delete()
    UserCategory.objects.all().delete()
    shutil.rmtree(settings.WHOOSH_INDEX_COMMENT, ignore_errors=True)
    os.makedirs(settings.WHOOSH_INDEX_COMMENT, exist_ok=True)
    
    timer.stop()
    print("El tiempo de ejecución ha sido de %f milisegundos" % (timer.get_time()))
    
def reset():
    timer = Timer()
    timer.start()
    print("----------------------RESET DATABASE-----------------------")
    
    User.objects.all().delete()
    Book.objects.all().delete()
    Collection.objects.all().delete()
    Category.objects.all().delete()
    UserCategory.objects.all().delete()
    Rating.objects.all().delete()
    Comment.objects.all().delete()
    shutil.rmtree(settings.WHOOSH_INDEX_BOOK, ignore_errors=True)
    os.makedirs(settings.WHOOSH_INDEX_BOOK, exist_ok=True)
    shutil.rmtree(settings.WHOOSH_INDEX_COMMENT, ignore_errors=True)
    os.makedirs(settings.WHOOSH_INDEX_COMMENT, exist_ok=True)
    
    timer.stop()
    print("El tiempo de ejecución ha sido de %f milisegundos" % (timer.get_time()))
    

def create_superuser():
    if not User.objects.filter(username='superuser').exists():
        User.objects.create_superuser('superuser', email='', password='superuser')
        print("Superuser created with credentials:\n\tusername: superuser\n\tpassword: superuser")

    else:
        print('Superuser already exists')

def create_user(username, password="contraseña1"):
    user = None
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username=username, password=password)
        user.save()
    return user
        
def create_rating(user, book):
    if not Rating.objects.filter(book=book, user=user).exists():
        rating = random.randint(1, 5)
        rating = Rating.objects.create(book=book, user=user, rating=rating)
        rating.save()

def create_comment(user, book, text):
    if not Comment.objects.filter(user=user, book=book, text=text).exists():
        comment = Comment.objects.create(user=user, book=book, text=text)
        comment.save()
        
def create_user_category(users, category):
    if not UserCategory.objects.filter(category=category).exists():
        uc = UserCategory.objects.create(category=category)
        uc.users.set(users)
        uc.save()