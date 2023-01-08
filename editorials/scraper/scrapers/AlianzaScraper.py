from .Scraper import Scraper

class AlianzaScraper(Scraper):
    def __init__(self, base_url):
        Scraper.__init__(self, base_url)
    
    @staticmethod
    def _get_paths(s, selenium=False):
        # Esta url funciona pero si se trabaja con hilos y recursividad rinde peor. 
        # En el caso de que no se quiera hacer uso de los hilos se puede descomentar la línea.
        # return ["https://www.alianzaeditorial.es/buscador/"] 
        return [a.get('href') for a in s.find_all('a', class_='books-wrapper-item tiny-text')]
    
    @staticmethod
    def _get_next_url(s, driver=None, selenium=False):
        first_part = s.find('section', class_='pagination')
        next_url = None
        if first_part:
            second_part = first_part.find('ul')
            if second_part:
                third_part = second_part.find_all('li')[-1]
                if third_part:
                    fourth_part = third_part.find('a')
                    if fourth_part and third_part.get_text().strip() == "chevron-right":
                        next_url = fourth_part.get('href')
                
        return next_url

    @staticmethod
    def _get_books_grid(s):
        result = []
        for grid in s.find_all('div', class_='books-list-container'):
            result += grid.find_all('a')
        return result
    
    @staticmethod
    def _get_book_url(book):
        return book.get('href')

    @staticmethod
    def _get_title(s):
        title = s.find('h1', class_='alpha')
        if title:
            return title.get_text().strip()
        return None

    @staticmethod
    def _get_author(s):
        author_div = s.find('p', class_='author')
        text = "Anónimo"
        if author_div:
            authors = author_div.find_all('a')
            if authors:
                text = authors[0].get_text().strip()
        return text

    @staticmethod
    def _get_description(s):
        text = ""
        sinopsis = s.find('div', class_='description')
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
        collections = s.find_all('li', class_='data-item')
        if collections:
            for c in collections:
                collection = c.find('p', class_="label", text='Colección')
                if collection:
                    sibling = collection.find_next_sibling('p', class_="value")
                    if sibling:
                        return sibling.get_text().strip()
        return None

    @staticmethod
    def _get_pages(s):
        pages_div = s.find_all('li', class_='data-item')
        pages = None
        if pages_div:
            for p in pages_div:
                page = p.find('p', class_="label", text='Páginas ')
                if page:
                    page_sibling = page.find_next_sibling('p', class_="value")
                    if page_sibling:
                        pages = page_sibling.get_text().strip()
                    
                        try:
                            pages = int(pages)
                        except Exception:
                            pages = None
                
        return pages

    @staticmethod
    def _get_editorial(s):
        return "Alianza Editorial"
    
    @staticmethod
    def _get_categories(s):
        return None

    @staticmethod
    def _get_cover(s):
        image = s.find('img', class_='book-cover-image')
        if image:    
            return image.get('src')
        return None