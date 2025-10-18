#!/bin/bash
# Quick test script for the refactored scraper

set -e  # Exit on error

echo "=================================================="
echo "   DARKWEB SCRAPER - QUICK TEST"
echo "=================================================="
echo

# Check prerequisites
echo "1. Checking prerequisites..."
echo

# Check Tor
if netstat -an | grep -q 9050; then
    echo "✅ Tor is running on port 9050"
else
    echo "❌ Tor is NOT running!"
    echo "   Start it with: brew services start tor"
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    echo "✅ Python3 is installed ($(python3 --version))"
else
    echo "❌ Python3 not found!"
    exit 1
fi

# Check required packages
echo
echo "2. Checking Python packages..."
for pkg in selenium requests beautifulsoup4 termcolor; do
    if python3 -c "import ${pkg//-/_}" 2>/dev/null; then
        echo "✅ $pkg is installed"
    else
        echo "❌ $pkg is NOT installed!"
        echo "   Install with: pip install $pkg"
        exit 1
    fi
done

echo
echo "3. Running extraction test (offline)..."
python3 test_extraction.py | tail -20

echo
echo "=================================================="
echo "   READY TO TEST WITH TOR!"
echo "=================================================="
echo
echo "Test options:"
echo
echo "A) Test single product page (quick, ~2 min):"
echo "   python3 scrape.py --socks --socks-port 9050 --manual"
echo
echo "B) Test category scraping (moderate, ~10 min):"
echo "   python3 scrape.py --socks --socks-port 9050 --manual \\"
echo "     --category-endpoints /product-category/buy-steroids/sexual-health/"
echo
echo "C) Test with page archival (comprehensive):"
echo "   python3 scrape.py --socks --socks-port 9050 --manual \\"
echo "     --save-pages \\"
echo "     --category-endpoints /product-category/buy-steroids/sexual-health/"
echo
echo "=================================================="
echo

read -p "Run test A (single product)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo
    echo "Starting test A..."
    echo "NOTE: Firefox will open. Solve any CAPTCHA, then press Enter in terminal."
    echo
    python3 scrape.py --socks --socks-port 9050 --manual --page-timeout 600
    
    echo
    echo "=================================================="
    echo "   TEST COMPLETE!"
    echo "=================================================="
    echo
    echo "Check results:"
    echo "  - products.json: $(wc -l < products.json 2>/dev/null || echo 0) lines"
    echo "  - products_html.json: $(wc -l < products_html.json 2>/dev/null || echo 0) lines"
    echo
    echo "View products:"
    echo "  python3 scrape.py --dump | python3 -m json.tool | less"
    echo
    echo "View detailed extraction:"
    echo "  cat products_html.json | python3 -m json.tool | less"
fi
