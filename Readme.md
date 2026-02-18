# Nexus Intelligence

Production-grade e-commerce product intelligence platform for Amazon India. Built with FastAPI, Playwright, and Streamlit.

## Overview

Nexus Intelligence is a real-time product data aggregation and analysis system designed for market research and competitive intelligence. The platform automatically scrapes product listings from Amazon India, parses structured data, and presents actionable insights through an interactive dashboard.

**Key capabilities:**
- Multi-page automated product scraping with anti-detection measures
- Smart relevance filtering to eliminate accessory noise
- RESTful API with OpenAPI documentation
- Interactive data visualization dashboard
- Intelligent caching system (24-hour TTL)
- Production-ready Docker deployment
- Comprehensive test coverage

## Architecture

```
┌─────────────┐      HTTP       ┌──────────┐      subprocess      ┌─────────────┐
│  Streamlit  │ ────────────────>│ FastAPI  │ ───────────────────> │  Scraper    │
│  Dashboard  │                  │   API    │                      │ (Playwright)│
│  (Port 8501)│ <────────────────│(Port 8000)│ <─────────────────  │             │
└─────────────┘    JSON          └──────────┘      HTML           └─────────────┘
                                       │                                  │
                                       │                                  │
                                       v                                  v
                                 ┌──────────┐                      ┌──────────┐
                                 │  Parser  │                      │   data/  │
                                 │(BeautifulSoup)                  │   raw/   │
                                 └──────────┘                      └──────────┘
                                       │
                                       v
                                 ┌──────────┐
                                 │   data/  │
                                 │processed/│
                                 │(.parquet)│
                                 └──────────┘
```

**Technology Stack:**
- **Backend:** FastAPI 0.109, Uvicorn ASGI server
- **Scraping:** Playwright (headless Chromium)
- **Parsing:** BeautifulSoup4, lxml
- **Data:** Pandas, PyArrow (Parquet columnar format)
- **Frontend:** Streamlit, Plotly
- **Deployment:** Docker, Docker Compose
- **Testing:** Pytest with 29 unit tests

## Quick Start

### Prerequisites
- Docker and Docker Compose
- 2GB RAM minimum
- Internet connection for Amazon.in access

### Installation

```bash
# Clone repository
git clone <repository-url>
cd nexus-intelligence

# Start services
docker-compose up -d

# Verify health
curl http://localhost:8000/health
```

**Access points:**
- Dashboard: http://localhost:8501
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### First Search

1. Open http://localhost:8501
2. Enter a product name (e.g., "Sony headphones")
3. Click "SCAN MARKET"
4. Wait 40-60 seconds for initial scrape
5. View results with price/rating analytics

Subsequent searches for the same product return instantly from cache.

## API Reference

### Endpoints

#### `GET /api/products`

Search for products on Amazon India.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Product search term (min 2 chars) |
| `limit` | integer | No | 20 | Max results to return (1-100) |
| `min_rating` | float | No | 0.0 | Minimum star rating filter (0-5) |

**Response:**
```json
{
  "query": "sony headphones",
  "count": 24,
  "cached": false,
  "products": [
    {
      "title": "Sony WH-1000XM5 Wireless Headphones",
      "price": 29990.0,
      "rating": 4.5,
      "url": "https://www.amazon.in/dp/B09XSQH1QH",
      "platform": "Amazon",
      "scraped_at": "2026-02-17T12:00:00"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/api/products?query=headphones&limit=10&min_rating=4.0"
```

#### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-17T12:00:00.000000",
  "version": "3.0.0"
}
```

## Development

### Local Setup (without Docker)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Create data directories
mkdir -p data/raw data/processed

# Run API
uvicorn src.api.main:app --reload --port 8000

# Run Dashboard (in separate terminal)
streamlit run src/dashboard/app.py
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

**Test Coverage:**
- `test_api.py`: 11 tests covering endpoints, validation, caching
- `test_parser.py`: 8 tests covering relevance filters, price parsing
- `test_scraper.py`: 10 tests covering URL building, pagination, error handling

### Configuration

Environment variables (set in `.env` or docker-compose.yml):

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_PAGES` | 3 | Number of Amazon pages to scrape per query |
| `CACHE_TTL_HOURS` | 24 | How long to cache results before re-scraping |
| `API_HOST` | 0.0.0.0 | API bind address |
| `API_PORT` | 8000 | API port |
| `DASHBOARD_PORT` | 8501 | Dashboard port |

## Project Structure

```
nexus-intelligence/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI pipeline
├── src/
│   ├── api/
│   │   ├── main.py             # FastAPI application
│   │   └── models.py           # Pydantic data models
│   ├── scraper/
│   │   └── amazon.py           # Playwright scraper
│   ├── parser/
│   │   └── html_parser.py      # BeautifulSoup parser
│   └── dashboard/
│       └── app.py              # Streamlit UI
├── tests/
│   ├── conftest.py             # Pytest configuration
│   ├── test_api.py
│   ├── test_parser.py
│   └── test_scraper.py
├── data/
│   ├── raw/                    # HTML files
│   └── processed/              # Parquet files
├── docker-compose.yml          # Service orchestration
├── Dockerfile.api              # API container definition
├── Dockerfile.dashboard        # Dashboard container definition
├── requirements.txt            # Python dependencies
└── README.md
```

## Features

### Smart Relevance Filtering

The parser implements multi-stage relevance filtering to eliminate false positives:

1. **Keyword matching:** All search terms must appear in product title
2. **Position awareness:** Primary keyword must appear in first 60 characters
3. **Accessory detection:** Blocks titles starting with "Compatible with", "Cable for", "Case for", etc.
4. **Plural normalization:** "iPhones" matches "iPhone"

Example: Searching "apple iPhones" will exclude USB cables that mention iPhone compatibility.

### Caching Strategy

- File-based caching using Parquet columnar format
- Per-query cache isolation (`headphones_20260217_120000.parquet`)
- Automatic cache invalidation after 24 hours
- Cache cleared on every new scrape to ensure freshness
- Sub-second response time for cached queries

### Anti-Detection Measures

The scraper implements multiple techniques to avoid bot detection:

- Removes `webdriver` JavaScript flag
- Realistic viewport size (1920x1080)
- Random delays between page loads (2-4 seconds)
- Variable scrolling patterns
- Human-like timing for interactions
- Proper user agent and headers

### Data Quality

- Deduplication by product title
- Price validation and normalization
- Rating range enforcement (0-5)
- URL sanitization
- Timestamp tracking for all records

## Deployment

### Docker Compose (Recommended)

```bash
# Production deployment
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d
```

### Cloud Deployment

#### AWS EC2

```bash
# SSH into instance
ssh -i key.pem ubuntu@<instance-ip>

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu

# Clone and deploy
git clone <repo-url>
cd nexus-intelligence
docker-compose up -d

# Configure security group to allow ports 8000, 8501
```

#### Google Cloud Run

```bash
# Deploy API
gcloud run deploy nexus-api \
  --source . \
  --platform managed \
  --region us-central1

# Deploy Dashboard
gcloud run deploy nexus-dashboard \
  --source . \
  --platform managed \
  --region us-central1
```

## Performance

| Metric | Value |
|--------|-------|
| First search (no cache) | 40-60 seconds |
| Cached search | < 2 seconds |
| Products per search | 60-90 (3 pages) |
| Cache duration | 24 hours (configurable) |
| API response time | < 100ms (cached) |
| Memory usage | ~500MB (API + Dashboard) |

## Troubleshooting

### "Playwright not found" error

```bash
# Install Playwright browsers
docker exec nexus-api playwright install chromium

# Or rebuild container
docker-compose build --no-cache api
```

### Network timeout errors

```bash
# Check DNS resolution
docker exec nexus-api ping -c 2 amazon.in

# If fails, DNS is misconfigured
# docker-compose.yml already includes 8.8.8.8 fallback
```

### No results returned

```bash
# Check API logs
docker logs nexus-api --tail 50

# Verify scraper works
docker exec -e SEARCH_TERM="test" nexus-api python -m src.scraper.amazon

# Check data files created
docker exec nexus-api ls -lh data/raw/
docker exec nexus-api ls -lh data/processed/
```

### Dashboard shows "API Offline"

```bash
# Verify API is running
curl http://localhost:8000/health

# Check container status
docker ps

# Restart API if needed
docker-compose restart api
```

## CI/CD Pipeline

The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs on every push:

1. **Lint:** flake8 and mypy type checking
2. **Unit Tests:** pytest with coverage reporting
3. **Docker Build:** Verifies both images build successfully
4. **Smoke Test:** Starts stack, hits endpoints, verifies responses

Coverage reports are automatically uploaded to Codecov.

## Security Considerations

- No API authentication (add if exposing publicly)
- Rate limiting not implemented (Amazon may block excessive requests)
- User input sanitization in place for query parameters
- No sensitive data stored (product listings are public)
- Docker containers run as non-root where possible

**Production recommendations:**
- Add API key authentication
- Implement rate limiting (e.g., 10 requests/minute)
- Use HTTPS/TLS with reverse proxy
- Monitor scraping volume to avoid IP blocks
- Set up alerts for error rates

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Make changes and add tests
4. Run test suite (`pytest tests/ -v`)
5. Commit changes (`git commit -m 'Add improvement'`)
6. Push to branch (`git push origin feature/improvement`)
7. Open a Pull Request

**Code quality requirements:**
- All tests must pass
- Code coverage should not decrease
- Follow PEP 8 style guidelines
- Add docstrings for new functions
- Update README if adding features

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- Built with FastAPI, Playwright, and Streamlit
- Inspired by Bloomberg Terminal and modern data platforms
- Data sourced from Amazon India for research purposes only

---

For issues, questions, or feature requests, please open an issue on GitHub.