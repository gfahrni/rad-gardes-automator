PY := .venv/bin/python
PYTEST := .venv/bin/pytest

.PHONY: install test run screenshots build-macos build-windows clean

install:
	uv venv .venv --python 3.12
	UV_HTTP_TIMEOUT=900 uv pip install --python .venv/bin/python -e ".[dev]"

test:
	QT_QPA_PLATFORM=offscreen $(PYTEST) -q

run:
	$(PY) -m gardes_gui

screenshots:
	QT_QPA_PLATFORM=offscreen $(PY) scripts/generate_screenshots.py

build-macos:
	packaging/build-macos.sh

build-windows:
	pwsh -File packaging/build-windows.ps1

clean:
	rm -rf data
