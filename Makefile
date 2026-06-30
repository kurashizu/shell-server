.PHONY: install run dev clean

VENV ?= .venv
PYTHON ?= python
UVICORN = $(VENV)/bin/uvicorn

# Install dependencies into a virtual environment
install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

# Run in production mode (no auto-reload)
run:
	$(UVICORN) app.main:app --host 127.0.0.1 --port 8080

# Run in development mode (auto-reload on file changes)
dev:
	$(UVICORN) app.main:app --host 127.0.0.1 --port 8080 --reload

# Clean Python cache artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
