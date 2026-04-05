"""
Planetary data api layer
"""

# import dependencies
import json
import logging
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import AsyncGenerator

import psycopg2.extras
from database import get_db, test_connection
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ######################################
# DEFINE HELPER FUNCTIONS
# ######################################


class DecimalEncoder(json.JSONEncoder):
    """"""

    def default(self, obj):  # type: ignore
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def decimal_response(data):
    """"""
    return JSONResponse(content=json.loads(json.dumps(data, cls=DecimalEncoder)))


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


# GET planets endpoint
@app.get("/planets")
def get_planets(db=Depends(get_db)):
    """"""
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT
            planet_name,
            host_star_name,
            planet_type,
            habitability_tier,
            temperature_description,
            star_type_description,
            distance_light_years,
            equilibrium_temp_celsius,
            esi_score,
            is_notable
        FROM marts.mart_planet_profile
        ORDER BY is_notable DESC, esi_score DESC NULLS LAST
    """)
    rows = cursor.fetchall()
    cursor.close()
    return decimal_response(rows)


# GET notable planets list endpoint
@app.get("/planets/notable/list")
def get_notable_planets(db=Depends(get_db)):
    """"""
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT
            pp.*,
            ip.image_prompt,
            pi.image_url
        FROM marts.mart_planet_profile AS pp
        LEFT JOIN marts.mart_planet_image_prompt AS ip
            ON pp.planet_name = ip.planet_name
        LEFT JOIN marts.planet_images AS pi ON pp.planet_name = pi.planet_name
        WHERE pp.is_notable = true
        ORDER BY pp.esi_score DESC NULLS LAST
    """)
    rows = cursor.fetchall()
    cursor.close()
    return decimal_response(rows)


# GET planets by habitability tier endpoint
@app.get("/planets/tier/{tier}")
def get_planets_by_tier(tier: str, db=Depends(get_db)):
    """"""
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        """
        SELECT
            planet_name,
            host_star_name,
            planet_type,
            habitability_tier,
            temperature_description,
            star_type_description,
            distance_light_years,
            equilibrium_temp_celsius,
            esi_score,
            is_notable
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
@app.get("/planets/search/{query}")
def search_planets(query: str, db=Depends(get_db)):
    """"""
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        """
        SELECT
            planet_name,
            host_star_name,
            planet_type,
            habitability_tier,
            temperature_description,
            star_type_description,
            distance_light_years,
            equilibrium_temp_celsius,
            esi_score,
            is_notable
        FROM marts.mart_planet_profile
        WHERE planet_name ILIKE %s
        ORDER BY esi_score DESC NULLS LAST
    """,
        (f"%{query}%",),
    )
    rows = cursor.fetchall()
    cursor.close()
    return decimal_response(rows)


# GET single planet endpoint
@app.get("/planets/{planet_name}")
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
            hs.escape_velocity_earth,
            pi.image_url
        FROM marts.mart_planet_profile AS pp
        LEFT JOIN marts.mart_habitability_scores AS hs 
            ON pp.planet_name = hs.planet_name
        LEFT JOIN marts.planet_images AS pi 
            ON pp.planet_name = pi.planet_name
        WHERE pp.planet_name = %s
    """,
        (planet_name,),
    )
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Planet not found")
    return decimal_response(row)
