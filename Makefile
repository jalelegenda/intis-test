.PHONY = run-dev

run-dev:
	poetry run uvicorn src.entrypoint.server:app --reload
