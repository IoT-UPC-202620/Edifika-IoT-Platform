# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Device discovery contracts: MQTT `announce` channel and `identify` command, `DeviceDiscovered` edge event (`edge.device-discovered`), `DiscoveredDeviceResource`, `AdoptDeviceRequest` and the `/iot/discovered-devices` endpoints, plus the discovery and adoption flow (section 1.4).
- Card enrollment contracts: MQTT `enrollment` channel and `enroll` command, `CardEnrolled` edge event (`edge.card-enrolled`, bound to `access.edge-events`), `CardEnrollmentResource` and the `/iot/devices/{id}/enrollment` endpoints.
- `POST /access/credentials` reassigns a `REVOKED` or `LOST` card to the new holder instead of answering 409.

## [0.2.0] - 2026-10-24

### Added
- End-to-end integration compose stack (`docker-compose.e2e.yml`) orchestrating RabbitMQ, Mosquitto, TimescaleDB, WireMock, IoT Access Management, IoT Telemetry, ApiGateway, and Edge Gateway.
- WireMock stubs for Residential (`/api/v1/residents?buildingId=12`) and Payment (`/api/v1/payments/debts/unit/*`) services.
- Integration test suite fixtures in `integration-tests/support/` covering:
  - HS256 JWT generator for user and admin claims.
  - REST client with automatic auth headers through ApiGateway.
  - Virtual ESP32 MQTT node speaking firmware dialect v1 with background heartbeat.
  - AMQP event spy consuming from `edifika.events`.
  - WireMock administrative client for programmatic debt control.
- Full H4 scenario test suite in `integration-tests/test_h4_scenarios.py` validating 7 end-to-end business flows through ApiGateway:
  1. Free access resident up-to-date granted entry.
  2. Delinquent resident denied access and blocked from creating reservations.
  3. Door reservation switching node to RESERVED mode.
  4. Access control during reservation allowing only holder and authorized guests.
  5. RGB LED control by reservation holder with non-holder rejection (403).
  6. Reservation ending offline with local gateway restoring FREE_ACCESS.
  7. Sensor telemetry ingestion and query via REST API.

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
