export PYGAME_HIDE_SUPPORT_PROMPT := 1

run:
	@pipenv run python src/main.py

dev:
	@export DEBUG=1 && pipenv run python src/main.py

sound:
	@pipenv run python src/main.py --action=sound

lint:
	@pipenv run black .
	@pipenv run isort .
	@pipenv run pylint src --output-format=colorized

test:
	@pipenv run pytest --cov -s --cov-report html --cov-report term

cov:
	@xdg-open htmlcov/index.html

clear:
	@pipenv run python src/main.py --action clear_db
	@rm player_db
	@rm world_db
