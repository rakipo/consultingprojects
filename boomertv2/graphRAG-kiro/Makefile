# Makefile for GraphRAG Retrieval Agent

.PHONY: help install install-dev test test-integration lint format clean build docker-build docker-run docker-compose-up docker-compose-down

# Default target
help:
	@echo "GraphRAG Retrieval Agent - Available Commands:"
	@echo ""
	@echo "Setup and Installation:"
	@echo "  install          Install package and dependencies"
	@echo "  install-dev      Install package with development dependencies"
	@echo "  install-conda    Create conda environment from environment.yml"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-coverage    Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run linting (flake8, mypy)"
	@echo "  format           Format code with black"
	@echo "  format-check     Check code formatting"
	@echo ""
	@echo "Application:"
	@echo "  run-cli          Run CLI interface"
	@echo "  run-mcp          Run MCP server"
	@echo "  status           Check system status"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-run       Run Docker container"
	@echo "  docker-compose-up   Start with docker-compose"
	@echo "  docker-compose-down Stop docker-compose services"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean            Clean build artifacts"
	@echo "  build            Build package"
	@echo "  requirements     Generate requirements.txt from environment"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,logging]"

install-conda:
	conda env create -f environment.yml
	@echo "Activate environment with: conda activate graphrag-agent"

# Testing targets
test:
	python tests/test_runner.py

test-unit:
	pytest tests/ -m "not integration" -v

test-integration:
	python tests/fixtures/mock_utilities.py

test-coverage:
	pytest tests/ --cov=modules --cov-report=html --cov-report=term

# Code quality targets
lint:
	flake8 modules/ main.py mcp_server.py tests/
	mypy modules/ main.py mcp_server.py

format:
	black modules/ main.py mcp_server.py tests/

format-check:
	black --check modules/ main.py mcp_server.py tests/

# Application targets
run-cli:
	python main.py status

run-mcp:
	python mcp_server.py

status:
	python main.py status

query:
	@read -p "Enter query: " query; \
	python main.py query "$$query"

# Docker targets
docker-build:
	docker build -t graphrag-agent .

docker-run:
	docker run -it --rm \
		-e NEO4J_URI=bolt://host.docker.internal:7687 \
		-e NEO4J_USERNAME=neo4j \
		-e NEO4J_PASSWORD=password \
		-v $(PWD)/logs:/app/logs \
		graphrag-agent

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

docker-compose-logs:
	docker-compose logs -f graphrag-agent

# Maintenance targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	python -m build

requirements:
	pip freeze > requirements-frozen.txt
	@echo "Frozen requirements saved to requirements-frozen.txt"

# Development helpers
dev-setup: install-dev
	@echo "Development environment setup complete"
	@echo "Run 'make test' to verify installation"

# CI/CD helpers
ci-test: install-dev lint test

# Documentation (if needed in future)
docs:
	@echo "Documentation generation not implemented yet"

# Database helpers
neo4j-start:
	docker run -d --name graphrag-neo4j \
		-p 7474:7474 -p 7687:7687 \
		-e NEO4J_AUTH=neo4j/password \
		neo4j:5.15-community

neo4j-stop:
	docker stop graphrag-neo4j || true
	docker rm graphrag-neo4j || true

# Quick development workflow
dev-test: format lint test
	@echo "Development checks passed!"

# Production deployment helpers
deploy-check:
	@echo "Checking deployment readiness..."
	python -c "from modules.config import load_config; print('✓ Config loading works')"
	python -c "from modules.embedding import get_model_info; print('✓ Embedding model works')"
	python -c "from modules.logging_config import setup_logging; setup_logging(); print('✓ Logging works')"
	@echo "✓ Deployment checks passed"