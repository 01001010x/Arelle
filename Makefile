.PHONY: install run clean

install:
    python3 -m venv .venv
    . .venv/bin/activate && pip install -r requirements-dev.txt

run:
    python arelleGUI.pyw

clean:
    find . -type f -name '*.py[co]' -delete
    find . -type d -name '__pycache__' -delete
    rm -rf .pytest_cache
    rm -rf .venv
    rm -rf build dist
    rm -f *.egg-info