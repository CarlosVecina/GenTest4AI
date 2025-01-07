.DEFAULT_GOAL := all

.PHONY: all
all: format lint

.PHONY: .uv
.uv: ## Check that uv is installed
	@uv --version || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: .pre-commit
.pre-commit: ## Check that pre-commit is installed
	@pre-commit -V || echo 'Please install pre-commit: https://pre-commit.com/'

.PHONY: format
format:
	uv sync --group lint
	uv run ruff format
	uv run ruff check --fix --fix-only

.PHONY: lint
lint:
	uv sync --group lint
	uv run ruff format --check
	uv run ruff check

.PHONY: install-chronium
install-chronium:
	uv run playwright install chromium

.PHONY: test
test:
	uv sync --group dev
	uv run pytest

.PHONY: local-demo-swagger
local-demo-swagger:
	uv run python ai_api_testing/agents/api_specs_agents/swagger_extractor.py --url https://petstore.swagger.io --endpoints /pet/findByStatus

.PHONY: local-demo-orchestrator
local-demo-orchestrator:
	uv run python ai_api_testing/agents/test_generator_agents/orchestrator.py
