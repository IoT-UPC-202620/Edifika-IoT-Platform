# Edifika IoT Platform — Milestones

| Hito | Fecha | Métrica | Comando | Resultado | Pendientes |
|---|---|---|---|---|---|
| H0 (Infra) | 2026-10-24 | `up --wait` < 120 s | `docker compose down -v; docker compose up -d --wait --wait-timeout 120` | 11.5 s (healthy: rabbitmq, mosquitto, postgres; 3 exchanges topic/durable; timescaledb) | — |
| H0 (Contratos) | 2026-10-24 | 100% ejemplos válidos contra schemas (53 tests) | `.venv/Scripts/python -m pytest -v` | 53 passed in 0.39s | Ninguno (H0 cerrado) |
| H5 (Rutas y Docs) | 2026-10-24 | Rutas con tests; nota de obsoleto en wokwi/README.md; colección cubre 100% endpoints del contrato (§4.2, §5, §6) | `.venv/Scripts/python -m pytest -v tests/test_postman_collection.py` | 2 passed in 0.01s (55 passed full suite); newman parse valid (ECONNREFUSED as expected) | Ninguno (H5 cerrado) |
