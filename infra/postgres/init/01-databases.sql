-- Create databases for Edifika IoT microservices
CREATE DATABASE access_db;
CREATE DATABASE telemetry_db;

\c telemetry_db;
CREATE EXTENSION IF NOT EXISTS timescaledb;

\c access_db;
CREATE EXTENSION IF NOT EXISTS timescaledb;
