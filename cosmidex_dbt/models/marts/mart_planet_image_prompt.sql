-- data mart to provide image prompts for AI generation of planet images

{{ config(materialized='materialized_view') }}

WITH base AS (
    SELECT *
    FROM {{ ref('mart_planet_profile') }}
),

-- Composition drives a flat color/texture treatment for the exoplanet sphere
-- (a coarse but real, data-derived category from mart_planet_profile) — not
-- invented surface features like continents, oceans, or volcanoes.
prompt_parts AS (
    SELECT
        *,
        CASE
            WHEN planet_composition = 'Rock/Iron'
                THEN 'a dark grey-brown rocky sphere with a metallic sheen, no surface markings'
            WHEN planet_composition = 'Rock/Silicate'
                THEN 'a reddish-brown rocky sphere with a matte stony texture, no surface markings'
            WHEN planet_composition = 'Water/Ice'
                THEN 'a deep blue sphere with pale white icy patches, no surface markings'
            WHEN planet_composition = 'Ice Giant'
                THEN 'a smooth pale blue-green sphere with faint cloud banding'
            WHEN planet_composition = 'Gas Giant'
                THEN 'a tan and white sphere with bold horizontal cloud bands'
            ELSE 'a grey sphere with an unknown composition'
        END AS composition_treatment
    FROM base
)

SELECT
    planet_name,
    host_star_name,
    habitability_tier,
    'A cartoon-style illustration comparing two spheres floating side by side against a starfield, '
    || 'for a size comparison. On the left: Earth, recognizable with blue oceans, green-brown '
    || 'continents, and white clouds, shown at a reference size. On the right, positioned at the '
    || 'same visual distance from the viewer: a second sphere representing an exoplanet, rendered '
    || 'at exactly ' || round(planet_radius_earth::numeric, 2) || 'x Earth''s diameter to show the '
    || 'true relative scale, textured as ' || composition_treatment || '. Both spheres are lit '
    || 'consistently from the same direction. '
    || 'Vibrant cel-shaded cartoon/anime art style, bold clean black outlines, simplified shapes, '
    || 'saturated flat colors, not photorealistic. No people, characters, creatures, animals, or '
    || 'figures of any kind. No text, words, letters, logos, or watermarks anywhere in the image.'
        AS image_prompt_body

FROM prompt_parts
