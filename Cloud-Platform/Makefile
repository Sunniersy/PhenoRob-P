PROJECT_NAME ?= robot-cloud-demo
STACK = PROJECT_NAME=$(PROJECT_NAME) ./scripts/docker_stack.sh

.PHONY: docker-up docker-down docker-reset docker-logs docker-ps docker-restart docker-rebuild \
	docker-smoke docker-cold-smoke docker-test-backend docker-test-frontend docker-clean \
	docker-demo-reset-admin docker-pull-base-images frontend-build test check

docker-up:
	$(STACK) up

docker-down:
	$(STACK) down

docker-reset:
	$(STACK) reset

docker-logs:
	$(STACK) logs

docker-ps:
	$(STACK) ps

docker-restart:
	$(STACK) restart

docker-rebuild:
	$(STACK) rebuild

docker-smoke:
	$(STACK) smoke

docker-cold-smoke:
	$(STACK) cold-smoke

docker-test-backend:
	$(STACK) test-backend

docker-test-frontend:
	$(STACK) test-frontend

frontend-build:
	$(STACK) frontend-build

docker-clean:
	$(STACK) clean

docker-demo-reset-admin:
	$(STACK) demo-reset-admin

docker-pull-base-images:
	$(STACK) pull-base-images

test:
	$(STACK) test

check:
	$(STACK) check
