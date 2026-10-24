# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-24

### Added
- Local Docker Compose stack with RabbitMQ 4, Eclipse Mosquitto 2, and TimescaleDB (PostgreSQL 17).
- RabbitMQ definitions with `edifika.events`, `edifika.edge.commands`, and `edifika.dlx` durable topic exchanges.
- Versioned IoT communication contracts v1 in JSON Schema (Draft 2020-12) covering:
  - AMQP Integration Envelope
  - Cache Sync Snapshot
  - Domain and Edge Payloads (16 event/command schemas)
  - MQTT Node Messages (heartbeat, access, readings, ack, command)
  - REST Access Management Resources and Requests
  - REST Telemetry Resources
  - REST Error Resource
- Full test suite in pytest validating 100% of contract examples against schemas.
