from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os

# Configure Selenium WebDriver
def setup_driver():
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--enable-unsafe-swiftshader")
    options.add_argument("--disable-webgl")  # Disable WebGL
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    return driver

# Function to log in to Amazon
def login_to_amazon(driver, email, password):
    login_url = "https://www.amazon.in/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.in%2F%3Fref_%3Dnav_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=inflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"
    driver.get(login_url)
    
    # Wait for the email field to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ap_email"))
    )
    
    # Enter email
    email_field = driver.find_element(By.ID, "ap_email")
    email_field.send_keys(email)
    
    # Click continue
    continue_button = driver.find_element(By.ID, "continue")
    continue_button.click()
    
    # Wait for the password field to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ap_password"))
    )
    
    # Enter password
    password_field = driver.find_element(By.ID, "ap_password")
    password_field.send_keys(password)
    
    # Click sign-in
    sign_in_button = driver.find_element(By.ID, "signInSubmit")
    sign_in_button.click()
    
    # Wait for login to complete
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "nav-tools"))  # Check for a logged-in element
    )
    print("Logged in successfully!")

def fetch_amazon_products(driver, query, num_results=5):
    url = f"https://www.amazon.in/s?k={query}"
    print(url)
    driver.get(url)
    
    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
    
    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    results = []
    products = soup.select("div.a-section")
   
    
    for product in products:
        if len(results) >= num_results:
            break
        
        name_elem = product.select_one("h2.a-text-normal span")
        price_elem = product.select_one("span.a-price span.a-offscreen")
        url_elem = product.select_one("a.a-link-normal")
        img_elem = product.select_one("img.s-image")
        
        if not all([name_elem, price_elem, url_elem, img_elem]):
            continue
        
        product_url = url_elem.get('href', '')
        
        results.append({
            "name": name_elem.get_text(strip=True),
            "price": price_elem.get_text(strip=True),
            "url": product_url,
            "img": img_elem.get("src", "")
        })
    
    return results

# Fetch customer reviews for a product
def fetch_amazon_reviews(driver, product_url):
    # Prepend the base URL if the product URL is relative
    reviews = []
    if not product_url.startswith("http"):
        product_url = "https://www.amazon.in" + product_url
    
    driver.get(product_url)
    
    # Wait for the page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')         
    
    # Extract the "All Reviews" URL
    all_reviews_url_elem = soup.select_one("a[data-hook='see-all-reviews-link-foot']")
    if not all_reviews_url_elem:
        return reviews
    
    all_reviews_url = f"https://www.amazon.in{all_reviews_url_elem.get('href', '')}"
    
    page_num = 1
    while True:
        review_url = f"{all_reviews_url}&pageNumber={page_num}"
        print(review_url)
        driver.get(review_url)
        time.sleep(5)  # Wait for the page to load
        
        # Take a screenshot and save the HTML content for the reviews page
        review_screenshot_path = os.path.join(os.getcwd(), f"reviews_page_{page_num}.png")
        driver.save_screenshot(review_screenshot_path)
        print(f"Screenshot saved to {review_screenshot_path}")
        
        review_html_path = os.path.join(os.getcwd(), f"reviews_page_{page_num}.html")
        with open(review_html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"HTML content saved to {review_html_path}")
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        review_elements = soup.find_all("div", class_="a-row.a-spacing-small.review-data")
        print(len(review_elements))
        print(review_elements[:1])
        
        if not review_elements:
            break
        
        for review in review_elements:
            review_text_elem = review.select_one("span[data-hook='review-body']")
            print(review_text_elem)
            if review_text_elem:
                review_text = review_text_elem.get_text(strip=True)
                print(review_text)
                reviews.append(review_text)
        
        page_num += 1
    
    print(f"Total reviews fetched: {len(reviews)}")
    return reviews

# Main function to test Amazon selectors
def main():
    query = "oppo+phone"  # Replace with your desired search query
    num_results = 1  # Number of products to fetch
    
    # Your Amazon credentials
    amazon_email = "aak44933@gmail.com"  # Replace with your Amazon email
    amazon_password = "qwerty12345"  # Replace with your Amazon password
    
    driver = setup_driver()
    
    try:
        # Log in to Amazon
        login_to_amazon(driver, amazon_email, amazon_password)
        
        # Fetch product information
        products = fetch_amazon_products(driver, query, num_results)
        print("Fetched Products:")
        for i, product in enumerate(products, 1):
            print(f"{i}. {product['name']}")
            print(f"   Price: {product['price']}")
            print(f"   URL: {product['url']}")
            print(f"   Image: {product['img']}")
            print()
        
        # Fetch reviews for the first product
        if products:
            first_product_url = products[0]['url']
            print(f"Fetching reviews for: {products[0]['name']}")
            reviews = fetch_amazon_reviews(driver, first_product_url)
            print("Customer Reviews:")
            for i, review in enumerate(reviews, 1):
                print(f"{i}. {review}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()