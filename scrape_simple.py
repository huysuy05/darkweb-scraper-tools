#!/usr/bin/env python3
"""
Simple HTML Scraper for Dark Web Marketplaces

This scraper:
1. Reads category URLs from pages_url.json
2. Extracts all product listing URLs from each category page
3. Fetches the raw HTML for each product page
4. Saves everything to products_html.json (overwrites each time)

General-purpose: Works with any marketplace HTML structure.
"""

import json
import os
import random
import time
import re
import urllib.parse
import argparse
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from termcolor import colored


# Configuration
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8118
TOR_SOCKS_PORT = 9050

# Input/Output files
PAGES_URL_FILE = "pages_url.json"
PRODUCTS_HTML_FILE = "products_html.json"


def load_pages_urls():
    """Load category URLs from pages_url.json"""
    if not os.path.exists(PAGES_URL_FILE):
        print(colored(f"❌ {PAGES_URL_FILE} not found!", "red"))
        print(colored(f"   Create it with category URLs, example:", "yellow"))
        print(colored(f'   ["http://marketplace.onion/category1/", "http://marketplace.onion/category2/"]', "yellow"))
        return []
    
    try:
        with open(PAGES_URL_FILE, 'r', encoding='utf-8') as f:
            urls = json.load(f)
            print(colored(f"✅ Loaded {len(urls)} category URLs from {PAGES_URL_FILE}", "green"))
            return urls
    except Exception as e:
        print(colored(f"❌ Error loading {PAGES_URL_FILE}: {e}", "red"))
        return []


def save_products_html(products, overwrite=True):
    """Save product HTML data to products_html.json"""
    mode = 'w' if overwrite else 'a'
    
    try:
        with open(PRODUCTS_HTML_FILE, mode, encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(colored(f"✅ Saved {len(products)} products to {PRODUCTS_HTML_FILE}", "green"))
    except Exception as e:
        print(colored(f"❌ Error saving to {PRODUCTS_HTML_FILE}: {e}", "red"))


def extract_cookies(driver, do_quit=False):
    """Extract cookies from Selenium driver"""
    cookies = driver.get_cookies()
    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    if do_quit:
        try:
            driver.quit()
        except Exception:
            pass
    return cookie_dict


def setup_requests_session(cookies, use_socks=False, socks_port=9050):
    """Setup requests session with cookies and proxy"""
    session = requests.Session()
    
    if use_socks:
        session.proxies = {
            'http': f'socks5h://{PROXY_HOST}:{socks_port}',
            'https': f'socks5h://{PROXY_HOST}:{socks_port}'
        }
    else:
        session.proxies = {
            'http': f'http://{PROXY_HOST}:{PROXY_PORT}',
            'https': f'http://{PROXY_HOST}:{PROXY_PORT}'
        }
    
    session.cookies.update(cookies)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0'
    })
    
    return session


def extract_product_links(html, base_url):
    """
    Extract product links from category page HTML.
    Only extracts actual product pages, NOT category/navigation links.
    """
    soup = BeautifulSoup(html, 'html.parser')
    product_links = set()
    
    # Strategy 1: WooCommerce specific selectors (most common on dark web markets)
    woocommerce_selectors = [
        'li.product a.woocommerce-LoopProduct-link',
        'li.product h2 a',
        'li.product a[href]',
        '.products li.product a',
        'ul.products li a'
    ]
    
    for selector in woocommerce_selectors:
        links = soup.select(selector)
        for link in links:
            href = link.get('href')
            if href:
                full_url = urllib.parse.urljoin(base_url, href)
                # Only add if it's NOT a category page
                if '/product-category/' not in full_url and '/category/' not in full_url:
                    product_links.add(full_url)
    
    # If we found products via WooCommerce selectors, return them
    if product_links:
        return list(product_links)
    
    # Strategy 2: Generic product link detection (fallback)
    # Look for links that have product-like patterns but exclude categories
    all_links = soup.find_all('a', href=True)
    for link in all_links:
        href = link['href']
        full_url = urllib.parse.urljoin(base_url, href)
        
        # Must match product indicators
        product_indicators = ['/shop/', '/item/', '/listing/', '/p/']
        
        # Must NOT match excluded patterns  
        excluded_patterns = [
            'cart', 'checkout', 'account', 'login',
            '/product-category/', '/category/', '/tag/',
            'page/', '/page-', 'author', 'search', 'filter'
        ]
        
        has_product_indicator = any(indicator in full_url.lower() for indicator in product_indicators)
        has_excluded = any(pattern in full_url.lower() for pattern in excluded_patterns)
        
        if has_product_indicator and not has_excluded:
            product_links.add(full_url)
    
    return list(product_links)
    
    return list(product_links)


def fetch_page_html(session, url, retries=3):
    """Fetch HTML from a URL with retries"""
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=30)
            if response.status_code == 200:
                return response.text
            else:
                print(colored(f"⚠️  HTTP {response.status_code} for {url}", "yellow"))
        except requests.exceptions.RequestException as e:
            print(colored(f"❌ Error fetching {url} (attempt {attempt+1}/{retries}): {e}", "red"))
            if attempt < retries - 1:
                time.sleep(5)
    
    return None


def scrape_category_page(session, category_url):
    """Scrape a category page and return all product links"""
    print(colored(f"\n📄 Scraping category: {category_url}", "cyan"))
    
    html = fetch_page_html(session, category_url)
    if not html:
        print(colored(f"❌ Failed to fetch category page", "red"))
        return []
    
    product_links = extract_product_links(html, category_url)
    print(colored(f"✅ Found {len(product_links)} product links", "green"))
    
    # Also check for pagination
    soup = BeautifulSoup(html, 'html.parser')
    pagination_links = []
    
    pagination_selectors = [
        'a[rel="next"]', 'a.next', 'li.next a',
        '.pagination a', 'ul.pagination a',
        'nav a', 'a[aria-label="Next"]'
    ]
    
    for selector in pagination_selectors:
        links = soup.select(selector)
        for link in links:
            href = link.get('href')
            if href:
                full_url = urllib.parse.urljoin(category_url, href)
                pagination_links.append(full_url)
        if pagination_links:
            break
    
    if pagination_links:
        print(colored(f"📑 Found {len(pagination_links)} pagination links", "blue"))
    
    return product_links, pagination_links


def scrape_product_page(session, product_url, category_url, market_name):
    """Scrape a single product page and return HTML data"""
    print(colored(f"  📦 Fetching: {product_url}", "blue"))
    
    html = fetch_page_html(session, product_url)
    if not html:
        return None
    
    return {
        "market": market_name,
        "category_page": category_url,
        "product_url": product_url,
        "fetched_at": int(time.time()),
        "html": html
    }


def main():
    parser = argparse.ArgumentParser(description='Simple HTML scraper for dark web marketplaces')
    parser.add_argument('--manual', action='store_true', 
                       help='Open browser and wait for manual CAPTCHA solving')
    parser.add_argument('--socks', action='store_true', 
                       help='Use Tor SOCKS5 (default uses HTTP proxy on 8118)')
    parser.add_argument('--socks-port', type=int, default=TOR_SOCKS_PORT,
                       help='Tor SOCKS port (default: 9050)')
    parser.add_argument('--page-timeout', type=int, default=300,
                       help='Selenium page load timeout in seconds')
    parser.add_argument('--tor-binary', type=str, default=None,
                       help='Path to Tor Browser firefox binary')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='Delay between requests in seconds (default: 2)')
    parser.add_argument('--max-products', type=int, default=None,
                       help='Maximum number of products to scrape (default: unlimited)')
    
    args = parser.parse_args()
    
    # Load category URLs
    category_urls = load_pages_urls()
    if not category_urls:
        print(colored("\n❌ No URLs to scrape. Exiting.", "red"))
        return
    
    print(colored(f"\n🚀 Starting scraper...", "cyan", attrs=['bold']))
    print(colored(f"   Categories to scrape: {len(category_urls)}", "white"))
    print(colored(f"   Delay between requests: {args.delay}s", "white"))
    
    # Initialize browser for CAPTCHA solving
    driver = None
    try:
        # Setup Firefox with proxy
        options = Options()
        if args.tor_binary:
            options.binary_location = args.tor_binary
        
        options.set_preference("network.proxy.type", 1)
        
        if args.socks:
            options.set_preference("network.proxy.socks", PROXY_HOST)
            options.set_preference("network.proxy.socks_port", args.socks_port)
            options.set_preference("network.proxy.socks_version", 5)
        else:
            options.set_preference("network.proxy.http", PROXY_HOST)
            options.set_preference("network.proxy.http_port", PROXY_PORT)
            options.set_preference("network.proxy.ssl", PROXY_HOST)
            options.set_preference("network.proxy.ssl_port", PROXY_PORT)
        
        options.set_preference("network.proxy.no_proxies_on", "")
        
        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(args.page_timeout)
        
        # Open first category URL for session establishment
        first_url = category_urls[0]
        print(colored(f"\n🌐 Opening: {first_url}", "blue"))
        
        try:
            driver.get(first_url)
        except TimeoutException:
            try:
                driver.execute_script("window.stop();")
            except Exception:
                pass
            print(colored("⏱️  Page load timed out, continuing...", "yellow"))
        
        print(colored("⏳ Waiting 60 seconds to establish session...", "yellow"))
        time.sleep(60)
        
        # Manual CAPTCHA solving
        if args.manual:
            print(colored("\n🔐 Manual mode: Please solve any CAPTCHA in the browser.", "yellow", attrs=['bold']))
            input(colored("   Press Enter when ready to continue...", "yellow"))
        
        # Extract cookies
        cookies = extract_cookies(driver, do_quit=True)
        driver = None
        
        print(colored(f"✅ Session established, extracted {len(cookies)} cookies", "green"))
        
        # Setup requests session
        session = setup_requests_session(cookies, args.socks, args.socks_port)
        
        # Scrape all categories
        all_products = []
        scraped_urls = set()
        
        for category_url in category_urls:
            print(colored(f"\n{'='*80}", "cyan"))
            print(colored(f"CATEGORY: {category_url}", "cyan", attrs=['bold']))
            print(colored(f"{'='*80}", "cyan"))
            
            # Extract market name from URL
            parsed = urllib.parse.urlparse(category_url)
            market_name = parsed.netloc
            
            # Scrape category page (no pagination - only the given URL)
            product_links, _ = scrape_category_page(session, category_url)
            all_product_links = set(product_links)
            
            print(colored(f"\n📊 Products found on this page: {len(all_product_links)}", "green", attrs=['bold']))
            
            # Scrape each product page
            for i, product_url in enumerate(all_product_links, 1):
                if product_url in scraped_urls:
                    print(colored(f"  ⏭️  Skipping duplicate: {product_url}", "yellow"))
                    continue
                
                if args.max_products and len(all_products) >= args.max_products:
                    print(colored(f"\n⚠️  Reached max products limit ({args.max_products})", "yellow"))
                    break
                
                print(colored(f"  [{i}/{len(all_product_links)}]", "white"), end=" ")
                
                product_data = scrape_product_page(session, product_url, category_url, market_name)
                
                if product_data:
                    all_products.append(product_data)
                    scraped_urls.add(product_url)
                    print(colored(f"    ✅ Saved (total: {len(all_products)})", "green"))
                else:
                    print(colored(f"    ❌ Failed", "red"))
                
                # Delay between requests
                time.sleep(args.delay + random.uniform(0, 1))
            
            if args.max_products and len(all_products) >= args.max_products:
                break
        
        # Save all products to JSON (overwrite mode)
        print(colored(f"\n{'='*80}", "cyan"))
        print(colored(f"💾 SAVING RESULTS", "cyan", attrs=['bold']))
        print(colored(f"{'='*80}", "cyan"))
        
        save_products_html(all_products, overwrite=True)
        
        print(colored(f"\n✅ Scraping complete!", "green", attrs=['bold']))
        print(colored(f"   Total products scraped: {len(all_products)}", "green"))
        print(colored(f"   Saved to: {PRODUCTS_HTML_FILE}", "green"))
        
    except KeyboardInterrupt:
        print(colored("\n\n⚠️  Scraping interrupted by user", "yellow"))
        if all_products:
            print(colored(f"💾 Saving {len(all_products)} products collected so far...", "yellow"))
            save_products_html(all_products, overwrite=True)
    
    except Exception as e:
        print(colored(f"\n❌ Error: {e}", "red"))
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    main()
