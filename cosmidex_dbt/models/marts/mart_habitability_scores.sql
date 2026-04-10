-- data mart model to calculate and store habitability scores for exoplanets made up of 4 CTEs

{{ config(
    materialized='materialized_view'
) }}

-- CTE to calculate the stellar luminosity so that it can be used
-- in downstream calculations/column creation
WITH stellar_calcs AS (
    SELECT
        -- identity
        planet_name,
        host_star_name,
        orbital_semi_major_axis_au,
        orbital_eccentricity,
        equilibrium_temp_k,
        insolation_flux_earth,
        planet_radius_earth,
        planet_mass_earth,
        planet_density_gcm3,
        stellar_effective_temp_k,

        /* stellar luminosity:
        a log base 10 value relative to our Sun.
        The Sun itself is 0.0 on this scale because log10(1) = 0.
        A star twice as bright as the Sun is log10(2) = 0.301.
        A star ten times as bright is log10(10) = 1.0.
        A star dimmer than the Sun has a negative value.
        Need to undo the log transform so downstream
        calculations have number format they need.
        */
        power(10, stellar_luminosity_log_solar) AS stellar_luminosity_solar

    FROM {{ ref('stg_exoplanets') }}
    WHERE has_minimum_habitability_data = true

),

-- CTE to use stellar luminosity to calculate habitability zone boundaries
hz_boundaries AS (
    SELECT
        *,

        /* habitability zone boundaries:
        The habitable zone is the orbital distance range around a star
        where a rocky planet could have liquid water on its surface - not too hot, not too cold. It's sometimes called the Goldilocks zone.
        The key insight is that the HZ scales with luminosity.
        A brighter star pushes the HZ further out. A dimmer star pulls it closer in.
        The relationship follows an inverse square law — if you double the luminosity,
        the HZ boundaries move outward by the square root of 2 (about 1.41x).

        Formula: hz_inner = sqrt(luminosity / flux_inner_limit)
                hz_outer = sqrt(luminosity / flux_outer_limit)
        */
        sqrt(stellar_luminosity_solar / 1.1) AS hz_inner_conservative_au,
        sqrt(stellar_luminosity_solar / 0.36) AS hz_outer_conservative_au,
        sqrt(stellar_luminosity_solar / 1.78) AS hz_inner_optimistic_au,
        sqrt(stellar_luminosity_solar / 0.29) AS hz_outer_optimistic_au,

        /*equilibrium temperature:
        Equilibrium temperature is the theoretical surface temperature of a planet
        if it were a simple blackbody with no atmosphere — purely a function of how much stellar energy it receives and how much it reflects.
        Formula: T_eq = 278.5 * (luminosity ^ 0.25) / sqrt(orbital_distance)
        */
        coalesce(
            equilibrium_temp_k,
            278.5 * power(stellar_luminosity_solar, 0.25)
            / sqrt(orbital_semi_major_axis_au)
        ) AS equilibrium_temp_k_final

    FROM stellar_calcs
),

planet_scores AS (
    SELECT
        *,

        sqrt(2 * planet_mass_earth / planet_radius_earth)
            AS escape_velocity_earth
    FROM hz_boundaries

),

scored AS (
    SELECT
        *,

        /*eccentricity risk tier:
        Eccentricity describes how circular or elliptical a planet's orbit is.
        It's a number between 0 and 1 where:
            0 = perfectly circular orbit.
            The planet stays the same distance from its star year-round.
            0 to 0.1 = nearly circular. Small seasonal variation in stellar flux.
            Earth is 0.017 — almost perfectly circular. 0.1 to 0.3 = moderately elliptical.
            Noticeable variation in distance between closest approach (perihelion) and furthest point (aphelion).
            Mars is 0.093, still fairly low. Above 0.3 = highly elliptical.
            The planet swings dramatically closer and further from its star.
            Think of a comet's orbit — very high eccentricity.
        */
        CASE
            WHEN orbital_eccentricity IS null THEN 'Unknown'
            WHEN orbital_eccentricity < 0.1 THEN 'High'
            WHEN orbital_eccentricity <= 0.3 THEN 'Moderate'
            WHEN orbital_eccentricity > 0.3 THEN 'Low'
        END AS orbital_stability,

        -- hz membership flag
        CASE
            WHEN
                orbital_semi_major_axis_au
                BETWEEN hz_inner_conservative_au AND hz_outer_conservative_au
                THEN 'conservative_hz'
            WHEN
                orbital_semi_major_axis_au
                BETWEEN hz_inner_optimistic_au AND hz_outer_optimistic_au
                THEN 'optimistic_hz'
            ELSE 'outside_hz'
        END AS hz_membership,

        /* ESI:
            how similar is this planet to Earth across its key physical properties?
            It produces a single number where 1.0 means identical to Earth and 0 means completely alien.
            The reason it multiplies four individual similarities together
            rather than averaging them is intentional — it's punishing.
            If any single property is wildly un-Earth-like, the whole score collapses toward zero.
            A planet that's the right size and density but has a surface temperature of 700K should score very low overall,
            not average out to something misleadingly moderate.
        */
        power(
            1 - abs(planet_radius_earth - 1.0) / (planet_radius_earth + 1.0),
            0.57
        )
        * power(
            1 - abs(planet_density_gcm3 - 5.51) / (planet_density_gcm3 + 5.51),
            1.07
        )
        * power(
            1 - abs(escape_velocity_earth - 1.0) / (escape_velocity_earth + 1.0),
            0.70
        )
        * power(
            1 - abs(equilibrium_temp_k_final - 288.0) / (equilibrium_temp_k_final + 288.0),
            5.58
        ) AS esi_score,

        /* Habitability zone distance:
        Intuitively this is just normalizing the planet's position onto a -1 to +1 scale where the HZ boundaries are the endpoints.
        */
        (2 * orbital_semi_major_axis_au - hz_inner_conservative_au - hz_outer_conservative_au)
        / nullif(hz_outer_conservative_au - hz_inner_conservative_au, 0) AS hzd_score

    FROM planet_scores
)

SELECT
    *,

    /* Habitability Tier:
    This is the editorial layer — combining ESI, HZD, and existing flags into a final habitability verdict.
    */
    CASE
        WHEN
            esi_score >= 0.8
            AND hzd_score BETWEEN -1 AND 1
            AND planet_radius_earth <= 1.75
            AND orbital_stability != 'Low'
            AND stellar_effective_temp_k BETWEEN 3700 AND 7500
            THEN 'tier_1_strong_candidate'
        WHEN
            esi_score >= 0.6
            AND hz_membership != 'outside_hz'
            AND planet_radius_earth <= 1.75
            THEN 'tier_2_moderate_candidate'
        WHEN
            hz_membership != 'outside_hz'
            THEN 'tier_3_in_hz_only'
        ELSE 'non_habitable'
    END AS habitability_tier,

    planet_name IN (
        'Proxima Cen b',
        'TRAPPIST-1 d',
        'TRAPPIST-1 e',
        'TRAPPIST-1 f',
        'Kepler-452 b',
        'Kepler-186 f',
        'LHS 1140 b',
        'K2-18 b',
        'Kepler-442 b',
        'Teegarden''s Star b',
        'TOI-700 d',
        'TOI-700 e',
        'Ross 128 b'
    ) AS is_notable,

    CASE
        WHEN
            esi_score IS NOT null
            AND planet_density_gcm3 IS NOT null
            THEN 'full'
        WHEN esi_score IS NOT null
            THEN 'partial'
        ELSE 'minimal'
    END AS data_completeness

FROM scored
