import json
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.init_db import get_db
from app.exceptions.http_exceptions import (
    InvalidPayScheduleException,
    PayrollNotFoundException,
)
from app.models import User
from app.schemas.flashcard import (
    DeckBase,
    DeckPost,
    DeckRead,
    FlashcardBase,
    FlashcardCreate,
)
from app.services.flashcard import (
    create_deck,
    create_flashcard,
    delete_flashcard,
    embed_and_store_flashcards,
    get_flashcard,
    search_flashcard,
    update_card,
)
from app.services.user import fastapi_users

router = APIRouter(prefix="/cards", tags=["cards"])

current_user = fastapi_users.current_user()


@router.post("/", response_model=FlashcardBase)
async def create_new_flashcard(
    flashcard: FlashcardCreate, db: AsyncSession = Depends(get_db)
):
    try:
        flashcard_model = await create_flashcard(db=db, flashcard=flashcard)
        return flashcard_model
    except DBAPIError as e:
        print(e)
        if "invalid input value for enum" in str(e):
            raise InvalidPayScheduleException()
        else:
            raise


@router.post("/deck", response_model=DeckRead)
async def create_new_deck(
    deck: DeckBase,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    try:
        deck_model = await create_deck(db=db, name=deck.name, user_id=str(user.id))
        return deck_model
    except DBAPIError as e:
        print(e)
        if "invalid input value for enum" in str(e):
            raise InvalidPayScheduleException()
        else:
            raise


@router.post("/deck/json")
async def generate_new_deck(
    deck: DeckPost,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Create a new deck from JSON data submitted in the request body.

    Expected format:
    {
        "deck_name": "My Deck",
        "flashcards": [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"}
        ]
    }
    """
    try:
        print("The deck is : ", deck)
        flash_card_list = [flashcard.model_dump() for flashcard in deck.flashcards]
        print("The deck flashcards are: ", flash_card_list)
        flash_cards = await embed_and_store_flashcards(
            db, deck.deck_name, flash_card_list, user_id=str(user.id)
        )
        return flash_cards
    except DBAPIError as e:
        print(e)
        raise


@router.post("/deck/upload")
async def upload_deck_from_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Create a new deck from a JSON file upload.

    Expected file format:
    {
        "deck_name": "My Deck",
        "flashcards": [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"}
        ]
    }
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.endswith(".json"):
            raise HTTPException(status_code=400, detail="Only JSON files are supported")

        # Read and parse the uploaded file
        contents = await file.read()

        try:
            deck_data = json.loads(contents.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(e)}")

        # Extract deck name and flashcards from the uploaded data
        deck_name = deck_data.get("deck_name")
        flashcards = deck_data.get("flashcards", [])

        if not deck_name:
            raise HTTPException(
                status_code=400, detail="deck_name is required in the JSON file"
            )

        if not flashcards:
            raise HTTPException(
                status_code=400, detail="flashcards list is required in the JSON file"
            )

        print(f"Uploaded deck: {deck_name} with {len(flashcards)} flashcards")

        # Use the same shared function as the JSON endpoint
        flash_cards = await embed_and_store_flashcards(
            db, deck_name, flashcards, user_id=str(user.id)
        )
        return flash_cards
    except DBAPIError as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{card_id}", response_model=FlashcardBase)
async def get_flashcard_by_id(card_id: str, db: AsyncSession = Depends(get_db)):
    db_payroll = await get_flashcard(db, card_id)
    if db_payroll is None:
        raise PayrollNotFoundException()
    return db_payroll


@router.delete("/{card_id}")
async def delete_flashcard_by_id(card_id: str, db: AsyncSession = Depends(get_db)):
    success = await delete_flashcard(db, card_id)
    if not success:
        raise PayrollNotFoundException()
    return {"ok": True}


@router.put("/{card_id}", response_model=FlashcardBase)
async def update_flashcard(
    card_id: str, flashcard: FlashcardCreate, db: AsyncSession = Depends(get_db)
):
    db_flashcard = await update_card(db, card_id, flashcard)
    if db_flashcard is None:
        raise PayrollNotFoundException()
    return db_flashcard


@router.get("/topic/{topic}", response_model=List[FlashcardBase])
async def search_flashcards_by_topic(
    topic: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Search for flashcards by topic using AI-powered semantic search.
    Only searches within flashcards from the current user's decks.

    Args:
        topic: The search query (e.g., "photosynthesis", "World War 2")

    Returns:
        List of up to 5 most relevant flashcards
    """
    flash_cards = await search_flashcard(db=db, topic=topic, user_id=str(user.id))
    return flash_cards
