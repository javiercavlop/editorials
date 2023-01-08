from .Scraper import Scraper

class SMScraper(Scraper):
    def __init__(self, base_url):
        Scraper.__init__(self, base_url)
    
    @staticmethod
    def _get_paths(s, selenium=False):
        return ["https://es.literaturasm.com/libros"]
    
    @staticmethod
    def _get_next_url(s, driver=None, selenium=False):
        first_part = s.find('li', class_='next')
        next_url = None
        if first_part:
            second_part = first_part.find('a')
            if second_part:
                next_url = second_part.get('href')
                
        return next_url

    @staticmethod
    def _get_books_grid(s):
        return set(s.find('ul', class_="search-results").find_all('a', class_="miniatura__enlace"))
    
    @staticmethod
    def _get_book_url(book):
        return book.get('href')

    @staticmethod
    def _get_title(s):
        title = s.find('h1', class_='page-header__titulo')
        if title:
            return title.get_text().strip()
        return None

    def _get_author(self, s):
        author = self._get_element(s, 'Autor:')
        if not author:
            author = "Desconocido"
        return author

    @staticmethod
    def _get_description(s):
        text = ""
        sinopsis = s.find('div', class_='sinopsis margen-pequeno')
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

    def _get_collection(self, s):
        return self._get_element(s, ' Colección: ')

    def _get_pages(self, s):
        pages = self._get_element(s, 'Número de páginas:')
                
        try:
            pages = int(pages)
        except Exception:
            pages = None
                
        return pages

    @staticmethod
    def _get_editorial(s):
        return "SM Ediciones"
    
    def _get_categories(self, s):
        categories = []
        g = self._get_element(s, ' Género: ')
        if g:
            categories.append(g)
        t = self._get_element(s, ' Tipo libro: ')
        if t:
            categories.append(t)
        
        if not categories:
            categories = None
        
        return categories

    @staticmethod
    def _get_cover(s):
        image_div = s.find('section', class_='visor-imagen')
        if image_div:    
            image = image_div.find('img')
            if image:
                return image.get('src')
        return None
    
    @staticmethod
    def _get_element(s, element):
        div = s.find('div', class_='js-collapsible-list-wrapper')
        if div:
            dl_element = s.find_all('dl', class_='dl dl--creditos')
            if dl_element:
                for d in dl_element:
                    dt_element = d.find('dt', class_='dl--creditos__titulo', text=element)
                    if dt_element:
                        dd_element = dt_element.find_next_sibling('dd', class_='dl--creditos__definicion')
                        if dd_element:
                            return dd_element.get_text().strip()
        return None