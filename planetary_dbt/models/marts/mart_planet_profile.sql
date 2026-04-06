-- data mart to define and summarize final planet profiles given all data


{{ config(
    materialized='materialized_view'
) }}


-- CTE for base query
WITH base AS (
    SELECT
        s.*,
        h.hz_membership,
        h.hzd_score,
        h.habitability_tier,
        h.orbital_stability,
        h.equilibrium_temp_k_final,
        h.escape_velocity_earth,
        h.esi_score,
        h.is_notable,
        h.data_completeness
    FROM {{ ref('stg_exoplanets') }} AS s
    LEFT JOIN {{ ref('mart_habitability_scores') }} AS h ON s.planet_name = h.planet_name
),

display_calcs AS (
    SELECT
        *,
        distance_parsecs * 3.26156 AS distance_light_years,
        equilibrium_temp_k_final - 273.15 AS equilibrium_temp_celsius,
        round(((equilibrium_temp_k_final - 273.15) * 9.0 / 5.0 + 32)::numeric, 1) AS equilibrium_temp_fahrenheit

    FROM base
),

travel_times AS (
    SELECT
        *,
        distance_light_years AS radio_signal_years,
        distance_light_years * 38544 AS shuttle_travel_years,
        distance_light_years * 17693 AS voyager_travel_years,
        distance_light_years * 1560 AS parker_probe_travel_years,
        distance_light_years * 100 AS one_percent_c_travel_years
    FROM display_calcs
),

descriptions AS (
    SELECT
        *,

        CASE
            WHEN equilibrium_temp_celsius IS NULL
                THEN 'Climate unknown'
            WHEN equilibrium_temp_celsius > 500
                THEN 'Class X — Uninhabitable'
            WHEN equilibrium_temp_celsius > 100
                THEN 'Class B — Hyper-Arid'
            WHEN equilibrium_temp_celsius > 50
                THEN 'Class B — Arid'
            WHEN equilibrium_temp_celsius > 18
                THEN 'Class A — Tropical'
            WHEN equilibrium_temp_celsius > 0
                THEN 'Class C — Temperate'
            WHEN equilibrium_temp_celsius > -15
                THEN 'Class D — Continental'
            WHEN equilibrium_temp_celsius > -40
                THEN 'Class E — Polar'
            ELSE
                'Class EF — Ice Cap'
        END AS temperature_description,

        CASE
            WHEN stellar_effective_temp_k < 3000
                THEN '~ a candle flame'
            WHEN stellar_effective_temp_k < 3700
                THEN '~ a welding torch'
            WHEN stellar_effective_temp_k < 4500
                THEN '~ molten lava'
            WHEN stellar_effective_temp_k < 5200
                THEN '~ a light bulb'
            WHEN stellar_effective_temp_k BETWEEN 5200 AND 6000
                THEN '~ the Sun'
            WHEN stellar_effective_temp_k BETWEEN 10000 AND 30000
                THEN '~ a lightning bolt'
        END AS star_temp_description,

        CASE
        -- Sub-terran: smaller than Earth, likely rocky
            WHEN planet_radius_earth < 0.5
                THEN 'Subterran'
            -- Terran: Earth-sized rocky worlds
            WHEN planet_radius_earth < 1.75 AND planet_density_gcm3 >= 3.5
                THEN 'Terran'
            -- Terran but lower density — possibly water or ice rich
            WHEN planet_radius_earth < 1.75 AND planet_density_gcm3 < 3.5
                THEN 'Volatile-rich Terran'
            -- Terran but no density data
            WHEN planet_radius_earth < 1.75 AND planet_density_gcm3 IS NULL
                THEN 'Likely Terran'
            -- Superterran in HZ — Hycean candidate
            WHEN planet_radius_earth < 3.5 AND hz_membership != 'outside_hz'
                THEN 'Superterran — Hycean Candidate'
            -- Superterran outside HZ
            WHEN planet_radius_earth < 3.5
                THEN 'Superterran'
            -- Neptunian
            WHEN planet_radius_earth < 6.0
                THEN 'Neptunian'
            -- Hot Jupiter
            WHEN orbital_period_days < 10 AND planet_radius_earth >= 6.0
                THEN 'Hot Jovian'
            -- Jovian
            WHEN planet_radius_earth < 12.0
                THEN 'Jovian'
            ELSE
                'Super Jovian'
        END AS planet_type,

        CASE
            WHEN planet_radius_earth < 0.3
                THEN 'Smaller than the Moon'
            WHEN planet_radius_earth < 0.4
                THEN 'Moon to Mercury sized'
            WHEN planet_radius_earth < 0.6
                THEN 'Mercury to Mars sized'
            WHEN planet_radius_earth < 0.8
                THEN 'Mars sized'
            WHEN planet_radius_earth BETWEEN 0.8 AND 1.2
                THEN 'Earth sized'
            WHEN planet_radius_earth < 1.5
                THEN 'Between Earth and Venus'
            WHEN planet_radius_earth < 1.75
                THEN 'Super Earth'
            WHEN planet_radius_earth < 2.5
                THEN 'Between Earth and Neptune'
            WHEN planet_radius_earth < 3.86
                THEN 'Approaching Neptune sized'
            WHEN planet_radius_earth < 6.0
                THEN 'Neptune to Uranus sized'
            WHEN planet_radius_earth < 9.14
                THEN 'Uranus to Saturn sized'
            WHEN planet_radius_earth < 11.2
                THEN 'Saturn to Jupiter sized'
            WHEN planet_radius_earth < 15.0
                THEN 'Jupiter sized'
            ELSE
                'Larger than Jupiter'
        END AS size_class,

        CASE
            WHEN stellar_effective_temp_k < 3700 THEN 'Red dwarf'
            WHEN stellar_effective_temp_k >= 3700 AND stellar_effective_temp_k < 5200 THEN 'Orange dwarf'
            WHEN stellar_effective_temp_k >= 5200 AND stellar_effective_temp_k < 6000 THEN 'Sun-like star'
            WHEN stellar_effective_temp_k >= 6000 AND stellar_effective_temp_k < 7500 THEN 'Warm yellow star'
            WHEN stellar_effective_temp_k >= 7500 THEN 'Hot blue-white star'
        END AS star_type_description,

        CASE
            WHEN stellar_age_gyr IS NULL
                THEN 'Age unknown'
            WHEN stellar_age_gyr < 0.5
                THEN round(stellar_age_gyr::numeric, 1)::text || ' billion years'
            WHEN stellar_age_gyr < 2.0
                THEN round(stellar_age_gyr::numeric, 1)::text || ' billion years'
            WHEN stellar_age_gyr < 5.0
                THEN round(stellar_age_gyr::numeric, 1)::text || ' billion years'
            WHEN stellar_age_gyr < 8.0
                THEN round(stellar_age_gyr::numeric, 1)::text || ' billion years'
            WHEN stellar_age_gyr < 12.0
                THEN round(stellar_age_gyr::numeric, 1)::text || ' billion years'
            ELSE
                round(stellar_age_gyr::numeric, 1)::text || ' billion years'
        END AS star_age_description,

        CASE
            WHEN shuttle_travel_years < 1000
                THEN round(shuttle_travel_years)::text || ' years'
            WHEN shuttle_travel_years < 1000000
                THEN round(shuttle_travel_years / 1000)::text || ' thousand years'
            WHEN shuttle_travel_years < 1000000000
                THEN round(shuttle_travel_years / 1000000)::text || ' million years'
            ELSE
                round(shuttle_travel_years / 1000000000)::text || ' billion years'
        END AS shuttle_travel_description,

        CASE
            WHEN distance_light_years < 1
                THEN round(distance_light_years * 365.25::numeric, 0)::text || ' Earth days'
            WHEN distance_light_years < 100
                THEN round(distance_light_years::numeric, 1)::text || ' years'
            WHEN distance_light_years < 1000
                THEN round(distance_light_years::numeric, 0)::text || ' years'
            ELSE
                round(distance_light_years::numeric, 0)::text || ' years'
        END AS radio_signal_description

    FROM travel_times
),

earth_comparisons AS (
    SELECT
        *,
        round((planet_radius_earth * 6371)::numeric, 0)::text
        || ' km (' || round(planet_radius_earth::numeric, 2)::text || '× Earth)'
            AS size_description,

        CASE
            WHEN planet_mass_earth IS NULL OR planet_radius_earth IS NULL
                THEN 'unknown'
            ELSE
                round(((planet_mass_earth / planet_radius_earth ^ 2) * 9.81)::numeric, 2)::text
                || ' m/s² (' || round((planet_mass_earth / planet_radius_earth ^ 2)::numeric, 2)::text || '× Earth)'
        END AS gravity_description,

        -- year length
        CASE
            WHEN orbital_period_days IS NULL
                THEN 'year length unknown'
            WHEN orbital_period_days < 1
                THEN
                    round(orbital_period_days::numeric * 24, 1)::text
                    || 'Earth hours'
            WHEN orbital_period_days < 300
                THEN
                    round(orbital_period_days::numeric, 1)::text
                    || ' Earth days'
            WHEN orbital_period_days > 300 AND orbital_period_days < 400
                THEN
                    round(orbital_period_days::numeric, 1)::text
                    || ' Earth days'
            WHEN orbital_period_days < 1000
                THEN
                    round((orbital_period_days / 365.25)::numeric, 1)::text
                    || ' Earth years'
            ELSE
                round((orbital_period_days / 365.25)::numeric, 1)::text
                || ' Earth years'
        END AS year_description,

        -- orbital distance relative to Earth
        CASE
            WHEN orbital_semi_major_axis_au < 0.1
                THEN
                    round(orbital_semi_major_axis_au::numeric, 3)::text
                    || ' AU'
            WHEN orbital_semi_major_axis_au < 0.4
                THEN
                    round(orbital_semi_major_axis_au::numeric, 2)::text
                    || ' AU'
            WHEN orbital_semi_major_axis_au < 0.8
                THEN
                    round(orbital_semi_major_axis_au::numeric, 2)::text
                    || ' AU'
            WHEN orbital_semi_major_axis_au BETWEEN 0.8 AND 1.2
                THEN
                    round(orbital_semi_major_axis_au::numeric, 2)::text
                    || ' AU'
            WHEN orbital_semi_major_axis_au < 2.0
                THEN
                    round(orbital_semi_major_axis_au::numeric, 2)::text
                    || ' AU'
            WHEN orbital_semi_major_axis_au < 6.0
                THEN
                    round(orbital_semi_major_axis_au::numeric, 2)::text
                    || ' AU'
            WHEN orbital_semi_major_axis_au < 12.0
                THEN
                    round(orbital_semi_major_axis_au::numeric, 2)::text
                    || ' AU'
            WHEN orbital_semi_major_axis_au < 20.0
                THEN
                    round(orbital_semi_major_axis_au::numeric, 2)::text
                    || ' AU'
            ELSE
                round(orbital_semi_major_axis_au::numeric, 1)::text
                || ' AU'
        END AS orbital_distance_description,

        -- Weather estimation
        CASE
            WHEN planet_type IN ('Jovian', 'Super Jovian', 'Hot Jovian')
                THEN 'Permanent storms larger than Earth, winds exceeding 1000 mph'
            WHEN planet_type = 'Neptunian'
                THEN 'Dense crushing atmosphere, extreme pressure at surface level'
            WHEN planet_type = 'Superterran — Hycean Candidate'
                THEN 'Global ocean beneath a thick hydrogen atmosphere — possible liquid water at surface'
            WHEN planet_type = 'Superterran'
                THEN 'Dense thick atmosphere, extreme pressures likely at surface'
            WHEN
                temperature_description = 'scorching'
                AND planet_type IN ('Terran', 'Likely Terran', 'Volatile-rich Terran', 'Subterran')
                THEN 'Surface hot enough to melt lead, any atmosphere likely stripped away'
            WHEN
                temperature_description = 'hot'
                AND planet_type IN ('Terran', 'Likely Terran', 'Volatile-rich Terran', 'Subterran')
                THEN 'Runaway greenhouse effect likely, similar to Venus'
            WHEN
                star_type_description = 'Red dwarf'
                AND planet_type IN ('Terran', 'Likely Terran', 'Volatile-rich Terran', 'Subterran')
                AND temperature_description IN ('temperate', 'cold', 'frozen')
                THEN 'Tidally locked — one side in permanent day, one in permanent night, extreme winds at the terminator boundary'
            WHEN
                temperature_description = 'temperate'
                AND planet_type IN ('Terran', 'Likely Terran', 'Volatile-rich Terran', 'Subterran')
                THEN 'Possible Earth-like weather patterns with liquid water cycles'
            WHEN
                temperature_description = 'cold'
                AND planet_type IN ('Terran', 'Likely Terran', 'Volatile-rich Terran', 'Subterran')
                THEN 'Thin cold atmosphere, similar to Mars — dust storms possible'
            WHEN
                temperature_description = 'frozen'
                AND planet_type IN ('Terran', 'Likely Terran', 'Volatile-rich Terran', 'Subterran')
                THEN 'Frozen surface, possible subsurface liquid ocean beneath ice'
            ELSE 'Atmospheric conditions unknown'
        END AS weather_estimation

    FROM descriptions
)

SELECT
    planet_name,
    host_star_name,
    discovery_year,
    discovery_method,
    planet_type,
    hz_membership,
    hzd_score,
    habitability_tier,
    orbital_eccentricity,
    orbital_stability,
    size_class,
    esi_score,
    is_notable,
    data_completeness,
    stellar_effective_temp_k,
    equilibrium_temp_k_final,
    equilibrium_temp_celsius,
    equilibrium_temp_fahrenheit,
    temperature_description,
    star_temp_description,
    star_type_description,
    star_age_description,
    escape_velocity_earth,
    distance_light_years,
    shuttle_travel_description,
    radio_signal_description,
    size_description,
    gravity_description,
    year_description,
    orbital_distance_description,
    weather_estimation
FROM earth_comparisons
