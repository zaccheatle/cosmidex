# CosmiDex — Project Context & Handoff Document

**Purpose:** This document gives a Claude instance full context on the CosmiDex project — architecture, current state, roadmap, and technical decisions made to date. Pass this file as context to pick up where the previous conversation left off.

---

## What is CosmiDex?

**CosmiDex: A Codex for the Cosmos** — a Pokédex-style cosmic explorer app that displays exoplanets as interactive cards with AI-generated artwork, Earth-relative stats, habitability scores, and experiential descriptions. Built as a full-stack data engineering portfolio project covering ingestion, transformation, API, frontend, orchestration, and AI layers.

Currently focused on NASA's confirmed exoplanet catalog (PSCompPars dataset) displaying the **top 50 planets** ordered by `is_notable DESC, esi_score DESC`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Raw data source | NASA Exoplanet Archive TAP service (PSCompPars dataset) |
| Orchestration | Dagster (local dev → Dagster Cloud Serverless) |
| Data validation | Python dataclasses (ExoplanetRecord) |
| Database | Postgres (Docker local → AWS RDS production) |
| Transformation | dbt (Bronze → Silver → Gold) |
| API | FastAPI |
| Frontend | React + Vite |
| Image storage | AWS S3 |
| Image generation | OpenAI DALL-E 3 |
| Description generation | OpenAI GPT-4o |
| Infrastructure | Terraform (AWS) |
| CI/CD | GitHub Actions |
| AI chat layer | Claude API + MCP tools + pgvector RAG (planned) |

---

## Project Structure

```
cosmidex/
├── cosmidex_pipeline/           ← Dagster project (orchestration)
│   └── cosmidex_pipeline/
│       ├── __init__.py
│       ├── assets.py            ← Dagster assets
│       ├── definitions.py       ← wires assets + resources
│       ├── models.py            ← dataclasses + validation
│       └── utils.py             ← hash_dataframe and helpers
├── cosmidex_dbt/                ← dbt project
│   ├── dbt_project.yml
│   ├── macros/
│   │   └── generate_schema_name.sql
│   └── models/
│       ├── staging/
│       │   ├── _sources.yml
│       │   └── stg_exoplanets.sql
│       └── marts/
│           ├── mart_habitability_scores.sql
│           ├── mart_planet_profile.sql
│           └── mart_planet_image_prompt.sql
├── cosmidex_api/                ← FastAPI
│   ├── database.py
│   └── main.py
├── cosmidex_frontend/           ← React + Vite
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       └── components/
│           └── Tooltip.jsx
├── src/                         ← legacy pipeline scripts
│   ├── exoplanet_extractor.py   ← NASA TAP query builder
│   ├── db_loader.py             ← SQLAlchemy Postgres loader
│   ├── pipeline.py              ← original run_pipeline()
│   ├── generate_images.py       ← DALL-E 3 image generation
│   └── generate_descriptions.py ← GPT-4o descriptions (in progress)
├── sql/                         ← raw SQL migrations
│   └── pipeline_state.sql       ← pipeline state tracking table
├── terraform/                   ← AWS infrastructure (planned)
├── docs/
├── tests/
├── docker-compose.yml
├── requirements.txt
└── .env
```

---

## Database Schema

### Raw layer (Bronze)
- `raw.exoplanets` — full NASA PSCompPars dataset, all columns, loaded via Dagster pipeline
- `raw.hwc` — Habitable World Catalog dataset
- `raw.pipeline_state` — pipeline run state tracking (hash, timestamp, planet count)
- `raw.pipeline_audit` — run metadata per execution (planned)
- `raw.change_log` — new planet detections per run (planned)

### Staging layer (Silver) — dbt views
- `staging.stg_exoplanets` — cleaned, renamed columns from raw

### Marts layer (Gold) — dbt materialized views
- `marts.mart_habitability_scores` — ESI score, HZD score, habitability tier, habitable zone membership
- `marts.mart_planet_profile` — full display stats, descriptions, Earth comparisons, travel times
- `marts.mart_planet_image_prompt` — AI image prompts for DALL-E 3

### Application tables (not dbt managed)
- `marts.planet_images` — S3 image URLs per planet
- `marts.planet_descriptions` — GPT-4o experiential descriptions (in progress)

---

## Dagster Pipeline — Current State

### Assets built and working:
1. `raw_nasa_data` — downloads NASA PSCompPars via TAP API, returns full DataFrame
2. `validated_nasa_data` — validates PKs (pl_name, hostname) via ExoplanetRecord dataclass, returns full DataFrame with all NASA columns intact

### Assets in progress:
3. `check_file_hash` — hash full DataFrame, compare to `raw.pipeline_state`, skip if unchanged, detect new planets
4. `load_bronze` — full reload to `raw.exoplanets` with CASCADE drop, store new hash in pipeline_state
5. `audit_log` — write run metadata to `raw.pipeline_audit`

### Architecture decisions made:
- **No CDC** — full reload on change is sufficient for this dataset size (~6300 rows, infrequent updates)
- **File hash check** — skip pipeline entirely if NASA data unchanged since last run
- **New planet detection** — log any new `pl_name` values on each changed run
- **Dataclass as PK validator only** — `ExoplanetRecord` validates PKs exist and are populated; all NASA columns pass through to Bronze unchanged
- **Generic validator** — `parse_row(row, data_class)` and `validate_records(df, data_class)` work for any dataclass, not just ExoplanetRecord

### Key files:

**`models.py`**
```python
@dataclass
class ExoplanetRecord:
    pl_name: str = field(metadata={"pk": True})
    hostname: str = field(metadata={"pk": True})

def parse_row(row: dict, data_class: type[T]) -> T:
    # validates PKs only, raises ValueError if missing/blank
    
def validate_records(df: pd.DataFrame, data_class: type[T]) -> tuple[list[T], list[dict]]:
    # loops rows, catches PK failures, returns (valid_rows, invalid_rows)
    # valid_rows = original full dicts (all NASA columns intact)
```

**`utils.py`**
```python
def hash_dataframe(df: pd.DataFrame) -> str:
    # sorts by pl_name, hashes with pd.util.hash_pandas_object
    # returns md5 hex string
```

---

## dbt Models

### stg_exoplanets.sql (Silver — view)
Selects and renames critical columns from `raw.exoplanets`:
- Identity: `pl_name → planet_name`, `hostname → host_star_name`, `disc_year → discovery_year`
- Planet physical: radius, mass, density, eccentricity, orbital period, insolation, equilibrium temp
- Stellar: effective temp, luminosity, mass, radius, age, surface gravity, metallicity
- Null flags: `planet_radius_earth_flag`, `planet_mass_earth_flag` etc
- `has_minimum_habitability_data` — boolean, True if all 5 critical fields present

### mart_habitability_scores.sql (Gold — materialized view)
- `stellar_luminosity_solar` — luminosity converted from log scale
- `hz_inner/outer_conservative_au` and `hz_inner/outer_optimistic_au` — habitable zone boundaries
- `equilibrium_temp_k_final` — NASA value or calculated fallback
- `eccentricity_risk` — low/moderate/high/unknown
- `hz_membership` — conservative_hz/optimistic_hz/outside_hz
- `escape_velocity_earth` — derived from mass/radius
- `esi_score` — Earth Similarity Index (0-1)
- `hzd_score` — Habitable Zone Distance (-1 to +1)
- `habitability_tier` — tier_1/tier_2/tier_3/non_habitable
- `is_notable` — boolean, 13 manually flagged famous planets
- `data_completeness` — full/partial/minimal

### mart_planet_profile.sql (Gold — materialized view)
Full display model combining staging + habitability scores + derived descriptions:
- Distance in light years, travel time, radio signal descriptions
- Temperature descriptions (Köppen classification)
- Planet type (PHL classification), size class, gravity description
- Star type, star temperature, star age descriptions
- Orbital distance, year length, season, weather estimations

### mart_planet_image_prompt.sql (Gold — materialized view)
- `image_prompt` — concatenated DALL-E 3 prompt string

---

## API Endpoints (FastAPI)

Base URL: `http://127.0.0.1:8000` (local)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/planets` | Top 50 planets ordered by `is_notable DESC, esi_score DESC` |
| GET | `/planets/notable/list` | 13 notable planets with image_url |
| GET | `/planets/tier/{tier}` | Filter by habitability tier |
| GET | `/planets/search/{query}` | ILIKE search by planet name |
| GET | `/planets/{planet_name}` | Single planet full detail |

Planned additions:
- `/planets` filter params (tier, planet type, star type, ESI range)
- `/audit/latest` — latest pipeline run metadata
- API key authentication

---

## Frontend (React)

Single page app, no routing. Layout:
```
┌─────────────────────────┬─────────────────────────┐
│  🪐 CosmiDex            │  Filter by Tier: [btns]  │
├─────────────────────────┼─────────────────────────┤
│                         │  Planet name             │
│    AI Planet Image      │  Stats in 2-column grid  │
│    (fills left half)    │  (scrollable)            │
├─────────────────────────┴─────────────────────────┤
│  ← Previous    1 / 50    Next →                   │
└───────────────────────────────────────────────────┘
```

Stats organized into sections: Identity, Solar System, Orbit, Planet, Habitability.

Planned additions:
- Filter controls (tier, planet type, ESI range)
- Sort controls
- Chat UI shell (prep for M7)
- Loading skeletons and error states

---

## The 13 Notable Planets

| Planet | Tier | ESI | Notes |
|---|---|---|---|
| TRAPPIST-1 d | Tier 2 | 0.799 | Most Earth-like by ESI |
| Teegarden's Star b | Tier 2 | 0.759 | Red dwarf |
| TOI-700 e | Tier 2 | 0.741 | Red dwarf |
| Ross 128 b | Tier 2 | 0.707 | Red dwarf |
| TOI-700 d | Tier 2 | 0.681 | Red dwarf |
| TRAPPIST-1 e | Tier 3 | 0.562 | Red dwarf |
| Kepler-452 b | Tier 3 | 0.432 | Sun-like star |
| Kepler-442 b | Tier 3 | 0.417 | Orange dwarf |
| K2-18 b | Tier 3 | 0.389 | Hycean candidate, JWST biosignature |
| Proxima Cen b | Tier 3 | 0.375 | Closest exoplanet at 4.2 ly |
| TRAPPIST-1 f | Tier 3 | 0.357 | Red dwarf |
| LHS 1140 b | Tier 3 | 0.264 | Red dwarf |
| Kepler-186 f | Tier 3 | 0.163 | First Earth-sized planet in HZ |

---

## Habitability Scoring

**ESI (Earth Similarity Index):** product of four component similarities:
- Radius (weight 0.57), Density (weight 1.07), Escape velocity (weight 0.70), Temperature (weight 5.58, most critical)

**HZD (Habitable Zone Distance):**
- `(2 × orbital_distance - hz_inner - hz_outer) / (hz_outer - hz_inner)`
- 0 = center of HZ, ±1 = edges, beyond ±1 = outside HZ

**Habitability Tier logic:**
- Tier 1: ESI ≥ 0.8 AND in HZ AND rocky AND low eccentricity AND G/K star
- Tier 2: ESI ≥ 0.6 AND in HZ AND rocky
- Tier 3: in HZ only
- Non-habitable: everything else

**Current results:** 0 Tier 1, 11 Tier 2, 288 Tier 3, 5175 Non-habitable

---

## Deployment Architecture

### Local (current)
```
Docker Compose → Postgres
Dagster dev → pipeline assets
FastAPI → uvicorn
React → Vite dev server
```

### Production (planned)
```
Dagster Cloud Serverless → orchestration UI, scheduling, alerting
AWS RDS → Postgres
AWS S3 → planet images
AWS EC2 → FastAPI (Dockerised)
GitHub Actions → CI/CD (test → build → deploy)
```

No ECS — Dagster Cloud Serverless handles orchestration, FastAPI runs on a single EC2 instance. Simpler than ECS for a solo project.

---

## Project Milestones

### M1 — NASA Exoplanet Data Pipeline (Dagster) — IN PROGRESS
1. ✓ Set up Dagster assets and project structure
2. ✓ Add ExoplanetRecord dataclass validation
3. ✗ Implement file-level hash check + new planet detection
4. ✗ Full reload to Bronze with CASCADE + store hash in pipeline_state
5. ✗ Add audit log asset + weekly Dagster schedule

### M2 — dbt Models
1. Audit and update staging models for pipeline changes
2. Convert marts to incremental models
3. Add dbt source freshness and schema tests
4. Add custom generic tests (ESI range, row count anomaly)
5. Add full dbt documentation and exposures

### M3 — API
1. Update /planets to return top 50 (is_notable DESC, esi_score DESC LIMIT 50)
2. Add advanced search and filter params
3. Add /audit/latest endpoint
4. Add API key authentication
5. Write pytest tests for all endpoints

### M4 — Frontend
1. Audit and update frontend for API changes
2. Add filter controls for top 50
3. Add sort controls
4. Add chat UI shell component (prep for M7)
5. Add loading states and error handling

### M5 — AWS Infrastructure
1. Set up Dagster Cloud Serverless
2. Dockerise FastAPI and deploy to EC2
3. Terraform — S3 and RDS
4. Terraform — IAM and networking
5. End-to-end deploy confirmation

### M6 — CI/CD (GitHub Actions)
1. Write test workflow (pytest + dbt test on every push)
2. Write build workflow (Docker image → ECR on push to main)
3. Write deploy workflow (ECS/EC2 deploy after successful build)
4. Add GitHub environment secrets
5. Add branch protection rules

### M7 — MCP Chat & RAG
1. Set up pgvector and document ingestion Dagster asset
2. Write MCP server tools (query_planets, get_planet, search_documents)
3. Wire Claude API with hybrid MCP + RAG routing
4. Build React chat component with starter questions
5. Add enrichment documents (NASA papers, JWST reports)

---

## Key Technical Decisions

| Decision | Choice | Reason |
|---|---|---|
| CDC vs full reload | Full reload | Dataset is ~6300 rows, infrequent updates, CDC complexity not justified |
| Change detection | File-level hash | Skip pipeline entirely if no changes, log new planets if changed |
| Dataclass scope | PK validation only | All NASA columns pass through to Bronze unchanged |
| Generic validator | parse_row/validate_records accept any dataclass | Reusable for HWC, solar system bodies, future datasets |
| Display scope | Top 50 planets | Curated experience, notable planets always included |
| Orchestration | Dagster Cloud Serverless | Avoids ECS complexity, free tier covers solo project |
| Streaming vs batch | Batch | NASA data updates weekly, streaming adds no value |
| RAG vs MCP | Hybrid both | MCP for structured SQL queries, RAG for unstructured research docs |

---

## Environment Variables (.env)

```
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_DB=planetary_data
POSTGRES_USER=
POSTGRES_PASSWORD=
OPENAI_API_KEY=
AWS_REGION=us-east-1
AWS_S3_BUCKET=planetary-data-images
NASA_URL=https://exoplanetarchive.ipac.caltech.edu/TAP/sync
HWC_URL=
```

AWS credentials from `~/.aws/credentials` [default] profile.

---

## Known Issues / Gotchas

- `to_sql` with `if_exists="replace"` fails when dependent dbt views exist — use `DROP ... CASCADE` before reload
- Postgres `Decimal` types don't serialize to JSON automatically — use `DecimalEncoder` in FastAPI
- dbt schema macro required — without it schemas get prefixed with target schema name
- `planet_stats` grid CSS requires `min-height: 0` on all flex parents for proper scrolling
- Tooltip `position: fixed` + `createPortal` required to avoid overflow clipping
- `0` eccentricity shows as 'unknown' without `!= null` check (JS falsy value bug)
- NASA PSCompPars has ~700 columns — dataclass only validates PKs, all columns pass through to Bronze
- pandas reads `disc_year` as `int64` not `str` — dataclass uses `Optional[int]`
- `pd.util.hash_pandas_object` returns ExtensionArray — use `.to_numpy().tobytes()` for hashing
- Dagster temp storage at `.tmp_dagster_home_*/` — add to `.gitignore`

---

## Immediate Next Tasks

1. **Complete `check_file_hash` asset** — query `raw.pipeline_state`, compare hashes, detect new planets, skip if unchanged
2. **Complete `load_bronze` asset** — DROP CASCADE + full reload + store new hash
3. **Complete `audit_log` asset** — write run metadata to `raw.pipeline_audit`
4. **Add weekly Dagster schedule** — `@schedule` decorator, Monday 6am
5. **Complete `generate_descriptions.py`** — GPT-4o experiential planet descriptions following same pattern as `generate_images.py`

---

*Last updated: July 2026. Pass this document to a new Claude instance to continue where the previous conversation left off.*
