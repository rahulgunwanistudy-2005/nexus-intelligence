"""Tests for the HTML parser."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.html_parser import AmazonParser

SAMPLE_CARD_HTML = """
<div data-component-type="s-search-result">
  <h2><a href="/dp/B001"><span class="a-text-normal">Sony WH-1000XM5 Wireless Headphones</span></a></h2>
  <span class="a-price"><span class="a-offscreen">₹29,990</span><span class="a-price-whole">29,990</span></span>
  <span aria-label="4.5 out of 5 stars">4.5 out of 5 stars</span>
  <img class="s-image" alt="Sony WH-1000XM5 Wireless Headphones" src="img.jpg">
</div>
"""

@pytest.fixture
def parser(tmp_path):
    p = AmazonParser()
    p.output_dir = tmp_path
    return p

def test_relevance_words_basic(parser):
    assert parser._relevance_words("sony headphones") == ["sony", "headphone"]

def test_relevance_words_strips_plurals(parser):
    words = parser._relevance_words("apple iPhones")
    assert "iphone" in words
    assert "apple" in words

def test_relevance_words_removes_stopwords(parser):
    words = parser._relevance_words("headphones for running")
    assert "for" not in words

def test_is_relevant_passes_good_title(parser):
    assert parser._is_relevant("Apple iPhone 16 Pro 256GB", ["apple", "iphone"])

def test_is_relevant_blocks_cable(parser):
    assert not parser._is_relevant(
        "USB C Cable Compatible with iPhone Apple MFi Certified", ["apple", "iphone"]
    )

def test_is_relevant_blocks_accessory_prefix(parser):
    assert not parser._is_relevant("Compatible with iPhone 15 Case Cover", ["iphone"])

def test_is_relevant_blocks_late_keyword(parser):
    title = "Fast Charging Cable USB C Braided Cord Works with Apple iPhone"
    assert not parser._is_relevant(title, ["apple", "iphone"])

def test_clean_price(parser):
    assert parser._clean_price("₹29,990") == 29990.0
    assert parser._clean_price("1,299.00") == 1299.0
    assert parser._clean_price("") == 0.0