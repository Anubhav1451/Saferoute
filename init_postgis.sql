-- Initialize PostGIS extension for SafeRoute AI
-- This script runs automatically when the PostgreSQL container starts

-- Create PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

-- Set default SRID to 4326 (WGS 84)
SELECT PostGIS_SetSRID('geometry', 4326);

-- Create spatial indexes will be handled by Alembic migrations
-- This script only ensures the extensions are available

-- Grant permissions to postgres user (container default)
GRANT USAGE ON SCHEMA topology TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA topology TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA topology TO postgres;

-- Output PostGIS version for verification
SELECT PostGIS_Full_Version();