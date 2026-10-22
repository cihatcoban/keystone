PYTHON ?= python3

.PHONY: help validate triggers test adapters adapters-check env-check lint all new stats hooks agents-doctor evals-live

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN{FS=":.*?## "}{printf "\033[36m%-15s\033[0m %s\n",$$1,$$2}'

validate: ## Structure, manifests, adapters, catalog budget, contract parity, evals
	@$(PYTHON) scripts/validate_repo.py

triggers: ## Static routing check on eval prompts
	@$(PYTHON) scripts/check_triggers.py

test: ## Unit tests for Keystone's own tooling
	@$(PYTHON) -m unittest discover -s scripts/tests -t . -q

adapters: ## Regenerate Gemini CLI commands from commands/*.md
	@$(PYTHON) scripts/build_adapters.py

adapters-check: ## Fail if generated adapters are stale
	@$(PYTHON) scripts/build_adapters.py --check

env-check: ## Secret and .env hygiene for this repository
	@$(PYTHON) scripts/check_env.py --strict

lint: ## Markdown lint
	@npx --yes markdownlint-cli2@0.22.1

all: validate triggers test adapters-check env-check ## Everything CI runs

evals-live: ## Optional, calls a model: skill compliance via a real CLI (ARGS="--cli claude --limit 1")
	@$(PYTHON) scripts/evals_live.py $(or $(ARGS),--cli claude)

agents-doctor: ## Which agent CLIs are installed, and their versions
	@for c in claude gemini codex; do \
	  printf "%-7s " $$c; command -v $$c >/dev/null && $$c --version 2>/dev/null | head -1 || echo "not installed"; \
	done

new: ## Scaffold a skill: make new NAME=my-skill CAT=architect
	@$(PYTHON) scripts/new_skill.py $(NAME) --category $(or $(CAT),build)

stats: ## Skill sizes
	@wc -w skills/*/SKILL.md | sort -n

hooks: ## Install pre-commit hooks
	@pre-commit install
