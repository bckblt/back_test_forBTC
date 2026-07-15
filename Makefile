CXXFLAGS = -std=c++98

VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

.PHONY: run setup clean

run:
	$(PYTHON) main.py

setup: $(VENV)/bin/activate
	$(PIP) install pandas pandas-ta

$(VENV)/bin/activate:
	python3 -m venv $(VENV)

clean:
	rm -rf __pycache__ $(VENV)