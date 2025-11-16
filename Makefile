.PHONY: install run format lint data-check

DATA_CHECK_OPTS ?=

install:
	pip install -r requirements.txt

run:
	streamlit run app.py

format:
	black app.py app_utils scripts theme.py

lint:
	flake8 app.py app_utils scripts theme.py

data-check:
	python scripts/data_check.py $(DATA_CHECK_OPTS)
