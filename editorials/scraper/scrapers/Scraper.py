from bs4 import BeautifulSoup
import urllib.request, threading
import sys
sys.path.insert(1, '/editorials')
from ..utils.Timer import Timer
from app.models import Book, Category, Collection
from abc import ABC, abstractmethod

class Scraper(ABC):
    
    def __init__(self, base_url):
        if not isinstance(base_url, str):
            raise TypeError("base_url must be a string")
        
        if not base_url.startswith('http'):
            raise ValueError("base_url must be a valid url like 'http(s)://www.example.com'")
        
        self.lock = threading.Lock()
        self.books_mem = []
        self.categories_mem = []
        self.collections_mem = []
        self.visited = set()
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.base_url = base_url
        
    def _clear_data(self):
        self.lock = threading.Lock()
        self.books_mem = []
        self.categories_mem = []
        self.collections_mem = []
        self.visited = set()
        self.headers = {'User-Agent': 'Mozilla/5.0'}
    
    def extract_data(self, selenium=False):
        
        if not isinstance(selenium, bool):
            raise TypeError("selenium must be a boolean")
        
        self._clear_data()
        
        timer = Timer()
        timer.start()
        r = urllib.request.Request(self.base_url, headers=self.headers)
        f = urllib.request.urlopen(r)
        s = BeautifulSoup(f,"lxml")
        
        if Book.objects.all().exists():
            self.visited = set(Book.objects.all().values_list('url', flat=True))
        
        paths = self._get_paths(s, selenium)
        print("PATHS DONE")
        threads = []

        for path in paths:
            driver = None
            if isinstance(path, str):
                path = self._parse_url(path)
                r1 = urllib.request.Request(path, headers=self.headers)
                f1 = urllib.request.urlopen(r1)
            else:
                f1, driver = path
            s1 = BeautifulSoup(f1,"lxml")
            t = threading.Thread(target=self._recursive_scraper, args=(path, s1, driver, selenium))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
            
        print("\n----------------------ENDING-----------------------")
        timer.stop()
        print("El tiempo de ejecución ha sido de %f milisegundos" % (timer.get_time()))
    
    def _parse_url(self, url):
        if not url.startswith('http'):
            if url.startswith('/') and self.base_url.endswith('/'):
                url =  self.base_url + url[1:]
            elif url.startswith('/') or self.base_url.endswith('/'):
                url =  self.base_url + url
            else:
                url =  self.base_url + "/" + url
        return url
    
    def extract_one_book(self, url):
        self._clear_data()
        try:
            self._get_book(url)
        finally:
            self.bulk_data()
        
    def bulk_data(self):
        timer = Timer()
        timer.start()
        print("----------------------BULKING DATA-----------------------")
        
        collections = self._bulk_collections()
        categories = self._bulk_categories()
        books = self._bulk_books()
        
        self._update_books(books, categories, collections)
        
        self._clear_data()

        timer.stop()
        print("El tiempo de ejecución ha sido de %f milisegundos" % (timer.get_time()))
        
    def _bulk_categories(self):
        categories = []
        print("Categories length: " + str(len(self.categories_mem)))
        for category in self.categories_mem:
            if category:
                new = [[Category.objects.get_or_create(name=cat.name)[0] for cat in category if cat]]
                if new:
                    categories += new
            else:
                categories.append(None)
        if not categories:
            categories = [None for _ in range(len(self.books_mem))]
        
        return categories
    
    def _bulk_collections(self):
        print("Collections length: " + str(len(self.collections_mem)))
        return [Collection.objects.get_or_create(name=collection.name)[0] if collection else None for collection in self.collections_mem]
    
    def _bulk_books(self):
        print("Books length: " + str(len(self.books_mem)))
        try:     
            books = Book.objects.bulk_create(self.books_mem)
        except Exception:
            books = [Book.objects.get_or_create(title=book.title, author=book.author, description=book.description, editorial=book.editorial, cover=book.cover, url=book.url)[0] for book in self.books_mem if book]
        
        return books
    
    def _update_books(self, books, categories, collections):
        for book, category, collection in zip(books, categories, collections):
            try:
                if book:
                    if collection:
                        book.collection = collection
                    
                    expr = category and category[0]
                    if expr:
                        book.categories.set(category)
                    
                    if collection or expr:
                        book.save()
            except Exception:
                print("----------------------ERROR-----------------------")
                print("Error with book: " + book)
                print("Error with category: " + category)
                print("Error with collection: " + collection)
    @staticmethod
    @abstractmethod
    def _get_paths(s, selenium=False):
        pass
                    
    def _recursive_scraper(self, url, s, driver=None, selenium=False, is_not_first=False):
        next_url = self._get_next_url(s, driver, selenium)
                
        if is_not_first and next_url:
            if not driver:
                next_url = self._parse_url(next_url)
                r = urllib.request.Request(next_url, headers=self.headers)
                f = urllib.request.urlopen(r)
                print("\n")
                print(next_url)
            else:
                print("DRIVER RECURSIVE")
                f, driver = next_url
            s = BeautifulSoup(f,"lxml")
            self._find_book(s)
            self._recursive_scraper(next_url, s, driver, selenium, True)
        else:
            if not driver:
                url = self._parse_url(url)
                r = urllib.request.Request(url, headers=self.headers)
                f = urllib.request.urlopen(r)
                print("\n")
                print(url)
            else:
                print("DRIVER RECURSIVE")
                f, _ = url
            s = BeautifulSoup(f,"lxml")
            self._find_book(s)
            if not is_not_first and next_url:
                self._recursive_scraper(url, s, driver, selenium, True)
            else:
                if driver:
                    driver.quit()

    def _find_book(self, s):
        books_grid = self._get_books_grid(s)
        threads = []
        for book in books_grid:
            new_url = self._get_book_url(book)
            if new_url not in self.visited:
                self._save_visited(new_url)
                t = threading.Thread(target=self._get_book, args=(new_url,))
                t.start()
                threads.append(t)
        
        for t in threads:
            t.join()
            
    def _save_visited(self, new_url):
        self.lock.acquire()
        try:
            self.visited.add(new_url)
        finally:
            self.lock.release()
    
    @staticmethod
    @abstractmethod
    def _get_next_url(s, driver=None, selenium=False):
        pass
    
    @staticmethod
    @abstractmethod
    def _get_books_grid(s):
        pass
    
    @staticmethod
    @abstractmethod
    def _get_book_url(book):
        pass
    
    def _get_book(self, new_url):
        try:
            new_url = self._parse_url(new_url)
            r = urllib.request.Request(new_url, headers=self.headers)
            f = urllib.request.urlopen(r)
            s = BeautifulSoup(f,"lxml")
            self._create_book(s, new_url)
            
        except Exception:
            print("Error: " + new_url)   

    def _create_book(self, s, url):
        title = self._get_title(s)
        if title:
            author = self._get_author(s)
            description = self._get_description(s)
            collection = self._get_collection(s)
            pages = self._get_pages(s)
            editorial = self._get_editorial(s)
            categories_list = self._get_categories(s)
            cover = self._get_cover(s)
            
            if cover:
                cover = self._parse_url(cover)

            if collection:
                collection = Collection(name=collection)
            
            categories = None
            if categories_list:
                categories = [Category(name=category) for category in categories_list]
            
            book = Book(title=title, author=author, description=description, pages=pages, editorial=editorial, cover=cover, url=url)
                
            if book:
                print(book)
                self._save_book(book, categories, collection)
                
    def _save_book(self, book, categories, collection):
        self.lock.acquire()
        try:
            self.books_mem.append(book)
            self.categories_mem.append(categories)
            self.collections_mem.append(collection)
        finally:
            self.lock.release()

    @staticmethod
    @abstractmethod
    def _get_title(s):
        pass

    @staticmethod
    @abstractmethod
    def _get_author(s):
        pass

    @staticmethod
    @abstractmethod
    def _get_description(s):
        pass

    @staticmethod
    @abstractmethod
    def _get_collection(s):
        pass

    @staticmethod
    @abstractmethod
    def _get_pages(s):
        pass

    @staticmethod
    @abstractmethod
    def _get_editorial(s):
        pass

    @staticmethod
    @abstractmethod
    def _get_categories(s):
        pass

    @staticmethod
    @abstractmethod
    def _get_cover(s):
        pass