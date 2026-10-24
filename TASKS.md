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
