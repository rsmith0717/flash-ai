# app/models/flashcard.py
import uuid

from langchain_community.embeddings import OllamaEmbeddings
from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, event, text, types
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base

N_DIM = 768  # The dimension for nomic-embed-text embeddings


class FlashCard(Base):
    __tablename__ = "flashcards"

    id: Mapped[uuid.UUID] = mapped_column(
        types.Uuid,
        primary_key=True,
        server_default=text("gen_random_uuid()"),  # use what you have on your server
    )
    deck_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(column="decks.id"))
    question: Mapped[str] = mapped_column(String)
    answer: Mapped[str] = mapped_column(String)
    embedding = mapped_column(Vector(N_DIM))

    def __repr__(self):
        return f"Flashcard(id={self.id}, question='{self.question[:30]}...')"


# @event.listens_for(FlashCard, "before_insert")
@event.listens_for(FlashCard, "before_update")
def receive_before_update(mapper, connection, target):
    """Generate and update the embedding before insert or update."""
    if target.question or target.answer:
        ollama_embedding = OllamaEmbeddings(
            model="nomic-embed-text", base_url="http://ollama:11434"
        )
        text_to_embed = f"Question: {target['question']} Answer: {target['answer']}"
        embedding = ollama_embedding.embed_query(text_to_embed)
        target.embedding = embedding


class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    name: Mapped[str] = mapped_column(String(100))

    def __str__(self):
        return f"({self.user_id}): {self.name}"
