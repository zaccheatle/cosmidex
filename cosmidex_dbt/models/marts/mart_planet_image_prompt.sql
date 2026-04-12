-- data mart to provide image prompts for AI generation of planet images 

{{ config(materialized='materialized_view') }}

-- Base CTE
WITH base AS (
    SELECT *
    FROM {{ ref('mart_planet_profile') }}
),

prompt_parts AS (
    SELECT
        *,

        -- Style suffix
        'viewed from orbit, a single prefectly spherical planet with a scientifically accurate, highly detailed, photorealistic NASA concept art style.'
            AS style_suffix,

        -- Block 1: Planet visual appearance (composition + equilibrium temp)
        CASE
            WHEN planet_composition = 'Rock/Iron' AND estimated_surface_temp_celsius > 500
                THEN 'a dense iron-rich exoplanet with a molten metal surface, rivers of liquid iron, no atmosphere, black sky'
            WHEN planet_composition = 'Rock/Iron' AND estimated_surface_temp_celsius > 100
                THEN 'a dark charred iron-rich exoplanet with a thin toxic atmosphere and faint red glow on the horizon'
            WHEN planet_composition = 'Rock/Iron' AND estimated_surface_temp_celsius > 50
                THEN 'a scorched dark basalt exoplanet with a thin haze atmosphere and deep orange sky'
            WHEN planet_composition = 'Rock/Iron' AND estimated_surface_temp_celsius > 18
                THEN 'a dark rocky iron-rich exoplanet with a thin atmosphere and pale sky'
            WHEN planet_composition = 'Rock/Iron' AND estimated_surface_temp_celsius > 0
                THEN 'a grey-black rocky iron-rich exoplanet with possible thin ice at the poles and a pale blue-grey sky'
            WHEN planet_composition = 'Rock/Iron' AND estimated_surface_temp_celsius > -15
                THEN 'a dark rocky iron-rich exoplanet with frost and thin ice sheets across the surface'
            WHEN planet_composition = 'Rock/Iron' AND estimated_surface_temp_celsius > -40
                THEN 'an iron-grey exoplanet covered in frost and ice with a thin cold atmosphere'
            WHEN planet_composition = 'Rock/Iron'
                THEN 'a dark metallic exoplanet buried under thick ice sheets with a black starry sky'

            WHEN planet_composition = 'Rock/Silicate' AND estimated_surface_temp_celsius > 500
                THEN 'a silicate rock exoplanet with glowing lava oceans, violent volcanic eruptions and a thick toxic orange atmosphere'
            WHEN planet_composition = 'Rock/Silicate' AND estimated_surface_temp_celsius > 100
                THEN 'a volcanic silicate rock exoplanet with a thick sulphurous yellow-orange atmosphere similar to Venus'
            WHEN planet_composition = 'Rock/Silicate' AND estimated_surface_temp_celsius > 50
                THEN 'an arid silicate rock exoplanet with red-orange sand dunes and a hazy thick atmosphere'
            WHEN planet_composition = 'Rock/Silicate' AND estimated_surface_temp_celsius > 18
                THEN 'a warm desert silicate exoplanet with scattered clouds and an orange-blue sky'
            WHEN planet_composition = 'Rock/Silicate' AND estimated_surface_temp_celsius > 0
                THEN 'a silicate rocky exoplanet with continental landmasses, blue oceans, white clouds and an Earth-like appearance'
            WHEN planet_composition = 'Rock/Silicate' AND estimated_surface_temp_celsius > -15
                THEN 'a silicate rocky exoplanet with prominent polar ice caps, frozen coastlines and thin cloud cover'
            WHEN planet_composition = 'Rock/Silicate' AND estimated_surface_temp_celsius > -40
                THEN 'a silicate rocky exoplanet with ice-covered surface and frozen oceans with a pale blue atmosphere'
            WHEN planet_composition = 'Rock/Silicate'
                THEN 'a completely frozen silicate exoplanet with thick ice sheets and a white and pale blue appearance'

            WHEN planet_composition = 'Water/Ice' AND estimated_surface_temp_celsius > 100
                THEN 'a steam world exoplanet with thick white cloud cover and boiling oceans hidden below an impenetrable atmosphere'
            WHEN planet_composition = 'Water/Ice' AND estimated_surface_temp_celsius > 18
                THEN 'a global ocean world exoplanet with a deep blue surface, swirling white clouds and no visible land'
            WHEN planet_composition = 'Water/Ice' AND estimated_surface_temp_celsius > 0
                THEN 'a mostly ocean exoplanet with scattered icy landmasses and a blue-white surface'
            WHEN planet_composition = 'Water/Ice' AND estimated_surface_temp_celsius > -15
                THEN 'a partially frozen ocean world exoplanet with blue-white surface and expanding ice sheets'
            WHEN planet_composition = 'Water/Ice'
                THEN 'a completely frozen ice world exoplanet, white and pale blue with no liquid water visible'

            WHEN planet_composition = 'Ice Giant' AND estimated_surface_temp_celsius > 100
                THEN 'a hot ice giant exoplanet with thick swirling blue-white atmosphere and no visible surface'
            WHEN planet_composition = 'Ice Giant' AND estimated_surface_temp_celsius > 0
                THEN 'a blue-green ice giant exoplanet with swirling cloud bands similar to Uranus'
            WHEN planet_composition = 'Ice Giant'
                THEN 'a deep blue ice giant exoplanet with swirling white cloud bands and an icy appearance'

            WHEN planet_composition = 'Gas Giant' AND estimated_surface_temp_celsius > 500
                THEN 'a hot Jupiter gas giant exoplanet with a glowing orange-red atmosphere and massive swirling storms'
            WHEN planet_composition = 'Gas Giant' AND estimated_surface_temp_celsius > 100
                THEN 'a warm gas giant exoplanet with orange and brown cloud bands and intense storm systems'
            WHEN planet_composition = 'Gas Giant' AND estimated_surface_temp_celsius > 0
                THEN 'a cool gas giant exoplanet with pale tan and white cloud bands and large storm systems'
            WHEN planet_composition = 'Gas Giant'
                THEN 'a cold gas giant exoplanet with blue-white cloud bands and subtle atmospheric banding'

            ELSE 'an alien exoplanet with an unknown composition and mysterious appearance'
        END AS planet_base,

        -- Block 2 & 3: Star appearance and lighting
        CASE
            WHEN star_spectral_type LIKE 'Class O%'
                THEN 'with an intensely bright blue-white star visible, casting harsh blue-white light and deep shadows across the scene'
            WHEN star_spectral_type LIKE 'Class B%'
                THEN 'with a bright blue-white star visible, casting cool blue-white light across the scene'
            WHEN star_spectral_type LIKE 'Class A%'
                THEN 'with a brilliant white star visible, casting crisp white light across the scene'
            WHEN star_spectral_type LIKE 'Class F%'
                THEN 'with a warm white star visible, slightly brighter and hotter than our Sun, casting warm white light'
            WHEN star_spectral_type LIKE 'Class G%'
                THEN 'with a familiar yellow-white star visible similar to our Sun, casting warm familiar light'
            WHEN star_spectral_type LIKE 'Class K%'
                THEN 'with a warm orange star visible, casting deep orange-tinted light and warm shadows'
            WHEN star_spectral_type LIKE 'Class M%'
                THEN 'with a small dim red-orange star visible low on the horizon, casting a deep moody red-orange glow'
            WHEN
                star_spectral_type LIKE 'Class L%'
                OR star_spectral_type LIKE 'Class T%'
                OR star_spectral_type LIKE 'Class Y%'
                THEN 'with a barely visible dark red smudge of a failed star, near total darkness'
            ELSE 'with an unknown star casting alien light across the scene'
        END AS star_lighting,

        -- Block 4: Habitability context
        CASE
            WHEN habitability_tier = 'Tier 1' AND estimated_surface_temp_celsius > 10
                THEN 'a potentially habitable world with lush cloud formations, possible ocean shimmer and Earth-like blue-green tones'
            WHEN habitability_tier = 'Tier 1' AND estimated_surface_temp_celsius > 0
                THEN 'a potentially habitable world with thin cloud cover, possible frozen coastlines and muted blue-grey tones'
            WHEN habitability_tier = 'Tier 1'
                THEN 'a cold but potentially habitable world with thick ice sheets and a thin breathable atmosphere'
            WHEN habitability_tier = 'Tier 2' AND estimated_surface_temp_celsius > 10
                THEN 'a potentially habitable world with partial cloud cover and hints of habitability in muted Earth tones'
            WHEN habitability_tier = 'Tier 2'
                THEN 'a cold potentially habitable world with partial ice coverage and a thin atmosphere'
            WHEN habitability_tier = 'Tier 3'
                THEN 'a world within its star''s habitable zone with cloud cover but no obvious signs of life'
            ELSE 'a non-habitable planet'
        END AS habitability_context,

        -- Block 5: Numeric anchors (temperature, size, gravity, atmosphere, composition)
        coalesce('equilibrium temperature ' || round(equilibrium_temp_celsius::numeric, 0)::text || '°C', 'equilibrium temperature unknown') || ', '
        || coalesce(
            'estimated surface temperature ' || round(estimated_surface_temp_celsius::numeric, 0)::text || '°C (assuming Earth-like atmosphere)',
            'estimated surface temperature unknown'
        )
        || ', '
        || coalesce(estimated_planet_climate, 'climate unknown') || ', '
        || coalesce(round(planet_radius_earth::numeric, 2)::text || '× Earth radius', 'radius unknown') || ', '
        || coalesce(round(planet_mass_earth::numeric, 2)::text || '× Earth mass', 'mass unknown') || ', '
        || coalesce(
            round(planet_density_gcm3::numeric, 2)::text || ' g/cm³ density ('
            || CASE
                WHEN planet_density_gcm3 > 5.0 THEN 'denser than Earth, iron-rich interior'
                WHEN planet_density_gcm3 > 3.0 THEN 'similar density to Earth, rocky silicate interior'
                WHEN planet_density_gcm3 > 2.0 THEN 'lower density, likely water or ice rich interior'
                WHEN planet_density_gcm3 >= 1.2 THEN 'low density, ice giant composition'
                WHEN planet_density_gcm3 < 1.2 THEN 'very low density, gas giant composition'
                ELSE 'unknown interior composition'
            END || ')',
            'density unknown'
        ) || ', '
        || coalesce(
            CASE
                WHEN planet_mass_earth IS NOT NULL AND planet_radius_earth IS NOT NULL AND planet_radius_earth > 0
                    THEN
                        'surface gravity ' || round((planet_mass_earth / planet_radius_earth ^ 2)::numeric, 2)::text || '× Earth ('
                        || CASE
                            WHEN (planet_mass_earth / planet_radius_earth ^ 2) > 1.5 THEN 'high gravity, thick dense atmosphere'
                            WHEN (planet_mass_earth / planet_radius_earth ^ 2) > 0.8 THEN 'Earth-like gravity, Earth-like atmosphere'
                            ELSE 'low gravity, thin atmosphere'
                        END || ')'
                ELSE 'gravity unknown'
            END,
            'gravity unknown'
        ) || ', '
        || coalesce(
            CASE
                WHEN planet_mass_earth IS NOT NULL AND planet_radius_earth IS NOT NULL AND planet_radius_earth > 0
                    THEN 'escape velocity ' || round((sqrt(planet_mass_earth / planet_radius_earth) * 11.2)::numeric, 2)::text || ' km/s'
                ELSE 'escape velocity unknown'
            END,
            'escape velocity unknown'
        )
            AS numeric_anchors

    FROM base
)

SELECT
    planet_name,
    host_star_name,
    habitability_tier,
    coalesce(planet_base, '')
    || ', ' || coalesce(star_lighting, '')
    || CASE
        WHEN habitability_context != '' AND habitability_context IS NOT NULL
            THEN ', ' || habitability_context
        ELSE ''
    END
    || ', ' || coalesce(numeric_anchors, '')
    || ', ' || coalesce(style_suffix, '')
        AS image_prompt

FROM prompt_parts
