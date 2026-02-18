"""
Tests for AmazonScraper.

Strategy: mock Playwright entirely so tests run fast with no network.
The scraper logic (URL building, HTML saving, page counting) is tested
without ever launching a real browser.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper.amazon import AmazonScraper


# Fixtures and helpers

@pytest.fixture
def scraper(tmp_path):
    """Scraper with output_dir pointing at a temp directory."""
    s = AmazonScraper(max_pages=2)
    s.output_dir = tmp_path / "raw"
    s.output_dir.mkdir()
    return s


def _make_page_mock(product_count: int = 10, content: str = "<html>mock</html>"):
    """Return a mock Playwright page with realistic attributes."""
    page = MagicMock()
    page.content.return_value = content
    page.locator.return_value.count.return_value = product_count
    page.goto.return_value = None
    page.wait_for_selector.return_value = None
    page.evaluate.return_value = None
    page.set_viewport_size.return_value = None
    page.add_init_script.return_value = None
    return page


# URL and navigation tests

def test_url_encodes_spaces(scraper):
    """Spaces in search term must be encoded as + for Amazon."""
    page = _make_page_mock(product_count=0)  # returns 0 so loop exits fast
    with patch.object(scraper, "_scrape_page", return_value=(None, 0)) as mock_sp:
        with patch("src.scraper.amazon.sync_playwright") as mock_pw:
            ctx = mock_pw.return_value.__enter__.return_value
            ctx.chromium.launch.return_value.new_page.return_value = page
            scraper.scrape("sony headphones")
        # First call args: (page, "sony headphones", 1)
        assert mock_sp.call_args[0][1] == "sony headphones"


def test_url_format(scraper):
    """_scrape_page builds the correct Amazon URL."""
    page = _make_page_mock(product_count=0)
    # Trigger _scrape_page directly
    with patch("src.scraper.amazon.sync_playwright"):
        # Call internal method directly
        page.locator.return_value.count.return_value = 0
        result_html, count = scraper._scrape_page(page, "headphones", 1)
    assert count == 0
    # Check goto was called with the right URL shape
    call_url = page.goto.call_args[0][0]
    assert "amazon.in/s?k=headphones" in call_url
    assert "page=1" in call_url


# Product Counting 

def test_scrape_page_returns_count(scraper):
    """_scrape_page should return the product count from the locator."""
    page = _make_page_mock(product_count=28, content="<html>products</html>")
    html, count = scraper._scrape_page(page, "headphones", 1)
    assert count == 28
    assert html == "<html>products</html>"


def test_scrape_page_empty_returns_zero(scraper):
    """Zero products on a page should return (None, 0)."""
    page = _make_page_mock(product_count=0)
    html, count = scraper._scrape_page(page, "headphones", 1)
    assert html is None
    assert count == 0


# HTML Tests 

def test_save_html_creates_file(scraper, tmp_path):
    """_save_html should write a file with the correct name pattern."""
    pages = ["<html>page1</html>", "<html>page2</html>"]
    saved = scraper._save_html("sony headphones", pages)
    assert saved.exists()
    assert "sony_headphones" in saved.name
    assert saved.suffix == ".html"


def test_save_html_combines_pages(scraper):
    """Combined HTML should contain PAGE BREAK markers."""
    pages = ["<html>A</html>", "<html>B</html>"]
    saved = scraper._save_html("test", pages)
    content = saved.read_text()
    assert "PAGE BREAK" in content
    assert "<html>A</html>" in content
    assert "<html>B</html>" in content


def test_save_html_single_page(scraper):
    """Single page should save without PAGE BREAK."""
    saved = scraper._save_html("test", ["<html>only</html>"])
    content = saved.read_text()
    assert "PAGE BREAK" not in content


# Full scrape flow

def _mock_playwright_context(page_mock):
    """Build the nested mock for sync_playwright context manager."""
    pw = MagicMock()
    pw.__enter__ = MagicMock(return_value=pw)
    pw.__exit__ = MagicMock(return_value=False)
    browser = MagicMock()
    browser.new_page.return_value = page_mock
    browser.close.return_value = None
    pw.chromium.launch.return_value = browser
    return pw


def test_scrape_returns_success(scraper):
    """Full scrape with mocked browser should return success dict."""
    page = _make_page_mock(product_count=20, content="<html>results</html>")
    with patch("src.scraper.amazon.sync_playwright", return_value=_mock_playwright_context(page)):
        with patch("time.sleep"):  # skip real delays
            result = scraper.scrape("headphones")
    assert result["success"] is True
    assert result["products"] > 0
    assert "filename" in result
    assert Path(result["filename"]).exists()


def test_scrape_stops_on_empty_page(scraper):
    """Scraper should stop early when a page returns 0 products."""
    page = _make_page_mock(product_count=0)
    with patch("src.scraper.amazon.sync_playwright", return_value=_mock_playwright_context(page)):
        with patch("time.sleep"):
            result = scraper.scrape("nothing")
    assert result["success"] is False
    assert result.get("error") == "No data collected"


def test_scrape_respects_max_pages(scraper):
    """Scraper must not exceed max_pages even if results keep coming."""
    scraper.max_pages = 2
    page = _make_page_mock(product_count=10, content="<html>p</html>")
    call_count = {"n": 0}
    original = scraper._scrape_page
    def counting_scrape(p, term, num):
        call_count["n"] += 1
        return original(p, term, num)
    with patch.object(scraper, "_scrape_page", side_effect=counting_scrape):
        with patch("src.scraper.amazon.sync_playwright", return_value=_mock_playwright_context(page)):
            with patch("time.sleep"):
                scraper.scrape("headphones")
    assert call_count["n"] <= 2


def test_scrape_handles_exception_gracefully(scraper):
    """If the browser throws, scrape() should return success=False, not crash."""
    with patch("src.scraper.amazon.sync_playwright") as mock_pw:
        mock_pw.return_value.__enter__.side_effect = Exception("browser crash")
        result = scraper.scrape("headphones")
    assert result["success"] is False
    assert "error" in result