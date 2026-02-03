nexus-intelligence/
│
├── .github/                    # CI/CD Automation
│   └── workflows/
│       ├── run_tests.yaml      # Automatically run tests on push
│       └── deploy.yaml         # Build and push Docker image
│
├── configs/                    # Configuration Management (No hardcoding!)
│   ├── base_config.yaml        # Default settings (batch size, urls)
│   ├── model_config.yaml       # LLM/Model specific params
│   └── logging_config.yaml     # Loguru/Logging settings
│
├── data/                       # Local Data Lake (Added to .gitignore)
│   ├── bronze/                 # Raw scrapes (HTML/JSON)
│   ├── silver/                 # Cleaned, structured DataFrames (Parquet)
│   └── gold/                   # Vector embeddings / Final Features
│
├── docker/                     # Containerization logic
│   ├── Dockerfile.api          # Image for the FastAPI backend
│   └── Dockerfile.scraper      # Image for the Playwright scraper
│
├── notebooks/                  # Lab Environment (Keep messy code here)
│   ├── 01_exploratory_analysis.ipynb
│   └── 02_prompt_engineering_gemini.ipynb
│
├── scripts/                    # Utility scripts for ops
│   ├── run_pipeline.sh         # One-click execution script
│   └── setup_env.sh            # Environment setup helper
│
├── src/                        # The Application Core (Production Code)
│   ├── __init__.py
│   ├── ingestion/              # Data Collection Layer
│   │   ├── __init__.py
│   │   ├── scraper.py          # Playwright logic
│   │   └── kafka_producer.py   # Streaming logic (Optional/Advanced)
│   │
│   ├── processing/             # ETL & Cleaning Layer
│   │   ├── __init__.py
│   │   ├── cleaner.py          # Text normalization
│   │   └── preprocessor.py     # Pandas transformations
│   │
│   ├── intelligence/           # ML & AI Layer
│   │   ├── __init__.py
│   │   ├── gemini_client.py    # Wrapper for Google Gemini API
│   │   ├── sentiment.py        # Local BERT model logic
│   │   └── vector_store.py     # Pinecone/ChromaDB interactions
│   │
│   ├── api/                    # Serving Layer
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI entry point
│   │   ├── routes.py           # API Endpoints
│   │   └── schemas.py          # Pydantic models for data validation
│   │
│   └── utils/                  # Shared Helpers
│       ├── logger.py           # Centralized logging config
│       └── db_connector.py     # Database connection manager
│
├── tests/                      # Automated Testing (Critical for Industry)
│   ├── unit/
│   │   ├── test_cleaner.py
│   │   └── test_scraper.py
│   └── integration/
│       └── test_api_endpoints.py
│
├── .env                        # Secrets (API Keys) - NEVER COMMIT THIS
├── .gitignore                  # Files to ignore
├── .pre-commit-config.yaml     # Auto-linting before committing
├── docker-compose.yaml         # Orchestrate the whole app locally
├── Makefile                    # Shortcuts (e.g., `make run`, `make test`)
├── pyproject.toml              # Modern dependency management
├── README.md                   # The Documentation (Your project's face)
└── requirements.txt            # Python dependencies

# ⚡ Nexus Intelligence: AI-Powered Market Analyst

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31-FF4B4B)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.0%20Flash-8E75B2)

**Nexus** is an autonomous market intelligence engine that ingests real-time e-commerce data, enriches it with GenAI-driven buyer personas, and exposes insights via a REST API and Live Dashboard.

## 🏗️ Architecture

The system follows a production-grade **ELT (Extract, Load, Transform)** pipeline:

1.  **Ingestion (Bronze Layer):** `Playwright` scraper triggers on-demand to fetch raw HTML from e-commerce targets.
2.  **Processing (Silver Layer):** `Pandas` & `BeautifulSoup` parsers clean and structure data into Parquet files.
3.  **Intelligence (Gold Layer):** `Google Gemini 2.0 Flash` acts as an agent to analyze "Value Propositions" and "Target Audiences" for every product.
4.  **Serving:**
    * **Backend:** `FastAPI` serves structured data and handles live ingestion triggers.
    * **Frontend:** `Streamlit` provides an interactive analytical dashboard.

## 🚀 Quick Start

### 1. Prerequisites
* Python 3.10+
* Google Gemini API Key

### 2. Installation
```bash
# Clone the repo
git clone [https://github.com/RahulGunwani/nexus-market-intelligence.git](https://github.com/RahulGunwani/nexus-market-intelligence.git)
cd nexus-market-intelligence

# Install dependencies
pip install -r requirements.txt

# Configure Secrets
# Create a .env file and add your key:
# GOOGLE_API_KEY=your_api_key_here