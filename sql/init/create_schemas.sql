-- sql schema for raw exoplanets data from NASA API

-- create schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- create types
CREATE TYPE discovery_methods AS ENUM (
    'Radial Velocity',
    'Imaging',
    'Eclipse Timing Variations',
    'Microlensing',
    'Transit',
    'Transit Timing Variations',
    'Astrometry',
    'Disk Kinematics',
    'Orbital Brightness Modulation',
    'Pulsation Timing Variations',
    'Pulsar Timing'
);
CREATE TYPE stellar_metallicity_ratios AS ENUM ('[Fe/H]', '[M/H]');
CREATE TYPE provenance AS ENUM (
    'Msini', 'Mass', 'Msin(i)/sin(i)', 'M-R relationship'
);

-- create tables
CREATE TABLE IF NOT EXISTS raw.exoplanets (
    pl_name varchar(100) PRIMARY KEY,
    hostname varchar(100),
    pl_rade double precision,
    pl_bmasse double precision,
    pl_eqt double precision,
    pl_orbper double precision,
    pl_orbsmax double precision,
    st_teff double precision,
    st_spectype varchar(25),
    st_rad double precision,
    st_mass double precision,
    sy_dist double precision,
    disc_year integer,
    discoverymethod discovery_methods,
    default_flag boolean
);
