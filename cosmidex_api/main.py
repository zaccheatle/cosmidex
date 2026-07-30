"""
Planetary data api layer
"""

# import dependencies
import datetime
import json
import logging
import os
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import AsyncGenerator

import psycopg2.extras
from database import get_db, test_connection
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import APIKeyHeader

load_dotenv()

# ######################################
# DEFINE HELPER FUNCTIONS
# ######################################


class DecimalEncoder(json.JSONEncoder):
    """"""

    def default(self, obj):  # type: ignore
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


def decimal_response(data):
    """"""
    return JSONResponse(content=json.loads(json.dumps(data, cls=DecimalEncoder)))


api_key_header = APIKeyHeader(name="X-API-Key")


def require_api_key(key: str = Security(api_key_header)) -> None:
    """Validate the X-API-Key header against the API_KEY env var."""
    if key != os.environ["API_KEY"]:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# Columns shared by the /planets list-style endpoints
PLANET_SUMMARY_COLUMNS = """
    planet_name,
    host_star_name,
    planet_composition,
    habitability_tier,
    estimated_planet_climate,
    star_spectral_type,
    star_distance_light_years,
    equilibrium_temp_celsius,
    esi_score
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """"""
    if not test_connection():
        raise RuntimeError("Database connection failed")
    logging.info("Database connection verified")

    yield

    logging.info("Database connection closing")


# ######################################
# DEFINE API
# ######################################


# Initialize app
app = FastAPI(lifespan=lifespan)


# Add middleware to allow frontend requests to API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Home page
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head>
            <title>CosmiDex API Homepage</title>
        </head>
        <body>
            <h1>Welcome to the CosmiDex API, view available endpoints here: <a href="/docs">API Documentation</a></h1>
        </body>
    </html>
    """


# GET planets endpoint
@app.get("/planets", dependencies=[Depends(require_api_key)])
def get_planets(
    db=Depends(get_db),
    tier: str | None = Query(None, description="Filter by habitability_tier"),
    planet_type: str | None = Query(None, description="Filter by planet_composition"),
    star_type: str | None = Query(
        None, description="Filter by star_spectral_type (prefix match, e.g. 'Class G')"
    ),
    min_esi: float | None = Query(None, ge=0, le=1),
    max_esi: float | None = Query(None, ge=0, le=1),
    limit: int = Query(25, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """"""
    filters = []
    params: list = []

    if tier is not None:
        filters.append("habitability_tier = %s")
        params.append(tier)
    if planet_type is not None:
        filters.append("planet_composition = %s")
        params.append(planet_type)
    if star_type is not None:
        filters.append("star_spectral_type ILIKE %s")
        params.append(f"{star_type}%")
    if min_esi is not None:
        filters.append("esi_score >= %s")
        params.append(min_esi)
    if max_esi is not None:
        filters.append("esi_score <= %s")
        params.append(max_esi)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        f"""
        SELECT {PLANET_SUMMARY_COLUMNS}
        FROM marts.mart_planet_profile
        {where_clause}
        ORDER BY esi_score DESC NULLS LAST
        LIMIT %s OFFSET %s
    """,
        (*params, limit, offset),
    )
    rows = cursor.fetchall()
    cursor.close()
    return decimal_response(rows)


# GET habitable planets list endpoint
@app.get("/planets/habitable/list", dependencies=[Depends(require_api_key)])
def get_habitable_planets(db=Depends(get_db)):
    """"""
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT
            pp.*,
            ip.image_prompt
        FROM marts.mart_planet_profile AS pp
        LEFT JOIN marts.mart_planet_image_prompt AS ip
            ON pp.planet_name = ip.planet_name
        WHERE pp.habitability_tier != 'Non-Habitable'
        ORDER BY pp.esi_score DESC NULLS LAST
    """)
    rows = cursor.fetchall()
    cursor.close()
    return decimal_response(rows)


# GET planets by habitability tier endpoint
@app.get("/planets/tier/{tier}", dependencies=[Depends(require_api_key)])
def get_planets_by_tier(tier: str, db=Depends(get_db)):
    """"""
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        f"""
        SELECT {PLANET_SUMMARY_COLUMNS}
        FROM marts.mart_planet_profile
        WHERE habitability_tier = %s
        ORDER BY esi_score DESC NULLS LAST
    """,
        (tier,),
    )
    rows = cursor.fetchall()
    cursor.close()
    return decimal_response(rows)


# GET search planets endpoint
@app.get("/planets/search/{query}", dependencies=[Depends(require_api_key)])
def search_planets(query: str, db=Depends(get_db)):
    """"""
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        f"""
        SELECT {PLANET_SUMMARY_COLUMNS}
        FROM marts.mart_planet_profile
        WHERE planet_name ILIKE %s
        ORDER BY esi_score DESC NULLS LAST
    """,
        (f"%{query}%",),
    )
    rows = cursor.fetchall()
    cursor.close()
    return decimal_response(rows)


# GET latest pipeline audit endpoint
@app.get("/audit/latest", dependencies=[Depends(require_api_key)])
def get_latest_audit(db=Depends(get_db)):
    """"""
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT
            pipeline_name,
            run_timestamp,
            changed,
            loaded,
            planet_count,
            new_planet_count,
            new_planets
        FROM raw.pipeline_audit
        ORDER BY run_timestamp DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        raise HTTPException(status_code=404, detail="No pipeline runs recorded yet")
    return decimal_response(row)


# GET single planet endpoint
@app.get("/planets/{planet_name}", dependencies=[Depends(require_api_key)])
def get_planet(planet_name: str, db=Depends(get_db)):
    """"""
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        """
        SELECT
            pp.*,
            hs.stellar_luminosity_solar,
            hs.hz_inner_conservative_au,
            hs.hz_outer_conservative_au,
            hs.s_escape,
            pi.image_url,
            pd.description
        FROM marts.mart_planet_profile AS pp
        LEFT JOIN marts.mart_habitability_scores AS hs
            ON pp.planet_name = hs.planet_name
        LEFT JOIN marts.planet_images AS pi
            ON pp.planet_name = pi.planet_name
        LEFT JOIN marts.planet_descriptions AS pd
            ON pp.planet_name = pd.planet_name
        WHERE pp.planet_name = %s
    """,
        (planet_name,),
    )
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Planet not found")
    return decimal_response(row)
