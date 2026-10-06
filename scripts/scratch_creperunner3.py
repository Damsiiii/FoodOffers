import requests
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
html = requests.get('https://creperunner.lk/menu/', headers=headers, verify=False).text
with open('crepe_menu.html', 'w', encoding='utf-8') as f:
    f.write(html)
