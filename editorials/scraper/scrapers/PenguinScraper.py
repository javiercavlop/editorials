from .Scraper import Scraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

class PenguinScraper(Scraper):
    def __init__(self, base_url):
        Scraper.__init__(self, base_url)
    
    def _get_paths(self, s, selenium=False):
        if not selenium:
            return ["https://www.penguinlibros.com/es/module/elastico/elasticosearch?fc=module&module=elastico&controller=elasticosearch&s="]
        else:
            paths = [a.get('href') for ul in s.find_all('ul', class_='cbp-links cbp-category-tree') for a in ul.find_all('a')]
            
            driver_options = webdriver.ChromeOptions()
            driver_options.headless = True
            driver_options.add_argument("--start-maximized")
            driver_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
            driver = webdriver.Chrome(options=driver_options)
            result = []
            
            for p in paths:
                self._get_paths_aux(p, result, driver)
                
            return result
    
    def _get_paths_aux(self, p, result, driver=None):
        self.lock.acquire()
        driver.get(p)
        try:
            try:
                WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(by=By.CSS_SELECTOR, value="#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")).click()
            except Exception:
                pass
            try:
                btn = WebDriverWait(driver, timeout=30).until(lambda d: d.find_element(by=By.CLASS_NAME, value="btn-traditional"))
                if btn:
                    btn.submit()
            finally:
                result.append((driver.page_source, driver))
                print("NEW DRIVER ADDED")
        finally:
            self.lock.release()
    
    @staticmethod
    def _get_next_url(s, driver=None, selenium=False):
        next_url = None
        if selenium:
            try:
                btn = WebDriverWait(driver, timeout=30).until(lambda d: d.find_element(by=By.ID, value="infinity-url"))
                if btn:
                    btn.click
            except Exception:
                return None
            finally:
                f = driver.page_source

            next_url = (f, driver)
        else:
            first_part = s.find('a', id='infinity-url')
            if first_part:
                next_url = first_part.get('href')
                
        return next_url

    @staticmethod
    def _get_books_grid(s):
        return s.find('div', id='products-row').find_all('a', class_="thumbnail product-thumbnail")
    
    @staticmethod
    def _get_book_url(book):
        return book.get('href')

    @staticmethod
    def _get_title(s):
        title_div = s.find('div', class_='product_header_container clearfix')
        if title_div:
            title = title_div.find('h1')
            if title:
                return title.get_text().strip()
        return None

    def _get_author(self, s):
        author = self._get_element(s, 'Autor')
        if not author:
            author = "Anónimo"
        return author

    @staticmethod
    def _get_description(s):
        text = ""
        sinopsis = s.find('div', class_='p_leer_menos')
        if not sinopsis:
            sinopsis = s.find('div', class_='rte-content')
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
        return self._get_element(s, 'Colección')

    def _get_pages(self, s):
        pages = self._get_element(s, 'Páginas')
                
        try:
            pages = int(pages)
        except Exception:
            pages = None
                
        return pages

    def _get_editorial(self, s):
        editorial = self._get_element(s, 'Editorial')
        if not editorial:
            editorial = "Penguin Libros"
        return editorial
    
    @staticmethod
    def _get_categories(s):
        categories_div = s.find_all('a', class_='tag_lvl2')
        subcategories_div = s.find_all('a', class_='tag_lvl3')
        categories = []
        if categories_div:
            categories += [category.get_text().strip() for category in categories_div]
        
        if subcategories_div:
            categories += [subcategory.get_text().strip() for subcategory in subcategories_div]
        
        if categories:
            return categories
        
        return None

    @staticmethod
    def _get_cover(s):
        image_div = s.find('div', class_='easyzoom easyzoom-product')
        if image_div:    
            image = image_div.find('a')
            if image:
                return image.get('href')
        return None
    
    @staticmethod
    def _get_element(s, element):
        dl_element = s.find('dl', class_='caracteristicas-prod data-sheet')
        if dl_element:
            dt_element = dl_element.find('dt', class_='name', text=element)
            if dt_element:
                dd_element = dt_element.find_next_sibling('dd', class_='value')
                if dd_element:
                    return dd_element.get_text().strip()
        return None