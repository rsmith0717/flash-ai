from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.init_db import get_db
from app.services.chat import agentic_graph

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatInputModel(BaseModel):
    input: str


@router.post("/study")
def agent_study(chat: ChatInputModel, db: AsyncSession = Depends(get_db)):
    # Only difference besides the function name & (/endpoint) is we're calling the agentic graph
    print("Inside agent study")
    result = agentic_graph.invoke(
        {"query": chat.input}, config={"configurable": {"thread_id": "demo_thread"}}
    )

    return {
        "route": result.get("route"),
        "answer": result.get("answer"),
        "sources": result.get("docs"),
        "message_memory": result.get("message_memory"),
    }
