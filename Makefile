PYTHON=.venv/bin/python
PYTHONPATH=src

install:
	python3 -m venv .venv
	.venv/bin/pip install -U pip
	.venv/bin/pip install -r requirements.txt

discover:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) scripts/00_discover_data.py

parse-pcap:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) scripts/01_parse_pcap.py

spread:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) scripts/02_build_wdo_calendar_spread.py

features:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) scripts/03_compute_vol_momentum.py

arbitrage:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) scripts/04_gold_arbitrage_research.py

validate:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m quant_assignment.validation

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q

all: discover parse-pcap spread features arbitrage validate test
