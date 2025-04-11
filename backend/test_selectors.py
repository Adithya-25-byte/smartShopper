import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_flipkart_selectors(query):
    url = f"https://www.flipkart.com/search?q={query}"
    
    # Multiple selector sets to test
    selector_sets = [
        {
            "product_container": "div._1sdMkc.LFEi7Z",
            "name": "a.WKTcLC.BwBZTg",
            "price": "div.Nx9bqj",
            "url": "a.rPDeLR",
            "img": "img._53J4C-"
        },
        {
            "product_container": "div.slAVV4",
            "name": "a.wjcEIp",
            "price": "div.Nx9bqj",
            "url": "a.VJA3rP",
            "img": "img.DByuf4"   
        },
        {
            "product_container": "div._75nlfW",
            "name": "div.KzDlHZ",
            "price": "div.Nx9bqj._4b5DiR",
            "url": "a.CGtC98",
            "img": "img.DByuf4"
        },
        # Add more potential selector sets here
    ]

    # Send request with headers to mimic browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        for selector_set in selector_sets:
            print(f"\nTesting Selector Set: {selector_set}")
            
            # Find containers
            containers = soup.select(selector_set['product_container'])
            print(f"Total Containers Found: {len(containers)}")

            # Test extraction for each container
            for i, container in enumerate(containers[:3], 1):
                print(f"\nContainer {i}:")
                
                try:
                    # Extract name
                    name_elem = container.select_one(selector_set['name'])
                    print(f"Name: {name_elem.get_text(strip=True) if name_elem else 'Not Found'}")
                    
                    # Extract price
                    price_elem = container.select_one(selector_set['price'])
                    print(f"Price: {price_elem.get_text(strip=True) if price_elem else 'Not Found'}")
                    
                    # Extract URL
                    url_elem = container.select_one(selector_set['url'])
                    print(f"URL: {url_elem.get('href') if url_elem else 'Not Found'}")
                    
                    # Extract Image
                    img_elem = container.select_one(selector_set['img'])
                    print(f"Image: {img_elem.get('src') if img_elem else 'Not Found'}")
                
                except Exception as e:
                    print(f"Error processing container: {e}")

    except Exception as e:
        logger.error(f"Request failed: {e}")

# Example usage
test_flipkart_selectors("smart+phone")