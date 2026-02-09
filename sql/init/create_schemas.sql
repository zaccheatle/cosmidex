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
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    planet_name varchar(100),
    host_name varchar(100),
    number_of_stars int,
    number_of_planets int,
    discovery_method discovery_methods,
    disc_year varchar(4),
    disc_facility text,
    controversial_flag boolean,
    orbital_period_days double precision,
    orbit_semi_major_axis_au double precision,
    planet_radius_earth double precision,
    planet_radius_jupiter double precision,
    planet_mass_earth double precision,
    planet_mass_jupiter double precision,
    planet_mass_provenance provenance,
    eccentricity double precision,
    insolation_flux_earth double precision,
    equilibrium_temperature_k double precision,
    data_show_transit_timing_variations boolean,
    spectral_type varchar(25),
    stellar_effective_temperature_k double precision,
    stellar_radius_solar double precision,
    stellar_mass_solar double precision,
    stellar_metallicity_dex double precision,
    stellar_metallicity_ratio stellar_metallicity_ratios,
    stellar_gravity_surface double precision,
    ra_sexagesimal text,
    dec_sexagesimal text,
    distance double precision,
    v_magnitude double precision,
    ks_magnitude double precision,
    gaia_magnitude double precision
);
