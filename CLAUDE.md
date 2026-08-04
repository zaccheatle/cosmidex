# CosmiDex

A Pokédex-style cosmic explorer app: NASA confirmed exoplanets (PSCompPars dataset) shown as interactive cards with AI-generated artwork, Earth-relative stats, habitability scores, and experiential descriptions. Solo full-stack data engineering portfolio project — displays all potentially habitable planets (habitability_tier IN Tier 1/2/3, currently 75 of 6,324 confirmed exoplanets), ordered by `esi_score DESC`. Note: an earlier `is_notable` curation flag was removed, and the display scope changed from a fixed top-N-by-ESI to a dynamic tier-based set on 2026-07-30 (ordering by ESI alone could surface Non-Habitable planets that just happened to score high on physical similarity but sit outside the habitable zone).

## Stack

| Layer | Technology |
|---|---|
| Raw data | NASA Exoplanet Archive TAP service (PSCompPars) |
| Orchestration | Dagster (local dev → Dagster Cloud Serverless) |
| Validation | Python dataclasses (`ExoplanetRecord`) |
| Database | Postgres (Docker local → AWS RDS) |
| Transformation | dbt (Bronze → Silver → Gold) |
| API | FastAPI |
| Frontend | React + Vite |
| Images | AWS S3 + Google Gemini (gemini-3.1-flash-image) |
| Descriptions | Google Gemini (gemini-3.5-flash) |
| Infra | Terraform (AWS), GitHub Actions CI/CD |
| Planned AI chat | Claude API + MCP tools + pgvector RAG |

## Project layout

- `cosmidex_pipeline/` — Dagster project. `assets.py` (assets), `definitions.py` (wiring), `models.py` (dataclasses + validation), `utils.py` (hashing/helpers)
- `cosmidex_dbt/` — dbt project. `models/staging/` (Silver views), `models/marts/` (Gold materialized views)
- `cosmidex_api/` — FastAPI (`main.py`, `database.py`)
- `cosmidex_frontend/` — React + Vite
- `src/` — legacy pipeline scripts (NASA extractor, DB loader, image/description generation) being superseded by `cosmidex_pipeline/`
- `sql/` — raw SQL migrations
- `terraform/` — AWS infra (planned)

## Architecture decisions

- **No CDC** — full reload on change; dataset is ~6300 rows with infrequent updates, so CDC complexity isn't justified.
- **File-level hash check** — hash the full NASA DataFrame, compare to `raw.pipeline_state`; skip the pipeline entirely if unchanged, log new `pl_name` values if changed.
- **Dataclass validates PKs only** — `ExoplanetRecord` checks `pl_name`/`hostname` exist and are populated; all ~700 NASA columns pass through to Bronze unchanged. Don't add broader schema validation here — that's dbt's job downstream.
- **Generic validator** — `parse_row(row, data_class)` / `validate_records(df, data_class)` in `models.py` work for any dataclass, not just `ExoplanetRecord` (reused for HWC and future datasets).
- **Dagster Cloud Serverless, not ECS** — simpler for a solo project, free tier covers it.
- **RAG + MCP hybrid (planned, M7)** — MCP for structured SQL queries, pgvector RAG for unstructured research docs.

## Database schema

- **Bronze (raw)**: `raw.exoplanets`, `raw.hwc`, `raw.pipeline_state`, `raw.pipeline_audit` (planned), `raw.change_log` (planned)
- **Silver (staging, dbt views)**: `staging.stg_exoplanets`
- **Gold (marts, dbt materialized views)**: `marts.mart_habitability_scores`, `marts.mart_planet_profile`, `marts.mart_planet_image_prompt`
- **App tables (not dbt-managed)**: `marts.planet_images`, `marts.planet_descriptions`

## Habitability scoring

- **ESI**: weighted product of radius/density/escape-velocity/temperature similarity to Earth (temp weighted heaviest, 5.58)
- **HZD**: `(2 × orbital_distance − hz_inner − hz_outer) / (hz_outer − hz_inner)`; 0 = center of HZ, ±1 = edges
- **Tiers**: tier_1 (ESI ≥0.8, in HZ, rocky, low eccentricity, G/K star) → tier_2 (ESI ≥0.6, in HZ, rocky) → tier_3 (in HZ only) → non_habitable

## Gotchas

- `to_sql(if_exists="replace")` fails when dependent dbt views exist on that table — `DROP ... CASCADE` first.
- Postgres `Decimal` doesn't JSON-serialize by default — use the `DecimalEncoder` in FastAPI responses.
- dbt schema macro (`generate_schema_name.sql`) is required, or schemas get prefixed with the target schema name.
- `planet_stats` grid CSS needs `min-height: 0` on all flex parents or scrolling breaks.
- Tooltip needs `position: fixed` + `createPortal` to avoid overflow clipping.
- Check `!= null` explicitly for eccentricity — `0` is falsy in JS and gets misread as "unknown".
- pandas reads `disc_year` as `int64`, not `str` — dataclass field must be `Optional[int]`.
- `pd.util.hash_pandas_object` returns an ExtensionArray — use `.to_numpy().tobytes()` before hashing.
- `.tmp_dagster_home_*/` is Dagster temp storage — keep it gitignored.

## Current focus (M1: Dagster pipeline)

Built: `raw_nasa_data`, `validated_nasa_data`.
In progress: `check_file_hash` (compare hash to `raw.pipeline_state`, skip if unchanged, detect new planets), `load_bronze` (DROP CASCADE + full reload + store new hash), `audit_log` (write run metadata to `raw.pipeline_audit`).
Next up: weekly Dagster schedule, then `generate_descriptions.py` (Gemini, mirrors the `generate_images.py` pattern in `src/`).

See milestone roadmap (M2 dbt, M3 API, M4 frontend, M5 AWS infra, M6 CI/CD, M7 MCP chat & RAG) in project history if needed — ask if you want it re-summarized.
