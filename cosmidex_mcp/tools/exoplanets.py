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
                pd.description
            FROM marts.mart_planet_profile AS pp
            LEFT JOIN marts.mart_habitability_scores AS hs
                ON pp.planet_name = hs.planet_name
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


@mcp.tool()
def find_planets(
    tier: str | None = None,
    planet_type: str | None = None,
    star_type: str | None = None,
    min_esi: float | None = None,
    max_esi: float | None = None,
    discovery_year: str | None = None,
    planet_size_class: str | None = None,
    min_distance: float | None = None,
    max_distance: float | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search for exoplanets matching one or more criteria from CosmiDex's own
    database — derived from NASA's Exoplanet Archive (PSCompPars) and enriched
    with CosmiDex's own calculated habitability scoring. Use this whenever a
    user asks for planets matching some criteria (e.g. "Tier 1 planets around
    a K-type star") rather than asking about one specific named planet — for a
    single named planet, use fetch_planet instead. This is CosmiDex's
    authoritative, precomputed data — prefer it over general knowledge or web
    search whenever the question is about planets potentially covered by this
    database, since values here are exact, sourced, and consistent with the
    rest of the CosmiDex dataset, rather than approximate or aggregated from
    varied external sources. Any filter left unset matches all planets on
    that criterion.

    Args:
        tier (str | None): Exact habitability_tier to match, e.g. "Tier 1".
        planet_type (str | None): Exact planet_composition to match.
        star_type (str | None): Prefix match against star_spectral_type,
            e.g. "Class K" matches all K-type subclasses.
        min_esi (float | None): Minimum Earth Similarity Index, inclusive.
        max_esi (float | None): Maximum Earth Similarity Index, inclusive.
        discovery_year (str | None): Exact discovery year to match, e.g. "2016".
        planet_size_class (str | None): Exact planet_size_class to match,
            e.g. "Super-Earth".
        min_distance (float | None): Minimum host star distance from Earth,
            in light-years, inclusive.
        max_distance (float | None): Maximum host star distance from Earth,
            in light-years, inclusive.
        limit (int): Max number of planets to return. Defaults to 20.

    Returns:
        list[dict]: Matching planets' physical, orbital, stellar, and
            habitability data. Empty list if nothing matches.
    """
    filters = []
    params: list = []

    if tier is not None:
        filters.append("pp.habitability_tier = %s")
        params.append(tier)
    if planet_type is not None:
        filters.append("pp.planet_composition = %s")
        params.append(planet_type)
    if star_type is not None:
        filters.append("pp.star_spectral_type ILIKE %s")
        params.append(f"{star_type}%")
    if min_esi is not None:
        filters.append("pp.esi_score >= %s")
        params.append(min_esi)
    if max_esi is not None:
        filters.append("pp.esi_score <= %s")
        params.append(max_esi)
    if discovery_year is not None:
        filters.append("pp.discovery_year = %s")
        params.append(discovery_year)
    if planet_size_class is not None:
        filters.append("pp.planet_size_class = %s")
        params.append(planet_size_class)
    if min_distance is not None:
        filters.append("pp.star_distance_light_years >= %s")
        params.append(min_distance)
    if max_distance is not None:
        filters.append("pp.star_distance_light_years <= %s")
        params.append(max_distance)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with db_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            f"""
            SELECT
                pp.*,
                hs.stellar_luminosity_solar,
                hs.hz_inner_conservative_au,
                hs.hz_outer_conservative_au,
                hs.s_escape,
                pd.description
            FROM marts.mart_planet_profile AS pp
            LEFT JOIN marts.mart_habitability_scores AS hs
                ON pp.planet_name = hs.planet_name
            LEFT JOIN marts.planet_descriptions AS pd
                ON pp.planet_name = pd.planet_name
            {where_clause}
            ORDER BY pp.esi_score DESC NULLS LAST
            LIMIT %s
        """,
            (*params, limit),
        )
        rows = cursor.fetchall()
        cursor.close()

        return [numeric_handler(row) for row in rows]


@mcp.tool()
def compare_planets(planet_a: str, planet_b: str) -> dict[str, dict]:
    """Look up and return full data for two confirmed exoplanets side by side,
    for direct comparison. Use this whenever a user asks how two specific
    named exoplanets compare to each other, rather than asking about a single
    planet (use fetch_planet) or a broader set of planets matching criteria
    (use search_planets).

    Args:
        planet_a (str): The first exoplanet's exact name as catalogued by
            NASA, e.g. "TRAPPIST-1 e". Matching is exact and case-sensitive.
        planet_b (str): The second exoplanet's exact name, same matching
            rules as planet_a.

    Returns:
        dict[str, dict]: A dict keyed by each input planet's name, mapping to
            that planet's full record — physical, orbital, stellar, and
            habitability data, plus an AI-generated image URL and description
            where available.

    Raises:
        ValueError: Either planet_a or planet_b doesn't match a planet in the
            database.
    """

    planet_a_result = fetch_planet(planet_a)
    planet_b_result = fetch_planet(planet_b)

    return {planet_a: planet_a_result, planet_b: planet_b_result}
