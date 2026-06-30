.PHONY: install run dev clean

VENV ?= .venv
PYTHON ?= python
RUNNER = $(VENV)/bin/python run.py

# Install dependencies into a virtual environment
install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

# Run in production mode (reads host/port from .env or env vars)
run:
	$(RUNNER)

# Run in development mode (auto-reload on file changes)
dev:
	$(RUNNER) --reload

# Clean Python cache artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
