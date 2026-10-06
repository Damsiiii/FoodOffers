import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # We need the direct store URL, e.g. for Mount Lavinia
        url = "https://www.ubereats.com/lk/store/subway-mount-lavinia/7k1Kqi0CwlCcmPGTacBjJZ2JpoOVcswUheLrBix6DJtiB3vkKInsCr1KUFbC9E-EdMtIXoWR9-XSsR62m5DDVice9sNt1Db-C8U-RqvBst_5W6LIs15hP77OhcPFCNZqx9jg0JIIXWh2WvrY78glUem-vm9KnXdHFqko_S5j4w=="
        # Alternatively, we can use a generic search URL or a known valid one
        url = "https://www.ubereats.com/lk/brand/subway"
        
        print(f"Navigating to {url}...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Look for deals or items
            items = await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                return links.map(a => a.href).filter(h => h.includes('/store/'));
            }''')
            print("Store Links found:", set(items))
            
            # Wait for network idle to see if we load store data
            await page.wait_for_timeout(3000)
            
            html = await page.content()
            print("HTML Length:", len(html))
            
            if "Cloudflare" in html or "captcha" in html.lower():
                print("Blocked by Cloudflare/Captcha!")
                
        except Exception as e:
            print("Error:", e)
            
        await browser.close()

asyncio.run(main())
