.PHONY = run-dev

run-dev:
	poetry run uvicorn src.web.server:app --reload

test:
	poetry run pytest -vv -s

migrate:
	poetry run alembic check || poetry run alembic upgrade head

revision:
	@if test -z "$(NAME)"; then \
		echo "Please provide revision message using NAME variable."; \
		exit 1; \
	fi
	poetry run alembic revision --autogenerate -m "$(NAME)"

downgrade:
	poetry run alembic downgrade -1

push_db: revision migrate

