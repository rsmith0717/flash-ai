from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.init_db import get_db
from app.models import User
from app.services.chat import build_agentic_graph, create_search_flashcards_tool
from app.services.user import fastapi_users

router = APIRouter(prefix="/chat", tags=["chat"])
current_user = fastapi_users.current_user()

# Store graphs and states per user
user_graphs = {}
user_states = {}


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    session_complete: bool
    score: int | None = None
    total_questions: int = 0
    questions_answered: int = 0


@router.post("/study", response_model=ChatResponse)
async def study_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Interactive study session using LangGraph with tool-based RAG.
    """
    user_id = str(user.id)

    # Get or create graph for user with tool
    if user_id not in user_graphs:
        # Create the search tool for this user
        search_tool = create_search_flashcards_tool(db, user_id)
        user_graphs[user_id] = build_agentic_graph(search_tool)

    graph = user_graphs[user_id]

    # Get existing state or create new
    is_new_session = user_id not in user_states or user_states[user_id] is None

    if is_new_session:
        # Start new session - greeting will be triggered
        print(f"Creating new session for user {user_id}")
        state = {
            "messages": [],
            "user_id": user_id,
            "study_topic": None,
            "retrieved_cards": [],
            "asked_card_indices": [],
            "current_card": None,
            "user_answer": None,
            "score": None,
            "session_scores": [],
            "session_complete": False,
            "current_step": "start",
            "needs_user_input": False,
        }

        # Run graph to get greeting
        result = graph.invoke(state)

        # Store state
        user_states[user_id] = result

        # Get the greeting message
        from langchain_core.messages import HumanMessage

        ai_messages = [
            msg for msg in result["messages"] if not isinstance(msg, HumanMessage)
        ]

        response_text = (
            ai_messages[-1].content
            if ai_messages
            else "Hello! What would you like to study?"
        )

        return ChatResponse(
            response=response_text,
            session_complete=result.get("session_complete", False),
            score=result.get("score"),
            total_questions=len(result.get("retrieved_cards", [])),
            questions_answered=len(result.get("asked_card_indices", [])),
        )

    else:
        # Continue existing session
        print(f"Continuing session for user {user_id}")
        state = user_states[user_id]

        # Add user message
        from langchain_core.messages import HumanMessage

        if request.message.strip():
            state["messages"].append(HumanMessage(content=request.message))
            print(f"User message: {request.message}")
            print(f"Current step before invoke: {state.get('current_step')}")
        else:
            return ChatResponse(
                response="Please send a message.",
                session_complete=False,
                score=None,
                total_questions=len(state.get("retrieved_cards", [])),
                questions_answered=len(state.get("asked_card_indices", [])),
            )

        # Run graph with existing state
        try:
            result = graph.invoke(state)

            print(f"Current step after invoke: {result.get('current_step')}")

            # Update stored state
            user_states[user_id] = result

            # Get the last AI message
            from langchain_core.messages import HumanMessage

            ai_messages = [
                msg for msg in result["messages"] if not isinstance(msg, HumanMessage)
            ]

            if ai_messages:
                response_text = ai_messages[-1].content
            else:
                response_text = "I'm processing your request..."

            if result.get("session_complete"):
                print(f"Session complete for user {user_id}")

            return ChatResponse(
                response=response_text,
                session_complete=result.get("session_complete", False),
                score=result.get("score"),
                total_questions=len(result.get("retrieved_cards", [])),
                questions_answered=len(result.get("asked_card_indices", [])),
            )

        except Exception as e:
            print(f"Error in study chat: {e}")
            import traceback

            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/study/reset")
async def reset_study_session(
    user: User = Depends(current_user),
):
    """Reset the study session for the current user."""
    user_id = str(user.id)

    print(f"Resetting session for user {user_id}")
    user_states[user_id] = None

    return {"message": "Study session reset successfully"}
