"""Generate embeddings for RAG source articles using Gemini and store them
in marts.rag_chunks for retrieval by the chatbot."""

import logging
from pathlib import Path

from google import genai
from google.genai import types
from psycopg2 import Error

from cosmidex_mcp.mcp_database import db_connection

logging.basicConfig(level=logging.DEBUG)

client = genai.Client()


def embed_text(folder_path: Path) -> None:
    """Chunk, embed, and store every markdown article in folder_path.

    Args:
        folder_path (Path): Directory containing .md article files, each with
            a `Source: <url>` line followed by the article body.

    Returns:
        None
    """
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT source_title FROM marts.rag_chunks")
        already_embedded = {row[0] for row in cursor.fetchall()}

        for file_path in Path(folder_path).glob("*.md"):
            text = file_path.read_text(encoding="utf-8")
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

            source_title = file_path.stem
            if source_title in already_embedded:
                continue

            source_url = ""
            for p in paragraphs:
                if p.startswith("Source:"):
                    source_url = p.removeprefix("Source:").strip()
                    break

            chunks = [
                p
                for p in paragraphs
                if not p.startswith("#")  # strip markdown header lines
                and not p.startswith("Source:")  # strip the source url line
            ]

            for i, chunk in enumerate(chunks):
                response = client.models.embed_content(
                    model="gemini-embedding-2",
                    contents=f"task: retrieval_document | {chunk}",
                    config=types.EmbedContentConfig(output_dimensionality=768),
                )
                if not response.embeddings:
                    logging.error(
                        f"No embedding returned for chunk {i} of {file_path.name}"
                    )
                    continue
                embedding = response.embeddings[0].values

                insert_script = """
                    INSERT INTO marts.rag_chunks
                        (source_title, source_url, chunk_index, chunk_text, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                """
                insert_values = (source_title, source_url, i, chunk, embedding)

                try:
                    cursor.execute(insert_script, insert_values)
                    conn.commit()
                except Error as e:
                    logging.error(f"Error inserting chunk into db: {e}.")
