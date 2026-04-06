# CosmiDex: A Codex for the Cosmos
### Roadmap

---

## Current State

A fully functional exoplanet explorer built on NASA's PSCompPars dataset. 
The pipeline runs from raw NASA data through dbt transformations to a React 
frontend served by FastAPI, with AI-generated artwork for 13 notable planets 
stored in AWS S3.

**Stack:** Postgres → dbt → FastAPI → React (Vite) → AWS S3

---

## Phase 1 — Data Enrichment (In Progress)

*Enrich existing exoplanet cards with richer context and generated content.*

### 1.1 Planet Descriptions
- [ ] Build `generate_descriptions.py` using GPT-4o
- [ ] Generate 3-sentence experiential descriptions for all notable planets
- [ ] Store in `marts.planet_descriptions` table
- [ ] Serve via API and display at the bottom of each planet card

### 1.2 Constellation Integration
- [ ] Add `ra` and `dec` columns to staging model
- [ ] Build `enrich_constellations.py` using `astropy`
- [ ] Derive constellation name, abbreviation, galactic region from coordinates
- [ ] Add `constellation`, `galactic_region` fields to `mart_planet_profile`
- [ ] Add constellation stat and tooltip to planet card

### 1.3 Full Planet Catalog
- [ ] Switch frontend from `/planets/notable/list` to full `/planets` endpoint
- [ ] Add pagination or virtual scrolling for 5,474 planets
- [ ] Generate AI artwork for all planets (not just 13 notable ones)
- [ ] Implement image cache invalidation — regenerate when `image_prompt` changes

---

## Phase 2 — Solar System Bodies

*Add habitable and notable bodies from our own solar system.*

### 2.1 Seed File
- [ ] Create `seeds/solar_system_bodies.csv` with curated data
- [ ] Include: Earth, Moon, Mars, Venus, Jupiter, Europa, Enceladus, Titan, Ganymede
- [ ] Add `body_type` field — `exoplanet` vs `solar_system`
- [ ] Generate AI artwork for each body

### 2.2 Card Support
- [ ] Update frontend to handle `solar_system` body type
- [ ] Earth as the reference card — ESI 1.0, HZD 0.0, the baseline
- [ ] Habitable moon cards — Europa, Enceladus, Titan with appropriate stats
- [ ] Notable planet cards — Jupiter, Venus as dramatic non-habitable entries

### 2.3 Filter Update
- [ ] Add Body Type filter — `All`, `Exoplanet`, `Solar System`
- [ ] Rename app from ExoDex → **CosmiDex** on Solar System launch

---

## Phase 3 — Galaxy Catalog

*Expand beyond individual planets to galactic-scale objects.*

### 3.1 Data Source
- [ ] Integrate NASA/IPAC Extragalactic Database (NED) API
- [ ] Load notable galaxies — Milky Way, Andromeda, Triangulum, Whirlpool, Sombrero
- [ ] Fields: type, distance (megaparsecs), diameter, estimated star count, notable features

### 3.2 Galaxy Cards
- [ ] New card layout for galactic scale — different stats than planet cards
- [ ] Distance in megaparsecs not light years
- [ ] Galaxy type classification — spiral, elliptical, irregular, lenticular
- [ ] AI artwork generation for each galaxy
- [ ] Add `galaxy` body type to filter system

---

## Phase 4 — Black Holes & Nebulae

*The most visually dramatic entries in the catalog.*

### 4.1 Black Holes
- [ ] Source data from Black Hole Transient Catalog and EHT Collaboration
- [ ] Notable entries: Sagittarius A*, M87*, Cygnus X-1
- [ ] Fields: mass (solar masses), event horizon radius, type (stellar/supermassive), host galaxy
- [ ] AI artwork — most dramatic imagery in the catalog
- [ ] Add `black_hole` body type to filter system

### 4.2 Nebulae
- [ ] Source data from NASA catalog
- [ ] Notable entries: Orion Nebula, Crab Nebula, Pillars of Creation, Helix Nebula
- [ ] Fields: type, distance, size (light years), composition, star formation activity
- [ ] Add `nebula` body type to filter system

---

## Phase 5 — Filter System Overhaul

*Dynamic multi-level filtering as the catalog grows.*

### 5.1 Primary Filter
Top-level body type selection:
- `All`
- `Exoplanets`
- `Solar System`
- `Galaxies`
- `Black Holes`
- `Nebulae`

### 5.2 Dynamic Sub-Filter
Secondary filter that changes based on primary selection:
- Exoplanets → filter by Habitability Tier
- Solar System → filter by Body Type (Planet / Moon)
- Galaxies → filter by Galaxy Type
- Black Holes → filter by Type (Stellar / Supermassive)
- Nebulae → filter by Type (Emission / Reflection / Planetary / Supernova Remnant)

---

## Phase 6 — MCP & AI Chat Layer

*Let users ask natural language questions about the catalog.*

### 6.1 MCP Tool
- [ ] Connect Claude to read-only Postgres MCP server pointed at dbt marts
- [ ] Natural language to SQL — "show me all rocky planets in the habitable zone orbiting red dwarfs"
- [ ] Planet comparison — "how does TRAPPIST-1 d compare to Earth?"
- [ ] Cross-catalog queries — "which constellation has the most notable planets?"

### 6.2 Planet-Specific Q&A
- [ ] Context-aware chat on individual planet cards
- [ ] "Could humans survive here?" "What would the sky look like?" "How does this compare to Mars?"
- [ ] RAG layer over scientific papers for well-known planets (K2-18b, Proxima Cen b)

---

## Phase 7 — AWS Deployment

*Production infrastructure on AWS.*

### 7.1 Infrastructure (Terraform)
- [ ] VPC with public/private subnets
- [ ] RDS Postgres instance (replace local Docker Postgres)
- [ ] ECS Fargate for FastAPI container
- [ ] S3 bucket for planet images (already exists locally)
- [ ] CloudFront CDN in front of S3
- [ ] Application Load Balancer for FastAPI
- [ ] Route53 for custom domain (cosmidex.com?)
- [ ] ACM SSL certificate

### 7.2 Pipeline Orchestration (MWAA)
- [ ] Managed Airflow on AWS
- [ ] DAG: fetch new NASA data → load to RDS → run dbt → refresh materialized views
- [ ] DAG: check for stale images → regenerate where `image_prompt` changed
- [ ] DAG: check for stale descriptions → regenerate where planet data changed
- [ ] Alerts on pipeline failure

### 7.3 Frontend Deployment
- [ ] Build React app with `bun run build`
- [ ] Deploy to S3 static hosting or Vercel/Netlify
- [ ] Connect to production API endpoint

---

## Phase 8 — CI/CD (GitHub Actions)

*Automated testing and deployment on every push.*

### 8.1 dbt Pipeline
- [ ] `dbt test` on every PR — catch data quality issues before merge
- [ ] `dbt run` on merge to main — rebuild marts automatically
- [ ] `dbt docs generate` — publish lineage documentation

### 8.2 API
- [ ] Lint and test FastAPI on every PR
- [ ] Build and push Docker image to ECR on merge
- [ ] Deploy new image to ECS Fargate automatically

### 8.3 Frontend
- [ ] Lint and build React on every PR
- [ ] Deploy to hosting on merge to main

---

## Future Ideas

- **Constellation pages** — dedicated view showing all planets within a constellation on a star map
- **Comparison mode** — side by side two planets or bodies
- **Timeline view** — discovery timeline showing when each planet was found
- **3D orbital viewer** — visualize a planet's orbit around its star
- **Solar system moons expansion** — Callisto, Triton, Io, and other notable moons
- **Rogue planets** — planets with no host star
- **Binary star systems** — planets orbiting two stars
- **Exomoon candidates** — potential moons around confirmed exoplanets

---

*Built with NASA PSCompPars data, dbt, FastAPI, React, AWS, and a healthy obsession with the cosmos.*
