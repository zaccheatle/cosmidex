-- Model to rename and properly type raw hwc data

{{ config(materialized='view') }}

SELECT
    "Name"::varchar(100) AS hwc_planet_name,
    "Type"::varchar(150) AS hwc_planet_type,
    "Detection Method"::varchar(150) AS hwc_discovery_method,
    "Mass<br>(M<sub>E</sub>)"::numeric AS hwc_planet_mass_earth,
    "Radius<br>(R<sub>E</sub>)"::numeric AS hwc_planet_radius_earth,
    "Flux<br>(S<sub>E</sub>)"::numeric AS hwc_average_stellar_flux_earth,
    "<i>T<sub>surf</sub></i><br>(K)"::numeric AS hwc_surface_temperature,
    "Period<br>(days)"::numeric AS hwc_orbital_period,
    "Distance<br>(ly)"::numeric AS hwc_distance_from_earth,
    "Age<br>(Gy)"::numeric AS hwc_host_star_age,
    "ESI"::numeric AS hwc_esi_score
FROM {{ source('raw', 'hwc') }}
