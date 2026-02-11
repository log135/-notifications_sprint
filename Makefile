SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE := docker compose --env-file .env -f infra/docker-compose.yml

API_URL ?= http://localhost:18100
MAILPIT_URL ?= http://localhost:18025
API_V1_PREFIX ?= /api/v1

API_SVC ?= notifications-api
WORKER_SVC ?= notifications-worker
SCHEDULER_SVC ?= campaign-scheduler
DB_SVC ?= notifications-db
KAFKA_SVC ?= kafka
MAILPIT_SVC ?= mailpit

help:
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

install-dev:
	pip install -r requirements.txt -r requirements-dev.txt

up:
	$(COMPOSE) up -d

up-build:
	$(COMPOSE) up -d --build

build:
	$(COMPOSE) build

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f --tail=200

logs-api:
	$(COMPOSE) logs -f --tail=200 $(API_SVC)

logs-worker:
	$(COMPOSE) logs -f --tail=200 $(WORKER_SVC)

logs-scheduler:
	$(COMPOSE) logs -f --tail=200 $(SCHEDULER_SVC)

docs:
	@echo "$(API_URL)/docs"

mailpit:
	@echo "$(MAILPIT_URL)"

health:
	@curl -sS $(API_URL)/health && echo

ready:
	@curl -sS $(API_URL)/ready && echo

health-all:
	@$(COMPOSE) ps --format "table {{.Name}}\t{{.State}}\t{{.Health}}"

sh-api:
	$(COMPOSE) exec $(API_SVC) bash

sh-worker:
	$(COMPOSE) exec $(WORKER_SVC) bash

sh-scheduler:
	$(COMPOSE) exec $(SCHEDULER_SVC) bash

psql:
	$(COMPOSE) exec $(DB_SVC) psql -U $$POSTGRES_USER -d $$POSTGRES_DB

kafka-topics:
	$(COMPOSE) exec $(KAFKA_SVC) bash -lc 'kafka-topics.sh --bootstrap-server localhost:9092 --list'

test-local:
	pytest -q

lint:
	ruff check .

fmt-check:
	ruff format --check .

fmt:
	ruff format .

test-e2e:
	$(COMPOSE) run --rm notifications-api-tests
	$(COMPOSE) run --rm notifications-worker-tests
	$(COMPOSE) run --rm notifications-campaign-scheduler-tests

test:
	$(COMPOSE) run --rm notifications-api-tests
	$(COMPOSE) run --rm notifications-worker-tests
	$(COMPOSE) run --rm notifications-campaign-scheduler-tests

ci: lint test

demo:
	@set -e; \
	API="$(API_URL)"; \
	MAIL="$(MAILPIT_URL)"; \
	EVENT_ID="$$(python -c "import uuid; print(uuid.uuid4())")"; \
	USER_ID="$$(python -c "import uuid; print(uuid.uuid4())")"; \
	echo "Creating template (welcome_email / en / email)..."; \
	curl -s -X POST "$$API/api/v1/templates" \
	  -H "Content-Type: application/json" \
	  -d '{"template_code":"welcome_email","locale":"en","channel":"email","subject":"Welcome!","body":"Registered via: {registration_channel}\nUser-Agent: {user_agent}"}' | cat; \
	echo ""; \
	echo "Publishing event user_registered..."; \
	curl -s -X POST "$$API/api/v1/events" \
	  -H "Content-Type: application/json" \
	  -d "$$(printf '%s' '{"event_id":"'"$$EVENT_ID"'","event_type":"user_registered","source":"demo","occurred_at":"2026-02-04T12:00:00Z","payload":{"user_id":"'"$$USER_ID"'","registration_channel":"web","locale":"en","user_agent":"make-demo"}}')" | cat; \
	echo ""; \
	echo "Expected recipient email (demo mode): user-$$USER_ID@example.com"; \
	echo "Now check Mailpit: $$MAIL"
