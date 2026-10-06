import requests
import re
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
html = requests.get('https://www.dinemoreonline.com', headers=headers, verify=False).text

urls = re.findall(r'href="([^"]+)"', html)
menu_urls = set([url for url in urls if 'dinemoreonline.com' in url])
print("Urls found on homepage:")
for url in list(menu_urls)[:20]:
    print(url)
