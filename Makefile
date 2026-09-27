.PHONY: setup format format-check lint test check run clean roots-guard-smoke roots-guard-checks security-audit-pdf site-serve site-open site-stop site-print-caddy site-print-htaccess site-print-minisign site-build site-release-update print-netmon-sha256

VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

setup:
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
	$(PIP) install black ruff pytest

format:
	PYTHON_BIN=$(PYTHON) bash scripts/run_black_filewise.sh $(FILES)

format-check:
	PYTHON_BIN=$(PYTHON) bash scripts/run_black_filewise.sh --check $(FILES)

lint:
	$(PYTHON) -m ruff check .

test:
	$(PYTHON) -m pytest

check:
	PYTHON_BIN=$(PYTHON) bash scripts/run_black_filewise.sh --check
	$(PYTHON) -m ruff check .
	$(PYTHON) -m pytest

run:
	$(PYTHON) -m netmon

roots-guard-smoke:
	bash scripts/run_roots_guard_smoke.sh

roots-guard-checks:
	bash scripts/run_roots_guard_checks.sh

security-audit-pdf:
	$(PYTHON) scripts/build_security_audit_pdf_r12.py

site-serve:
	python3 -m http.server 8765

site-open:
	bash scripts/open_netmon_site.sh

site-stop:
	bash scripts/stop_netmon_site.sh

site-print-caddy:
	sed -n '1,220p' site/Caddyfile

site-print-htaccess:
	sed -n '1,220p' site/.htaccess

site-print-minisign:
	sed -n '1,240p' docs/MINISIGN_RELEASES.md

site-build:
	bash scripts/build_netmon_site_bundle.sh

site-release-update:
	bash scripts/build_netmon_release_update_bundle.sh

print-netmon-sha256:
	sha256sum dist/netmon_1.1.21_all.deb

clean:
	rm -rf $(VENV) .pytest_cache __pycache__
