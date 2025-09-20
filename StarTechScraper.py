import requests
from bs4 import BeautifulSoup

def get_price(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()  # Raise error if status code is not 200
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

    try:
        soup = BeautifulSoup(res.text, 'html.parser')
        product_name = soup.find("h1", {"class": "product-name"})
        price_tag = soup.find("span", {"class": "price"})   # Adjust selector if needed
        price_tag = price_tag.text.strip()
        product_name = product_name.text.strip() 
        data = {"product": product_name, "price": price_tag}
        return  data if data else "Error: Price tag not found"
    except Exception as e:
        return f"Error while parsing: {str(e)}"