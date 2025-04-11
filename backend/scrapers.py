import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import asyncio
from urllib.parse import quote, urlparse, parse_qs, urlencode
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import queue
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebScraper")

class WebDriverPool:
    def __init__(self, pool_size=3):
        self.pool = queue.Queue()
        self.pool_size = pool_size
        self.lock = threading.Lock()
        self._initialize_pool()

    def _initialize_pool(self):
        for _ in range(self.pool_size):
            driver = self._create_driver()
            self.pool.put(driver)

    def _create_driver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")
        options.add_argument("--start-maximized")
        options.add_argument("--enable-unsafe-swiftshader")
        options.add_argument("--disable-webgl")  # Disable WebGL
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        return driver

    def get_driver(self):
        return self.pool.get()

    def return_driver(self, driver):
        self.pool.put(driver)

    def close_all(self):
        while not self.pool.empty():
            driver = self.pool.get()
            driver.quit()

class OptimizedScraper:
    def __init__(self, pool_size=3):
        self.driver_pool = WebDriverPool(pool_size)
        self.executor = ThreadPoolExecutor(max_workers=pool_size)

    def _fetch_with_retry(self, url, max_retries=3, wait_time=3):
        driver = self.driver_pool.get_driver()
        try:
            for attempt in range(max_retries):
                try:
                    driver.get(url)
                    WebDriverWait(driver, wait_time).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    page_source = driver.page_source
                    return page_source
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to fetch {url} after {max_retries} attempts: {e}")
                        raise
                    time.sleep(1)
        finally:
            self.driver_pool.return_driver(driver)

    def parallel_fetch(self, urls):
        fetch_partial = partial(self._fetch_with_retry)
        results = list(self.executor.map(fetch_partial, urls))
        return results

    def close(self):
        self.executor.shutdown()
        self.driver_pool.close_all()

class FlipkartScraper:
    _scraper = OptimizedScraper(pool_size=3)
    
    @staticmethod
    def build_url(query, sort_by="relevance", page=1):
        base_url = f"https://www.flipkart.com/search?q={query}"
        
        if sort_by == "popularity":
            base_url += "&sort=popularity"
        elif sort_by == "price_low_to_high":
            base_url += "&sort=price_asc"
        elif sort_by == "price_high_to_low":
            base_url += "&sort=price_desc"
        elif sort_by == "newest":
            base_url += "&sort=recency_desc"
            
        if page > 1:
            base_url += f"&page={page}"
            
        print(f"Built URL for page {page}: {base_url}")
        return base_url
    
    @staticmethod
    def fetch_products(query, sort_by="relevance", page=1, batch_size=10):
        url = FlipkartScraper.build_url(query, sort_by, page)
        page_source = FlipkartScraper._scraper._fetch_with_retry(url)
        soup = BeautifulSoup(page_source, 'html.parser')
        print(batch_size)
        selector_sets = [
            {
                "product_container": "div._1sdMkc.LFEi7Z",
                "name": "a.WKTcLC.BwBZTg",
                "price": "div.Nx9bqj",
                "url": "a.rPDeLR",
                "img": "img._53J4C-",
                "discount": "div.UkUFwK span"
            },
            {
                "product_container": "div.slAVV4",
                "name": "a.wjcEIp",
                "price": "div.Nx9bqj",
                "url": "a.VJA3rP",
                "img": "img.DByuf4",
                "discount": "div.UkUFwK span"
            },
            {
                "product_container": "div._75nlfW",
                "name": "div.KzDlHZ",
                "price": "div.Nx9bqj._4b5DiR",
                "url": "a.CGtC98",
                "img": "img.DByuf4",
                "discount": "div.UkUFwK span"
            }
        ]

        results = []
        for selectors in selector_sets:
            products = soup.select(selectors["product_container"])
            print(len(products))
            if len(products)> batch_size:
                batch_size = len(products)
            for product in products:
                if len(results) >= batch_size:
                    break

                name_elem = product.select_one(selectors["name"])
                price_elem = product.select_one(selectors["price"])
                url_elem = product.select_one(selectors["url"])
                img_elem = product.select_one(selectors["img"])
                discount_elem = product.select_one(selectors["discount"])

                if not all([name_elem, price_elem, url_elem, img_elem]):
                    continue

                results.append({
                    "name": name_elem.get_text(strip=True),
                    "price": price_elem.get_text(strip=True),
                    "url": f"https://www.flipkart.com{url_elem.get('href', '')}",
                    "img": img_elem.get("src", ""),
                    "discount": discount_elem.get_text(strip=True) if discount_elem else "0% off",
                    "platform": "flipkart"
                })
        print(len(results))
        return results[:batch_size]

    @staticmethod
    def fetch_reviews(url):
        page_source = FlipkartScraper._scraper._fetch_with_retry(url)
        soup = BeautifulSoup(page_source, 'html.parser')
        reviews = soup.select("div.RcXBOT")
        return [review.get_text(strip=True) for review in reviews[:5]]

class AmazonScraper:
    _scraper = OptimizedScraper(pool_size=3)
    
    @staticmethod
    def build_url(query, sort_by="relevance", page=1):
        base_url = f"https://www.amazon.in/s?k={query}"
        
        if sort_by == "popularity":
            base_url += "&s=exact-aware-popularity-rank"
        elif sort_by == "price_low_to_high":
            base_url += "&s=price-asc-rank"
        elif sort_by == "price_high_to_low":
            base_url += "&s=price-desc-rank"
        elif sort_by == "newest":
            base_url += "&s=date-desc-rank"
            
        if page > 1:
            # Amazon uses page parameter in a different way
            parsed_url = urlparse(base_url)
            query_params = parse_qs(parsed_url.query)
            query_params['page'] = page
            updated_query = urlencode(query_params, doseq=True)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{updated_query}"
            
        print(f"Updated URL for page {page}: {base_url}")    
        return base_url

    @staticmethod
    def fetch_products(query, sort_by="relevance", page=1, batch_size=10):
        url = AmazonScraper.build_url(query, sort_by, page)
        page_source = AmazonScraper._scraper._fetch_with_retry(url)
        soup = BeautifulSoup(page_source, 'html.parser')
        print(batch_size)
        results = []
        products = soup.select("div.a-section.a-spacing-base")
        print(len(products))
        for product in products:
            if len(results) >= batch_size:
                break

            name_elem = product.select_one("h2.a-text-normal span")
            price_elem = product.select_one("span.a-price span.a-offscreen")
            url_elem = product.select_one("a.a-link-normal")
            img_elem = product.select_one("img.s-image")
            
            
            # Get discount information - look for the third span without class in .a-row
            discount_elem = None
            discount_row = product.select_one("div.a-row")
            if discount_row:
                spans = discount_row.select("span")
                discount_spans = [span for span in spans if not span.has_attr('class')]
                if len(discount_spans) >= 1:
                    discount_elem = discount_spans[0]

            if not all([name_elem, price_elem, url_elem, img_elem]):
                continue

            results.append({
                "name": name_elem.get_text(strip=True),
                "price": price_elem.get_text(strip=True),
                "url": f"https://www.amazon.in{url_elem.get('href', '')}",
                "img": img_elem.get("src", ""),
                "discount": discount_elem.get_text(strip=True) if discount_elem else "0% off",
                "platform": "amazon"
            })
        print(len(results))
        return results[:batch_size]

    @staticmethod
    def fetch_reviews(url):
        page_source = AmazonScraper._scraper._fetch_with_retry(url)
        soup = BeautifulSoup(page_source, 'html.parser')
        
        review_selectors = [
            "div.review-text-content span",
            "span.review-text",
            "div.a-expander-content.reviewText",
            "span.-a-size-base.review-text"
        ]
        
        for selector in review_selectors:
            reviews = soup.select(selector)
            if reviews:
                return [review.get_text(strip=True) for review in reviews[:5]]
        
        return []