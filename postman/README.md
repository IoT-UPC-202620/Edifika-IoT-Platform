# Colección Postman de Edifika IoT Platform

Colección oficial de Postman v2.1 y variables de entorno para consumir y validar todos los endpoints de la plataforma IoT de Edifika a través del API Gateway (`http://localhost:8080/api/v1`).

Respalda el hito **H5** de la hoja de ruta (`docs/superpowers/plans/2026-10-23-plan4-gateway-routes-and-docs.md`) y cubre el 100 % de los contratos REST descritos en `docs/superpowers/specs/2026-10-23-iot-contracts.md` (§4.2, §5 y §6).

## Archivos

- `Edifika-IoT.postman_collection.json`: Colección completa v2.1 con 10 carpetas y 37 requests.
- `Edifika-IoT.local.postman_environment.json`: Variables de entorno para ejecución local.

## Estructura de carpetas

| Carpeta | Descripción | Autenticación |
|---|---|---|
| `00 Auth` | Login de administrador y residente en IAM (`/authentication/sign-in`) para poblar `token` y `residentToken` | Pública (`noauth`) |
| `01 Gateways` | Registro, listado, detalle y rotación de API key de edge gateways | Bearer (`token` admin) |
| `02 Devices` | Registro, listado, detalle, actualización, mantenimiento y decommission de dispositivos | Bearer (`token` admin) |
| `03 Credentials` | Creación de credenciales RFID, listado y actualización de estado | Bearer (`token` admin) |
| `04 Reservations & Guests` | Disponibilidad, reserva de puerta, gestión de autorizaciones/invitados y cancelación | Bearer (`token` admin / residente) |
| `05 LED` | Cambio de color del LED RGB (comando asíncrono 202) y consulta de estado del comando | Bearer (`token` titular / admin) |
| `06 Me (residente)` | Vista personal del residente: puertas asignadas, tarjetas RFID, reservas e historial | Bearer (`residentToken`) |
| `07 Audit & Debts` | Auditoría de accesos físicos, estado de morosidad y verificación forzada de deudas | Bearer (`token` admin) |
| `08 Telemetry` | Listado de nodos, última telemetría (`latest`), series de lecturas y alertas | Bearer (`token`) |
| `09 Edge sync` | Endpoint de sincronización de caché para el Edge Gateway con headers `X-Gateway-Id` y `Authorization: Bearer <apiKey>` | Header `Authorization: Bearer {{apiKey}}` |

## Variables de Entorno

La colección no contiene secretos ni tokens hardcodeados. Utiliza variables parametrizadas:

| Variable | Descripción | Valor por defecto local |
|---|---|---|
| `baseUrl` | URL base del API Gateway | `http://localhost:8080/api/v1` |
| `adminEmail` | Correo de usuario administrador | `admin@edifika.com` |
| `adminPassword` | Contraseña del administrador | `AdminPassword123!` |
| `residentEmail` | Correo de usuario residente | `residente@edifika.com` |
| `residentPassword` | Contraseña del residente | `ResidentPassword123!` |
| `token` | Token JWT obtenido tras sign-in admin | (Auto-poblado en test o pre-request) |
| `residentToken` | Token JWT obtenido tras sign-in residente | (Auto-poblado en test o pre-request) |
| `gatewayId` | Identificador numérico del edge gateway | `1` |
| `gatewayCode` | Código del gateway | `edge-gateway-01` |
| `apiKey` | API Key secreta del gateway | (Auto-poblado al crear/rotar gateway) |
| `deviceId` | Identificador numérico del dispositivo IoT | `3` |
| `deviceCode` | Código del dispositivo IoT | `esp32-acc-01` |
| `credentialId` | Identificador de credencial RFID | `9` |
| `reservationId` | Identificador de la reserva de puerta | `7` |
| `commandId` | Identificador UUID de orden/comando | `5b0e1111222233334444555566667777` |
| `residentUserId` | ID de usuario del residente | `15` |
| `guestUserId` | ID de usuario del invitado | `16` |

## Ejecución con Newman

Para validar sintaxis y formato de la colección:

```bash
npx --yes newman@6 run postman/Edifika-IoT.postman_collection.json --folder "00 Auth" -e postman/Edifika-IoT.local.postman_environment.json --bail
```

Para correr la suite completa con los servicios levantados:

```bash
npx --yes newman@6 run postman/Edifika-IoT.postman_collection.json -e postman/Edifika-IoT.local.postman_environment.json
```

## Validación automatizada por tests

La cobertura completa de los endpoints del contrato se verifica mediante el test automatizado en Python:

```bash
.venv/Scripts/python -m pytest -v tests/test_postman_collection.py
```
