from langchain_community.embeddings import OllamaEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flashcard import Deck, FlashCard
from app.schemas.flashcard import FlashcardCreate

ollama_embedding = OllamaEmbeddings(
    model="nomic-embed-text", base_url="http://ollama:11434"
)


async def create_flashcard(db: AsyncSession, flashcard: FlashcardCreate) -> FlashCard:
    new_flashcard = FlashCard(
        deck_id=flashcard.deck_id,
        question=flashcard.question,
        answer=flashcard.answer,
    )

    db.add(new_flashcard)
    await db.flush()
    await db.commit()
    await db.refresh(new_flashcard)
    return new_flashcard


async def get_flashcard(
    db: AsyncSession,
    card_id: str,
) -> FlashCard | None:
    stmt = select(FlashCard).where(FlashCard.id == card_id)
    # session.query(Post).join(User).filter(User.id == 1).all()

    result = await db.execute(stmt)
    flash_card: FlashCard | None = result.scalar_one_or_none()
    return flash_card


async def search_flashcard(
    db: AsyncSession,
    topic: str,
    user_id: str,
) -> list[FlashCard]:
    """
    Search for flashcards by topic using semantic search.
    Only returns flashcards from decks owned by the specified user.

    Args:
        db: Database session
        topic: Search query text
        user_id: ID of the user to filter decks by

    Returns:
        List of FlashCard objects ordered by relevance
    """
    # 1. Define the search expression
    query_embedding = ollama_embedding.embed_query(text=topic)

    # 2. Construct the query with JOIN to Deck table to filter by user_id
    search_query = (
        select(FlashCard)
        .join(Deck, FlashCard.deck_id == Deck.id)
        .where(Deck.user_id == user_id)
        .order_by(
            # The cosine_distance method translates to the <=> operator
            FlashCard.embedding.cosine_distance(query_embedding)
        )
        .limit(5)
    )

    result = await db.execute(search_query)
    flash_cards = result.scalars().all()
    return flash_cards


async def update_card(
    db: AsyncSession, card_id: str, flashcard: FlashcardCreate
) -> FlashCard | None:
    db_flashcard = await get_flashcard(db, card_id)
    if not flashcard:
        return None
    db_flashcard.question = flashcard.question
    db_flashcard.answer = flashcard.answer
    await db.commit()
    db.refresh(db_flashcard)
    return db_flashcard


async def delete_flashcard(
    db: AsyncSession,
    card_id: str,
) -> bool:
    flashcard = await get_flashcard(db, card_id)
    if not flashcard:
        return False
    await db.delete(flashcard)
    await db.commit()
    return True


async def create_deck(db: AsyncSession, name: str, user_id: str) -> Deck:
    print(f"THe deck name is: {name} and the user id is: {user_id}")
    new_deck = Deck(
        name=name,
        user_id=user_id,
    )

    db.add(new_deck)
    await db.flush()
    await db.commit()
    await db.refresh(new_deck)
    return new_deck


async def embed_and_store_flashcards(
    db: AsyncSession, deck_name: str, flashcards: list[dict], user_id: str
):
    """
    Embeds flashcard data and stores it in the PostgreSQL database.

    Args:
        flashcards_json: A JSON string representing a list of flashcards,
                        each with 'question' and 'answer' keys.
    """
    # flashcards_list = json.loads(flashcards_json)

    # Prepare data for embedding
    texts_to_embed = [
        f"Question: {card['question']} Answer: {card['answer']}" for card in flashcards
    ]
    print("The texts to embed is: ", texts_to_embed)
    # for card in flashcards_list:
    #     card['text_to_embed'] = f"Question: {card['question']} Answer: {card['answer']}"

    # Add a prefix to the chunks
    # documents = ["search_document: " + chunk for chunk in chunks]

    # Embed the chunks using the ollama model

    document_embeddings = ollama_embedding.embed_documents(texts=texts_to_embed)
    print("The document embeddings are: ", document_embeddings)

    # Create Flashcard objects
    db_objects = []
    new_deck = await create_deck(db, deck_name, user_id=user_id)
    for card_data, embedding_vector in zip(flashcards, document_embeddings):
        db_objects.append(
            FlashCard(
                deck_id=str(new_deck.id),
                question=card_data["question"],
                answer=card_data["answer"],
                embedding=embedding_vector,
            )
        )

    # Store in the database
    db.add_all(db_objects)
    await db.flush()
    await db.commit()
    print(f"Stored {len(db_objects)} flashcards with embeddings.")
    return db_objects
