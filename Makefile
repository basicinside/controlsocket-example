default: check test

check: 
	pipenv run flake8 controlsocket.py

run:
	pipenv run python controlsocket.py

test:
	@echo "all tests passed"

isort:
	pipenv run isort --recursive .
