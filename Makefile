.PHONY = run-dev

run-dev:
	docker compose up app --build

stop:
	docker compose stop
 
test:
	@if test -n "$(NAME)" && test -n "$(MODS)"; then \
		echo "Error! Can't specify both NAME and PATH"; \
	elif test -n "$(NAME)"; then \
		poetry run pytest -vv -s -k "$(NAME)"; \
	elif test -n "$(MODS)"; then \
		echo "$(MODS)"; \
		poetry run pytest -vv -s "$(MODS)"; \
	else \
		docker compose up test; \
	fi

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

update_db: revision migrate

coverage:
	poetry run coverage report -m
