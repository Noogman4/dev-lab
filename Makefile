.PHONY: setup format lint test check run clean roots-guard-smoke roots-guard-checks site-serve site-open site-stop site-print-caddy site-print-htaccess site-print-minisign site-build site-release-update print-netmon-sha256

VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

setup:
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
	$(PIP) install black ruff pytest

format:
	$(PYTHON) -m black .

lint:
	$(PYTHON) -m ruff check .

test:
	$(PYTHON) -m pytest

check:
	$(PYTHON) -m black --check .
	$(PYTHON) -m ruff check .
	$(PYTHON) -m pytest

run:
	$(PYTHON) -m netmon

roots-guard-smoke:
	bash scripts/run_roots_guard_smoke.sh

roots-guard-checks:
	bash scripts/run_roots_guard_checks.sh

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
	sha256sum dist/netmon_1.1.16_all.deb

clean:
	rm -rf $(VENV) .pytest_cache __pycache__
