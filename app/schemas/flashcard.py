from uuid import UUID

from pydantic import BaseModel, Field


class FlashcardBase(BaseModel):
    question: str = Field()
    answer: str = Field()


class FlashcardCreate(FlashcardBase):
    deck_id: UUID


class FlashcardRead(FlashcardCreate):
    id: UUID


class DeckBase(BaseModel):
    name: str = Field()


class DeckRead(DeckBase):
    id: UUID
    user_id: UUID


class DeckPost(BaseModel):
    deck_name: str
    flashcards: list[FlashcardBase]
