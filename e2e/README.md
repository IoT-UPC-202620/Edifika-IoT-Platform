# End-to-End Testing Environment (H4)

This directory contains configuration, WireMock stubs, and documentation for the complete Edifika IoT end-to-end integration stack.

## Architecture

The end-to-end stack orchestrates all components of the IoT platform:
1. **Infrastructure**:
   - RabbitMQ (`5672`, `15672`)
   - Mosquitto MQTT (`1883`)
   - PostgreSQL / TimescaleDB (`5432`)
2. **External Dependencies (Mocks)**:
   - WireMock (`8099`, container `8080`): Stubs for Residential Management (`/api/v1/residential/...`) and Payment (`/api/v1/payments/...`).
3. **Core Backend Services**:
   - `access`: IoT Access Management (`8089`)
   - `telemetry`: IoT Telemetry (`8090`)
   - `api-gateway`: Spring Cloud Gateway (`8080`) routing all public and internal IoT requests.
4. **Edge Layer**:
   - `edge-gateway`: Flask/Peewee Edge Gateway (`8000`)
   - `sim-door`: ESP32 door node simulator (or controllable MQTT test node)

## Seed Data

- Building: `12`
- Edge Gateway: `edge-gateway-01`
- Door Device: `esp32-acc-01`
- Residents & Units:
  - User `15` (Holder, up to date) -> Unit `40` -> Card `04A1B2C3`
  - User `16` (Guest, up to date) -> Unit `41` -> Card `04A1B2C4`
  - User `17` (Resident, up to date) -> Unit `42` -> Card `04A1B2C5`
  - User `18` (Delinquent) -> Unit `43` -> Card `04A1B2C6`

## WireMock Mappings

- `residents-building-12.json`: Active residents 15, 16, 17, 18 in building 12.
- `debts-default.json`: Default empty list `[]` for `/api/v1/payments/debts/unit/*` (priority 10). Dynamic debt scenarios are configured via WireMock admin API (`POST http://localhost:8099/__admin/mappings`).

## Usage

Validate configuration:
```bash
docker compose -f docker-compose.e2e.yml config
```

Start the stack:
```bash
docker compose -f docker-compose.e2e.yml up -d --wait --wait-timeout 300 rabbitmq mosquitto postgres wiremock access telemetry api-gateway
```

Stop and clean up:
```bash
docker compose -f docker-compose.e2e.yml down -v
```
