.PHONY: bootstrap build test demo

bootstrap:
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }
	@command -v vhs >/dev/null 2>&1 || { echo "Installing vhs..."; brew install vhs; }
	uv sync --dev

build:
	uv build

test:
	uv run pre-commit run --all-files
	uv run pytest tests/ -v

demo:
	@command -v vhs >/dev/null 2>&1 || { echo "VHS not installed. Run 'make bootstrap' first."; exit 1; }
	cd docs && vhs demo.tape
	@echo "Generated docs/demo.gif"
