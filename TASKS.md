# Edifika-IoT-Platform — Task Progress

## Task 1 — Infraestructura local   [x] hecha
- Rama: feature/H0-local-infrastructure
- Paso actual: Step 6 — Commit and merge to develop
- Archivos tocados: .gitignore, README.md, TASKS.md, docker-compose.yml, infra/rabbitmq/*, infra/mosquitto/*, infra/postgres/init/*, .env.example, MILESTONES.md
- Tests: docker compose down -v; up -d --wait (11.5s, all healthy); rabbitmqctl list_exchanges (3 topic durable exchanges); timescaledb extension verified
- Último commit: chore(infra): local RabbitMQ, Mosquitto and TimescaleDB stack (H0)
- Métricas: up --wait 11.5s (< 120s)
- Bloqueos / notas: stack saludable y verificado

## Task 2 — Contratos como JSON Schema   [x] hecha
- Rama: feature/H0-contracts-schemas
- Paso actual: Step 5 — Commit and merge to develop
- Archivos tocados: contracts/README.md, contracts/schemas/**, contracts/examples/**, requirements-dev.txt, tests/test_contracts.py, MILESTONES.md, TASKS.md
- Tests: .venv/Scripts/python -m pytest -v (53 passed in 0.39s)
- Último commit: docs(contracts): v1 JSON schemas for MQTT, AMQP, sync and REST (H0)
- Métricas: 53 tests passed (47 schema validations, 16 envelope validations, enum & timezone checks)
- Bloqueos / notas: H0 completado con éxito

## Task 3 — Colección Postman de la API para la app móvil   [x] hecha
- Rama: feature/H5-postman-collection
- Paso actual: Step 5 — Commit and merge to develop
- Archivos tocados: tests/test_postman_collection.py, postman/Edifika-IoT.postman_collection.json, postman/Edifika-IoT.local.postman_environment.json, postman/README.md, MILESTONES.md, TASKS.md
- Tests: .venv/Scripts/python -m pytest -v (55 passed in 0.35s); npx newman@6 parse valid (ECONNREFUSED on localhost:8080 as expected)
- Último commit: docs(postman): full IoT API collection for the mobile app (H5)
- Métricas: Colección cubre 100% endpoints del contrato (36/36 endpoints en §4.2, §5, §6), 0 secretos hardcodeados
- Bloqueos / notas: H5 completado con éxito

## Task 4 (Plan 5 Task 1) — Compose de punta a punta   [x] hecha
- Rama: feature/H4-e2e-compose
- Paso actual: Step 3 — Commit and merge to develop
- Archivos tocados: docker-compose.e2e.yml, e2e/wiremock/mappings/residents-building-12.json, e2e/wiremock/mappings/debts-default.json, e2e/README.md, TASKS.md
- Tests: docker compose -f docker-compose.e2e.yml build (OK); docker compose -f docker-compose.e2e.yml up -d --wait (all 7 services healthy)
- Último commit: chore(e2e): end-to-end compose with services, gateway, simulator and WireMock stubs (H4)
- Métricas: 7/7 servicios saludables (rabbitmq, mosquitto, postgres, wiremock, access, telemetry, api-gateway)
- Bloqueos / notas: ninguno

## Task 5 (Plan 5 Task 2) — Fixtures del suite   [ ] pendiente
- Rama: feature/H4-e2e-fixtures
- Paso actual: pendiente
- Archivos tocados: pendiente
- Tests: pendiente
- Último commit: pendiente
- Métricas: pendiente
- Bloqueos / notas: ninguno

## Task 6 (Plan 5 Task 3) — Los 7 escenarios de H4   [ ] pendiente
- Rama: feature/H4-scenarios
- Paso actual: pendiente
- Archivos tocados: pendiente
- Tests: pendiente
- Último commit: pendiente
- Métricas: pendiente
- Bloqueos / notas: ninguno
