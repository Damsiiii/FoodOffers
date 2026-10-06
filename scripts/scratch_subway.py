import requests
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_subway():
    try:
        r = requests.get('https://subway.lk', verify=False, timeout=10)
        print("Final URL:", r.url)
        html = r.text
        
        # Save HTML for inspection
        with open('subway_dump.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("HTML dumped to subway_dump.html")
        
        # Look for images and endpoints
        apis = re.findall(r'https://[^"\']*?api[^"\']*', html)
        print("API endpoints found in HTML:", list(set(apis)))
        
        images = re.findall(r'https?://[^\s"\'<>]+(?:jpg|png|jpeg)', html)
        print("First 10 images:", images[:10])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    get_subway()
