.PHONY: help dev test lint docker-build docker-run docker-stop clean install

# Default target - show help
help:
	@echo "🚀 OpenQQuantify AI Travel Platform - Developer Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  make install       - Create venv and install dependencies"
	@echo "  make dev           - Run app locally with hot reload (port 8080)"
	@echo "  make test          - Run pytest tests"
	@echo "  make lint          - Run code linting (flake8)"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container (port 8080)"
	@echo "  make docker-stop   - Stop and remove Docker container"
	@echo "  make compose-up    - Start full observability stack (app + Prometheus + Grafana)"
	@echo "  make compose-down  - Stop observability stack"
	@echo "  make clean         - Remove cache, pyc files, and build artifacts"
	@echo ""

# Install dependencies
install:
	@echo "📦 Creating virtual environment and installing dependencies..."
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip setuptools wheel
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install pytest flake8 pytest-flask
	@echo "✅ Dependencies installed. Activate with: source .venv/bin/activate"

# Run app locally
dev:
	@if [ ! -d ".venv" ]; then \
		echo "⚠️  Virtual environment not found. Running 'make install' first..."; \
		make install; \
	fi
	@echo "🚀 Starting app on http://localhost:8080"
	@echo "📊 Metrics available at http://localhost:8080/metrics"
	@echo "❤️  Health check at http://localhost:8080/healthz"
	@echo "✅ Readiness check at http://localhost:8080/readyz"
	@echo ""
	.venv/bin/python app.py

# Run tests
test:
	@if [ ! -d ".venv" ]; then \
		echo "⚠️  Virtual environment not found. Running 'make install' first..."; \
		make install; \
	fi
	@echo "🧪 Running tests..."
	.venv/bin/pytest tests/ -v

# Run linting
lint:
	@if [ ! -d ".venv" ]; then \
		echo "⚠️  Virtual environment not found. Running 'make install' first..."; \
		make install; \
	fi
	@echo "🔍 Running linter..."
	.venv/bin/flake8 app.py ai_routes.py cache.py limiter_config.py --max-line-length=120 --extend-ignore=E501,W503

# Build Docker image
docker-build:
	@echo "🐳 Building Docker image: airports-ai:local"
	docker build -t airports-ai:local .
	@echo "✅ Image built successfully"
	@docker images | grep airports-ai

# Run Docker container
docker-run:
	@echo "🐳 Running Docker container on port 8080..."
	docker run --rm -d \
		--name airports-ai \
		-p 8080:8080 \
		--env-file .env \
		airports-ai:local
	@echo "✅ Container started: airports-ai"
	@echo "🚀 App available at http://localhost:8080"
	@echo "📊 Metrics at http://localhost:8080/metrics"
	@echo ""
	@echo "To view logs: docker logs -f airports-ai"
	@echo "To stop: make docker-stop"

# Stop Docker container
docker-stop:
	@echo "🛑 Stopping Docker container..."
	docker stop airports-ai || true
	@echo "✅ Container stopped"

# Start full observability stack
compose-up:
	@echo "🚀 Starting full observability stack..."
	@echo "   - App (port 8080)"
	@echo "   - Prometheus (port 9090)"
	@echo "   - Grafana (port 3000)"
	@echo "   - Loki (port 3100)"
	docker compose up -d
	@echo ""
	@echo "✅ Stack started!"
	@echo "🚀 App: http://localhost:8080"
	@echo "📊 Prometheus: http://localhost:9090"
	@echo "📈 Grafana: http://localhost:3000 (admin/secret)"
	@echo ""
	@echo "To view logs: docker compose logs -f"
	@echo "To stop: make compose-down"

# Stop observability stack
compose-down:
	@echo "🛑 Stopping observability stack..."
	docker compose down
	@echo "✅ Stack stopped"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Deep clean (including venv)
clean-all: clean
	@echo "🧹 Deep cleaning (including venv)..."
	rm -rf .venv
	@echo "✅ Deep cleanup complete"
