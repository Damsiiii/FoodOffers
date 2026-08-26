# Lanka Food Offer Ledger (🇱🇰)

Automated fast food discount tracker and offer aggregator for mainstream food chains in Sri Lanka including KFC, Pizza Hut, Domino's, Taco Bell, Burger King, Popeyes, Fuller Burgers, Crepe Runner, Subway, Dinemore, Perera & Sons, Chinese Dragon Cafe, Baskin-Robbins, and BreadTalk.

---

## ⚡ Hosting on Vercel Free Tier (Hobby Plan)

**Yes! You can host this project 100% free on Vercel's Free (Hobby) Tier.**

Because the site is built with **Astro** as a ultra-fast static website (`output: "static"`), Vercel can host it with zero runtime cost, free SSL certificates, and fast global CDN distribution.

### Option 1: Deploy via Vercel Git Integration (Recommended)

1. Push this repository to **GitHub**, **GitLab**, or **Bitbucket**.
2. Log in to [Vercel](https://vercel.com/) and click **Add New Project**.
3. Import your repository.
4. Vercel will automatically detect **Astro**:
   - **Framework Preset**: `Astro`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Click **Deploy**.

> **Automatic Offer Updates on Vercel:**
> Since GitHub Actions runs the Python scraper workflow periodically and commits updated `src/data/offers.json` back to your branch, Vercel will automatically trigger a clean zero-downtime rebuild whenever new offers are pushed!

### Option 2: Deploy via Vercel CLI

```bash
npm install -g vercel
vercel login
vercel
```

---

## 🛠️ Local Development

```bash
# Install dependencies
npm install

# Run Python scraper to fetch latest food offers
PYTHONPATH=. python3 scripts/update_offers.py

# Start local Astro development server
npm run dev
```

---

## 🧪 Testing & Verification

```bash
# Run backend scraper unit tests
PYTHONPATH=. pytest

# Build static production bundle
npm run build
```
