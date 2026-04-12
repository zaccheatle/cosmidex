-- sql schema for raw exoplanets data from NASA API

-- create schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- create planet images table
CREATE TABLE IF NOT EXISTS marts.planet_images (
    planet_name VARCHAR(150) PRIMARY KEY,
    image_url TEXT NOT NULL,
    image_prompt TEXT,
    generation_model VARCHAR(100),
    generated_at TIMESTAMP DEFAULT now()
);
