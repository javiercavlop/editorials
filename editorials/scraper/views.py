from django.shortcuts import render
from django.contrib import auth, messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseNotFound, HttpResponseRedirect, \
    HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.models import User
from django.urls import reverse
from .scrapers.PlanetaScraper import PlanetaScraper
from .scrapers.PenguinScraper import PenguinScraper
from .scrapers.SMScraper import SMScraper
from .scrapers.AlianzaScraper import AlianzaScraper
from app.models import Book, Category, Collection, Rating, Comment
from django.conf import settings
from whoosh import index, fields
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup, AndGroup
from whoosh.query import Term, Or, And, Not
from .whoosh_lib import BOOK_SCHEMA, COMMENT_SCHEMA
import threading

# ------------------------ Constants ------------------------

MAX_VALUES = [10, 20, 50, 100]
URL_ERRORS = {}

planeta_scraper = PlanetaScraper("https://www.planetadelibros.com/libros")
penguin_scraper = PenguinScraper("https://www.penguinlibros.com/es")
sm_scraper = SMScraper("https://es.literaturasm.com")
alianza_scraper = AlianzaScraper("https://www.alianzaeditorial.es")

# ------------------------ Helpers ------------------------

def not_authenticated(request):
    messages.error(request, "No tienes permisos para acceder a esta página")
    return HttpResponseRedirect(reverse('app:index'))

# ------------------------ Populate ------------------------

def populate_all(request):
    
    if not request.user.is_superuser:
        return not_authenticated(request)
    
    scrapers = [planeta_scraper, penguin_scraper, sm_scraper, alianza_scraper]
    threads = []
    
    try:
        try:
            for scraper in scrapers:
                t = threading.Thread(target=scraper.extract_data)
                t.start()
                threads.append(t)
        finally:
            for t in threads:
                t.join()
            
            bulk_all()
    
        for scraper in reversed(scrapers):
            try:
                scraper.extract_data()
            finally:
                scraper.bulk_data()
        
        try:
            penguin_scraper.extract_data(selenium=True)
        finally:
            penguin_scraper.bulk_data()
            
    finally:
        bulk_all()
        print("SUPUESTAMENTE HA TERMINADO COMPLETAMENTE")
        messages.success(request, "Se han añadido los libros correctamente")
    
    return HttpResponseRedirect(reverse('app:index'))

def populate_planeta(request):
    if not request.user.is_superuser:
        return not_authenticated(request)
    
    try:
        planeta_scraper.extract_data()
    except Exception:
        messages.error(request, "Error al añadir los libros")
    finally:
        planeta_scraper.bulk_data()
        messages.success(request, "Se han añadido los libros correctamente")
        
    return HttpResponseRedirect(reverse('app:index'))

def populate_penguin(request):
    if not request.user.is_superuser:
        return not_authenticated(request)
    
    try:
        penguin_scraper.extract_data()
    except Exception:
        messages.error(request, "Error al añadir los libros")
    finally:
        penguin_scraper.bulk_data()
        messages.success(request, "Se han añadido los libros correctamente")
        
    return HttpResponseRedirect(reverse('app:index'))

def populate_sm(request):
    if not request.user.is_superuser:
        return not_authenticated(request)
    
    try:
        sm_scraper.extract_data()
    except Exception:
        messages.error(request, "Error al añadir los libros")
    finally:
        sm_scraper.bulk_data()
        messages.success(request, "Se han añadido los libros correctamente")
        
    return HttpResponseRedirect(reverse('app:index'))

def populate_alianza(request):
    if not request.user.is_superuser:
        return not_authenticated(request)
        
    try:
        alianza_scraper.extract_data()
    except Exception:
        messages.error(request, "Error al añadir los libros")
    finally:
        alianza_scraper.bulk_data()
        messages.success(request, "Se han añadido los libros correctamente")
        
    return HttpResponseRedirect(reverse('app:index'))

def bulk_all():
    try:
        planeta_scraper.bulk_data()
    except Exception:
        print("Error scraper planeta")
        
    try:
        penguin_scraper.bulk_data()
    except Exception:
        print("Error scraper penguin")
        
    try:
        sm_scraper.bulk_data()
    except Exception:
        print("Error scraper sm")
        
    try:
        alianza_scraper.bulk_data()
    except Exception:
       print("Error scraper alianza")
       
def populate_one(request):
    if not request.user.is_superuser:
        return not_authenticated(request)
    
    user = User.objects.get(username=request.user.username)
    url_errors = URL_ERRORS[user.username+'url_errors'] if URL_ERRORS and URL_ERRORS[user.username+'url_errors'] else []
        
    if request.method == "POST":
        
        url = request.POST["url"].strip()
        book = Book.objects.filter(url=url)
        
        if book.exists():
            messages.warning(request, "El libro ya existe")
            return HttpResponseRedirect(reverse('app:show_book', args=(book[0].id,)))
        
        scrapers = [planeta_scraper, penguin_scraper, sm_scraper, alianza_scraper]
        final_scraper = None
        for scraper in scrapers:
            base_url = scraper.base_url
            base_url_split = base_url.split("://")
            base_url = base_url_split[0]+"://"+base_url_split[1].split("/")[0] if "/" in base_url_split[1] else base_url
            if url.startswith(scraper.base_url):
                final_scraper = scraper
                break
        
        if not final_scraper:
            URL_ERRORS[user.username+'url_errors'] = ["La url no es válida"]
            URL_ERRORS[user.username+'url'] = url
            messages.error(request, "La url no es válida")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
             
        result = None       
        try:
            final_scraper.extract_one_book(url)
        except Exception:
            messages.error(request, "Error al añadir el libro")
        finally:
            result = Book.objects.get(url=url)
            messages.success(request, "Se ha añadido el libro correctamente")
        
        if result:
            return HttpResponseRedirect(reverse('app:show_book', args=(result.id,)))
        
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
       
# ------------------------ Clear ------------------------
       
def clear_db(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('app:index'))
    
    try:
        Book.objects.all().delete()
        Collection.objects.all().delete()
        Category.objects.all().delete()
        Rating.objects.all().delete()
        Comment.objects.all().delete()
    except Exception:
        messages.error(request, "Error al borrar los datos")
    finally:
        messages.success(request, "Datos borrados correctamente")
    
    return HttpResponseRedirect(reverse('app:index'))

# ------------------------ Whoosh ------------------------
def search(request):
    result = []
    books_size = None
    form = create_form(request)
    
    if not request.user.is_authenticated:
        messages.error(request, "Debes estar registrado para acceder a esta página")
        return HttpResponseRedirect(reverse("app:signup"))
    
    if request.method == "POST":
        
        ix_book = index.open_dir(settings.WHOOSH_INDEX_BOOK, schema=BOOK_SCHEMA)
        ix_comment = index.open_dir(settings.WHOOSH_INDEX_COMMENT, schema=COMMENT_SCHEMA)
        
        description_query = create_query_part(ix_book, "description", form["description_all"], form["description_exact"], form["description_any"], form["description_not"])
        comments = create_query_part(ix_comment, "text", form["comments_all"], form["comments_exact"], form["comments_any"], form["comments_not"], True)
        title_query = create_query_part(ix_book, "title", form["title_all"], form["title_exact"], form["title_any"], form["title_not"])
        author_query = create_query_part(ix_book, "author", form["author_all"], form["author_exact"], form["author_any"], form["author_not"])
        editorial_query = create_query_part(ix_book, "editorial", form["editorial_all"], form["editorial_exact"], form["editorial_any"], form["editorial_not"])
        collection_query = create_query_part(ix_book, "collection", form["collection_all"], form["collection_exact"], form["collection_any"], form["collection_not"])
        categories_query = create_query_part(ix_book, "categories", form["categories_all"], None, form["categories_any"], form["categories_not"])
        
        multi_query = []
        if description_query: multi_query.append(description_query)
        if title_query: multi_query.append(title_query) 
        if author_query: multi_query.append(author_query)
        if editorial_query: multi_query.append(editorial_query)
        if collection_query: multi_query.append(collection_query)
        if categories_query: multi_query.append(categories_query)
        
        comments_query = None
        comments_not_query = None
        if comments:
            comments_query, comments_not_query = comments
        
        books = None
        if multi_query:
            multi_query = multi_query if len(multi_query)>1 else multi_query[0]
            print(multi_query)
            #FALLA CUANDO INTENTO HACER UNA CONSULTA MÚLTIPLE 'list' object has no attribute 'matcher'
            book_searcher = ix_book.searcher()
            book_hits = book_searcher.search(multi_query)
            if book_hits.docs():
                hits = [int(hit['id']) for hit in book_hits]
                books = Book.objects.filter(id__in=hits)
            else:
                books = Book.objects.none()
        
        comment_books = None
        not_hits_books = None
        if comments_query:
            comment_searcher = ix_comment.searcher()
            comment_hits = comment_searcher.search(comments_query)
            if comments_not_query:
                comment_not_hits = comment_searcher.search(comments_not_query)
            if comment_hits.docs():
                hits = [int(hit['id']) for hit in comment_hits]
                if comments_not_query and comment_not_hits.docs():
                    not_hits = [int(hit['id']) for hit in comment_not_hits]
                    not_hits_books = Comment.objects.filter(id__in=not_hits).values_list('book', flat=True)
                comment_books = Comment.objects.filter(id__in=hits).values_list('book', flat=True)
            else:
                comment_books = Comment.objects.none()
        
        if books and comment_books:
            result = books.filter(id__in=comment_books)
        elif books and not isinstance(comment_books, type(Comment.objects.none())):
                result = books
        elif comment_books and not isinstance(books, type(Book.objects.none())):
                result = Book.objects.filter(id__in=comment_books)
        
        if not_hits_books and result:
            result = result.exclude(id__in=not_hits_books)
        
        try:
            max_books = int(str(request.POST['max_books']).strip())
        except ValueError:
            max_books = 10
        
        if max_books not in MAX_VALUES:
            max_books = 10
        
        if result:
            result = result[:max_books]
            
        books_size = len(result)

    return render(request,  'search.html', {'books': result, 'max_books': MAX_VALUES, 'books_size': books_size, "form":form})

def create_query_part(ix, field, query_all, query_exact, query_any, query_not, comments=False):
    
    queries = []
    
    if query_all:
        query = [QueryParser(field, ix.schema).parse(q) for q in query_all.split(" ") if q.strip()]
        queries.append(And(query))
                    
    if query_exact:
        queries.append(QueryParser(field, ix.schema).parse('"'+query_exact+'"'))
        
    if query_any:
        query = [QueryParser(field, ix.schema).parse(q) for q in query_any.split(" ") if q.strip()]
        queries.append(Or(query))

        
    if query_not:
        query = [Not(QueryParser(field, ix.schema).parse(q)) for q in query_not.split(" ") if q.strip()]
        queries.append(Or(query))
    
    if queries:
        if comments:
            if query_not:
                return And(queries), Or([QueryParser(field, ix.schema).parse(q) for q in query_not.split(" ") if q.strip()])
            else:
                return And(queries), None
        return And(queries)
    else:
        return None
    
def create_form(request):
    description_all = request.POST['description_all'].strip() if 'description_all' in request.POST else ""
    description_exact = request.POST['description_exact'].strip() if 'description_exact' in request.POST else ""
    description_any = request.POST['description_any'].strip() if 'description_any' in request.POST else ""
    description_not = request.POST['description_not'].strip() if 'description_not' in request.POST else ""
    
    comments_all = request.POST['comments_all'].strip() if 'comments_all' in request.POST else ""
    comments_exact = request.POST['comments_exact'].strip() if 'comments_exact' in request.POST else ""
    comments_any = request.POST['comments_any'].strip() if 'comments_any' in request.POST else ""
    comments_not = request.POST['comments_not'].strip() if 'comments_not' in request.POST else ""
    
    title_all = request.POST['title_all'].strip() if 'title_all' in request.POST else ""
    title_exact = request.POST['title_exact'].strip() if 'title_exact' in request.POST else ""
    title_any = request.POST['title_any'].strip() if 'title_any' in request.POST else ""
    title_not = request.POST['title_not'].strip() if 'title_not' in request.POST else ""
    
    author_all = request.POST['author_all'].strip() if 'author_all' in request.POST else ""
    author_exact = request.POST['author_exact'].strip() if 'author_exact' in request.POST else ""
    author_any = request.POST['author_any'].strip() if 'author_any' in request.POST else ""
    author_not = request.POST['author_not'].strip() if 'author_not' in request.POST else ""
    
    editorial_all = request.POST['editorial_all'].strip() if 'editorial_all' in request.POST else ""
    editorial_exact = request.POST['editorial_exact'].strip() if 'editorial_exact' in request.POST else ""
    editorial_any = request.POST['editorial_any'].strip() if 'editorial_any' in request.POST else ""
    editorial_not = request.POST['editorial_not'].strip() if 'editorial_not' in request.POST else ""
    
    collection_all = request.POST['collection_all'].strip() if 'collection_all' in request.POST else ""
    collection_exact = request.POST['collection_exact'].strip() if 'collection_exact' in request.POST else ""
    collection_any = request.POST['collection_any'].strip() if 'collection_any' in request.POST else ""
    collection_not = request.POST['collection_not'].strip() if 'collection_not' in request.POST else ""
    
    categories_all = request.POST['categories_all'].strip() if 'categories_all' in request.POST else ""
    categories_any = request.POST['categories_any'].strip() if 'categories_any' in request.POST else ""
    categories_not = request.POST['categories_not'].strip() if 'categories_not' in request.POST else ""
    
    form = {
        "description_all": description_all,
        "description_exact": description_exact,
        "description_any": description_any,
        "description_not": description_not,
        "comments_all": comments_all,
        "comments_exact": comments_exact,
        "comments_any": comments_any,
        "comments_not": comments_not,
        "title_all": title_all,
        "title_exact": title_exact,
        "title_any": title_any,
        "title_not": title_not,
        "author_all": author_all,
        "author_exact": author_exact,
        "author_any": author_any,
        "author_not": author_not,
        "editorial_all": editorial_all,
        "editorial_exact": editorial_exact,
        "editorial_any": editorial_any,
        "editorial_not": editorial_not,
        "collection_all": collection_all,
        "collection_exact": collection_exact,
        "collection_any": collection_any,
        "collection_not": collection_not,
        "categories_all": categories_all,
        "categories_any": categories_any,
        "categories_not": categories_not,
    }
    return form