import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
html = requests.get('https://creperunner.lk/menu/', headers=headers, verify=False).text
soup = BeautifulSoup(html, 'html.parser')

items = soup.select('.elementor-widget-image-box, .product, .foodmenu, .elementor-image-box-wrapper')
if not items:
    # Maybe simple images with descriptions
    items = soup.select('.elementor-text-editor')
    
for item in items[:5]:
    print("-----")
    print(item.get_text(strip=True)[:100])
    img = item.find('img')
    if img:
        print("IMG:", img.get('src'))
