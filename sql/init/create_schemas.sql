-- sql schema for raw exoplanets data from NASA API

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- Enables the `vector` column type and similarity-search operators used by
-- the RAG layer's chunk/embedding storage.
CREATE EXTENSION IF NOT EXISTS vector;

-- image_url holds the AI-generated Earth-size-comparison image. image_url_orbital
-- is an unused legacy column from an earlier dual-image design — kept nullable
-- for backward compatibility, no longer populated by generate_images.py.
CREATE TABLE IF NOT EXISTS marts.planet_images (
    planet_name VARCHAR(150) PRIMARY KEY,
    image_url TEXT NOT NULL,
    image_url_orbital TEXT,
    image_prompt TEXT,
    generation_model VARCHAR(100),
    generated_at TIMESTAMP DEFAULT now()
);

ALTER TABLE marts.planet_images ADD COLUMN IF NOT EXISTS image_url_orbital TEXT;

CREATE TABLE IF NOT EXISTS marts.planet_descriptions (
    planet_name VARCHAR(150) PRIMARY KEY,
    description TEXT NOT NULL,
    generation_model VARCHAR(100),
    generated_at TIMESTAMP DEFAULT now()
);

-- table for vector embeddings to support RAG integration
CREATE TABLE IF NOT EXISTS marts.rag_chunks (
    id SERIAL PRIMARY KEY,
    source_title TEXT,
    source_url TEXT,
    chunk_index INT,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(768),
    created_at TIMESTAMP DEFAULT now()
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
