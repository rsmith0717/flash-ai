import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import List, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

# Initialize the chat model
chat_model = ChatOllama(
    model="llama3.2:3b-instruct-q4_K_M",
    base_url="http://ollama:11434",
    temperature=0.7,
)

# Thread pool for running async code
executor = ThreadPoolExecutor(max_workers=3)


class StudySessionState(TypedDict):
    """State for the study session graph."""

    messages: list  # Conversation history
    user_id: str  # User ID for card retrieval
    study_topic: str | None  # What the user wants to study
    retrieved_cards: list[dict]  # Flashcards from RAG
    asked_card_indices: list[int]  # Indices of cards already asked
    current_card: dict | None  # Current flashcard being asked
    user_answer: str | None  # User's answer to current question
    score: int | None  # Score for current answer (1-10)
    session_scores: list[dict]  # History of all scores
    session_complete: bool  # Whether study session is done
    current_step: str  # Track which step we're on
    needs_user_input: bool  # Flag to indicate we're waiting for user


def create_search_flashcards_tool(db_session, user_id: str):
    """
    Factory function to create a search tool bound to a specific DB session and user.
    """

    @tool
    def search_flashcards(topic: str) -> List[dict]:
        """
        Search for flashcards relevant to the given topic using semantic search.

        Args:
            topic: The study topic to search for (e.g., "photosynthesis", "calculus")

        Returns:
            List of flashcard dictionaries with 'id', 'question', and 'answer' keys
        """
        from sqlalchemy import select

        from app.models.flashcard import Deck, FlashCard
        from app.services.flashcard import ollama_embedding

        def sync_search():
            """Synchronous wrapper that runs async code in a thread."""

            async def async_search():
                """Async search implementation."""
                try:
                    print(f"Searching for flashcards about: {topic}")

                    # Generate embedding for the topic
                    query_embedding = ollama_embedding.embed_query(text=topic)

                    # Search with vector similarity
                    search_query = (
                        select(FlashCard)
                        .join(Deck, FlashCard.deck_id == Deck.id)
                        .where(Deck.user_id == user_id)
                        .order_by(FlashCard.embedding.cosine_distance(query_embedding))
                        .limit(5)
                    )

                    result = await db_session.execute(search_query)
                    flash_cards = result.scalars().all()

                    # Convert to dict format
                    cards = [
                        {
                            "id": str(card.id),
                            "question": card.question,
                            "answer": card.answer,
                        }
                        for card in flash_cards
                    ]

                    print(f"Found {len(cards)} flashcards")
                    return cards

                except Exception as e:
                    print(f"Error in async search: {e}")
                    import traceback

                    traceback.print_exc()
                    return []

            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(async_search())
                return result
            finally:
                loop.close()

        # Run the sync wrapper in a thread pool
        try:
            future = executor.submit(sync_search)
            result = future.result(timeout=30)  # 30 second timeout
            return result
        except Exception as e:
            print(f"Error in search tool: {e}")
            import traceback

            traceback.print_exc()
            return []

    return search_flashcards


def build_agentic_graph(search_tool):
    """
    Build a LangGraph for interactive study sessions.

    Args:
        search_tool: LangChain tool for searching flashcards

    Returns:
        Compiled LangGraph
    """

    # Node 1: Greet and ask what to study
    def greet_user(state: StudySessionState) -> StudySessionState:
        """Start the conversation and ask what the user wants to study."""
        print("Node: greet_user")

        greeting = AIMessage(
            content="""Hello! I'm your AI study assistant! 📚

            I'll help you study by quizzing you on flashcards. 

            What topic would you like to study today? For example:
            - "photosynthesis"
            - "World War 2"
            - "calculus"
            - "Python programming"

            Just tell me what you'd like to focus on!"""
        )

        state["messages"].append(greeting)
        state["session_complete"] = False
        state["asked_card_indices"] = []
        state["session_scores"] = []
        state["current_step"] = "waiting_for_topic"
        state["needs_user_input"] = True

        return state

    # Node 2: Extract study topic from user's message
    def extract_topic(state: StudySessionState) -> StudySessionState:
        """Extract the study topic from the user's message."""
        print("Node: extract_topic")

        # Get the last user message
        user_messages = [
            msg for msg in state["messages"] if isinstance(msg, HumanMessage)
        ]
        if not user_messages:
            state["current_step"] = "waiting_for_topic"
            state["needs_user_input"] = True
            return state

        last_message = user_messages[-1].content

        # Use LLM to extract topic
        extraction_prompt = f"""Extract the main study topic from this message. Return ONLY the topic, nothing else.

        User message: "{last_message}"

        Topic:"""

        response = chat_model.invoke(extraction_prompt)
        topic = response.content.strip()

        state["study_topic"] = topic
        state["current_step"] = "topic_extracted"
        state["needs_user_input"] = False
        print(f"Extracted topic: {topic}")

        return state

    # Node 3: Search for flashcards using the tool
    def search_flashcards_node(state: StudySessionState) -> StudySessionState:
        """Use the search tool to retrieve relevant flashcards."""
        print("Node: search_flashcards")

        topic = state["study_topic"]

        if not topic:
            state["messages"].append(
                AIMessage(
                    content="I couldn't understand what you'd like to study. Could you please tell me the topic again?"
                )
            )
            state["retrieved_cards"] = []
            state["current_step"] = "waiting_for_topic"
            state["needs_user_input"] = True
            return state

        # Call the tool
        try:
            print(f"Invoking search tool for topic: {topic}")
            flashcards = search_tool.invoke({"topic": topic})

            if not flashcards:
                state["messages"].append(
                    AIMessage(
                        content=f"I couldn't find any flashcards about '{topic}'. Would you like to study something else?"
                    )
                )
                state["retrieved_cards"] = []
                state["session_complete"] = True
                state["current_step"] = "session_complete"
                state["needs_user_input"] = False
            else:
                # Store the flashcards
                state["retrieved_cards"] = flashcards

                state["messages"].append(
                    AIMessage(
                        content=f"Great! I found {len(flashcards)} flashcards about '{topic}'. Let's start studying! 🎓"
                    )
                )
                state["current_step"] = "ready_to_ask"
                state["needs_user_input"] = False

                print(f"Retrieved {len(flashcards)} flashcards")

        except Exception as e:
            print(f"Error using search tool: {e}")
            import traceback

            traceback.print_exc()
            state["messages"].append(
                AIMessage(
                    content=f"Sorry, I had trouble finding flashcards. Error: {str(e)}"
                )
            )
            state["retrieved_cards"] = []
            state["session_complete"] = True
            state["current_step"] = "session_complete"
            state["needs_user_input"] = False

        return state

    # Node 4: Ask a question from flashcards
    def ask_question(state: StudySessionState) -> StudySessionState:
        """Select an unasked flashcard and ask the question."""
        print("Node: ask_question")

        cards = state["retrieved_cards"]
        asked_indices = state["asked_card_indices"]

        # Find an unasked card
        unasked_indices = [i for i in range(len(cards)) if i not in asked_indices]

        if not unasked_indices:
            # No more cards to ask
            state["session_complete"] = True
            state["current_step"] = "session_complete"
            state["needs_user_input"] = False

            # Calculate final statistics
            scores = state["session_scores"]
            if scores:
                avg_score = sum(s["score"] for s in scores) / len(scores)

                summary = f"""🎉 Great job! You've completed all the flashcards!

                📊 Your Results:
                - Questions answered: {len(scores)}
                - Average score: {avg_score:.1f}/10

                """
                # Show breakdown by performance
                excellent = [s for s in scores if s["score"] >= 8]
                good = [s for s in scores if 6 <= s["score"] < 8]
                needs_work = [s for s in scores if s["score"] < 6]

                summary += f"✅ Excellent (8-10): {len(excellent)}\n"
                summary += f"👍 Good (6-7): {len(good)}\n"
                summary += f"📖 Needs review (1-5): {len(needs_work)}\n"

                if needs_work:
                    summary += "\n💡 Topics to review:\n"
                    for s in needs_work[:3]:  # Show top 3
                        summary += f"- {s['question'][:50]}...\n"

                summary += "\nWould you like to study another topic?"

                state["messages"].append(AIMessage(content=summary))
            else:
                state["messages"].append(
                    AIMessage(
                        content="We're done! Would you like to study another topic?"
                    )
                )

            return state

        # Get next unasked card
        next_index = unasked_indices[0]
        card = cards[next_index]

        state["current_card"] = card
        state["asked_card_indices"].append(next_index)

        # Ask the question
        remaining = len(unasked_indices)
        question_msg = f"""Question {len(asked_indices) + 1}/{len(cards)} ❓

        {card["question"]}

        Take your time and answer as best as you can!"""

        state["messages"].append(AIMessage(content=question_msg))
        state["current_step"] = "waiting_for_answer"
        state["needs_user_input"] = True

        return state

    # Node 5: Grade the user's answer
    def grade_answer(state: StudySessionState) -> StudySessionState:
        """Grade the user's answer and provide feedback."""
        print("Node: grade_answer")

        current_card = state["current_card"]

        # Get the user's answer (last human message)
        user_messages = [
            msg for msg in state["messages"] if isinstance(msg, HumanMessage)
        ]
        if not user_messages:
            return state

        user_answer = user_messages[-1].content
        state["user_answer"] = user_answer

        # Use LLM to grade the answer
        grading_prompt = f"""You are grading a student's answer to a flashcard question.

        Question: {current_card["question"]}
        Correct Answer: {current_card["answer"]}
        Student's Answer: {user_answer}

        Grade the student's answer on a scale from 1-10 where:
        - 10: Perfect, complete answer
        - 8-9: Very good, mostly correct
        - 6-7: Good effort, partially correct
        - 4-5: Some understanding, needs improvement
        - 1-3: Incorrect or shows misunderstanding

        Provide:
        1. A score (1-10)
        2. Brief feedback (2-3 sentences)
        3. If score < 8, explain what was missing

        Return ONLY valid JSON:
        {{
        "score": 8,
        "feedback": "Your feedback here",
        "correct_answer": "{current_card["answer"]}"
        }}

        JSON:"""

        try:
            response = chat_model.invoke(grading_prompt)
            content = response.content.strip()

            # Extract JSON
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                content = json_match.group()

            result = json.loads(content)

            score = result.get("score", 5)
            feedback = result.get("feedback", "Good try!")
            correct_answer = result.get("correct_answer", current_card["answer"])

            # Ensure score is between 1-10
            score = max(1, min(10, score))

            state["score"] = score

            # Record score
            state["session_scores"].append(
                {
                    "question": current_card["question"],
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "score": score,
                    "feedback": feedback,
                }
            )

            # Create feedback message with emoji
            if score >= 9:
                emoji = "🌟"
                grade_text = "Excellent!"
            elif score >= 7:
                emoji = "👍"
                grade_text = "Good job!"
            elif score >= 5:
                emoji = "📚"
                grade_text = "Not bad!"
            else:
                emoji = "💡"
                grade_text = "Keep practicing!"

            feedback_msg = f"""{emoji} Score: {score}/10 - {grade_text}

            {feedback}

            📖 Correct answer: {correct_answer}

            Ready for the next question? Just say "next" or "continue"!"""

            state["messages"].append(AIMessage(content=feedback_msg))
            state["current_step"] = "waiting_for_continue"
            state["needs_user_input"] = True

        except Exception as e:
            print(f"Error grading answer: {e}")
            state["messages"].append(
                AIMessage(
                    content="I had trouble grading your answer, but let's continue!"
                )
            )
            state["score"] = 5
            state["current_step"] = "waiting_for_continue"
            state["needs_user_input"] = True

        return state

    # Helper function to check if we have a NEW user message
    def has_new_user_message(state: StudySessionState) -> bool:
        """Check if there's a user message after the last AI message."""
        messages = state["messages"]
        if not messages:
            return False

        print(f"Checking messages: {messages}")
        # Find the last AI message index
        last_ai_index = -1
        for i in range(len(messages) - 1, -1, -1):
            if isinstance(messages[i], AIMessage):
                last_ai_index = i
                break

        # Check if there's a user message after it
        if last_ai_index == -1:
            # No AI message yet, check if there's any user message
            return any(isinstance(msg, HumanMessage) for msg in messages)

        # Check messages after last AI message
        for i in range(last_ai_index + 1, len(messages)):
            if isinstance(messages[i], HumanMessage):
                return True

        return False

    # Routing function
    def route_conversation(state: StudySessionState) -> str:
        """Determine next step based on current state."""
        current_step = state.get("current_step", "greet")

        print(f"Routing from step: {current_step}")
        print(f"Needs user input: {state.get('needs_user_input', False)}")

        # Check if we have a new user message
        has_user_msg = has_new_user_message(state)
        print(f"Has new user message: {has_user_msg}")

        # Route based on current step
        if current_step == "greet" or current_step == "start":
            return "greet_user"

        elif current_step == "waiting_for_topic":
            if has_user_msg:
                return "extract_topic"
            return END

        elif current_step == "topic_extracted":
            return "search_flashcards"

        elif current_step == "ready_to_ask":
            return "ask_question"

        elif current_step == "waiting_for_answer":
            if has_user_msg:
                # Check if user wants to skip or is answering
                messages = state["messages"]
                user_messages = [
                    msg for msg in messages if isinstance(msg, HumanMessage)
                ]
                if user_messages:
                    last_msg = user_messages[-1].content.lower().strip()
                    if any(
                        keyword in last_msg for keyword in ["next", "continue", "skip"]
                    ):
                        return "ask_question"
                    else:
                        return "grade_answer"
            return END

        elif current_step == "waiting_for_continue":
            if has_user_msg:
                return "ask_question"
            return END

        elif current_step == "session_complete":
            return END

        return END

    # Build the graph
    workflow = StateGraph(StudySessionState)

    # Add all nodes
    workflow.add_node("greet_user", greet_user)
    workflow.add_node("extract_topic", extract_topic)
    workflow.add_node("search_flashcards", search_flashcards_node)
    workflow.add_node("ask_question", ask_question)
    workflow.add_node("grade_answer", grade_answer)

    # Conditional entry point based on state
    def entry_router(state: StudySessionState) -> str:
        """Determine entry point based on whether we're starting or continuing."""
        current_step = state.get("current_step", "start")

        print(f"Entry router - current_step: {current_step}")

        # If starting a new session, greet
        if current_step == "start":
            return "greet_user"

        # Otherwise, route based on current step
        return route_conversation(state)

    # Set entry point to router
    workflow.set_conditional_entry_point(
        entry_router,
        {
            "greet_user": "greet_user",
            "extract_topic": "extract_topic",
            "search_flashcards": "search_flashcards",
            "ask_question": "ask_question",
            "grade_answer": "grade_answer",
            END: END,
        },
    )

    # All nodes route through the same routing function
    for node_name in [
        "greet_user",
        "extract_topic",
        "search_flashcards",
        "ask_question",
        "grade_answer",
    ]:
        workflow.add_conditional_edges(
            node_name,
            route_conversation,
            {
                "greet_user": "greet_user",
                "extract_topic": "extract_topic",
                "search_flashcards": "search_flashcards",
                "ask_question": "ask_question",
                "grade_answer": "grade_answer",
                END: END,
            },
        )

    # Compile the graph
    return workflow.compile()
