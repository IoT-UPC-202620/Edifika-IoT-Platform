-- Databases for the rest of the Edifika microservices (docker-compose.full.yml).
-- Only runs on a fresh postgres_data volume: `docker compose down -v` to re-run it.
CREATE DATABASE iam_db;
CREATE DATABASE residential_db;
CREATE DATABASE reservation_db;
CREATE DATABASE payment_db;
CREATE DATABASE communication_db;
CREATE DATABASE forum_db;
CREATE DATABASE notification_db;
CREATE DATABASE report_db;
