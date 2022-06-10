.PHONY: clean-pyc

build: clean-pyc
	docker-compose build swish-crawler-build

run: build clean-container
	docker-compose up -d swish-crawler-run

ssh:
	docker-compose exec swish-crawler-run bash

clean-pyc:
	# clean all pyc files
	find . -name '__pycache__' | xargs rm -rf | cat
	find . -name '*.pyc' | xargs rm -f | cat

clean-container:
	# stop and remove useless containers
	docker-compose down --remove-orphans
