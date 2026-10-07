PYTHON ?= python3
VENV := .venv
RUN := $(VENV)/bin/python

.PHONY: setup pipeline dashboard

setup:
	$(PYTHON) -m venv $(VENV)
	$(RUN) -m pip install -r requirements.txt

pipeline:
	$(RUN) load_data.py
	$(RUN) pipeline.py

dashboard:
	$(RUN) -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true --browser.gatherUsageStats false
