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
        stellar_luminosity_log_solar,

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
        */
        -- T* = stellar temp offset from Sun
        stellar_effective_temp_k - 5780 AS t_star,

        -- Conservative inner (Moist Greenhouse)
        sqrt(
            greatest(
                stellar_luminosity_solar / nullif(
                    1.0140
                    + (8.1774e-5 * (stellar_effective_temp_k - 5780))
                    + (1.7063e-9 * power(stellar_effective_temp_k - 5780, 2))
                    + (-4.3241e-12 * power(stellar_effective_temp_k - 5780, 3))
                    + (-6.6462e-16 * power(stellar_effective_temp_k - 5780, 4)),
                    0
                ),
                0
            )
        ) AS hz_inner_conservative_au,

        -- Conservative outer (Maximum Greenhouse)
        sqrt(
            greatest(
                stellar_luminosity_solar / nullif(
                    0.3438
                    + (5.8942e-5 * (stellar_effective_temp_k - 5780))
                    + (1.6558e-9 * power(stellar_effective_temp_k - 5780, 2))
                    + (-3.0045e-12 * power(stellar_effective_temp_k - 5780, 3))
                    + (-5.2983e-16 * power(stellar_effective_temp_k - 5780, 4)),
                    0
                ),
                0
            )
        ) AS hz_outer_conservative_au,

        -- Optimistic inner (Recent Venus)
        sqrt(
            greatest(
                stellar_luminosity_solar / nullif(
                    1.7763
                    + (1.4335e-4 * (stellar_effective_temp_k - 5780))
                    + (3.3954e-9 * power(stellar_effective_temp_k - 5780, 2))
                    + (-7.6364e-12 * power(stellar_effective_temp_k - 5780, 3))
                    + (-1.1950e-15 * power(stellar_effective_temp_k - 5780, 4)),
                    0
                ),
                0
            )
        ) AS hz_inner_optimistic_au,

        -- Optimistic outer (Early Mars)
        sqrt(
            greatest(
                stellar_luminosity_solar / nullif(
                    0.3179
                    + (5.4513e-5 * (stellar_effective_temp_k - 5780))
                    + (1.5313e-9 * power(stellar_effective_temp_k - 5780, 2))
                    + (-2.7786e-12 * power(stellar_effective_temp_k - 5780, 3))
                    + (-4.8997e-16 * power(stellar_effective_temp_k - 5780, 4)),
                    0
                ),
                0
            )
        ) AS hz_outer_optimistic_au

    FROM stellar_calcs
),

planet_scores AS (
    SELECT
        *,

        (1 - abs(planet_radius_earth - 1.0) / (planet_radius_earth + 1.0)) AS s_radius,
        (1 - abs(planet_density_gcm3 - 5.51) / (planet_density_gcm3 + 5.51)) AS s_density,
        CASE
            WHEN planet_radius_earth = 0 OR planet_mass_earth = 0 THEN null
            ELSE (
                1 - abs(sqrt(planet_mass_earth / planet_radius_earth) - 1.0)
                / (sqrt(planet_mass_earth / planet_radius_earth) + 1.0)
            )
        END AS s_escape,
        -- compare to earths equilibrium temp which is 255k not 288k
        (1 - abs(equilibrium_temp_k - 255.0) / (equilibrium_temp_k + 255.0)) AS s_temp,

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

    FROM hz_boundaries

),

scored AS (
    SELECT
        *,

        /* ESI:
            how similar is this planet to Earth across its key physical properties?
            It produces a single number where 1.0 means identical to Earth and 0 means completely alien.
            The reason it multiplies four individual similarities together
            rather than averaging them is intentional — it's punishing.
            If any single property is wildly un-Earth-like, the whole score collapses toward zero.
            A planet that's the right size and density but has a surface temperature of 700K should score very low overall,
            not average out to something misleadingly moderate.
        */
        power(s_radius, 0.57 / 4.0)
        * power(s_density, 1.07 / 4.0)
        * power(s_escape, 0.70 / 4.0)
        * power(s_temp, 5.58 / 4.0) AS esi_score,

        /*orbital stability:
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
            WHEN orbital_eccentricity < 0.1 THEN 'Stable'
            WHEN orbital_eccentricity <= 0.3 THEN 'Moderate'
            WHEN orbital_eccentricity > 0.3 THEN 'Unstable'
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

        /* Habitability zone distance:
        Intuitively this is just normalizing the planet's position onto a -1 to +1 scale where the HZ boundaries are the endpoints.
        */
        (2 * orbital_semi_major_axis_au - hz_inner_conservative_au - hz_outer_conservative_au)
        / nullif(hz_outer_conservative_au - hz_inner_conservative_au, 0) AS hzd_score

    FROM planet_scores
)

SELECT
    *,

    CASE
        WHEN
            planet_mass_earth IS NOT null
            AND planet_radius_earth IS NOT null
            AND planet_density_gcm3 IS NOT null
            AND equilibrium_temp_k IS NOT null
            AND orbital_semi_major_axis_au IS NOT null
            AND stellar_luminosity_log_solar IS NOT null
            AND stellar_effective_temp_k IS NOT null
            THEN 'Full'
        WHEN
            planet_mass_earth IS NOT null
            AND planet_radius_earth IS NOT null
            AND orbital_semi_major_axis_au IS NOT null
            AND stellar_luminosity_log_solar IS NOT null
            THEN 'Partial'
        ELSE 'Minimal'
    END AS data_completeness

FROM scored
