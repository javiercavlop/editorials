from .Scraper import Scraper

class PlanetaScraper(Scraper):
    def __init__(self, base_url):
        Scraper.__init__(self, base_url)
    
    @staticmethod
    def _get_paths(s, selenium=False):
        paths = s.select('div.tematiques > a')
        return [a.get('href') for a in paths]
    
    @staticmethod
    def _get_next_url(s, driver=None, selenium=False):
        first_part = s.find('div', class_='paginacio-seguent')
        next_url = None
        if first_part:
            second_part = first_part.find('a')
            if second_part:
                next_url = second_part.get('href')
                
        return next_url

    @staticmethod
    def _get_books_grid(s):
        return s.find_all('ul', class_='llibres-miniatures llibres-graella')[-1].find_all('a')
    
    @staticmethod
    def _get_book_url(book):
        return book.get('href')

    @staticmethod
    def _get_title(s):
        title_div = s.find('div', class_='fitxa-bloc-b1')
        if title_div:
            title = title_div.find('h1')
            if title:
                return title.get_text().strip()
        return None

    @staticmethod
    def _get_author(s):
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

    @staticmethod
    def _get_description(s):
        text = ""
        sinopsis = s.find('div', class_='sinopsi')
        if sinopsis:
            descriptions = sinopsis.find_all('p')
            if descriptions:
                for p in descriptions:
                    if p == descriptions[-1]:
                        text += p.get_text().strip()
                    else:
                        text += p.get_text().strip() + "\n"
                return text if text.endswith(".") else text + "."
        return None

    @staticmethod
    def _get_collection(s):
        collections = s.find('div', class_='coleccions')
        if collections:    
            collection = collections.find('a')
            if collection:
                return collection.get_text().strip()
        return None

    @staticmethod
    def _get_pages(s):
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
            except Exception:
                pages = None
                
        return pages

    @staticmethod
    def _get_editorial(s):
        editorial_div = s.find('div', class_='segell-nom')
        if editorial_div:
            editorial = editorial_div.find('a')
            if editorial:
                return editorial.get_text().strip()
        return "Planeta de Libros"
    
    @staticmethod
    def _get_categories(s):
        categories_div = s.find('div', class_='tematiques')
        if categories_div:
            categories = categories_div.find_all('a')
            if categories:
                return [category.get_text().strip() for category in categories]
        return None

    @staticmethod
    def _get_cover(s):
        image_div = s.find('div', class_='foto')
        if image_div:    
            image = image_div.find('img')
            if image:
                return image.get('data-src')
        return None