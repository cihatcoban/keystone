.PHONY: help validate triggers lint all new stats hooks

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN{FS=":.*?## "}{printf "\033[36m%-12s\033[0m %s\n",$$1,$$2}'

validate: ## Structure, frontmatter, links, contract parity, eval coverage
	@python3 scripts/validate_repo.py

triggers: ## Static routing check on eval prompts
	@python3 scripts/check_triggers.py

lint: ## Markdown lint
	@npx --yes markdownlint-cli2 >/dev/null 2>&1 || npx --yes markdownlint-cli2

all: validate triggers ## Everything CI runs

new: ## Scaffold a skill: make new NAME=my-skill CAT=architect
	@python3 scripts/new_skill.py $(NAME) --category $(or $(CAT),build)

stats: ## Skill sizes
	@wc -w skills/*/SKILL.md | sort -n

hooks: ## Install pre-commit hooks
	@pre-commit install
