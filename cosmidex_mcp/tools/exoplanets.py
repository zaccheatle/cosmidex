"""Exoplanet-related MCP tools for the CosmiDex server."""

import psycopg2.extras

from cosmidex_mcp.mcp_database import db_connection, numeric_handler
from cosmidex_mcp.mcp_instance import mcp


@mcp.tool()
def fetch_planet(planet_name: str) -> dict:
    """Look up precise, structured data for one confirmed exoplanet from CosmiDex's
    own database — derived from NASA's Exoplanet Archive (PSCompPars) and enriched
    with CosmiDex's own calculated habitability scoring. Use this whenever a user
    asks about a specific named exoplanet's physical properties (radius, mass,
    density, composition, size class), orbital characteristics (semi-major axis,
    eccentricity, period, stability), host star data (spectral type, temperature,
    age, distance from Earth), or habitability metrics (Earth Similarity Index,
    habitable-zone membership and distance, habitability tier). This is CosmiDex's
    authoritative, precomputed data for these planets — prefer it over general
    knowledge or web search whenever the question is about a planet potentially
    covered by this database, since values here are exact, sourced, and consistent
    with the rest of the CosmiDex dataset, rather than approximate or aggregated
    from varied external sources.

    Args:
        planet_name (str): The exoplanet's exact name as catalogued by NASA,
            e.g. "TRAPPIST-1 e", "Kepler-442 b", "Proxima Cen b". Matching is
            an exact, case-sensitive string match against the stored name —
            not a fuzzy or partial search.

    Returns:
        dict: The planet's full record — physical, orbital, stellar, and
            habitability data, plus an AI-generated image URL and description
            where available.

    Raises:
        ValueError: No planet in the database matches `planet_name` exactly.
    """
    with db_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
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
            raise ValueError(f"{planet_name} not found")
        return numeric_handler(row)
