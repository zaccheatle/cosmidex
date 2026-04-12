-- data mart to define and summarize final planet profiles given all data


{{ config(
    materialized='materialized_view'
) }}


-- CTE for base query
WITH base AS (
    SELECT
        s.*,
        h.hz_inner_conservative_au,
        h.hz_outer_conservative_au,
        h.hz_membership,
        h.hzd_score,
        h.orbital_stability,
        h.equilibrium_temp_k_final,
        h.s_escape,
        h.esi_score,
        h.data_completeness
    FROM {{ ref('stg_exoplanets') }} AS s
    LEFT JOIN {{ ref('mart_habitability_scores') }} AS h ON s.planet_name = h.planet_name
),

display_calcs AS (
    SELECT
        *,
        distance_parsecs * 3.26156 AS star_distance_light_years,
        equilibrium_temp_k_final - 273.15 AS equilibrium_temp_celsius,
        round(((equilibrium_temp_k_final - 273.15) * 9.0 / 5.0 + 32)::numeric, 1) AS equilibrium_temp_fahrenheit,

        -- Estimated surface temperature assuming Earth-like greenhouse effect (+33K)
        -- Per Méndez & Rivera-Valentín (2017) / PHL methodology
        -- Actual temperature highly dependent on atmospheric composition
        equilibrium_temp_k_final + 33 AS estimated_surface_temp_k,
        (equilibrium_temp_k_final + 33) - 273.15 AS estimated_surface_temp_celsius,
        round((((equilibrium_temp_k_final + 33) - 273.15) * 9.0 / 5.0 + 32)::numeric, 1) AS estimated_surface_temp_fahrenheit

    FROM base
),

travel_times AS (
    SELECT
        *,
        star_distance_light_years AS radio_signal_years,
        star_distance_light_years * 38544 AS shuttle_travel_years,
        star_distance_light_years * 17693 AS voyager_travel_years,
        star_distance_light_years * 1560 AS parker_probe_travel_years,
        star_distance_light_years * 100 AS one_percent_c_travel_years

    FROM display_calcs
),

descriptions AS (
    SELECT
        *,

        -- PLANET DESCRIPTIONS -------------------------------------------------
        CASE
            WHEN estimated_surface_temp_celsius IS NULL
                THEN 'Climate unknown'
            WHEN estimated_surface_temp_celsius > 500
                THEN 'Hotter than Venus'' surface (462°C)'
            WHEN estimated_surface_temp_celsius > 100
                THEN 'Hotter than boiling water'
            WHEN estimated_surface_temp_celsius > 50
                THEN 'Hotter than Death Valley in summer (~56°C)'
            WHEN estimated_surface_temp_celsius > 18
                THEN 'Tropical Earth conditions'
            WHEN estimated_surface_temp_celsius > 0
                THEN 'Temperate Earth conditions'
            WHEN estimated_surface_temp_celsius > -15
                THEN 'Polar winter conditions'
            WHEN estimated_surface_temp_celsius > -40
                THEN 'Antarctic winter'
            WHEN estimated_surface_temp_celsius > -90
                THEN 'Mars average surface temp (~-60°C)'
            ELSE
                'Colder than anywhere on Earth'
        END AS estimated_planet_climate,

        CASE
            WHEN planet_density_gcm3 IS NULL THEN 'Unknown'
            WHEN planet_density_gcm3 > 5.0 THEN 'Rock/Iron'
            WHEN planet_density_gcm3 > 3.0 THEN 'Rock/Silicate'
            WHEN planet_density_gcm3 > 2.0 THEN 'Water/Ice'
            WHEN planet_density_gcm3 >= 1.2 THEN 'Ice Giant'
            WHEN planet_density_gcm3 < 1.2 THEN 'Gas Giant'
        END AS planet_composition,

        CASE
            WHEN planet_radius_earth IS NULL THEN 'Unknown'
            WHEN planet_radius_earth > 15.0 THEN 'Gas Giant - Super Jovian'
            WHEN planet_radius_earth > 11.2 THEN 'Gas Giant'
            WHEN planet_radius_earth > 4.0 THEN 'Neptunian'
            WHEN planet_radius_earth > 2.0 THEN 'Super-Earth | Mini-Neptune'
            WHEN planet_radius_earth > 1.5 THEN 'Super-Earth'
            WHEN planet_radius_earth >= 0.5 THEN 'Terrestrial - Earth sized'
            WHEN planet_radius_earth < 0.5 THEN 'Terrestrial - Smaller than Earth'
        END AS planet_size_class,

        CASE
            WHEN planet_mass_earth IS NULL OR planet_radius_earth IS NULL
                THEN 'Unknown'
            WHEN planet_radius_earth = 0
                THEN 'Unknown'
            ELSE
                round((sqrt(planet_mass_earth / planet_radius_earth) * 11.2)::numeric, 2)::text
                || ' km/s ('
                || round(sqrt(planet_mass_earth / planet_radius_earth)::numeric, 2)::text
                || '× Earth)'
        END AS planet_escape_velocity,

        -- HOST STAR DESCRIPTIONS -----------------------------------------------
        CASE
            WHEN stellar_effective_temp_k IS NULL THEN 'Unknown'
            WHEN stellar_effective_temp_k > 30000 THEN 'Hotter than a lightning bolt'
            WHEN stellar_effective_temp_k > 10000 THEN 'As hot as a lightning bolt'
            WHEN stellar_effective_temp_k > 7500 THEN 'As hot as rocket exhuast'
            WHEN stellar_effective_temp_k > 6000 THEN 'Hotter than our Sun'
            WHEN stellar_effective_temp_k > 5200 THEN 'As hot as our Sun'
            WHEN stellar_effective_temp_k > 3700 THEN 'As hot as molten lava'
            WHEN stellar_effective_temp_k > 2400 THEN 'As hot as the tip of a candle flame'
            WHEN stellar_effective_temp_k > 1300 THEN 'As hot as a campfire'
            WHEN stellar_effective_temp_k >= 700 THEN 'As hot as iron in a forge'
            WHEN stellar_effective_temp_k < 700 THEN 'Cooler than a kitchen oven'
        END AS star_temp_description,

        CASE
            WHEN stellar_effective_temp_k IS NULL THEN 'Unknown'
            WHEN stellar_effective_temp_k >= 30000 THEN 'Class O - Blue'
            WHEN stellar_effective_temp_k >= 10000 THEN 'Class B - Blue-white'
            WHEN stellar_effective_temp_k >= 7500 THEN 'Class A - White'
            WHEN stellar_effective_temp_k >= 6000 THEN 'Class F - Yellow-white'
            WHEN stellar_effective_temp_k >= 5200 THEN 'Class G - Yellow'
            WHEN stellar_effective_temp_k >= 3700 THEN 'Class K - Orange'
            WHEN stellar_effective_temp_k >= 2400 THEN 'Class M - Red-orange'
            WHEN stellar_effective_temp_k >= 1300 THEN 'Class L - Red'
            WHEN stellar_effective_temp_k >= 700 THEN 'Class T - Magenta'
            ELSE 'Class Y - Infrared'
        END AS star_spectral_type,

        CASE
            WHEN stellar_radius_solar IS NULL OR stellar_luminosity_log_solar IS NULL
                THEN 'Unknown'
            WHEN (stellar_radius_solar < 0.02) AND (stellar_luminosity_log_solar < -2)
                THEN 'White Dwarf - Dead Star'
            WHEN
                (stellar_radius_solar > 0.02 AND stellar_radius_solar <= 0.8)
                AND (stellar_luminosity_log_solar < -2)
                AND stellar_effective_temp_k > 3700
                THEN 'Subdwarf - Dim Star'
            WHEN
                (stellar_radius_solar > 0.02 AND stellar_radius_solar <= 1.5)
                OR (stellar_luminosity_log_solar >= -4 AND stellar_luminosity_log_solar < 0.3)
                THEN 'Main Sequence - Active Star'
            WHEN
                (stellar_radius_solar > 1.5 AND stellar_radius_solar <= 3.5)
                OR (stellar_luminosity_log_solar >= 0.3 AND stellar_luminosity_log_solar < 1.0)
                THEN 'Subgiant - Aging Star'
            WHEN
                (stellar_radius_solar > 3.5 AND stellar_radius_solar <= 10)
                OR (stellar_luminosity_log_solar >= 1.0 AND stellar_luminosity_log_solar < 2.0)
                THEN 'Giant - Expanded and Cooling'
            WHEN
                (stellar_radius_solar > 10 AND stellar_radius_solar <= 30)
                OR (stellar_luminosity_log_solar >= 2.0 AND stellar_luminosity_log_solar < 3.0)
                THEN 'Bright Giant - Highly Luminous'
            WHEN
                (stellar_radius_solar > 30 AND stellar_radius_solar <= 100)
                OR (stellar_luminosity_log_solar >= 3.0 AND stellar_luminosity_log_solar < 4.0)
                THEN 'Supergiant - Near End of Life'
            WHEN (stellar_radius_solar > 100) OR (stellar_luminosity_log_solar >= 4.0)
                THEN 'Hypergiant - Massive and Unstable'
            ELSE 'Unclassified'
        END AS star_life_stage,

        CASE
            WHEN stellar_radius_solar IS NULL
                THEN 'Unknown'
            ELSE
                round(stellar_radius_solar::numeric, 2)::text || '× our Sun'
        END AS star_size_description,

        CASE
            WHEN stellar_age_gyr IS NULL THEN 'Age unknown'
            ELSE round(stellar_age_gyr::numeric, 1)::text || ' billion years'
        END AS star_age_description,

        -- TRAVEL DESCRIPTIONS ------------------------------------------------------------------
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
            WHEN star_distance_light_years < 1
                THEN round(star_distance_light_years * 365.25::numeric, 0)::text || ' Earth days'
            WHEN star_distance_light_years < 100
                THEN round(star_distance_light_years::numeric, 1)::text || ' years'
            WHEN star_distance_light_years < 1000
                THEN round(star_distance_light_years::numeric, 0)::text || ' years'
            ELSE
                round(star_distance_light_years::numeric, 0)::text || ' years'
        END AS radio_signal_description

    FROM travel_times
),

earth_comparisons AS (
    SELECT
        *,

        CASE
            WHEN planet_radius_earth IS NULL THEN 'Unknown'
            ELSE
                round((planet_radius_earth * 6371)::numeric, 0)::text
                || ' km (' || round(planet_radius_earth::numeric, 2)::text || '× Earth)'
        END AS planet_size_description,

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
                THEN 'Unknown'
            WHEN orbital_period_days < 1
                THEN
                    round(orbital_period_days::numeric * 24, 1)::text
                    || ' Earth hours'
            WHEN orbital_period_days <= 365.25
                THEN
                    round(orbital_period_days::numeric, 1)::text
                    || ' Earth days'
            WHEN orbital_period_days > 365.25 THEN
                round((orbital_period_days / 365.25)::numeric, 1)::text
                || ' Earth years'
        END AS year_length,

        -- orbital distance relative to Earth
        CASE
            WHEN orbital_semi_major_axis_au IS NULL THEN 'Unknown'
            WHEN orbital_semi_major_axis_au < 0.1
                THEN round(orbital_semi_major_axis_au::numeric, 3)::text || ' AU'
            ELSE
                round(orbital_semi_major_axis_au::numeric, 2)::text || ' AU'
        END AS orbital_distance_description,

        /* Habitability Tier: -----------------------------------------------------------------------
            A three-tier classification of a planet's potential to support life,
            based on orbital position, physical composition, stellar environment,
            and data quality.

            Tier 1 — Strong Candidate:
                The most stringent criteria. Planet must be in the conservative
                habitable zone (Kopparapu 2014), rocky by composition or radius,
                below PHL optimistic sample mass/radius limits (≤2.5 RE, ≤10 ME),
                on a stable or moderate orbit, orbiting a main sequence F/G/K star
                (3700–7500K), and have sufficient data to trust the classification.
                Red dwarfs (< 3700K) are excluded due to tidal locking and flare risks.

            Tier 2 — Moderate Candidate:
                Relaxed criteria allowing M dwarfs and optimistic HZ membership.
                Planet must still be rocky, within PHL size/mass limits, and orbiting
                a main sequence star. Includes TRAPPIST-1 and Proxima Cen planets.

            Tier 3 — In Habitable Zone Only:
                Planet is within the optimistic or conservative HZ and below 2.5 RE,
                but does not meet the stricter composition or stellar criteria above.
                Includes larger super-Earths and mini-Neptunes in the HZ.

            Non-Habitable:
                Everything else — gas giants, planets outside the HZ, planets around
                evolved or unstable stars.

            Note: Planet composition is prioritized over radius when density data is
            available. At gas giant radii (>2.5 RE), density values from PSCompPars
            can be physically inconsistent due to data from multiple sources, so
            explicit mass and radius caps are applied regardless of composition.

            HZ boundaries calculated using Kopparapu et al. (2014) stellar
            flux polynomial coefficients for conservative (moist greenhouse /
            maximum greenhouse) and optimistic (recent Venus / early Mars) limits.
        */
        CASE
            WHEN
                hz_membership = 'conservative_hz'
                AND (
                    (planet_composition IN ('Rock/Iron', 'Rock/Silicate') AND planet_composition IS NOT NULL AND planet_composition != 'Unknown')
                    OR ((planet_composition IS NULL OR planet_composition = 'Unknown') AND planet_radius_earth <= 1.6)
                )
                AND planet_radius_earth <= 2.5
                AND planet_mass_earth <= 10
                AND orbital_stability != 'Unstable'
                AND stellar_effective_temp_k BETWEEN 3700 AND 7500
                AND star_life_stage = 'Main Sequence - Active Star'
                AND data_completeness != 'Minimal'
                THEN 'Tier 1'
            WHEN
                hz_membership != 'outside_hz'
                AND (
                    (planet_composition IN ('Rock/Iron', 'Rock/Silicate') AND planet_composition IS NOT NULL AND planet_composition != 'Unknown')
                    OR ((planet_composition IS NULL OR planet_composition = 'Unknown') AND planet_radius_earth <= 1.6)
                )
                AND planet_radius_earth <= 2.5
                AND planet_mass_earth <= 10
                AND stellar_effective_temp_k <= 7500 AND stellar_effective_temp_k >= 2400
                AND star_life_stage = 'Main Sequence - Active Star'
                AND data_completeness != 'Minimal'
                THEN 'Tier 2'
            WHEN
                hz_membership != 'outside_hz'
                AND planet_radius_earth < 2.5
                THEN 'Tier 3'
            ELSE 'Non-Habitable'
        END AS habitability_tier

    FROM descriptions
)

SELECT
    planet_name,
    host_star_name,
    discovery_year,
    discovery_method,
    data_completeness,

    -- planet fields
    equilibrium_temp_k_final,
    equilibrium_temp_celsius,
    equilibrium_temp_fahrenheit,
    estimated_surface_temp_celsius,
    estimated_surface_temp_fahrenheit,
    estimated_planet_climate,
    planet_radius_earth,
    planet_mass_earth,
    planet_density_gcm3,
    planet_composition,
    planet_size_class,
    planet_size_description,
    gravity_description,
    planet_escape_velocity,
    esi_score,

    -- orbit fields
    orbital_eccentricity,
    orbital_stability,
    orbital_distance_description,
    year_length,

    -- stellar fields 
    stellar_effective_temp_k,
    star_temp_description,
    star_age_description,
    stellar_radius_solar,
    stellar_luminosity_log_solar,
    star_spectral_type,
    star_life_stage,
    star_size_description,
    star_distance_light_years,

    -- habitability fields
    hz_membership,
    hzd_score,
    habitability_tier,
    hz_inner_conservative_au,
    hz_outer_conservative_au,

    -- misc fields
    shuttle_travel_description,
    radio_signal_description
FROM earth_comparisons
