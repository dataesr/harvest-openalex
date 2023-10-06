CURRENT_VERSION=$(shell cat project/__init__.py | cut -d "'" -f 2)
DOCKER_IMAGE_NAME=dataesr/harvest-openalex
GHCR_IMAGE_NAME=ghcr.io/$(DOCKER_IMAGE_NAME)

docker-build:
	@echo Building a new docker image
	docker build -t $(DOCKER_IMAGE_NAME):$(CURRENT_VERSION) -t $(DOCKER_IMAGE_NAME):latest .
	@echo Docker image built

docker-push:
	@echo Pushing a new docker image
	docker tag $(DOCKER_IMAGE_NAME) $(GHCR_IMAGE_NAME):$(CURRENT_VERSION)
	docker tag $(DOCKER_IMAGE_NAME) $(GHCR_IMAGE_NAME):latest
	docker push $(GHCR_IMAGE_NAME):$(CURRENT_VERSION)
	docker push $(GHCR_IMAGE_NAME):latest
	@echo Docker image pushed

install:
	@echo Installing dependencies...
	pip install -r requirements.txt
	@echo End of dependencies installation

release:
	echo "__version__ = '$(VERSION)'" > project/__init__.py
	git commit -am '[release] version $(VERSION)'
	git tag $(VERSION)
	@echo If everything is OK, you can push with tags i.e. git push origin main --tags
