from bs4 import BeautifulSoup
import urllib.request, threading
import sys
sys.path.insert(1, '/editorials')
from ..utils.Timer import Timer
from app.models import Book, Category, Collection

BASE_URL = "https://www.planetadelibros.com"
  
def scraper():
    timer = Timer()
    timer.start()
    f = urllib.request.urlopen(BASE_URL+"/libros")
    s = BeautifulSoup(f,"lxml")
    visited = set()
    
    if Book.objects.all().exists():
        visited = set(Book.objects.all().values_list('url', flat=True))
    
    a_paths = s.select('div.tematiques > a')
    paths = [a.get('href') for a in a_paths]
    T = []
    books_mem = []
    categories_mem = []
    collections_mem = []

    for path in paths:
        f1 = urllib.request.urlopen(path)
        s1 = BeautifulSoup(f1,"lxml")
        t = threading.Thread(target=recursive_scraper, args=(path, s1, visited, books_mem, categories_mem, collections_mem))
        t.start()
        T.append(t)
    
    for t in T:
        t.join()
        
    print("----------------------BULKING DATA-----------------------")
    categories = []
    print("Collections length: " + str(len(collections_mem)))
    collections = [Collection.objects.get_or_create(name=collection.name)[0] if collection else None for collection in collections_mem]
    
    print("Categories length: " + str(len(categories_mem)))
    for category in categories_mem:
        if category:
            new = [[Category.objects.get_or_create(name=cat.name)[0] for cat in category if cat]]
            if new:
                categories += new
    if not categories:
        categories = [None for _ in range(len(books_mem))]
        
    print("Books length: " + str(len(books_mem)))
    books = Book.objects.bulk_create(books_mem)
    
    for book, category, collection in zip(books, categories, collections):
        try:
            if book:
                #     if collection:
                #         if book.pages == 0:
                #             book, _ = Book.objects.get_or_create(title=book.title, author=book.author, description=book.description, collection=book.collection, editorial=book.editorial, cover=book.cover, url=book.url)
                #         else:
                #             book, _ = Book.objects.get_or_create(title=book.title, author=book.author, description=book.description, collection=book.collection, pages=book.pages, editorial=book.editorial, cover=book.cover, url=book.url)
                #     else:
                #         if book.pages == 0:
                #             book, _ = Book.objects.get_or_create(title=book.title, author=book.author, description=book.description, editorial=book.editorial, cover=book.cover, url=book.url)
                #         else:
                #             book, _ = Book.objects.get_or_create(title=book.title, author=book.author, description=book.description, pages=book.pages, editorial=book.editorial, cover=book.cover, url=book.url)
                if collection:
                    book.collection = collection
                
                expr = categories[0] and category and category[0]
                if expr:
                    book.categories.set(category)
                
                if collection or expr:
                    book.save()
        except Exception as e:
            print("----------------------ERROR-----------------------")
            print("Error with book: " + book)
            print("Error with category: " + category)
            print("Error with collection: " + collection)
            print(e)
        
    print("\n----------------------ENDING-----------------------")
    timer.end()
    print("El tiempo de ejecución ha sido de %f milisegundos" % (timer.get_time()))
                
def recursive_scraper(url, s, visited, books_mem, categories_mem, collections_mem, is_not_first=False):
    first_part = s.find('div', class_='paginacio-seguent')
    next_url = None
    if first_part:
        second_part = first_part.find('a')
        if second_part:
            next_url = second_part.get('href')
            
    if is_not_first and next_url:
        f = urllib.request.urlopen(next_url)
        s = BeautifulSoup(f,"lxml")
        print("\n")
        print(next_url)
        books, categories, collections  = find_book(s, visited)
        books_mem += books
        categories_mem += categories
        collections_mem += collections
        
        recursive_scraper(next_url, s, visited, books_mem, categories_mem, collections_mem, True)
    else:
        
        f = urllib.request.urlopen(url)
        s = BeautifulSoup(f,"lxml")
        print("\n")
        print(url)
    
        books, categories, collections = find_book(s, visited)
        books_mem += books
        categories_mem += categories
        collections_mem += collections
        if not is_not_first:
            recursive_scraper(url, s, visited, books_mem, categories_mem, collections_mem, True)

def find_book(s, visited):
    books_grid = s.find_all('ul', class_='llibres-miniatures llibres-graella')[-1].find_all('a')
    G = []
    books = []
    categories = []
    collections = []
    for book in books_grid:
        new_url = book.get('href')
        if new_url not in visited:
            visited.add(new_url)
            t = threading.Thread(target=get_book, args=(new_url, books, categories, collections))
            t.start()
            G.append(t)
    
    for t in G:
        t.join()
    
    return books, categories, collections
            
  
def get_book(new_url, books, categories, collections):
    try:
        f = urllib.request.urlopen(new_url)
        s = BeautifulSoup(f,"lxml")
        book, category, collection = create_book(s, new_url)
        if book:
            books.append(book)
            categories.append(category)
            collections.append(collection)
        
    except Exception as e:
        print("Error: " + new_url)
        print(e)    

def create_book(s, url):
    title = get_title(s)
    if title:
        author = get_author(s)
        description = get_description(s)
        collection = get_collection(s)
        pages = get_pages(s)
        editorial = get_editorial(s)
        categories_list = get_categories(s)
        cover = get_cover(s)

        if collection:
            collection = Collection(name=collection)
        
        categories = None
        if categories_list:
            categories = [Category(name=category) for category in categories_list]
        
        if pages:
            book = Book(title=title, author=author, description=description, pages=pages, editorial=editorial, cover=cover, url=url)
        else:
            book = Book(title=title, author=author, description=description, editorial=editorial, cover=cover, url=url)
            
        if book:
            print(book)
            return book, categories, collection
    return None, None, None

def get_title(s):
    title_div = s.find('div', class_='fitxa-bloc-b1')
    if title_div:
        title = title_div.find('h1')
        if title:
            return title.get_text().strip()
    return None

def get_author(s):
    author_div = s.find('div', class_='autors')
    text = "Anónimo"
    if author_div:
        authors = author_div.find_all('a')
        if authors:
            text = ""
            for author in authors:
                text += author.get_text().strip() + ", "
            text = text[:-2]
    return text

def get_description(s):
    text = ""
    sinopsis = s.find('div', class_='sinopsi')
    if sinopsis:
        descriptions = sinopsis.find_all('p')
        if descriptions:
            for p in descriptions:
                text += p.get_text().strip() + "\n"
            return text
    return None

def get_collection(s):
    collections = s.find('div', class_='coleccions')
    if collections:    
        collection = collections.find('a')
        if collection:
            return collection.get_text().strip()
    return None

def get_pages(s):
    pages_div = s.find('div', id='num_pagines')
    pages = None
    if pages_div:
        pages_str = pages_div.get_text().strip()
        if ":" in pages_str:
            pages = pages_str.split(":")[1].strip()
        else:
            pages = pages_str
            
        try:
            pages = int(pages)
        except Exception as e:
            pages = None
            print(e)
            
    return pages

def get_editorial(s):
    editorial_div = s.find('div', class_='segell-nom')
    if editorial_div:
        editorial = editorial_div.find('a')
        if editorial:
            return editorial.get_text().strip()
    return "Planeta de Libros"

def get_categories(s):
    categories_div = s.find('div', class_='tematiques')
    if categories_div:
        categories = categories_div.find_all('a')
        if categories:
            return [category.get_text().strip() for category in categories]
    return None

def get_cover(s):
    image_div = s.find('div', class_='foto')
    if image_div:    
        image = image_div.find('img')
        if image:
            return image.get('data-src')
    return None