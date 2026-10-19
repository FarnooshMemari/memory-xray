# Convenience targets. Every target is a plain Python command (see README) and needs no GPU.
PYTHON ?= python3

.PHONY: help install install-dev test verify reproduce reanalyze figures key-numbers clean

help:
	@echo "make install      core CPU requirements (results, analysis, figures, most tests)"
	@echo "make install-dev  + PyTorch/transformers for the tiny-model tests and notebook tooling"
	@echo "make test         run the test suite"
	@echo "make verify       verify the release from the distributed files (about 30 s)"
	@echo "make reproduce    regenerate results/*.json in place (byte-identical with Python >= 3.12 on x86-64)"
	@echo "make reanalyze    recompute pipeline checks for the full run into outputs/"
	@echo "make figures      redraw publication and poster figures (report figures in results/figures/ are left as is)"
	@echo "make key-numbers  regenerate poster_materials/KEY_NUMBERS.md"
	@echo "make clean        remove outputs/ and caches"

install:
	$(PYTHON) -m pip install -r requirements.txt

install-dev:
	$(PYTHON) -m pip install -r requirements-dev.txt

test:
	$(PYTHON) -m pytest -q

verify:
	$(PYTHON) scripts/verify_release.py

reproduce:
	$(PYTHON) analysis_full/independent_reanalysis.py
	$(PYTHON) analysis_full/report_numbers.py
	$(PYTHON) analysis_full/content_only_baseline.py

reanalyze:
	$(PYTHON) reanalyze.py runs/full_20261017T223452Z

figures:
	$(PYTHON) analysis_full/export_figures.py
	$(PYTHON) analysis_full/poster_figures.py

key-numbers:
	$(PYTHON) scripts/make_key_numbers.py

clean:
	rm -rf outputs .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
