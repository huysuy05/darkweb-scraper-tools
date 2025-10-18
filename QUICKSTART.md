# Quick Start - Simplified Scraper

## What Changed

✅ **SIMPLIFIED** - Now `scrape.py` is much simpler:
- Just reads URLs from `pages_url.json`
- Scrapes raw HTML from all product pages
- Saves everything to `products_html.json` (overwrites each run)
- No complex parsing - just HTML collection
- Works with ANY marketplace

## How to Use

### 1. You already have `pages_url.json` ✅

Your file contains:
```json
[
  "http://drugj7dwjgdxyrqlciswny7ioa6wt2bbljifqspw2mg2cxv4n36ihcyd.onion/product-category/sex-aids/",
  "http://drugj7dwjgdxyrqlciswny7ioa6wt2bbljifqspw2mg2cxv4n36ihcyd.onion/product-category/buy-steroids/sexual-health/",
  "http://drugj7dwjgdxyrqlciswny7ioa6wt2bbljifqspw2mg2cxv4n36ihcyd.onion/product-category/buy-steroids/hormones-peptides/",
  "http://drugj7dwjgdxyrqlciswny7ioa6wt2bbljifqspw2mg2cxv4n36ihcyd.onion/product-category/buy-steroids/injectable-steroids/"
]
```

### 2. Run the Scraper

```bash
python scrape.py --socks --socks-port 9050 --manual
```

This will:
1. Open Firefox through Tor
2. Wait 60 seconds
3. Prompt you to solve CAPTCHA
4. Scrape all products from all 4 categories
5. Save to `products_html.json`

### 3. Optional Arguments

```bash
# Test with just 10 products
python scrape.py --socks --socks-port 9050 --manual --max-products 10

# Faster scraping (1 second delay)
python scrape.py --socks --socks-port 9050 --manual --delay 1

# Disable JavaScript
python scrape.py --socks --socks-port 9050 --manual --disable-js
```

## Output Format

`products_html.json` contains:
```json
[
  {
    "market": "drugj7dwjgdxyrqlciswny7ioa6wt2bbljifqspw2mg2cxv4n36ihcyd.onion",
    "category_page": "http://.../product-category/sex-aids/",
    "product_url": "http://.../shop/product-name/",
    "fetched_at": 1729200000,
    "html": "<!DOCTYPE html>...full HTML here..."
  },
  ...
]
```

## View Results

```bash
# Count products
cat products_html.json | python3 -m json.tool | grep -c '"product_url"'

# View first product
cat products_html.json | python3 -m json.tool | head -50

# Extract all product URLs
cat products_html.json | python3 -c "import sys, json; [print(p['product_url']) for p in json.load(sys.stdin)]"
```

## What Was Removed

❌ Removed complex parsing logic  
❌ Removed `products.json` output  
❌ Removed field extraction (title, price, description, etc.)  
❌ Removed `--category-endpoints` (use `pages_url.json` instead)  
❌ Removed checkpoint system  

## Old Scraper Backed Up

Your old scraper is saved as: `scrape_old.py`

If you need it back:
```bash
mv scrape_old.py scrape.py
```

## Benefits

✅ **Simpler**: ~400 lines instead of 1200  
✅ **General**: Works with any marketplace  
✅ **Flexible**: Parse HTML later however you want  
✅ **Complete**: Stores full HTML, nothing lost  
✅ **Clean**: Overwrites file each run (no duplicates)  

## Ready to Test!

```bash
python scrape.py --socks --socks-port 9050 --manual --max-products 5
```
