# Edifika IoT Platform — Milestones

| Hito | Fecha | Métrica | Comando | Resultado | Pendientes |
|---|---|---|---|---|---|
| H0 (Infra) | 2026-10-24 | `up --wait` < 120 s | `docker compose down -v; docker compose up -d --wait --wait-timeout 120` | 11.5 s (healthy: rabbitmq, mosquitto, postgres; 3 exchanges topic/durable; timescaledb) | Contratos como JSON Schema (Task 2) |
