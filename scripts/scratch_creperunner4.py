import re
from bs4 import BeautifulSoup

html = open('crepe_menu.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')

print("Images inside specific containers:")
for img in soup.find_all('img'):
    src = img.get('src', '')
    if 'uploads' in src:
        # Get parent text
        parent = img.parent.parent
        text = parent.get_text(strip=True)[:100]
        if text:
            print("IMG:", src)
            print("TXT:", text)
            print("---")
