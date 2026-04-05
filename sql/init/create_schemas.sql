-- sql schema for raw exoplanets data from NASA API

-- create schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;


-- create planet_images table
CREATE TABLE IF NOT EXISTS marts.planet_images (
    planet_name varchar(150) PRIMARY KEY,
    image_url text,
    image_prompt text,
    generated_at timestamp DEFAULT now(),
    generation_model varchar(50)
);
