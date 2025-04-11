import scrapy
from scrapy import Spider, Request
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy_playwright.page import PageMethod
from typing import List, Dict
import json
import os
from scrapy.utils.log import configure_logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebScraper")

class BaseSpider(Spider):
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.PlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.PlaywrightDownloadHandler",
        },
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        },
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1
    }

class FlipkartSpider(BaseSpider):
    name = 'flipkart'
    
    def __init__(self, query=None, num_results=None, **kwargs):
        super().__init__(**kwargs)
        self.start_urls = [f"https://www.flipkart.com/search?q={query}"]
        self.num_results = int(num_results) if num_results else 5
        self.items = []

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_methods=[
                        PageMethod('wait_for_selector', 'div._1YokD2._3Mn1Gg'),
                    ]
                )
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        
        selectors = [
            {
                "product_container": "div._1sdMkc.LFEi7Z",
                "name": "a.WKTcLC.BwBZTg::text",
                "price": "div.Nx9bqj::text",
                "url": "a.rPDeLR::attr(href)",
                "img": "img._53J4C-::attr(src)"
            },
            {
                "product_container": "div.slAVV4",
                "name": "a.wjcEIp::text",
                "price": "div.Nx9bqj::text",
                "url": "a.VJA3rP::attr(href)",
                "img": "img.DByuf4::attr(src)"   
            },
            {
                "product_container": "div._75nlfW",
                "name": "div.KzDlHZ::text",
                "price": "div.Nx9bqj._4b5DiR::text",
                "url": "a.CGtC98::attr(href)",
                "img": "img.DByuf4::attr(src)"
            }
        ]

        count = 0
        for selector_set in selectors:
            if count >= self.num_results:
                break
                
            products = response.css(selector_set["product_container"])
            for product in products:
                if count >= self.num_results:
                    break
                    
                name = product.css(selector_set["name"]).get()
                price = product.css(selector_set["price"]).get()
                url = product.css(selector_set["url"]).get()
                img = product.css(selector_set["img"]).get()
                
                if all([name, price, url]):
                    item = {
                        "name": name.strip(),
                        "price": price.strip(),
                        "url": f"https://www.flipkart.com{url}",
                        "img": img or ""
                    }
                    self.items.append(item)
                    count += 1

        await page.close()

    def closed(self, reason):
        with open('items.json', 'w') as f:
            json.dump(self.items, f)

class AmazonSpider(BaseSpider):
    name = 'amazon'
    
    def __init__(self, query=None, num_results=None, **kwargs):
        super().__init__(**kwargs)
        self.start_urls = [f"https://www.amazon.in/s?k={query}"]
        self.num_results = int(num_results) if num_results else 5
        self.items = []

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_methods=[
                        PageMethod('wait_for_selector', 'div.s-main-slot'),
                    ]
                )
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        
        products = response.css("div.s-main-slot div.s-result-item")
        count = 0
        
        for product in products:
            if count >= self.num_results:
                break
                
            name = product.css("div.a-section.a-spacing-none.puis-padding-right-small.s-title-instructions-style > a > h2 > span::text").get()
            price = product.css("span.a-price span.a-offscreen::text").get()
            url = product.css("a.a-link-normal::attr(href)").get()
            img = product.css("img.s-image::attr(src)").get()
            
            if all([name, price, url]):
                item = {
                    "name": name.strip(),
                    "price": f"₹{price.strip()}",
                    "url": f"https://www.amazon.in{url}",
                    "img": img or ""
                }
                self.items.append(item)
                count += 1

        await page.close()

    def closed(self, reason):
        with open('items.json', 'w') as f:
            json.dump(self.items, f)

def run_spider(spider_class, query: str, num_results: int) -> List[Dict]:
    if os.path.exists('items.json'):
        os.remove('items.json')
        
    configure_logging()
    process = CrawlerProcess(get_project_settings())
    process.crawl(spider_class, query=query, num_results=num_results)
    process.start()
    
    with open('items.json', 'r') as f:
        return json.load(f)

class FlipkartScraper:
    @staticmethod
    def fetch_products(query: str, n: int) -> List[Dict]:
        return run_spider(FlipkartSpider, query, n)

    @staticmethod
    def fetch_reviews(url: str) -> List[str]:
        if os.path.exists('items.json'):
            os.remove('items.json')
            
        process = CrawlerProcess(get_project_settings())
        spider = FlipkartSpider(start_urls=[url])
        process.crawl(spider)
        process.start()
        
        with open('items.json', 'r') as f:
            return json.load(f)

class AmazonScraper:
    @staticmethod
    def fetch_products(query: str, n: int) -> List[Dict]:
        return run_spider(AmazonSpider, query, n)

    @staticmethod
    def fetch_reviews(url: str) -> List[str]:
        if os.path.exists('items.json'):
            os.remove('items.json')
            
        process = CrawlerProcess(get_project_settings())
        spider = AmazonSpider(start_urls=[url])
        process.crawl(spider)
        process.start()
        
        with open('items.json', 'r') as f:
            return json.load(f)