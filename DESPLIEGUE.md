# Despliegue local de Edifika: backend, ESP32 y app móvil

Guía de traspaso para levantar todo el sistema en una PC de desarrollo:

1. El **backend** completo en Docker: infraestructura, microservicios, API Gateway y Edge Gateway.
2. El **firmware del ESP32** apuntando a ese backend.
3. La **app móvil** (Flutter) apuntando a ese backend.

```
 ESP32 ──MQTT :1883──▶ Mosquitto ──▶ Edge Gateway :8000 ──AMQP──▶ RabbitMQ ──▶ microservicios
                                          └──HTTP sync──▶ IoT Access Management :8089
 App móvil / Web ──HTTP──▶ API Gateway :8080 ──▶ microservicios (:8081–8090) ──▶ PostgreSQL :5432
```

## 0. Requisitos

| Herramienta | Para qué |
|---|---|
| Docker Desktop (con Compose v2.20+, por `include:`) | Backend |
| Git | Clonar los repos |
| `arduino-cli` (o Arduino IDE 2) con el core **esp32 3.x** | Firmware |
| Flutter 3.38.x + Android SDK (`adb`) | App móvil |

Todos los repos de la organización `IoT-UPC-202620` deben estar clonados **en la misma carpeta**, porque el compose los construye por ruta relativa (`../<repo>`):

```
iot/
├── Edifika-IoT-Platform/                         ← este repo (compose e infraestructura)
├── Edifika-ApiGateway/
├── Edifika-Microservice-IAM/
├── Edifika-Microservice-Residential-Managemen/
├── Edifika-Microservice-Reservation/
├── Edifika-Microservice-Payment/
├── Edifika-Microservice-Communications/
├── Edifika-Microservice-Forum/
├── Edifika-Microservice-Notification/
├── Edifika-Microservice-Report/
├── Edifika-Microservice-IoT-Access-Management/
├── Edifika-Microservice-IoT-Telemetry/
├── Edifika-Microservice-IoT-Gateway/             ← Edge Gateway (Python)
├── Edifika-MobileApp/
└── esp32/
```

Averigua la **IP local de la PC** en la red Wi-Fi (`ipconfig` en Windows → "Dirección IPv4", p. ej. `192.168.1.50`). La usan el ESP32 y el teléfono físico. En esta guía aparece como `<IP_PC>`.

---

## 1. Backend en Docker

### 1.1 Qué se levanta

Todo está en [`docker-compose.full.yml`](docker-compose.full.yml), que incluye [`docker-compose.yml`](docker-compose.yml) (la infraestructura).

| Servicio | Puerto | Repo | Notas |
|---|---|---|---|
| `postgres` (TimescaleDB, PG 17) | 5432 | este | Crea una base por microservicio (`infra/postgres/init/`) |
| `rabbitmq` | 5672 / 15672 (UI) | este | Usuario `edifika` / `edifika-dev` |
| `mosquitto` | 1883 | este | Broker MQTT para los ESP32, anónimo |
| `api-gateway` | **8080** | Edifika-ApiGateway | Punto de entrada único: `/api/v1/**` |
| `iam` | 8081 | Microservice-IAM | Login y JWT. Crea los usuarios semilla |
| `residential` | 8082 | Microservice-Residential-Managemen | Edificios, unidades, residentes |
| `reservation` | 8083 | Microservice-Reservation | |
| `payment` | 8084 | Microservice-Payment | Culqi opcional (`CULQI_SECRET_KEY`) |
| `communications` | 8085 | Microservice-Communications | Comunicados |
| `forum` | 8086 | Microservice-Forum | |
| `notification` | 8087 | Microservice-Notification | **Perfil `notifications`**: requiere Firebase |
| `report` | 8088 | Microservice-Report | |
| `access` | 8089 | Microservice-IoT-Access-Management | Gateways, dispositivos, tarjetas, sync del edge |
| `telemetry` | 8090 | Microservice-IoT-Telemetry | |
| `edge-gateway` | 8000 | Microservice-IoT-Gateway | **Perfil `edge`**: requiere una API key (paso 1.4) |

Las tablas las crea cada servicio al arrancar (`ddl-auto=update`); no hay migraciones manuales.

### 1.2 Configuración (`.env`)

En `Edifika-IoT-Platform/` copia `.env.example` a `.env`. Los valores por defecto sirven para desarrollo. Variables adicionales que lee el compose completo:

```dotenv
# Comunes (ya en .env.example)
RABBITMQ_USER=edifika
RABBITMQ_PASSWORD=edifika-dev
POSTGRES_USER=edifika
POSTGRES_PASSWORD=edifika-dev

# El mismo secreto para TODOS los servicios: el JWT que firma IAM lo validan los demás
JWT_SECRET=<cadena de al menos 32 caracteres>

# Edge Gateway (se completa en el paso 1.4)
GATEWAY_ID=edge-gateway-01
GATEWAY_API_KEY=

# Opcionales
CULQI_SECRET_KEY=
FIREBASE_CREDENTIALS=          # JSON completo del service account, en una línea
```

> `.env` está en `.gitignore`: nunca lo subas. Ahí va la API key del gateway.

### 1.3 Levantar el backend

```bash
cd Edifika-IoT-Platform
docker compose -f docker-compose.full.yml up -d --build
docker compose -f docker-compose.full.yml ps
docker compose -f docker-compose.full.yml logs -f api-gateway access   # ver arranque
```

La primera vez compila 11 imágenes Maven y tarda varios minutos. Para comprobar que responde:

```bash
curl -s -X POST http://localhost:8080/api/v1/authentication/sign-in \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@edifika.com","password":"Edifika#2026"}'
```

Usuarios semilla de IAM (configurables con `SEED_*`, ver README de IAM):

| Rol | Email | Contraseña |
|---|---|---|
| Admin | `admin@edifika.com` | `Edifika#2026` |
| Propietario | `propietario@edifika.com` | `Edifika#2026` |

> Si `postgres_data` ya existía de antes, el script que crea las bases nuevas **no corre**. En ese caso ejecuta `docker compose -f docker-compose.full.yml down -v`, que borra los datos, y vuelve a levantar.

### 1.4 Registrar el Edge Gateway y arrancarlo

El Edge Gateway se autentica ante Access Management con una API key que solo se entrega **una vez**, al registrarlo. Ese registro necesita un edificio existente.

```bash
# 1) Token de admin
TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/authentication/sign-in \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@edifika.com","password":"Edifika#2026"}' | jq -r .token)

# 2) Edificio (si no existe ya uno creado desde la web o la app)
curl -s -X POST http://localhost:8080/api/v1/residential/buildings \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Torre A","address":"Av. Principal 123","district":"Miraflores","city":"Lima"}'
#    → anota el id del edificio (idBuilding)

# 3) Registrar el gateway. gatewayCode debe ser igual a GATEWAY_ID del .env
curl -s -X POST http://localhost:8080/api/v1/iot/gateways \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"gatewayCode":"edge-gateway-01","buildingId":<idBuilding>,"name":"Gateway Torre A"}'
#    → { "gatewayId": ..., "gatewayCode": "edge-gateway-01", "apiKey": "..." }
```

Copia `apiKey` a `GATEWAY_API_KEY` en `.env` y arranca el gateway:

```bash
docker compose -f docker-compose.full.yml --profile edge up -d edge-gateway
docker compose -f docker-compose.full.yml logs -f edge-gateway     # debe sincronizar sin 401
```

Si se pierde la key, se rota con `POST /api/v1/iot/gateways/{id}/rotate-api-key` y se actualiza el `.env`.

### 1.5 Firewall de Windows

El ESP32 y el teléfono llegan a la PC por la red Wi-Fi. Hay que permitir la entrada a **1883** (MQTT) y **8080** (API Gateway). En PowerShell como administrador:

```powershell
New-NetFirewallRule -DisplayName "Edifika MQTT" -Direction Inbound -Protocol TCP -LocalPort 1883 -Action Allow
New-NetFirewallRule -DisplayName "Edifika API"  -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
```

La red Wi-Fi debe estar marcada como **privada**, y la PC, el ESP32 y el teléfono deben estar en la misma red. Las redes de universidad o de invitados suelen aislar a los clientes entre sí.

### 1.6 Notificaciones push (opcional)

`notification` no arranca sin credenciales de Firebase. Pon el JSON del service account en `FIREBASE_CREDENTIALS` y levántalo:

```bash
docker compose -f docker-compose.full.yml --profile notifications up -d notification
```

Sin este servicio, el resto funciona; solo `/api/v1/notifications` y `/api/v1/device-tokens` devuelven error.

### 1.7 Apagar / reiniciar

```bash
docker compose -f docker-compose.full.yml --profile edge --profile notifications down      # conserva datos
docker compose -f docker-compose.full.yml --profile edge --profile notifications down -v   # borra todo
```

---

## 2. Firmware del ESP32

Repo `esp32/`. Placa **ESP32 Dev Module**, core **esp32 3.x**. Detalle de pines y comportamiento: `esp32/README.md`.

### 2.1 Apuntar al backend

El ESP32 **no** habla con el API Gateway: publica por MQTT en el Mosquitto del paso 1. Solo necesita Wi-Fi y la IP del broker.

```bash
cd esp32
cp src/config/Secrets.example.h src/config/Secrets.h     # Secrets.h está en .gitignore
```

Edita `src/config/Secrets.h`:

```cpp
constexpr const char* WIFI_SSID = "<red Wi-Fi 2.4 GHz>";   // el ESP32 no se conecta a 5 GHz
constexpr const char* WIFI_PASSWORD = "<contraseña>";
constexpr const char* MQTT_BROKER_HOST = "<IP_PC>";        // p. ej. 192.168.1.50, NO "localhost"
constexpr uint16_t MQTT_BROKER_PORT = 1883;
```

En `src/config/NodeConfig.h` deja:

- `UNLOCK_ON_ANY_CARD = false`: la puerta solo abre cuando el gateway valida la tarjeta.
- `DEVICE_ID_OVERRIDE = ""`: el id sale de la MAC (`esp32-xxxxxx`), así un mismo binario sirve para todas las placas.
- `PRESENCE_DEBUG_LOG`: en `true` imprime la distancia del HC-SR04 cada segundo. Ponlo en `false` para producción.

### 2.2 Compilar y flashear

Instalación del core y las librerías (una sola vez):

```bash
arduino-cli config add board_manager.additional_urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core update-index
arduino-cli core install esp32:esp32
arduino-cli lib install ArduinoJson "DHT sensor library" "Adafruit Unified Sensor" "Adafruit SSD1306" \
  "Adafruit GFX Library" MFRC522 "LiquidCrystal I2C" ESP32Servo HX711 PubSubClient
```

Compilar y subir (el puerto se ve con `arduino-cli board list`, p. ej. `COM5`):

```bash
arduino-cli compile -b esp32:esp32:esp32 .
arduino-cli upload  -b esp32:esp32:esp32 -p COM5 .
arduino-cli monitor -p COM5 -c baudrate=115200      # ver logs
```

Con Arduino IDE: abrir `firmware.ino`, elegir *ESP32 Dev Module* y el puerto, y subir. Si el binario no cabe, usar el esquema de partición *Huge APP*.

### 2.3 Comprobar y adoptar el nodo

1. Por serie debe verse la conexión Wi-Fi y la sesión MQTT. Para ver el tráfico en el broker:
   ```bash
   docker exec -it $(docker ps -qf name=mosquitto) mosquitto_sub -t 'edifika/#' -v
   ```
2. Mientras no está adoptado, la OLED muestra **"Sin registrar"** y un **código de 4 dígitos**, y el nodo ignora las tarjetas.
3. En la app móvil (cuenta admin) → **Gestión IoT** → "N dispositivos nuevos" → *Identificar* (el nodo da feedback y así se confirma cuál es) → **Adoptar**.
4. En unos segundos el nodo recibe su configuración, deja de mostrar el código y queda *En línea*.

Para dar de alta tarjetas: Gestión IoT → dispositivo → modo registro → pasar la tarjeta → **Asociar** a un residente.

---

## 3. App móvil (Flutter)

Repo `Edifika-MobileApp/edifika_mobile`. La URL del backend es un único `--dart-define`, `API_BASE_URL` (ver `lib/core/config/app_config.dart`). Siempre termina en `/api/v1` y apunta al **API Gateway (8080)**, nunca a un microservicio directo.

```bash
cd Edifika-MobileApp/edifika_mobile
flutter pub get
```

### 3.1 Qué URL usar

| Dónde corre la app | `API_BASE_URL` |
|---|---|
| Emulador Android | `http://10.0.2.2:8080/api/v1` (`10.0.2.2` es el localhost de la PC) |
| Teléfono físico por USB | `http://localhost:8080/api/v1` + `adb reverse tcp:8080 tcp:8080` |
| Teléfono físico por Wi-Fi | `http://<IP_PC>:8080/api/v1` (requiere el firewall del paso 1.5) |
| Backend publicado | `https://<dominio-api-gateway>/api/v1` |

> **HTTP sin TLS solo funciona en builds *debug*** (`android/app/src/debug/res/xml/network_security_config.xml`). Una build *release* exige `https://`.

> Sin `--dart-define`, la app apunta por defecto a la **fake API** del repo FrontEnd (`http://10.0.2.2:3000/api/v1`), no al backend real.

### 3.2 Ejecutar en desarrollo

```bash
flutter devices                                   # lista emulador / teléfono
flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8080/api/v1

# teléfono por USB (depuración USB activada)
adb reverse tcp:8080 tcp:8080
flutter run -d <id-del-teléfono> --dart-define=API_BASE_URL=http://localhost:8080/api/v1
```

### 3.3 Generar e instalar un APK

Contra el backend local (debug, admite HTTP):

```bash
flutter build apk --debug --dart-define=API_BASE_URL=http://<IP_PC>:8080/api/v1
adb install -r build/app/outputs/flutter-apk/app-debug.apk
```

Contra un backend publicado con HTTPS (release):

```bash
flutter build apk --release --dart-define=API_BASE_URL=https://<dominio-api-gateway>/api/v1
# → build/app/outputs/flutter-apk/app-release.apk
```

> La build release está firmada con la **clave debug** (`android/app/build.gradle.kts`). Sirve para instalar a mano, pero no para Play Store: antes hay que configurar un keystore propio.

### 3.4 Probar

Entra con `admin@edifika.com` / `Edifika#2026`. La cuenta admin abre **Gestión IoT**, con el edificio, el gateway, los dispositivos, la telemetría y los dispositivos nuevos por adoptar.

---

## 4. Problemas frecuentes

| Síntoma | Causa probable |
|---|---|
| Un servicio Java reinicia en bucle con `database "..._db" does not exist` | El volumen de Postgres es anterior al script de bases. Ejecuta `down -v` y vuelve a levantar |
| 401/403 entre servicios aunque el login funciona | `JWT_SECRET` distinto entre servicios. Usa un único valor en `.env` |
| Edge Gateway con `401` en el sync | `GATEWAY_API_KEY` incorrecta, o `GATEWAY_ID` distinto del `gatewayCode` registrado |
| ESP32 conecta al Wi-Fi pero no al broker | `MQTT_BROKER_HOST` es `localhost`, falta abrir el puerto 1883 en el firewall, o la red aísla clientes |
| ESP32 no conecta al Wi-Fi | Red de 5 GHz, o portal cautivo |
| El nodo sigue en "Sin registrar" | No fue adoptado desde Gestión IoT, o el `edge-gateway` no está levantado |
| La app dice "Pendiente de integración" o usa datos de prueba | Falta `--dart-define=API_BASE_URL=...`, así que está contra la fake API |
| La app no conecta desde el teléfono | La build es release con `http://`, la IP es incorrecta o el firewall bloquea el 8080 |

## 5. No incluido en esta guía

- **Web (FrontEnd):** su imagen nginx (puerto 10000) usa `serverBaseUrl: '/api/v1'` relativo y no trae proxy hacia el API Gateway. Para usarla contra este backend hay que añadir un `location /api/` en `nginx.conf` o cambiar `serverBaseUrl`. En desarrollo: `npm start` en el repo FrontEnd.
- **Simuladores de nodos** (sin hardware): ver `Edifika-Microservice-IoT-Gateway/README.md` (`python -m simulator ...`).
- **Despliegue en la nube:** algunos `application.properties` traen por defecto una base Supabase. El compose de esta guía los sobreescribe todos con el Postgres local.
