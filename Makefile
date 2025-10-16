# Collapse System Logic (CSL) — MUI Makefile

PY = python
MAIN = mathematical_proof_system.py
CSLX = $(MAIN).cslx

all: info pack unpack run

compile:
	$(PY) -m py_compile $(MAIN)

info:
	$(PY) CSL-PyKernel/csl_any_collapse.py $(MAIN) --info

pack:
	$(PY) CSL-PyKernel/csl_any_collapse.py $(MAIN) --pack

unpack:
	$(PY) CSL-PyKernel/csl_any_collapse.py $(CSLX) --unpack

run:
	/usr/bin/time -l $(PY) -u $(MAIN)

clean:
	rm -f $(CSLX) $(CSLX).cslx
	rm -rf __pycache__
