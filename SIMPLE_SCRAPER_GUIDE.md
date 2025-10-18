# Simple HTML Scraper - Usage Guide

## Overview

This is a **simplified, general-purpose scraper** that:
1. Reads category URLs from `pages_url.json`
2. Extracts all product links from each category
3. Fetches raw HTML for each product page
4. Saves everything to `products_html.json` (overwrites each run)

**No complex parsing** - just raw HTML storage for later analysis.

---

## Quick Start

### 1. Create `pages_url.json`

Create a JSON file with your target category URLs:

```json
[
  "http://marketplace.onion/product-category/category1/",
  "http://marketplace.onion/product-category/category2/",
  "http://marketplace.onion/shop/category3/"
]
```

Example:
```bash
cp pages_url.json.example pages_url.json
# Edit pages_url.json with your target URLs
```

### 2. Start Tor

```bash
brew services start tor
# Wait 10 seconds
netstat -an | grep 9050  # Should show LISTEN
```

### 3. Run the Scraper

**Basic usage:**
```bash
python3 scrape_simple.py --socks --socks-port 9050 --manual
```

**What happens:**
1. Firefox opens through Tor
2. Waits 60 seconds for session establishment
3. Prompts you to solve CAPTCHA
4. Press Enter to continue
5. Scrapes all products from all categories
6. Saves to `products_html.json`

---

## Command-Line Options

### Required
- `--socks` - Use Tor SOCKS5 proxy (recommended)
- `--manual` - Enable manual CAPTCHA solving

### Optional
- `--socks-port PORT` - Tor SOCKS port (default: 9050)
- `--page-timeout SECONDS` - Browser timeout (default: 300)
- `--delay SECONDS` - Delay between requests (default: 2.0)
- `--max-products N` - Stop after N products
- `--tor-binary PATH` - Custom Firefox binary path

---

## Usage Examples

### Example 1: Basic Scraping
```bash
python3 scrape_simple.py --socks --socks-port 9050 --manual
```

### Example 2: Faster Scraping (shorter delay)
```bash
python3 scrape_simple.py --socks --socks-port 9050 --manual --delay 1
```

### Example 3: Test Run (limit to 10 products)
```bash
python3 scrape_simple.py --socks --socks-port 9050 --manual --max-products 10
```

### Example 4: With Tor Browser
```bash
python3 scrape_simple.py \
  --socks \
  --socks-port 9050 \
  --manual \
  --tor-binary "/Applications/Tor Browser.app/Contents/MacOS/firefox"
```

---

## Output Format

### `products_html.json` Structure

```json
[
  {
    "market": "marketplace.onion",
    "category_page": "http://marketplace.onion/product-category/drugs/",
    "product_url": "http://marketplace.onion/shop/product-name/",
    "fetched_at": 1729200000,
    "html": "<!DOCTYPE html><html>...entire page HTML...</html>"
  },
  {
    "market": "marketplace.onion",
    "category_page": "http://marketplace.onion/product-category/drugs/",
    "product_url": "http://marketplace.onion/shop/another-product/",
    "fetched_at": 1729200002,
    "html": "<!DOCTYPE html><html>...entire page HTML...</html>"
  }
]
```

**Fields:**
- `market` - Domain of the marketplace
- `category_page` - Category URL where product was found
- `product_url` - Direct URL to the product page
- `fetched_at` - Unix timestamp
- `html` - Complete raw HTML of the product page

---

## Processing the HTML Later

You can parse the saved HTML later with your own scripts:

### Example: Extract product titles
```python
import json
from bs4 import BeautifulSoup

with open('products_html.json', 'r') as f:
    products = json.load(f)

for product in products:
    soup = BeautifulSoup(product['html'], 'html.parser')
    
    # Try multiple selectors
    title = None
    for selector in ['h1.product_title', 'h1', '.product-title']:
        elem = soup.select_one(selector)
        if elem:
            title = elem.get_text(strip=True)
            break
    
    print(f"{product['product_url']}: {title}")
```

### Example: Count total products
```bash
cat products_html.json | python3 -m json.tool | grep -c '"product_url"'
```

### Example: Extract all URLs
```bash
cat products_html.json | python3 -c "import sys, json; data=json.load(sys.stdin); print('\n'.join(p['product_url'] for p in data))"
```

---

## How It Works

### Step 1: Load Category URLs
Reads all URLs from `pages_url.json`

### Step 2: Establish Session
Opens Firefox through Tor, waits for you to solve CAPTCHA, extracts cookies

### Step 3: Find Product Links
For each category URL:
- Fetches the category page HTML
- Looks for product links using multiple strategies:
  - WooCommerce selectors (`li.product a`)
  - Generic product patterns (`a[href*="/product/"]`)
  - URL heuristics (links containing `/shop/`, `/buy-`, etc.)
- Handles pagination (up to 10 pages per category)

### Step 4: Scrape Product Pages
For each product link:
- Fetches the full HTML
- Stores it with metadata
- Delays between requests (default: 2 seconds)

### Step 5: Save Results
Overwrites `products_html.json` with all scraped data

---

## Advantages of This Approach

✅ **General-purpose** - Works with ANY marketplace HTML structure
✅ **Simple** - No complex parsing logic to maintain
✅ **Flexible** - Parse HTML later however you want
✅ **Complete** - Stores entire HTML, nothing is lost
✅ **Portable** - JSON file can be analyzed anywhere
✅ **Debuggable** - Can re-parse HTML without re-scraping

---

## Tips & Best Practices

### 1. Start Small
Test with 1-2 category URLs first:
```bash
# In pages_url.json
["http://marketplace.onion/product-category/test/"]
```

### 2. Use Max Products for Testing
```bash
python3 scrape_simple.py --socks --socks-port 9050 --manual --max-products 5
```

### 3. Adjust Delay Based on Site
- Slow/overloaded sites: `--delay 5`
- Fast sites: `--delay 1`
- Default is safe: `--delay 2`

### 4. Monitor Progress
The scraper shows colored output:
- 🟢 Green: Success
- 🔵 Blue: Info
- 🟡 Yellow: Warning
- 🔴 Red: Error

### 5. Handle Interruptions
Press Ctrl+C to stop. The scraper will save all products collected so far.

### 6. Check File Size
```bash
ls -lh products_html.json
# Large HTML collection can be 10-100MB+
```

---

## Troubleshooting

### Issue: `pages_url.json not found`
**Solution:** Create the file with category URLs
```bash
echo '["http://marketplace.onion/category/"]' > pages_url.json
```

### Issue: No products found
**Solution:** 
- The scraper uses broad patterns to find product links
- Check the terminal output to see what links were found
- Verify your category URLs are correct

### Issue: Connection errors
**Solution:**
- Check Tor is running: `netstat -an | grep 9050`
- Restart Tor: `brew services restart tor`
- Increase timeout: `--page-timeout 600`

### Issue: Browser doesn't close
**Solution:** Kill it manually
```bash
pkill -f firefox
```

---

## Differences from Old Scraper

| Feature | Old Scraper | New Simple Scraper |
|---------|-------------|-------------------|
| Parsing | Extracts fields (title, price, etc.) | Just saves raw HTML |
| Flexibility | WooCommerce-specific | Works with any site |
| Output | `products.json` with parsed data | `products_html.json` with raw HTML |
| Complexity | ~1200 lines | ~400 lines |
| Processing | Done during scraping | Done later, separately |
| File mode | Appends to JSON | Overwrites each run |

---

## Example Workflow

### 1. Collect URLs
Create `pages_url.json` with target categories

### 2. Scrape HTML
```bash
python3 scrape_simple.py --socks --socks-port 9050 --manual
```

### 3. Parse HTML (your own script)
```python
import json
from bs4 import BeautifulSoup

with open('products_html.json', 'r') as f:
    products = json.load(f)

for product in products:
    soup = BeautifulSoup(product['html'], 'html.parser')
    
    # Your custom parsing logic here
    title = soup.select_one('h1')
    price = soup.select_one('.price')
    
    # Save to database, CSV, etc.
```

### 4. Analyze Data
Use pandas, SQLite, or any tool to analyze your parsed data

---

## Performance

- **Speed**: ~2-3 seconds per product (with default delay)
- **100 products**: ~5-10 minutes
- **1000 products**: ~1 hour

Adjust `--delay` to go faster/slower.

---

## Safety & Legal

⚠️ **Important:**
- Only scrape sites you have permission to scrape
- Respect robots.txt and terms of service
- Use appropriate delays to avoid overloading servers
- Be aware of legal implications in your jurisdiction

---

## Quick Reference

```bash
# Create input file
echo '["http://site.onion/category/"]' > pages_url.json

# Start Tor
brew services start tor

# Run scraper
python3 scrape_simple.py --socks --socks-port 9050 --manual

# View results
cat products_html.json | python3 -m json.tool | less

# Count products
cat products_html.json | python3 -m json.tool | grep -c '"product_url"'
```

---

Good luck! 🚀
