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

test:
	@pipenv run pytest --cov -s

clear:
	@pipenv run python src/main.py --action clear_db
	@rm player_db
	@rm world_db
