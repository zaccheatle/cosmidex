"""Dagster Definitions wiring: assets, the weekly ingestion job, and its schedule."""

from dagster import (
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_modules,
)

from cosmidex_pipeline import assets  # noqa: TID252

all_assets = load_assets_from_modules([assets])

nasa_exoplanets_job = define_asset_job(
    name="nasa_exoplanets_job", selection=all_assets
)

nasa_exoplanets_schedule = ScheduleDefinition(
    job=nasa_exoplanets_job,
    cron_schedule="0 6 * * 1",  # Monday 6am
)

defs = Definitions(
    assets=all_assets,
    jobs=[nasa_exoplanets_job],
    schedules=[nasa_exoplanets_schedule],
)
