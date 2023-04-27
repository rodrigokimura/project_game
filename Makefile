run:
	@pipenv run python src/main.py

dev:
	@export DEBUG=1 && pipenv run python src/main.py

lint:
	@pipenv run black .
	@pipenv run isort .

test:
	@pipenv run pytest

clear:
	@pipenv run python src/main.py --action clear_db
