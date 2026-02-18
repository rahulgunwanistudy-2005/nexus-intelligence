.PHONY: help install run stop clean test lint

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies locally
	pip install -r requirements.txt
	playwright install chromium

run:  ## Start all services with Docker
	docker-compose up -d
	@echo "[OK] Services started!"
	@echo "API: http://localhost:8000"
	@echo "Dashboard: http://localhost:8501"
	@echo "API Docs: http://localhost:8000/docs"

stop:  ## Stop all services
	docker-compose down

restart:  ## Restart all services
	docker-compose restart

logs:  ## Show logs
	docker-compose logs -f

build:  ## Rebuild Docker images
	docker-compose build --no-cache

clean:  ## Clean data and Docker volumes
	rm -rf data/raw/*.html
	rm -rf data/processed/*.parquet
	docker-compose down -v

test:  ## Run tests
	pytest tests/ -v

lint:  ## Run code linters
	black src/
	flake8 src/

dev-api:  ## Run API locally (without Docker)
	uvicorn src.api.main:app --reload --port 8000

dev-dashboard:  ## Run dashboard locally (without Docker)
	streamlit run src/dashboard/app.py

scrape:  ## Run scraper manually
	python -m src.scraper.amazon

parse:  ## Run parser manually
	python -m src.parser.html_parser