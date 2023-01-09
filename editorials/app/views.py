from django.contrib import auth, messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseNotFound, HttpResponseRedirect, \
    HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from .models import Book, Collection, Category, Rating, Comment, ProfilePicture, UserCategory
from django.contrib.auth.models import User
from django.urls import reverse
from scraper.recommendations import get_categories_recommendations, get_ratings_recommendations, get_books_recommendations, RATINGS_RS
import os

# ------------------------ Constants ------------------------

MAX_BOOKS_PER_PAGE = 16
MAX_PAGES = 5
PROFILE_ERRORS = {}

# ------------------------ Helpers ------------------------

def is_authenticated(request):  
    messages.error(request, "Debes estar registrado para acceder a esta página")
    return HttpResponseRedirect(reverse("app:signup"))

# ------------------------ General ------------------------

def index(request):

    books = Book.objects.all()
    all_books_size = 0
    
    warning = False
    if not books:
        warning = True
        messages.warning(request, "No hay libros en la base de datos")
    
    if books:
        all_books_size = books.count()
        
        books = filter_books(request, books)
    
    if not books and not warning:
        warning = True
        messages.error(request, "No se han encontrado libros con esos parámetros")

    try:
        search_param = str(request.GET['buscar']).strip()
        if search_param:
            books = books.filter(
                title__icontains=search_param) or books.filter(
                author__icontains=search_param) or books.filter(
                editorial__icontains=search_param)
        else:
            return HttpResponseRedirect(reverse('app:index'))

    except KeyError:
        pass

    if not books and not warning:
        warning = True
        messages.error(request, "No se han encontrado libros con esos parámetros")
        
    books_to_list = []

    try:
        page_number = int(str(request.GET['page']).strip())
    except KeyError:
        page_number = 0

    if len(books) % MAX_BOOKS_PER_PAGE == 0:
        possible_pages = int(len(books) / MAX_BOOKS_PER_PAGE)
    else:
        possible_pages = int(len(books) / MAX_BOOKS_PER_PAGE) + 1

    # Load books to show in view

    for i in range(page_number * MAX_BOOKS_PER_PAGE,
                   page_number * MAX_BOOKS_PER_PAGE + MAX_BOOKS_PER_PAGE):
        if i < len(books):
            books_to_list.append(books[i])
    
    max_range, min_range = get_limits_pages(page_number, possible_pages)

    showcase_categories = []
    if request.user.is_authenticated:
        user_categories = set(Category.objects.filter(usercategory__users=request.user))
        if user_categories:
            categories_recommendations = get_categories_recommendations(user_categories)
            showcase_categories = [Book.objects.get(id=book) for book in categories_recommendations][:10]
        
    showcase_ratings = []
    if request.user.is_authenticated:
        user = User.objects.get(pk=request.user.id)
        if os.path.exists(RATINGS_RS):
            ratings_recommendations = get_ratings_recommendations(user)
            print(ratings_recommendations)
            if ratings_recommendations:
                showcase_ratings = [Book.objects.get(id=book) for book, _ in ratings_recommendations]
                print(showcase_ratings)
    
    # Load collections and categories
    
    collections = Collection.objects.all()
    categories = Category.objects.all()

    return render(request, "index.html", context={"user": request.user,
                                                  "all_books_size": all_books_size,
                                                  "books": books_to_list,
                                                  "showcase_categories": showcase_categories,
                                                  "pages_range": range(0, possible_pages),
                                                  "max_range": max_range,
                                                  "min_range": min_range,
                                                  "current_page": page_number,
                                                  "needs_pagination": possible_pages > 1,
                                                  "collections": collections,
                                                  "categories": categories,
                                                  }
                  )

def get_limits_pages(page_number, possible_pages):
    max_range = page_number+MAX_PAGES if page_number+MAX_PAGES <= possible_pages else possible_pages
    min_range = page_number-MAX_PAGES if page_number-MAX_PAGES > 0 else 0
    
    if max_range-min_range != MAX_PAGES*2:
        if (max_range - page_number) < MAX_PAGES:
            min_range -= MAX_PAGES - (max_range-page_number)
            min_range = min_range if min_range > 0 else 0
        
        if (page_number - min_range) < MAX_PAGES:
            max_range += MAX_PAGES - (page_number-min_range)-1
            max_range = max_range if max_range <= possible_pages else possible_pages
    
    return max_range, min_range
        

def filter_books(request, books):
    
    try:
        if str(request.GET['collection']):
            books = books.filter(collection=int(str(request.GET['collection']).strip()))

    except KeyError:
        pass
    
    try:
        if str(request.GET['category']):
            book_categories = Category.objects.filter(id=int(str(request.GET['category']).strip()))
            books = books.filter(categories__in=book_categories)

    except KeyError:
        pass
    
    try:
        if str(request.GET['order-by']).strip() == 'collection':
            books = books.order_by('collection')

    except KeyError:
        pass
    
    try:
        if str(request.GET['order-by']).strip() == 'author':
            books = books.order_by('author')

    except KeyError:
        pass
    
    try:
        if str(request.GET['order-by']).strip() == 'editorial':
            books = books.order_by('editorial')

    except KeyError:
        pass
    
    try:
        if str(request.GET['order-by']).strip() == 'title':
            books = books.order_by('title')

    except KeyError:
        pass
    
    return books

def login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("app:index"))
    
    if request.method == "GET":
        messages.error(request, "Usuario o contraseña incorrectos")
        return HttpResponseRedirect(reverse("app:index"))
    
    username = request.POST['username'].strip()
    password = request.POST['password'].strip()
    
    if not (username and password):
        messages.error(request, "Usuario o contraseña incorrectos")
        return HttpResponseRedirect(reverse("app:signin"))
    
    user = authenticate(username=username, password=password)

    if user is not None:
        auth.login(request, user)
        return HttpResponseRedirect(reverse("app:index"))
    else:
        messages.error(request, "Usuario o contraseña incorrectos")
        return HttpResponseRedirect(reverse("app:signin"))
    
def signin(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("app:index"))
    else:
        return render(request, "login.html", context={"is_signin": True})

def signout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse("app:index"))

def signup(request):
    if request.method == "POST":

        username = request.POST['username'].strip()
        password = request.POST['password'].strip()
        first_name = request.POST['first_name'].strip()
        last_name = request.POST['last_name'].strip()
        email = request.POST['email'].strip()

        errors = []
        if not (username or password or first_name or last_name or email):
            empty = "Todos los campos del formulario deben estar rellenos"
            errors.append(empty)
        if first_name[0].islower():
            first_letter_name = "La primera letra del nombre debe ser mayúscula"
            errors.append(first_letter_name)
        if last_name[0].islower():
            first_letter_surname = "La primera letra del apellido debe ser mayúscula"
            errors.append(first_letter_surname)
        if len(password) < 8:
            password_length = "La contraseña debe tener al menos 8 caracteres"
            errors.append(password_length)
        if len(username) < 4:
            username_length = "El nombre de usuario debe tener al menos 4 caracteres"
            errors.append(username_length)
        for user in User.objects.all():
            if user.username == username:
                username_exists = "El nombre de usuario ya existe"
                errors.append(username_exists)
            if user.email == email:
                email_exists = "El email ya existe"
                errors.append(email_exists)
        if len(errors) > 0:
            are_errors = True
            return render(request, "login.html", {
                "errors": errors,
                "username": username,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "are_errors": are_errors
            })
        else:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            first_name=first_name,
                                            last_name=last_name, email=email)
            user.save()
            ProfilePicture.objects.create(user=user)
            auth.login(request, user)
            return HttpResponseRedirect(reverse("app:index"))

    else:
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("app:index"))
        else:
            return render(request, "login.html")
        
def edit_user(request):
    
    if not request.user.is_authenticated:
        return is_authenticated(request)
    
    user = User.objects.get(username=request.user)
    profile_picture, _ = ProfilePicture.objects.get_or_create(user=user)
    
    name_errors = PROFILE_ERRORS[user.username+'name_errors'] if PROFILE_ERRORS and PROFILE_ERRORS[user.username+'name_errors'] else []
    surname_errors = PROFILE_ERRORS[user.username+'surname_errors'] if PROFILE_ERRORS and PROFILE_ERRORS[user.username+'surname_errors'] else []
    username_errors = PROFILE_ERRORS[user.username+'username_errors'] if PROFILE_ERRORS and PROFILE_ERRORS[user.username+'username_errors'] else []
    email_errors = PROFILE_ERRORS[user.username+'email_errors'] if PROFILE_ERRORS and PROFILE_ERRORS[user.username+'email_errors'] else []
    profile_pic_errors = PROFILE_ERRORS[user.username+'profile_pic_errors'] if PROFILE_ERRORS and PROFILE_ERRORS[user.username+'profile_pic_errors'] else []
    
    if request.method == 'GET':
        first_name = user.first_name
        surname = user.last_name
        username = user.username
        email = user.email
        profile_picture = str(profile_picture.image)
        
        if PROFILE_ERRORS:
            first_name= PROFILE_ERRORS[user.username+'name']
            surname = PROFILE_ERRORS[user.username+'surname']
            username = PROFILE_ERRORS[user.username+'username']
            email = PROFILE_ERRORS[user.username+'email']
            profile_picture = PROFILE_ERRORS[user.username+'profile_pic']
            
            del PROFILE_ERRORS[user.username+'name']
            del PROFILE_ERRORS[user.username+'surname']
            del PROFILE_ERRORS[user.username+'username']
            del PROFILE_ERRORS[user.username+'email']
            del PROFILE_ERRORS[user.username+'profile_pic']
            
            del PROFILE_ERRORS[user.username+'name_errors']
            del PROFILE_ERRORS[user.username+'surname_errors']
            del PROFILE_ERRORS[user.username+'username_errors']
            del PROFILE_ERRORS[user.username+'email_errors']
            del PROFILE_ERRORS[user.username+'profile_pic_errors']
            
        return render(request, "profile.html", {
            'first_name': first_name,
            'last_name': surname,
            'username': username,
            'email': email,
            'profile_picture': profile_picture,
            'name_errors': name_errors,
            'surname_errors': surname_errors,
            'username_errors': username_errors,
            'email_errors': email_errors,
            'profile_pic_errors': profile_pic_errors,
        })
    else:
        user_attrs = request.POST
        first_name = str(user_attrs['first_name']).strip()
        surname = str(user_attrs['last_name']).strip()
        username = str(user_attrs['username']).strip()
        email = str(user_attrs['email']).strip()
        profile_pic = str(user_attrs['profile_pic']).strip()
        
        required_field = "Este campo es obligatorio"
        if not first_name or first_name == '':
            name_errors.append(required_field)
        if not surname or surname == '':
            surname_errors.append(required_field)
        if not username or username == '':
            username_errors.append(required_field)
        if not email or email == '':
            email_errors.append(required_field)
        if not profile_pic:
            profile_pic = ""
        
        if first_name and first_name[0].islower():
            name_errors.append("La primera letra del nombre debe ser mayúscula")
        if surname and surname[0].islower():
            surname_errors.append("La primera letra del apellido debe ser mayúscula")
        if username and 3 >= len(username) <= 24:
            username_errors.append("El nombre de usuario debe tener entre 4 y 24 caracteres")
        if email and 3 >= len(email) <= 64:
            email_errors.append("El email debe tener entre 4 y 64 caracteres")
        if profile_pic and len(profile_pic) >= 90:
            profile_pic_errors.append("La imagen debe tener menos de 90 caracteres")
            
        try:
            if user.username != username and username:
                User.objects.get(username=username)
                username_errors.append("El nombre de usuario ya existe")
        except User.DoesNotExist:
            pass
        
        try:
            if user.email != email and email:
                User.objects.get(email=email)
                email_errors.append("El email ya está registrado")
        except User.DoesNotExist:
            pass
        
        if name_errors or surname_errors or username_errors or email_errors or profile_pic_errors:
            PROFILE_ERRORS[user.username+'name'] = first_name
            PROFILE_ERRORS[user.username+'surname'] = surname
            PROFILE_ERRORS[user.username+'username'] = username
            PROFILE_ERRORS[user.username+'email'] = email
            PROFILE_ERRORS[user.username+'profile_pic'] = profile_pic
            PROFILE_ERRORS[user.username+'name_errors'] = name_errors
            PROFILE_ERRORS[user.username+'surname_errors'] = surname_errors
            PROFILE_ERRORS[user.username+'username_errors'] = username_errors
            PROFILE_ERRORS[user.username+'email_errors'] = email_errors
            PROFILE_ERRORS[user.username+'profile_pic_errors'] = profile_pic_errors
            return HttpResponseRedirect(reverse("app:profile"))
            
        user.first_name = first_name
        user.last_name = surname
        user.username = username
        user.email = email
        profile_picture.image = profile_pic
        
        try:
            user.save()
            profile_picture.save()
            messages.success(request, "Perfil actualizado correctamente")
        except Exception:
            messages.error(request, "Ha ocurrido un error al actualizar el perfil")

    return HttpResponseRedirect(reverse("app:profile"))

def categories(request):
    if not request.user.is_authenticated:
        return is_authenticated(request)
    
    if request.method == "POST":
        user = User.objects.get(pk=request.user.id)
        categories = request.POST.getlist("categories")
        if categories:
            for category in categories:
                cat = Category.objects.get(id=int(category))
                uc, _ = UserCategory.objects.get_or_create(category=cat)
                if user not in uc.users.all():
                    uc.users.add(user)
                uc.save()
                
        user_categories = Category.objects.filter(usercategory__users=user)
        deleted_categories = [cat for cat in user_categories if str(cat.id) not in categories]
        
        for uc in UserCategory.objects.filter(category__in=deleted_categories):
            uc.users.remove(user)
            uc.save()
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# ------------------------ Books ------------------------

def book_details(request, book_id):
    book = get_object_or_404(Book, pk=book_id)

    average_rating = 0
    ratings = Rating.objects.filter(book=book)
    if ratings:
        for rating in ratings:
            average_rating += rating.rating
        average_rating /= len(ratings)
    

    comments = Comment.objects.filter(book=book)
    categories = book.categories.all()
    
    showcase_categories = []
    book_categories = set(categories)
    if book_categories and os.path.exists(RATINGS_RS):
        categories_recommendations = get_categories_recommendations(book_categories)
        showcase_categories = [Book.objects.get(id=b) for b in categories_recommendations if b != book.id][:10]
        
    showcase_ratings = []
    ratings_recommendations = get_books_recommendations(book)
    if ratings_recommendations:
        showcase_ratings = [Book.objects.get(id=book) for book, _ in ratings_recommendations]

    return render(request, "book_details.html",
                  context={"user": request.user, "book": book,
                            "categories": categories,
                            "suggested_books": None,
                            "average_rating": average_rating,
                            "showcase_categories": showcase_categories,
                            "showcase_ratings": showcase_ratings,
                            "comments": comments,})
    
# ------------------------ Comments ------------------------

def add_comment(request, book_id):
    
    if not request.user.is_authenticated:
        return is_authenticated(request)
    
    if request.method == "POST":
        book = get_object_or_404(Book, pk=book_id)
        user = User.objects.get(pk=request.user.id)

        text = request.POST['comment'].strip()
        
        if text:
            comment = Comment(text=text, book=book, user=user)
            comment.save()
        else:
            messages.error(request, "No puedes dejar un comentario vacío")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# ------------------------ Ratings ------------------------

def add_rating(request, book_id):
    
    if not request.user.is_authenticated:
        return is_authenticated(request)
    
    if request.method == "POST":
        book = get_object_or_404(Book, pk=book_id)
        user = User.objects.get(pk=request.user.id)

        rate = int(request.POST['rating'])
        
        if rate and rate >= 1 and rate <= 5:
            prev_rating = Rating.objects.filter(book=book, user=user)
            if prev_rating:
                prev_rating[0].rating = rate
                prev_rating[0].save()
            else:
                rating = Rating(rating=rate, book=book, user=user)
                rating.save()
        else:
            messages.error(request, "Se necesita introducir una puntuación válida")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
