from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import ChatOllama
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flashcard import Deck, FlashCard
from app.schemas.flashcard import FlashcardCreate
from app.services.chunker import AgenticChunker

ollama_embedding = OllamaEmbeddings(
    model="nomic-embed-text", base_url="http://ollama:11434"
)

# Initialize ChatOllama for the agentic chunker
ollama_chat = ChatOllama(
    model="llama3.2:3b-instruct-q4_K_M",  # Quantized for speed
    base_url="http://ollama:11434",
    temperature=0.3,  # More deterministic
    num_predict=2048,  # Limit response length
    num_ctx=4096,  # Good context window
    repeat_penalty=1.1,  # Reduce repetition
    top_k=40,  # Sampling parameter
    top_p=0.9,  # Nucleus sampling
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


async def get_user_decks(db: AsyncSession, user_id: str) -> list[Deck]:
    """
    Get all decks for a specific user.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        List of Deck objects owned by the user
    """
    stmt = select(Deck).where(Deck.user_id == user_id)
    result = await db.execute(stmt)
    decks = result.scalars().all()
    return list(decks)


async def get_deck_cards(
    db: AsyncSession,
    deck_id: int,
    user_id: str,  # Changed deck_id from str to int
) -> list[FlashCard] | None:
    """
    Get all flashcards for a specific deck.
    Verifies deck ownership before returning cards.

    Args:
        db: Database session
        deck_id: Integer ID of the deck
        user_id: ID of the user requesting the cards

    Returns:
        List of FlashCard objects if deck exists and user owns it, None otherwise
    """
    # First verify the deck exists and user owns it
    deck_stmt = select(Deck).where(Deck.id == deck_id)
    deck_result = await db.execute(deck_stmt)
    deck = deck_result.scalar_one_or_none()

    if deck is None:
        return None

    # Check ownership
    if str(deck.user_id) != str(user_id):
        return None

    # Get all flashcards for this deck
    cards_stmt = select(FlashCard).where(FlashCard.deck_id == deck_id)
    cards_result = await db.execute(cards_stmt)
    flashcards = cards_result.scalars().all()

    return list(flashcards)


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


async def process_text_file_to_flashcards(
    db: AsyncSession, file_content: bytes, deck_name: str, user_id: str
) -> list[FlashCard]:
    """
    Process a text file using AgenticChunker to extract QA pairs and create flashcards.

    Args:
        db: Database session
        file_content: Raw bytes from the uploaded .txt file
        deck_name: Name for the new deck
        user_id: ID of the user creating the flashcards

    Returns:
        List of created FlashCard objects
    """
    try:
        # Decode file content
        text_content = file_content.decode("utf-8")

        print(f"Processing text file with {len(text_content)} characters")

        # Initialize the agentic chunker with ChatOllama
        chunker = AgenticChunker(model=ollama_chat)

        # Process the text and extract QA pairs
        chunks = await chunker.chunk_text_async(text_content)

        print(f"Generated {len(chunks)} chunks from text")

        # Extract all QA pairs from chunks
        all_qa_pairs = chunker.get_all_qa_pairs(chunks)

        print(f"Extracted {len(all_qa_pairs)} QA pairs before filtering")

        if not all_qa_pairs:
            raise ValueError(
                "No question-answer pairs could be extracted from the text"
            )

        # FILTER: Remove any QA pairs with empty questions or answers
        filtered_qa_pairs = []
        rejected_count = 0

        for qa in all_qa_pairs:
            question = qa.get("question", "").strip()
            answer = qa.get("answer", "").strip()

            # Strict validation
            if not question or len(question) < 5:
                print(f"  ❌ Rejected - Invalid question: '{question}'")
                rejected_count += 1
                continue

            if not answer or len(answer) < 3:
                print(f"  ❌ Rejected - Invalid answer for '{question}': '{answer}'")
                rejected_count += 1
                continue

            # Check for generic/placeholder answers
            if answer.lower() in [
                "it",
                "this",
                "that",
                "something",
                "unknown",
                "n/a",
                "none",
            ]:
                print(f"  ❌ Rejected - Placeholder answer: '{answer}'")
                rejected_count += 1
                continue

            # All checks passed
            filtered_qa_pairs.append({"question": question, "answer": answer})

        print(
            f"Filtered: {len(filtered_qa_pairs)} valid QA pairs, {rejected_count} rejected"
        )

        if not filtered_qa_pairs:
            raise ValueError(
                f"All {len(all_qa_pairs)} extracted QA pairs were invalid. Please check your document content."
            )

        # Use existing function to embed and store flashcards
        db_flashcards = await embed_and_store_flashcards(
            db=db, deck_name=deck_name, flashcards=filtered_qa_pairs, user_id=user_id
        )

        return db_flashcards

    except UnicodeDecodeError as e:
        raise ValueError(
            f"Failed to decode text file. Please ensure it's a valid UTF-8 text file: {str(e)}"
        )
    except Exception as e:
        raise ValueError(f"Failed to process text file: {str(e)}")
