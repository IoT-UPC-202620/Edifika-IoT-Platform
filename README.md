# Edifika-IoT-Platform

Local IoT platform infrastructure (RabbitMQ, Eclipse Mosquitto, TimescaleDB/PostgreSQL) and versioned communication contracts (JSON Schema draft 2020-12, examples, and pytest validation suite) for the Edifika IoT ecosystem.

## Components

- **RabbitMQ 4:** Event bus (`edifika.events`), command routing (`edifika.edge.commands`), and dead-letter exchange (`edifika.dlx`).
- **Eclipse Mosquitto 2:** MQTT broker on port 1883 for edge nodes (ESP32).
- **TimescaleDB (PostgreSQL 17):** Persistence for `access_db` and `telemetry_db`.
- **Contracts:** JSON Schemas and examples under `contracts/` defining MQTT, sync, AMQP, and REST contracts.
