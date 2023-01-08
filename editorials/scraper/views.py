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
import threading, shutil
from app.views import MAX_BOOKS_PER_PAGE, MAX_PAGES

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
        shutil.rmtree(settings.WHOOSH_INDEX_BOOK, ignore_errors=True)
        shutil.rmtree(settings.WHOOSH_INDEX_COMMENT, ignore_errors=True)
    except Exception:
        messages.error(request, "Error al borrar los datos")
    finally:
        messages.success(request, "Datos borrados correctamente")
    
    return HttpResponseRedirect(reverse('app:index'))

# ------------------------ Whoosh ------------------------
def search(request):
    result = []
    books_to_list = []
    books_size = None
    possible_pages = len(result)
    max_range = None
    min_range = None
    page_number = None
    
    if not request.user.is_authenticated:
        messages.error(request, "Debes estar registrado para acceder a esta página")
        return HttpResponseRedirect(reverse("app:signup"))
    
    form = create_form(request)
        
    empty = True
    for key in form:
        if form[key]:
            empty = False
    if empty:
        return render(request,  'search.html', {'books': result, 'max_books': MAX_VALUES, 'books_size': books_size, "form":form})
    
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
    
    comments_not_query = None
    not_queries = None
    all_query = None
    exact_query = None
    or_query = None
    if comments:
        all_query, exact_query, or_query, not_queries, comments_not_query = comments
    
    books = None
    
    for query in multi_query:
        books = get_book_hits(ix_book, query, books)
        if books and isinstance(books, bool):
            books = Book.objects.none()
            break
    
    queries = [all_query, exact_query, or_query, not_queries, comments_not_query]
    all_hits, exact_hits, any_hits, not_hits, not_hits_books = get_comment_hits(queries, ix_comment)
    hits = Comment.objects.none() if comments else None
    
    if all_hits:
        hits = all_hits
        
    if exact_hits:
        if hits:
            hits = hits.filter(id__in=exact_hits)
        else:
            hits = exact_hits
    
    if not_hits:
        if hits:
            hits = hits.exclude(id__in=not_hits)
        else:
            hits = Book.objects.all().exclude(id__in=not_hits)
    
    if any_hits:
        if not_hits:
            any_hits = any_hits.exclude(id__in=not_hits)
        if hits:
            hits = hits.union(any_hits)
        else:
            hits = any_hits     
            
    
    if books and hits:
        result = books.filter(id__in=hits)
    elif books and not isinstance(hits, type(Comment.objects.none())):
            result = books
    elif hits and not isinstance(books, type(Book.objects.none())):
            result = Book.objects.filter(id__in=hits)
    
    if not_hits_books and result:
        result = result.exclude(id__in=not_hits_books)
        if any_hits:
            result = result.union(any_hits)
    
    try:
        max_book = int(str(request.GET['max_books']).strip())
    except ValueError:
        max_book = MAX_VALUES[0]
    
    if max_book not in MAX_VALUES:
        max_book = MAX_VALUES[0]
    
    if result:
        result = result[:max_book]
        
    books_size = len(result)
    
    try:
        page_number = int(str(request.GET['page']).strip())
    except KeyError:
        page_number = 0

    if len(result) % MAX_BOOKS_PER_PAGE == 0:
        possible_pages = int(len(result) / MAX_BOOKS_PER_PAGE)
    else:
        possible_pages = int(len(result) / MAX_BOOKS_PER_PAGE) + 1

    # Load books to show in view

    for i in range(page_number * MAX_BOOKS_PER_PAGE,
                page_number * MAX_BOOKS_PER_PAGE + MAX_BOOKS_PER_PAGE):
        if i < len(result):
            books_to_list.append(result[i])
    
    max_range, min_range = get_limits_pages(page_number, possible_pages)

    return render(request,  'search.html', {'books': books_to_list, 'max_books': MAX_VALUES, 'max_book': max_book, 'books_size': books_size, "form":form,
                                            "pages_range": range(0, possible_pages), "max_range": max_range, "min_range": min_range,
                                            "current_page": page_number, "needs_pagination": possible_pages > 1,})
    
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

def create_query_part(ix, field, query_all, query_exact, query_any, query_not, comments=False):
    
    queries = []
    
    all_query = False
    if query_all:
        query = [QueryParser(field, ix.schema).parse(q) for q in query_all.split(" ") if q.strip()]
        all_query = And(query)
        queries.append(all_query)
    
    exact_query = False     
    if query_exact:
        exact_query = QueryParser(field, ix.schema).parse('"'+query_exact+'"')
        queries.append(exact_query)
    
    or_queries = False
    if query_any:
        query = [QueryParser(field, ix.schema).parse(q) for q in query_any.split(" ") if q.strip()]
        or_queries = Or(query)

    not_queries = False
    if query_not:
        query = [Not(QueryParser(field, ix.schema).parse(q)) for q in query_not.split(" ") if q.strip()]
        not_queries = Or(query)
        queries.append(not_queries)
    
    if queries or or_queries:
        if comments:
            return all_query, exact_query, or_queries, not_queries, Or([QueryParser(field, ix.schema).parse(q) for q in query_not.split(" ") if q.strip()])
        return get_final_query(queries, or_queries, not_queries)
    else:
        return None
    
def get_comment_hits(queries, ix_comment):
    hits_results = []
    for query in queries:
        if query:
            comment_searcher = ix_comment.searcher()
            comment_hits = comment_searcher.search(query)
            if comment_hits.docs():
                hits = [int(hit['id']) for hit in comment_hits]
                comment_books = Comment.objects.filter(id__in=hits).values_list('book', flat=True)
            else:
                comment_books = None
        else:
            comment_books = None
        hits_results.append(comment_books)
        
    return hits_results

def get_final_query(queries, or_queries, not_queries):
    if queries and or_queries and not_queries:
        return Or(And(queries), And(or_queries, not_queries))
    elif queries and or_queries:
        return Or(And(queries), or_queries)
    elif queries:
        return And(queries)
    elif or_queries:
        return or_queries


def create_form(request):
    description_all = request.GET['description_all'].strip() if 'description_all' in request.GET else ""
    description_exact = request.GET['description_exact'].strip() if 'description_exact' in request.GET else ""
    description_any = request.GET['description_any'].strip() if 'description_any' in request.GET else ""
    description_not = request.GET['description_not'].strip() if 'description_not' in request.GET else ""
    
    comments_all = request.GET['comments_all'].strip() if 'comments_all' in request.GET else ""
    comments_exact = request.GET['comments_exact'].strip() if 'comments_exact' in request.GET else ""
    comments_any = request.GET['comments_any'].strip() if 'comments_any' in request.GET else ""
    comments_not = request.GET['comments_not'].strip() if 'comments_not' in request.GET else ""
    
    title_all = request.GET['title_all'].strip() if 'title_all' in request.GET else ""
    title_exact = request.GET['title_exact'].strip() if 'title_exact' in request.GET else ""
    title_any = request.GET['title_any'].strip() if 'title_any' in request.GET else ""
    title_not = request.GET['title_not'].strip() if 'title_not' in request.GET else ""
    
    author_all = request.GET['author_all'].strip() if 'author_all' in request.GET else ""
    author_exact = request.GET['author_exact'].strip() if 'author_exact' in request.GET else ""
    author_any = request.GET['author_any'].strip() if 'author_any' in request.GET else ""
    author_not = request.GET['author_not'].strip() if 'author_not' in request.GET else ""
    
    editorial_all = request.GET['editorial_all'].strip() if 'editorial_all' in request.GET else ""
    editorial_exact = request.GET['editorial_exact'].strip() if 'editorial_exact' in request.GET else ""
    editorial_any = request.GET['editorial_any'].strip() if 'editorial_any' in request.GET else ""
    editorial_not = request.GET['editorial_not'].strip() if 'editorial_not' in request.GET else ""
    
    collection_all = request.GET['collection_all'].strip() if 'collection_all' in request.GET else ""
    collection_exact = request.GET['collection_exact'].strip() if 'collection_exact' in request.GET else ""
    collection_any = request.GET['collection_any'].strip() if 'collection_any' in request.GET else ""
    collection_not = request.GET['collection_not'].strip() if 'collection_not' in request.GET else ""
    
    categories_all = request.GET['categories_all'].lower().strip() if 'categories_all' in request.GET else ""
    categories_any = request.GET['categories_any'].lower().strip() if 'categories_any' in request.GET else ""
    categories_not = request.GET['categories_not'].lower().strip() if 'categories_not' in request.GET else ""
    
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

def get_book_hits(ix_book, query, books):
    book_searcher = ix_book.searcher()
    book_hits = book_searcher.search(query)
    if book_hits.docs():
        hits = [int(hit['id']) for hit in book_hits]
        if books:
            books = books.filter(id__in=hits)
        else:  
            books = Book.objects.filter(id__in=hits)
    else:
        books = True
    return books