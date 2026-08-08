"""Planetary data api layer."""

import datetime
import json
import logging
import os
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import AsyncGenerator

import anthropic
import psycopg2.extras
from anthropic.types import ToolParam
from database import get_db, test_connection
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from cosmidex_mcp.tools.exoplanets import fetch_planet

load_dotenv()

# ######################################
# DEFINE HELPER FUNCTIONS
# ######################################

client = anthropic.Anthropic()


class ChatRequest(BaseModel):
    message: str


# Chat bot system prompt
SYSTEM_PROMPT = (
    "You are Cosmo, CosmiDex's cosmic exploration assistant. CosmiDex is an interactive, "
    "Pokédex-style web application for exploring cosmic entities throughout the universe. "
    "Right now, only the exoplanet entity has been added, but datasets on galaxies, "
    "constellations, and our solar system are planned. "
    "Speak with vivid, enthusiastic curiosity about space — like a great science communicator like Niel Degrasse Tyson "
    "sharing a cool fact with a friend — while staying scientifically accurate and grounded in "
    "real data. Keep answers concise. "
    "Use the fetch_planet tool whenever a user asks about a specific named exoplanet's real "
    "physical, orbital, stellar, or habitability data — never guess or rely on general "
    "knowledge for facts this tool can answer precisely. "
    "Stay focused on space and CosmiDex's mission; gently redirect unrelated questions back "
    "toward cosmic exploration."
)

FETCH_PLANET_TOOL: ToolParam = {
    "name": "fetch_planet",
    "description": (
        "Look up precise, structured data for one confirmed exoplanet from CosmiDex's "
        "own database — derived from NASA's Exoplanet Archive (PSCompPars) and enriched "
        "with CosmiDex's own calculated habitability scoring. Use this whenever a user "
        "asks about a specific named exoplanet's physical properties (radius, mass, "
        "density, composition, size class), orbital characteristics (semi-major axis, "
        "eccentricity, period, stability), host star data (spectral type, temperature, "
        "age, distance from Earth), or habitability metrics (Earth Similarity Index, "
        "habitable-zone membership and distance, habitability tier). This is CosmiDex's "
        "authoritative, precomputed data for these planets — prefer it over general "
        "knowledge or web search whenever the question is about a planet potentially "
        "covered by this database, since values here are exact, sourced, and consistent "
        "with the rest of the CosmiDex dataset, rather than approximate or aggregated "
        "from varied external sources. Returns the planet's full physical, orbital, "
        "stellar, and habitability data, plus an AI-generated image URL and description "
        "where available."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "planet_name": {
                "type": "string",
                "description": (
                    "The exoplanet's exact name as catalogued by NASA, e.g. "
                    "'TRAPPIST-1 e', 'Kepler-442 b', 'Proxima Cen b'. Matching is an "
                    "exact, case-sensitive string match against the stored name — "
                    "not a fuzzy or partial search."
                ),
            }
        },
        "required": ["planet_name"],
    },
}


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that serializes Decimal and date/datetime values.

    Postgres numeric columns come back as Decimal and don't JSON-serialize by
    default; this encoder converts them (and dates) to JSON-safe types.
    """

    def default(self, obj):  # type: ignore
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


def decimal_response(data):
    """Serialize query result data to a JSON response via DecimalEncoder.

    Args:
        data: A dict, list, or RealDictRow (or list thereof) from a db query.

    Returns:
        JSONResponse: The data serialized as a JSON response.
    """
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
    """Verify the database is reachable on startup and log shutdown.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None.

    Raises:
        RuntimeError: If the database connection check fails on startup.
    """
    if not test_connection():
        raise RuntimeError("Database connection failed")
    logging.info("Database connection verified")

    yield

    logging.info("Database connection closing")


# ######################################
# DEFINE API
# ######################################


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
def home():
    """Serve a minimal HTML landing page linking to the API docs.

    Returns:
        str: Raw HTML for the homepage.
    """
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


@app.get("/planets", dependencies=[Depends(require_api_key)])
def get_planets(
    db=Depends(get_db),
    tier: str | None = Query(
        None,
        description="Filter by habitability_tier, or 'Habitable' for Tier 1/2/3 combined",
    ),
    planet_type: str | None = Query(None, description="Filter by planet_composition"),
    star_type: str | None = Query(
        None, description="Filter by star_spectral_type (prefix match, e.g. 'Class G')"
    ),
    min_esi: float | None = Query(None, ge=0, le=1),
    max_esi: float | None = Query(None, ge=0, le=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List planets from mart_planet_profile, filtered, sorted by ESI, and paginated.

    Args:
        db: Database connection (injected).
        tier (str | None): Filter by habitability_tier, or 'Habitable' for Tier 1/2/3 combined.
        planet_type (str | None): Filter by planet_composition.
        star_type (str | None): Filter by star_spectral_type (prefix match, e.g. 'Class G').
        min_esi (float | None): Minimum ESI score, inclusive.
        max_esi (float | None): Maximum ESI score, inclusive.
        limit (int): Max rows to return (1-500).
        offset (int): Row offset for pagination.

    Returns:
        JSONResponse: List of matching planet summary rows.
    """
    filters = []
    params: list = []

    if tier == "Habitable":
        filters.append("habitability_tier != 'Non-Habitable'")
    elif tier is not None:
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


@app.get("/planets/habitable/list", dependencies=[Depends(require_api_key)])
def get_habitable_planets(db=Depends(get_db)):
    """List every potentially habitable planet (Tier 1/2/3), including its image prompt body.

    Args:
        db: Database connection (injected).

    Returns:
        JSONResponse: List of habitable planet rows with image_prompt_body.
    """
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT
            pp.*,
            ip.image_prompt_body
        FROM marts.mart_planet_profile AS pp
        LEFT JOIN marts.mart_planet_image_prompt AS ip
            ON pp.planet_name = ip.planet_name
        WHERE pp.habitability_tier != 'Non-Habitable'
        ORDER BY pp.esi_score DESC NULLS LAST
    """)
    rows = cursor.fetchall()
    cursor.close()
    return decimal_response(rows)


@app.get("/planets/tier/{tier}", dependencies=[Depends(require_api_key)])
def get_planets_by_tier(tier: str, db=Depends(get_db)):
    """List planets matching an exact habitability_tier value.

    Args:
        tier (str): Habitability tier to match exactly (e.g. 'Tier 1').
        db: Database connection (injected).

    Returns:
        JSONResponse: List of matching planet summary rows.
    """
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


@app.get("/planets/search/{query}", dependencies=[Depends(require_api_key)])
def search_planets(query: str, db=Depends(get_db)):
    """Search planets by a case-insensitive substring match on planet_name.

    Args:
        query (str): Substring to search for within planet_name.
        db: Database connection (injected).

    Returns:
        JSONResponse: List of matching planet summary rows.
    """
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


@app.get("/audit/latest", dependencies=[Depends(require_api_key)])
def get_latest_audit(db=Depends(get_db)):
    """Fetch the most recent pipeline run's audit record.

    Args:
        db: Database connection (injected).

    Returns:
        JSONResponse: The latest row from raw.pipeline_audit.

    Raises:
        HTTPException: 404 if no pipeline runs have been recorded yet.
    """
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


@app.get("/planets/{planet_name}", dependencies=[Depends(require_api_key)])
def get_planet(planet_name: str, db=Depends(get_db)):
    """Fetch full detail for a single planet, including habitability scores,
    image URL, and AI-generated description.

    Args:
        planet_name (str): Exact planet name to look up.
        db: Database connection (injected).

    Returns:
        JSONResponse: The full planet detail row.

    Raises:
        HTTPException: 404 if no planet matches planet_name.
    """
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


# ######################################
# CHAT REQUESTS
# ######################################


def extract_text(content_blocks) -> str | None:
    """Find the text of the first text-type block in an Anthropic response.

    Args:
        content_blocks: The `.content` list from an Anthropic Message response.

    Returns:
        str | None: The first text block's text, or None if there isn't one.
    """
    for block in content_blocks:
        if block.type == "text":
            return block.text
    return None


@app.post("/chat", dependencies=[Depends(require_api_key)])
def chat(request: ChatRequest):
    """Answer a user's chat message, calling `fetch_planet` if Claude decides
    it needs CosmiDex data to respond.

    Args:
        request (ChatRequest): The user's chat message.

    Returns:
        str | None: Claude's final natural-language response.
    """
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[FETCH_PLANET_TOOL],
        messages=[{"role": "user", "content": request.message}],
    )

    if response.stop_reason != "tool_use":
        return extract_text(response.content)

    for element in response.content:
        if element.type != "tool_use":
            continue

        try:
            result = fetch_planet(planet_name=str(element.input["planet_name"]))
            result_text = str(result)
        except ValueError:
            result_text = "Hmm... I didn't find the planet you are looking for, can you double check the spelling?"

        follow_up_messages = [
            {"role": "user", "content": request.message},
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": element.id,
                        "content": result_text,
                    }
                ],
            },
        ]

        final_response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[FETCH_PLANET_TOOL],
            messages=follow_up_messages,
        )

        return extract_text(final_response.content)

    return None
