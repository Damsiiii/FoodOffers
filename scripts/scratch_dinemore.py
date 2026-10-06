import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
html = requests.get('https://www.dinemoreonline.com', headers=headers, verify=False).text
soup = BeautifulSoup(html, 'html.parser')

products = soup.find_all('li', class_=lambda c: c and 'product' in c)
if not products:
    products = soup.find_all('div', class_=lambda c: c and 'product' in c)
    
print(f"Found {len(products)} products on homepage")
if products:
    for p in products[:3]:
        title_el = p.find(['h2', 'h3'])
        title = title_el.get_text(strip=True) if title_el else 'No title'
        price_el = p.find(class_='price')
        price = price_el.get_text(strip=True) if price_el else 'No price'
        img_el = p.find('img')
        img = img_el.get('src') if img_el else 'No image'
        print(f"{title} - {price} - {img}")

# Look for categories/menu URLs
menus = soup.find_all('a', href=True)
category_links = set([a['href'] for a in menus if 'product-category' in a['href']])
print("\nCategory Links:")
for link in list(category_links)[:5]:
    print(link)
