-- model to identify fields critical for defining planet habitability 
-- to clean and prepare them for marts

{{ config(
    materialized='view'
) }}

SELECT
    -- identity
    pl_name::varchar(150) AS planet_name,
    hostname::varchar(150) AS host_star_name,
    disc_year::varchar(4) AS discovery_year,
    discoverymethod::varchar(150) AS discovery_method,
    disc_facility::varchar(150) AS discovery_facility,
    disc_telescope::varchar(150) AS discovery_telescope,
    disc_instrument::varchar(150) AS discovery_instrument,
    disc_locale::varchar(150) AS discovery_locale,
    sy_dist::numeric AS distance_parsecs,

    -- planet physical
    pl_rade::numeric AS planet_radius_earth,
    pl_bmasse::numeric AS planet_mass_earth,
    pl_dens::numeric AS planet_density_gcm3,
    pl_orbeccen::numeric AS orbital_eccentricity,
    pl_orbsmax::numeric AS orbital_semi_major_axis_au,
    pl_orbper::numeric AS orbital_period_days,
    pl_insol::numeric AS insolation_flux_earth,
    pl_eqt::numeric AS equilibrium_temp_k,

    -- stellar
    st_teff::numeric AS stellar_effective_temp_k,
    st_lum::numeric AS stellar_luminosity_log_solar,
    st_mass::numeric AS stellar_mass_solar,
    st_rad::numeric AS stellar_radius_solar,
    st_age::numeric AS stellar_age_gyr,
    st_logg::numeric AS stellar_surface_gravity_log,
    st_met::numeric AS stellar_metallicity_dex,

    -- null flags
    pl_rade IS NOT NULL AS planet_radius_earth_flag,
    pl_bmasse IS NOT NULL AS planet_mass_earth_flag,
    pl_orbsmax IS NOT NULL AS orbital_semi_major_axis_au_flag,
    st_lum IS NOT NULL AS stellar_luminosity_log_solar_flag,
    st_teff IS NOT NULL AS stellar_effective_temp_flag,

    -- minimum habitability flag
    pl_rade IS NOT NULL
    AND pl_bmasse IS NOT NULL
    AND pl_orbsmax IS NOT NULL
    AND st_lum IS NOT NULL
    AND st_teff IS NOT NULL AS has_minimum_habitability_data

FROM {{ source('raw', 'exoplanets') }}
