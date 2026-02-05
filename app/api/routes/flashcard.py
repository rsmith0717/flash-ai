from typing import List

from fastapi import APIRouter, Depends
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
    try:
        print("The deck is : ", deck)
        # deck_model = await create_deck(db=db, name=deck.deck_name, user_id=str(user.id))
        # print("The deck model is: ", deck_model)
        flash_card_list = [flashcard.model_dump() for flashcard in deck.flashcards]
        print("The deck flashcards are: ", flash_card_list)
        flash_cards = await embed_and_store_flashcards(
            db, deck.deck_name, flash_card_list, user_id=str(user.id)
        )
        return flash_cards
    except DBAPIError as e:
        print(e)
        if "invalid input value for enum" in str(e):
            raise InvalidPayScheduleException()
        else:
            raise


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
    updated = await update_card(db=db, card_id=card_id, flashcard=flashcard)
    if updated is None:
        raise PayrollNotFoundException()
    return updated


@router.get("/topic/{topic}", response_model=List[FlashcardBase])
async def search_flashcards_by_topic(topic: str, db: AsyncSession = Depends(get_db)):
    flash_cards = await search_flashcard(db=db, topic=topic)
    return flash_cards
