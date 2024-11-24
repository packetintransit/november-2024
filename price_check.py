import requests
from bs4 import BeautifulSoup
import unicodedata
from send_email import send_email

# Constants
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US, en;q=0.5',
}

def fetch_page_content(url):
    """
    Fetches the content of the page for the given URL.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def parse_product_info(page_content):
    """
    Parses product information (title, price, availability) from the page content.
    """
    soup = BeautifulSoup(page_content, features="lxml")

    # Extract product title
    try:
        title = soup.find(id='productTitle').get_text().strip()
    except AttributeError:
        print("Error extracting product title.")
        title = None

    # Extract product price
    try:
        price_str = soup.find(id='priceblock_ourprice').get_text()
        price = float(
            unicodedata.normalize("NFKD", price_str)
            .replace(',', '.')
            .replace('$', '')
        )
    except (AttributeError, ValueError):
        print("Error extracting or parsing product price.")
        price = None

    # Extract availability status
    try:
        # Check for availability text
        availability = soup.select_one('#availability .a-color-success')
        available = availability is not None and "in stock" in availability.get_text().lower()
    except AttributeError:
        available = False

    return title, price, available

def get_product_info(url):
    """
    Combines fetching page content and parsing product information.
    """
    page_content = fetch_page_content(url)
    if page_content is None:
        return None, None, None
    return parse_product_info(page_content)

def filter_products(products):
    """
    Filters products below the price limit and available.
    """
    products_below_limit = []
    for product_url, price_limit in products:
        title, price, available = get_product_info(product_url)
        if title and price and price < price_limit and available:
            products_below_limit.append((product_url, title, price))
    return products_below_limit

def compose_email_message(products_below_limit):
    """
    Composes an email message for products below the price limit.
    """
    message = "Subject: Price Alert - Product Below Limit!\n\n"
    message += "The following products are below your price limit:\n\n"
    for url, title, price in products_below_limit:
        message += f"{title}\n"
        message += f"Price: ${price:.2f}\n"
        message += f"Link: {url}\n\n"
    return message

def main():
    # Example tracked products: (URL, price_limit)
    tracked_products = [
        (
            "https://www.amazon.com/Samsung-Factory-Unlocked-Smartphone-Pro-Grade/dp/B08FYTSXGQ/ref=sr_1_1_sspa?dchild=1&keywords=samsung%2Bs20&qid=1602529762&sr=8-1-spons&psc=1&spLa=ZW5jcnlwdGVkUXVhbGlmaWVyPUExOTdFSllWVkhNMFRFJmVuY3J5cHRlZElkPUEwNDAyODczMktKMDdSVkVHSlA2WCZlbmNyeXB0ZWRBZElkPUEwOTc5NTcxM1ZXRlJBU1k1U0ZUSyZ3aWRnZXROYW1lPXNwX2F0ZiZhY3Rpb249Y2xpY2tSZWRpcmVjdCZkb05vdExvZ0NsaWNrPXRydWU=",
            700,
        ),
    ]

    # Check for products below price limit
    products_below_limit = filter_products(tracked_products)

    # If any products match the criteria, send an email alert
    if products_below_limit:
        email_message = compose_email_message(products_below_limit)
        send_email(email_message)
        print("Email sent successfully.")
    else:
        print("No products below the price limit.")

if __name__ == "__main__":
    main()