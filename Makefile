SHELL := /bin/zsh

VENV ?= 3.11_venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYINSTALLER := $(VENV)/bin/pyinstaller
CLI_BIN := dist/CompliSenseCLI
AGENT_CACHE_DIR := /tmp/complisense_agents
PYI_CACHE_DIR := .pyinstaller-cache

.PHONY: help ensure-venv install-deps build-cli build-cli-clean clean-agent-cache smoke-cli-all smoke-cli-compiled refresh-agent-bundles

help:
	@echo "Available targets:"
	@echo "  make refresh-agent-bundles  # rebuild CLI, clear cached zips, run 4-pack smoke tests"
	@echo "  make build-cli              # build dist/CompliSenseCLI"
	@echo "  make build-cli-clean        # clean build (uses pyinstaller --clean)"
	@echo "  make clean-agent-cache      # remove generated bundle cache (/tmp/complisense_agents)"
	@echo "  make smoke-cli-all          # validate all 4 rulepacks via python -m agent.cli"
	@echo "  make smoke-cli-compiled     # validate all 4 rulepacks via dist/CompliSenseCLI"

ensure-venv:
	@test -x "$(PYTHON)" || (echo "Missing $(PYTHON). Create it with: python3.11 -m venv $(VENV)"; exit 1)

install-deps: ensure-venv
	$(PIP) install -r requirements.txt

build-cli: install-deps
	mkdir -p "$(PYI_CACHE_DIR)"
	PYINSTALLER_CONFIG_DIR="$(PWD)/$(PYI_CACHE_DIR)" $(PYINSTALLER) -y packaging/CompliSenseCLI.spec
	@test -x "$(CLI_BIN)" || (echo "Build failed: $(CLI_BIN) not found"; exit 1)
	@echo "Built $(CLI_BIN)"

build-cli-clean: install-deps
	mkdir -p "$(PYI_CACHE_DIR)"
	PYINSTALLER_CONFIG_DIR="$(PWD)/$(PYI_CACHE_DIR)" $(PYINSTALLER) --clean -y packaging/CompliSenseCLI.spec
	@test -x "$(CLI_BIN)" || (echo "Build failed: $(CLI_BIN) not found"; exit 1)
	@echo "Built $(CLI_BIN)"

clean-agent-cache:
	rm -rf "$(AGENT_CACHE_DIR)"
	@echo "Cleared agent bundle cache: $(AGENT_CACHE_DIR)"

smoke-cli-all: build-cli
	$(PYTHON) -m agent.cli scan --root artefacts --out /tmp/check_euai_core_v1 --pack-id euai_core_v1 --no-pdf
	$(PYTHON) -m agent.cli scan --root artefacts --out /tmp/check_euai_extended_v1 --pack-id euai_extended_v1 --no-pdf
	$(PYTHON) -m agent.cli scan --root sample_artefacts/dpdp_india --out /tmp/check_dpdp_india_core_v1 --pack-id dpdp_india_core_v1 --no-pdf
	$(PYTHON) -m agent.cli scan --root sample_artefacts/dpdp_india --out /tmp/check_dpdp_india_extended_v1 --pack-id dpdp_india_extended_v1 --no-pdf
	@echo "All 4 pack smoke tests passed (python module path)."

smoke-cli-compiled: build-cli
	$(CLI_BIN) scan --root artefacts --out /tmp/check_euai_core_v1 --pack-id euai_core_v1 --no-pdf
	$(CLI_BIN) scan --root artefacts --out /tmp/check_euai_extended_v1 --pack-id euai_extended_v1 --no-pdf
	$(CLI_BIN) scan --root sample_artefacts/dpdp_india --out /tmp/check_dpdp_india_core_v1 --pack-id dpdp_india_core_v1 --no-pdf
	$(CLI_BIN) scan --root sample_artefacts/dpdp_india --out /tmp/check_dpdp_india_extended_v1 --pack-id dpdp_india_extended_v1 --no-pdf
	@echo "All 4 pack smoke tests passed (compiled CLI path)."

refresh-agent-bundles: build-cli clean-agent-cache smoke-cli-all
	@echo "CLI rebuilt, cache cleared, and smoke tests passed."
	@echo "Now download/generate agent zip again from SaaS."
