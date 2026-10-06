import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

html = requests.get('https://creperunner.lk', verify=False, timeout=10).text

urls = re.findall(r'href="(https://creperunner\.lk/[^"]+)"', html)
for url in set(urls):
    if any(x in url.lower() for x in ['menu', 'product', 'shop', 'category']):
        print(url)
