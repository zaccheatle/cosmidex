# CosmiDex — Project Context & Handoff Document

This document summarizes the full context of the CosmiDex project for a new 
Claude instance to pick up where the previous conversation left off.

---

## Project Overview

**CosmiDex: A Codex for the Cosmos** — a Pokédex-style cosmic explorer app 
that displays exoplanets as interactive cards with AI-generated artwork, 
Earth-relative stats, habitability scores, and experiential descriptions.

Currently focused on NASA's confirmed exoplanet catalog (PSCompPars dataset) 
with plans to expand to solar system bodies, galaxies, black holes, and nebulae.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Raw data | NASA PSCompPars dataset loaded into Postgres |
| Transformation | dbt (models in `planetary_dbt/`) |
| Database | Postgres (Docker, local) |
| API | FastAPI (`planetary_api/main.py`) |
| Frontend | React + Vite (`planetary-frontend/`) |
| Image storage | AWS S3 |
| Image generation | OpenAI DALL-E 3 |
| Description generation | OpenAI GPT-4o (in progress) |
| Future orchestration | AWS MWAA (Airflow) |
| Future deployment | AWS (Terraform) |

---

## Project Structure

```
planetary-data-platform/
├── planetary_dbt/                    ← dbt project
│   ├── dbt_project.yml
│   ├── macros/
│   │   └── generate_schema_name.sql  ← custom schema macro (required)
│   └── models/
│       ├── staging/
│       │   ├── _sources.yml
│       │   └── stg_exoplanets.sql
│       └── marts/
│           ├── mart_habitability_scores.sql
│           ├── mart_planet_profile.sql
│           └── mart_planet_image_prompt.sql
├── planetary_api/
│   ├── database.py                   ← psycopg2 connection
│   └── main.py                       ← FastAPI endpoints
├── src/
│   ├── generate_images.py            ← DALL-E 3 image generation
│   └── generate_descriptions.py      ← GPT-4o description generation (in progress)
├── planetary-frontend/
│   └── src/
│       ├── App.jsx                   ← main React component
│       ├── App.css                   ← styles
│       └── components/
│           └── Tooltip.jsx           ← custom tooltip component
├── .env                              ← credentials (never committed)
├── requirements.txt
└── ROADMAP.md
```

---

## Database Schema

**Raw data:** `planetary_data.raw.exoplanets` — NASA PSCompPars table

**dbt models:**

`staging.stg_exoplanets` — view, cleaned and renamed columns from raw

`marts.mart_habitability_scores` — materialized view, scientific scoring:
- `stellar_luminosity_solar` — luminosity converted from log scale
- `hz_inner/outer_conservative_au` — habitable zone boundaries
- `hz_inner/outer_optimistic_au`
- `equilibrium_temp_k_final` — NASA value or calculated fallback
- `eccentricity_risk` — low/moderate/high/unknown
- `hz_membership` — conservative_hz/optimistic_hz/outside_hz
- `escape_velocity_earth` — derived from mass/radius
- `esi_score` — Earth Similarity Index (0-1)
- `hzd_score` — Habitable Zone Distance (-1 to +1)
- `habitability_tier` — tier_1_strong_candidate/tier_2_moderate_candidate/tier_3_in_hz_only/non_habitable
- `is_notable` — boolean, 13 manually flagged famous planets
- `data_completeness` — full/partial/minimal

`marts.mart_planet_profile` — materialized view, display stats:
- All staging columns
- All habitability score columns
- `distance_light_years` — parsecs × 3.26156
- `equilibrium_temp_celsius` — K - 273.15
- `equilibrium_temp_fahrenheit` — derived from K
- `shuttle_travel_years` — distance × 38544
- `radio_signal_description` — formatted one-way signal travel time
- `temperature_description` — Köppen climate classification (Class A/B/C/D/E/EF/X)
- `planet_type` — PHL classification (Subterran/Terran/Volatile-rich Terran/Likely Terran/Superterran/Superterran — Hycean Candidate/Neptunian/Hot Jovian/Jovian/Super Jovian)
- `size_class` — solar system size reference (Moon sized/Mercury to Mars sized/Mars sized/Earth sized/Super Earth/etc)
- `size_description` — diameter in km + Earth multiplier
- `gravity_description` — m/s² + Earth multiplier
- `star_type_description` — Red dwarf/Orange dwarf/Sun-like star/Warm yellow star/Hot blue-white star
- `star_temp_description` — human comparison (candle flame/welding torch/our Sun/lightning bolt/etc)
- `star_age_description` — age in billions of years with context
- `orbital_distance_description` — AU with solar system reference
- `year_description` — orbital period with context
- `season_description` — inferred from eccentricity and star type
- `weather_estimation` — inferred atmospheric conditions
- `size_description` — Earth-relative size
- `distance_description` — galactic region description
- `shuttle_travel_description` — formatted shuttle travel time
- `galaxy` — hardcoded 'Milky Way'

`marts.mart_planet_image_prompt` — materialized view, AI image prompts:
- `image_prompt` — concatenated prompt string for DALL-E 3

**Application tables (not dbt managed):**

`marts.planet_images` — S3 image URLs:
- `planet_name` (PK)
- `image_url` — permanent S3 URL
- `image_prompt` — prompt used (cache key for invalidation)
- `generated_at`
- `generation_model`

`marts.planet_descriptions` — GPT-4o descriptions (in progress):
- `planet_name` (PK)
- `description` — 3-sentence experiential description
- `generated_at`
- `generation_model`

---

## API Endpoints

Base URL: `http://127.0.0.1:8000` (local)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/planets` | All planets, ordered by notable then ESI |
| GET | `/planets/notable/list` | 13 notable planets with image_url |
| GET | `/planets/tier/{tier}` | Filter by habitability tier |
| GET | `/planets/search/{query}` | ILIKE search by planet name |
| GET | `/planets/{planet_name}` | Single planet full detail |

All responses use `DecimalEncoder` to serialize Postgres Decimal types as floats.

CORS is configured for `http://localhost:5173`.

---

## The 13 Notable Planets

These planets are flagged `is_notable = true` in the database and have 
AI-generated S3 images:

| Planet | Tier | ESI | Notes |
|---|---|---|---|
| TRAPPIST-1 d | Tier 2 | 0.799 | Most Earth-like by ESI, red dwarf, 4 day year |
| Teegarden's Star b | Tier 2 | 0.759 | Red dwarf |
| TOI-700 e | Tier 2 | 0.741 | Red dwarf |
| Ross 128 b | Tier 2 | 0.707 | Red dwarf |
| TOI-700 d | Tier 2 | 0.681 | Red dwarf |
| TRAPPIST-1 e | Tier 3 | 0.562 | Red dwarf |
| Kepler-452 b | Tier 3 | 0.432 | Sun-like star, 385 day year |
| Kepler-442 b | Tier 3 | 0.417 | Orange dwarf |
| K2-18 b | Tier 3 | 0.389 | Hycean candidate, JWST biosignature detection |
| Proxima Cen b | Tier 3 | 0.375 | Closest exoplanet at 4.2 ly |
| TRAPPIST-1 f | Tier 3 | 0.357 | Red dwarf |
| LHS 1140 b | Tier 3 | 0.264 | Red dwarf |
| Kepler-186 f | Tier 3 | 0.163 | First Earth-sized planet in HZ |

---

## Habitability Scoring

**ESI (Earth Similarity Index):** 0-1 score, product of four component similarities:
- Radius (weight 0.57, Earth ref = 1.0)
- Density (weight 1.07, Earth ref = 5.51 g/cm³)
- Escape velocity (weight 0.70, Earth ref = 1.0, derived from mass/radius)
- Temperature (weight 5.58, Earth ref = 288K — highest weight, temperature is most critical)

**HZD (Habitable Zone Distance):**
- Formula: `(2 × orbital_distance - hz_inner - hz_outer) / (hz_outer - hz_inner)`
- 0 = center of HZ, -1 = inner edge, +1 = outer edge, beyond ±1 = outside HZ

**Habitability Tier logic:**
- Tier 1: ESI ≥ 0.8 AND HZD between -1 and 1 AND rocky AND eccentricity not high AND G/K star
- Tier 2: ESI ≥ 0.6 AND in HZ AND rocky
- Tier 3: in HZ only
- Non-habitable: everything else

**Result with current data:** 0 Tier 1, 11 Tier 2, 288 Tier 3, 5175 Non-habitable

---

## Frontend Architecture

**Single page app** — no routing, one immersive screen.

**Layout:**
```
┌─────────────────────────┬─────────────────────────┐
│  🪐 ExoDex              │  Filter by Tier: [btns]  │  ← top-bar (64px)
├─────────────────────────┼─────────────────────────┤
│                         │  Planet name             │
│    AI Planet Image      │  Stats in 2-column grid  │
│    (fills left half)    │  (scrollable)            │
│                         │                          │
├─────────────────────────┴─────────────────────────┤
│  ← Previous    1 / 13    Next →                   │
└───────────────────────────────────────────────────┘
```

**Key React state:**
- `planets` — array of planet objects from API
- `selectedTier` — current filter ('all' or tier string)
- `currentIndex` — index into filteredPlanets array
- `filteredPlanets` — derived from planets filtered by selectedTier

**Tooltip component** (`src/components/Tooltip.jsx`):
- Uses React Portal (`createPortal`) to render into `document.body`
- Uses `useRef` + `getBoundingClientRect()` + `useEffect` to measure actual 
  rendered height and prevent viewport overflow
- Position: fixed, z-index 9999
- Superscript `i` icon using `vertical-align: super`

**Color palette:**
- Background: `#0a0a0f`
- Panel surface: `#12121a`
- Image background: `#050508`
- Accent blue: `#4a9eff` (title, filter label, section headers)
- Muted text: `#8888aa`
- Border: `#1e1e2e`
- Active button: `#4a9eff`

---

## Stats Panel Sections

Stats are organized into four sections with blue section labels:

**Identity (top, no section header):**
Planet name, Planet Type (PHL classification), ESI Score

**Solar System:**
Galaxy, Host Star, Distance to System, Host Star Type, Travel Time from Earth,
Host Star Temperature, Radio Signal Travel Time, Host Star Age

**Orbit:**
Planet Year, Orbital Eccentricity, Orbital Distance, Orbital Stability, Seasons

**Planet:**
Size (diameter km + ×Earth), Size Class (solar system reference), 
Gravity (m/s² + ×Earth), Climate (Köppen class), Equilibrium Temperature,
Escape Velocity (km/s + ×Earth), Weather Guesstimate

**Habitability:**
Habitability Tier, Habitable Zone Distance, Habitable Zone

---

## Image Generation

**Script:** `src/generate_images.py`

**Flow:**
1. Query `marts.mart_planet_image_prompt` for notable planets
2. Call DALL-E 3 with the `image_prompt` field
3. Download image bytes from temporary OpenAI URL
4. Upload bytes to S3 bucket (`planetary-data-images`)
5. Store permanent S3 URL in `marts.planet_images`

**Image prompts** are built in `mart_planet_image_prompt` by concatenating:
- `planet_base` (planet type description)
- `temperature_character` (surface/atmosphere description)
- `star_lighting` (star type lighting description)
- `habitability_context` (optional HZ context)
- Fixed style suffix: "photorealistic sci-fi concept art, cinematic lighting, detailed, atmospheric"

**S3 bucket:** `planetary-data-images` (us-east-1, public read)
**URL format:** `https://planetary-data-images.s3.us-east-1.amazonaws.com/{planet_name}.png`

---

## Description Generation (In Progress)

**Script:** `src/generate_descriptions.py` — not yet complete

**Goal:** 3-sentence experiential description of what it would feel like to 
stand on the planet. Written in present tense. Covers gravity, sky appearance, 
weather, year length. Vivid and sensory, not a stat rephrasing.

**Model:** GPT-4o, temperature=0.7, max_tokens=200

**Storage:** `marts.planet_descriptions` table (already created)

**Next step:** Write the script following the same pattern as `generate_images.py`

---

## dbt Key Patterns

**Schema macro** (`macros/generate_schema_name.sql`) — overrides dbt's default 
behavior of prepending target schema to custom schema names. Required for clean 
`staging` and `marts` schema names.

**CTE chain in mart_planet_profile:**
```
base → display_calcs → travel_times → descriptions → earth_comparisons → final SELECT
```

**CTE chain in mart_habitability_scores:**
```
stellar_calcs → hz_boundaries → planet_scores → scored → final SELECT
```

**Materialization:**
- staging: `view`
- marts: `materialized_view`

**Running models:**
```bash
dbt run --select mart_planet_profile
dbt run --full-refresh --select mart_planet_profile
dbt run --full-refresh  # rebuild everything
```

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
```

AWS credentials come from `~/.aws/credentials` [default] profile — not in .env.

---

## Immediate Next Tasks (in order)

1. **Complete `generate_descriptions.py`** — GPT-4o experiential planet descriptions
2. **Add description to frontend** — display at bottom of stats panel
3. **Constellation integration** — `enrich_constellations.py` using astropy
4. **Solar system seed file** — Europa, Enceladus, Titan, Earth, Mars etc
5. **All 5474 planets** — switch from notable-only to full catalog
6. **AWS deployment** — Terraform infrastructure
7. **GitHub CI/CD** — Actions workflows
8. **MCP chat layer** — Claude natural language queries over marts

---

## Known Issues / Gotchas

- Postgres `Decimal` types don't serialize to JSON automatically — use `DecimalEncoder` in FastAPI
- dbt schema macro is required — without it schemas get prefixed with target schema name
- `planet_stats` grid CSS requires `min-height: 0` on all flex parents for proper scrolling
- Tooltip `position: fixed` + `createPortal` required to avoid overflow clipping
- `vertical-align: super` on tooltip icon only works with `display: inline` not `inline-flex`
- `0` eccentricity shows as 'unknown' without `!= null` check (JS falsy value bug)
- `.planet-stats p` overrides `.section-label` color — use `.planet-stats p.section-label` for specificity
- CORS configured for `localhost:5173` only — update for production URL

---

## Future Vision

**CosmiDex: A Codex for the Cosmos** — expanding beyond exoplanets to a full 
cosmic catalog covering solar system bodies, galaxies, black holes, and nebulae.

Body types planned:
- Exoplanet (current)
- Solar System Body (Phase 2)
- Galaxy (Phase 3)
- Black Hole (Phase 4)
- Nebula (Phase 4)

Filter system: Primary body type filter → dynamic sub-filter based on selection

MCP layer: Claude connected to read-only Postgres for natural language queries
