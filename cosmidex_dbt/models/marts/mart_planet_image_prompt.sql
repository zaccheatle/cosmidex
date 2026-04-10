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
        'photorealistic sci-fi concept art, cinematic lighting, detailed, atmospheric, grounded in reality' AS style_suffix,

        CASE
            WHEN planet_type = 'rocky' THEN 'A rocky terrestrial planet'
            WHEN planet_type = 'sub-earth' THEN 'A small rocky world'
            WHEN planet_type = 'sub-neptune' THEN 'A sub-Neptune planet with a thick atmosphere'
            WHEN planet_type = 'neptune-like' THEN 'A Neptune-like ice giant'
            WHEN planet_type = 'gas giant' THEN 'A massive gas giant'
        END AS planet_base,

        CASE
            WHEN planet_type = 'rocky' AND temperature_description = 'frozen' THEN 'covered in vast ice sheets and frozen oceans'
            WHEN planet_type = 'rocky' AND temperature_description = 'cold' THEN 'with a cold barren rocky surface'
            WHEN planet_type = 'rocky' AND temperature_description = 'temperate' THEN 'with potential liquid water and blue oceans visible'
            WHEN planet_type = 'rocky' AND temperature_description = 'warm' THEN 'with a warm dense atmosphere and arid surface'
            WHEN planet_type = 'rocky' AND temperature_description = 'hot' THEN 'with a scorching volcanic surface and lava flows'
            WHEN planet_type = 'rocky' AND temperature_description = 'scorching' THEN 'with a molten surface, extreme volcanic activity'
            WHEN planet_type = 'sub-earth' AND temperature_description = 'frozen' THEN 'a tiny frozen world with a thin icy crust'
            WHEN planet_type = 'sub-earth' AND temperature_description = 'cold' THEN 'a small cold rocky world with a thin atmosphere'
            WHEN planet_type = 'sub-earth' AND temperature_description = 'temperate' THEN 'a small rocky world with a surprisingly mild climate'
            WHEN planet_type = 'sub-earth' AND temperature_description = 'warm' THEN 'a small dry rocky world baked by its star'
            WHEN planet_type = 'sub-earth' AND temperature_description = 'hot' THEN 'a tiny scorched rock with no atmosphere'
            WHEN planet_type = 'sub-earth' AND temperature_description = 'scorching' THEN 'a tiny molten world, surface glowing with heat'
            WHEN planet_type = 'neptune-like' AND temperature_description = 'frozen' THEN 'a frozen ice giant with deep blue and white cloud bands'
            WHEN planet_type = 'neptune-like' AND temperature_description = 'cold' THEN 'a cold ice giant with swirling pale blue atmosphere'
            WHEN planet_type = 'neptune-like' THEN 'an ice giant with deep blue swirling cloud layers'
            WHEN planet_type = 'gas giant' THEN 'with swirling storm bands and turbulent cloud layers'
            WHEN planet_type = 'sub-neptune' THEN 'shrouded in thick atmospheric haze'
            ELSE 'with an alien landscape unlike anything in our solar system'
        END AS temperature_character,

        CASE
            WHEN star_type_description = 'Red dwarf' THEN 'illuminated by the dim red glow of a red dwarf star'
            WHEN star_type_description = 'Orange dwarf' THEN 'bathed in the warm orange light of its host star'
            WHEN star_type_description = 'Sun-like star' THEN 'lit by a familiar yellow sun-like star'
            WHEN star_type_description = 'Warm yellow star' THEN 'under the bright light of a warm yellow star'
            WHEN star_type_description = 'Hot blue-white star' THEN 'under the intense blue-white light of a hot star'
            ELSE 'orbiting an unknown type of star'
        END AS star_lighting,

        CASE
            WHEN habitability_tier = 'tier_1_strong_candidate' OR habitability_tier = 'tier_2_moderate_candidate' THEN 'a potentially habitable world'
            WHEN habitability_tier = 'tier_3_in_hz_only' THEN 'orbiting within its star''s habitable zone'
            WHEN habitability_tier = 'non_habitable' THEN ''
        END AS habitability_context

    FROM base
)

SELECT

    planet_name,
    host_star_name,
    habitability_tier,
    is_notable,
    coalesce(planet_base, '')
    || ', ' || coalesce(temperature_character, '')
    || ', ' || coalesce(star_lighting, '')
    || CASE
        WHEN habitability_context != '' AND habitability_context IS NOT NULL
            THEN ', ' || habitability_context
        ELSE ''
    END
    || ', ' || coalesce(style_suffix, '')
        AS image_prompt

FROM prompt_parts
