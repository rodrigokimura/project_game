run:
	@pipenv run python src/main.py

lint:
	@pipenv run black .
	@pipenv run isort .
