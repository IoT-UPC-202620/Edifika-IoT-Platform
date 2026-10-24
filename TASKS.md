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
