-- sql schema for raw exoplanets data from NASA API

-- create schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- create planet images table
-- image_url holds the ground-level surface view; image_url_orbital holds the
-- full-planet space/orbital portrait view
CREATE TABLE IF NOT EXISTS marts.planet_images (
    planet_name VARCHAR(150) PRIMARY KEY,
    image_url TEXT NOT NULL,
    image_url_orbital TEXT,
    image_prompt TEXT,
    generation_model VARCHAR(100),
    generated_at TIMESTAMP DEFAULT now()
);

ALTER TABLE marts.planet_images ADD COLUMN IF NOT EXISTS image_url_orbital TEXT;

-- create planet descriptions table
CREATE TABLE IF NOT EXISTS marts.planet_descriptions (
    planet_name VARCHAR(150) PRIMARY KEY,
    description TEXT NOT NULL,
    generation_model VARCHAR(100),
    generated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.pipeline_state (
    pipeline_name VARCHAR PRIMARY KEY,
    last_file_hash VARCHAR,
    last_run_timestamp TIMESTAMP,
    last_planet_count INT
);

CREATE TABLE IF NOT EXISTS raw.pipeline_audit (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR NOT NULL,
    run_timestamp TIMESTAMP DEFAULT now(),
    changed BOOLEAN NOT NULL,
    loaded BOOLEAN NOT NULL,
    planet_count INT,
    new_planet_count INT,
    new_planets TEXT []
);
