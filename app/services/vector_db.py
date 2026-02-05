# This service will help us initialize and interact with a ChromaDB vector database
import hashlib
from typing import Any

from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

COLLECTION = "flash_cards"  # What kind of data we're storing (like the tables in SQL)

# See docker command above to launch a postgres instance with pgvector enabled.
connection_url = "postgresql+psycopg://user:password@db:5432/flashcarddb"
collection_name = "flash_cards"


embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://ollama:11434")


# Get an instance of the Chroma vector store (lets us interact with the DB instance)
# Takes in a collection to use, or defaults to COLLECTION ("evil_items")
def get_vector_store(collection: str = COLLECTION):
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection,
        connection=connection_url,
        use_jsonb=True,
    )
    return vector_store


# Ingest documents into the vector store (this is where the embeddings happen)
def ingest_items(items: list[dict[str, Any]], collection: str = COLLECTION) -> int:
    # Get an instance of the vector store
    db_instance = get_vector_store(collection)

    # Turn the input into a list of documents to get inserted
    docs = [
        Document(page_content=item["text"], metadata=item.get("metadata", {}))
        for item in items
    ]
    # Also, attach IDs to the documents (also found in the sample data)
    ids = [item["id"] for item in items]

    # Add the documents, return the length of the ingested items
    # THIS IS WHERE THE EMBEDDING HAPPENS
    # (text has been converted to vector, which goes into the vector DB)
    db_instance.add_documents(docs, ids=ids)
    return len(items)


# Different ingest function for ingesting plain text (we'll need to made IDs/metadata)
def ingest_text(text: str) -> int:
    # Strip the string, removing whitespace from the ends
    text = text.strip()
    if not text:
        return 0  # If there's nothing to ingest, end the function here and return 0

    # Chunk the raw text into smaller pieces for better embedding
    # Using a LangChain Transformer (RecursiveCharacterTextSplitter)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # max size of each chunk - 500 chars (~2 paragraphs)
        chunk_overlap=100,  # how much each chunk overlaps - 100 chars (helps retain context)
        separators=["\n\n", "\n", " ", ""],  # preferred split points
        # (double new line, single new line, space, then any char
    )

    # Get our chunks as a list[str] so we can iterate over them and reformat them
    chunks = splitter.split_text(text)

    # Finally, call ingest_items() now that we have a structured object for embedding
    items = []

    # What's enumerate? Give us a (index, value) pair when iterating over a list
    for index, chunk in enumerate(chunks):
        # Define and attach a stable-ish ID so reingestion doesn't create duplicates
        content_hash = hashlib.md5(chunk.encode("utf-8")).hexdigest()[:8]
        chunk_id = f"chunk_{content_hash}"
        # This^ will look like "chunk_a1b2c3d4"

        # Append the chunk to the items list with ID and metadata
        items.append(
            {
                "id": chunk_id,
                "text": chunk,
                "metadata": {
                    "chunk_index": index,
                    "source": "raw_text_ingestion",  # Helps with filtering information in queries
                },
            }
        )

    # Finally, send the new structured items to our original ingest_items function
    return ingest_items(items, collection="boss_plans")


# Search the vector store for similar or relevant documents based on a query
def search(
    query: str, k: int = 10, collection: str = COLLECTION
) -> list[dict[str, Any]]:
    # Get an instance of the vector store
    db_instance = get_vector_store(collection)

    # Save the results of the similarity search
    results = db_instance.similarity_search_with_score(query, k=k)
    print("The generic search results are: ", results)

    # Return the results as a list of dicts with the expected fields
    return [
        {
            "text": result[0].page_content,
            "metadata": result[0].metadata,
            "score": result[1],
        }
        for result in results
    ]
