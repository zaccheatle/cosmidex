"""Article RAG MCP tools for the CosmiDex server."""

import logging

from google import genai
from google.genai import types
from psycopg2 import Error

from cosmidex_mcp.mcp_database import db_connection
from cosmidex_mcp.mcp_instance import mcp

logging.basicConfig(level=logging.DEBUG)

client = genai.Client()


@mcp.tool()
def search_articles(query: str) -> list[dict[str, str]]:
    """Search CosmiDex's reference article knowledge base for content
    relevant to a general astronomy/space question — star types, the
    habitable zone, how exoplanets are detected, and similar conceptual
    topics. Use this when a user asks something explanatory or conceptual
    that isn't about one specific planet's data (for planet-specific facts,
    use fetch_planet instead).

    Args:
        query (str): The user's question, in natural language.

    Returns:
        list[dict[str, str]]: The most relevant article chunks, each with its
            text, source title, and source URL for citation. Empty list if
            nothing relevant was found or the search failed.

    Raises:
        ValueError: The embedding API returned no result for the query.
    """
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=f"task: question_answering | {query}",
        config=types.EmbedContentConfig(output_dimensionality=768),
    )
    if not response.embeddings:
        raise ValueError("No embedding returned for the search query.")
    query_embedding = response.embeddings[0].values

    with db_connection() as conn:
        cursor = conn.cursor()
        select_script = """
            SELECT chunk_text, source_title, source_url
            FROM marts.rag_chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        try:
            cursor.execute(select_script, (query_embedding, 3))
            rows = cursor.fetchall()
        except Error as e:
            logging.error(f"Error searching articles: {e}.")
            return []

    return [
        {"chunk_text": row[0], "source_title": row[1], "source_url": row[2]}
        for row in rows
    ]
