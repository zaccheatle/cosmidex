"""Dagster Definitions wiring: assets, the weekly ingestion job, and its schedule."""

from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_modules,
)

from cosmidex_pipeline import assets_exoplanets, assets_galaxies  # noqa: TID252

all_assets = load_assets_from_modules([assets_exoplanets, assets_galaxies])

# EXOPLANETS
nasa_exoplanets_job = define_asset_job(
    name="nasa_exoplanets_job",
    selection=AssetSelection.groups("exoplanets"),
)

nasa_exoplanets_schedule = ScheduleDefinition(
    job=nasa_exoplanets_job, cron_schedule="0 4 * * 1"
)

# NGC OBJECTS
ngc_objects_job = define_asset_job(
    name="ngc_objects_job",
    selection=AssetSelection.groups("galaxies"),
)

ngc_objects_schedule = ScheduleDefinition(
    job=ngc_objects_job, cron_schedule="0 4 * * 1"
)


# DEFINITIONS
defs = Definitions(
    assets=all_assets,
    jobs=[nasa_exoplanets_job, ngc_objects_job],
    schedules=[nasa_exoplanets_schedule, ngc_objects_schedule],
)
