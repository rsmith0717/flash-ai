"""
This Service accomplishes the same thing as langgraph_service
BUT we'll use an AGENT in the routing node instead of keyword matching
The vectorDB retrieval nodes become tools
The chat nodes pretty much stay the same
"""

from typing import Annotated, Any, TypedDict

from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, add_messages
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import FlashCard
from app.services.vector_db import search

llm = ChatOllama(
    model="llama3.2:3b-instruct-q4_K_M",  # Quantized for speed
    base_url="http://ollama:11434",
    temperature=0.3,  # More deterministic
    num_predict=2048,  # Limit response length
    num_ctx=4096,  # Good context window
    repeat_penalty=1.1,  # Reduce repetition
    top_k=40,  # Sampling parameter
    top_p=0.9,  # Nucleus sampling
)

ollama_embedding = OllamaEmbeddings(
    model="nomic-embed-text", base_url="http://ollama:11434"
)


# Same state as the old service
class GraphState(TypedDict, total=False):  # total=False makes all fields optional
    query: str
    route: str
    docs: list[dict[str, Any]]
    answer: str
    # with add_messages reducer
    message_memory: Annotated[list[BaseMessage], add_messages]


# TOOLS ---------------------------
# The agentic route node will use one or none of these based on the User's query
# Remember, tools are just python functions that an agent CAN execute at run time
# We also won't directly use state in a tool. The agent calls these.
# IMPORTANT: Each tool needs '''docstrings''' to describe what they do for the agent


@tool(name_or_callable="search_cards")
def search_cards_tool(
    query: str,
    k: int = 10,
    collection: str = "flash_cards",
) -> list[dict[str, Any]]:
    """
    Based on the user's input, the "query" arg, do a semantic for existing flash cards.
    Retrieve relevant flash cards from the flash_cards vectorDB collection.
    """
    print("Extracting flash card data.")
    # db: AsyncSession = Depends(get_db)
    query_embedding = ollama_embedding.embed_query(text=query)

    engine = create_engine(settings.database_url)

    # Use the engine within a session context
    with Session(engine) as db:
        search_query = (
            select(FlashCard)
            .order_by(
                # The cosine_distance method translates to the <=> operator
                FlashCard.embedding.cosine_distance(query_embedding)
            )
            .limit(10)
        )

        result = db.execute(search_query)

        results = result.scalars().all()
        # return flash_cards

        # Save the results of the similarity search
        # results: Unknown = db_instance.similarity_search_with_score(query, k=k)
        print("The flash card search results are: ", results)

        # Return the results as a list of dicts with the expected fields
        return [
            {
                "text": f"Question: {result.question} Answer: {result.answer}",
                "metadata": {"id": str(result.id), "deck": str(result.deck_id)},
            }
            for result in results
        ]


@tool(name_or_callable="extract_cards")
def extract_cards_tool(query: str) -> list[dict[str, Any]]:
    """
    Based on the user's input, the "query" arg, do a semantic search.
    Retrieve relevant evil items or products based on the evil_items vectorDB collection.
    """
    print("Extracting flash card data.")
    return search(query, k=5, collection="flash_cards")


# Some variables that will help us make the agent aware of the tools

# List of the available tools
TOOLS = [extract_cards_tool, search_cards_tool]

# Map tool names to their functions in a scalable way
# We need this to call tools by their name in the agentic router node
# (See us defining and assigning names in the agentic router node)
TOOL_MAP = {tool.name: tool for tool in TOOLS}

# Get a version of the LLM that is aware of its toolbox
llm_with_tools = llm.bind_tools(TOOLS)

# NODES (including our agentic router)--------------------------------------------


# Here's the AGENT part - this routing node uses agentic AI to determine what tool to call, if any
def agentic_router_node(state: GraphState) -> GraphState:
    # Get the user query from State
    query = state.get("query", "")

    # Using this different chat prompting style just cuz it looks cool
    # Feel free to use the typical prompt string like we've been doing
    messages = [
        SystemMessage(
            content=(
                """
            You are an internal agent that decides whether VectorDB retrieval is needed. 
            If the User is asking about studying or material use the "search_cards" tool. 
            If neither applies or the user is just stating something, it's a general chat. 
            DO NOT call a tool for general chats. 
            If you call a tool, call EXACTLY ONE tool.
            """
            )
        ),
        HumanMessage(content=query),
    ]

    # First LLM call to decide which tool to use
    agentic_response = llm_with_tools.invoke(messages)

    # If there was no tool call, route to general chat
    # tool_calls contains a list of ToolCall objects, which has metadata like the tool name
    if not agentic_response.tool_calls:
        return {"route": "chat"}

    # If a tool WAS called, invoke it and store results and the appropriate route in State
    tool_call = agentic_response.tool_calls[0]  # We only expect one tool call
    tool_name = tool_call["name"]  # Extract the name of the tool that was called

    # Finally, here's us actually invoking the tool by name
    results = TOOL_MAP[tool_name].invoke({"query": query})

    # Automatically set the route to the answer_with_context node
    return {"route": "answer", "docs": results}


# ANSWER WITH CONTEXT & GENERAL CHAT will stay the same as before :)


# The node that answers the user's query based on docs retrieved from either "extract" node
def answer_with_context_node(state: GraphState):
    print("Answering with context")
    query = state.get("query", "")
    docs = state.get("docs", [])
    combined_docs = "\n\n".join(item["text"] for item in docs)
    print("The combined docs are: ", combined_docs)

    prompt = f"""You are an tutor helping a student studying for an exam.
        You are helpful and want the student to do their best.
        Select a question based ONLY on the Data below.
        Ask the user a question they haven't already been asked."
        If there is a previous response to a question grade the user's last answer from 1 - 10 with 10 being best.
        Explain to the user how they can improve their answer.

        Flash Card Data:\n{combined_docs}"
        User Query:\n{query}"
        Answer: """

    response = llm.invoke(prompt)
    # return {"answer": response}
    return {
        "route": "grade",
        "answer": response,
        "message_memory": [
            HumanMessage(content=query),
            AIMessage(content=response.content),
        ],
    }
    # return {"answer": response}


# The node that answers the user's query based on docs retrieved from either "extract" node
def grade_the_answer_node(state: GraphState) -> GraphState:
    query = state.get("query", "")
    docs = state.get("docs", [])
    combined_docs = "\n\n".join(item["text"] for item in docs)
    checkpointer = MemorySaver()
    checkpointer.delete_thread(thread_id="demo_thread")

    prompt = f"""You are an tutor helping a student studying for an exam.
        You are helpful and want the student to do their best.
        Grade the user's answer from 1 - 10 with 10 being best.
        Explain to the user how they can improve their answer.
        Extracted Data:\n{combined_docs}
        User Answer:\n{query}
        Answer: """

    response = llm.invoke(prompt)
    # return {"answer": response}
    return {
        "route": "grade",
        "answer": response,
        "message_memory": [
            HumanMessage(content=query),
            AIMessage(content=response.content),
        ],
    }


# Here's the fallback node for general chats (no tools)
def general_chat_node(state: GraphState) -> GraphState:
    prompt = f"""You are an internal assistant at the Evil Scientist Corp.
        You are pretty evil yourself, but still helpful.
        You have context from previous interactions: \n{state.get("message_memory")}
        Answer the User's Query to the best of your ability.
        User Query:\n{state.get("query", "")}
        Answer: """

    result = llm.invoke(prompt).content
    return {
        "answer": result,
        "message_memory": [
            HumanMessage(content=state.get("query")),
            AIMessage(content=result),
        ],
    }


# THE GRAPH BUILDER --------------------------------
# Mostly the same, but uses our new agentic router, and the tools are no longer nodes
def build_agentic_graph():
    # Define the graph state and the build variable
    build = StateGraph(GraphState)

    # Register each node within the graph
    # NOTE: extract_cards and extract_plans are TOOLS now, not nodes
    build.add_node("route", agentic_router_node)
    build.add_node("answer", answer_with_context_node)
    build.add_node("chat", general_chat_node)
    build.add_node("grade", grade_the_answer_node)

    # Set our entry point node (the first one to invoke after a user query)
    build.set_entry_point("route")

    # After the router runs, conditionally choose the next node based on "route" in state
    build.add_conditional_edges(
        "route",  # Based on the "route" state field...
        lambda state: state["route"],  # Getting the value
        {
            "answer": "answer",  # If route is "answer, go to answer node
            "chat": "chat",  # Otherwise, go to chat node
        },
    )
    # build.add_edge("answer", "grade")
    # build.add_edge("grade", "answer")

    # After answer OR chat invoke, we're done! Set that.
    # build.set_finish_point("answer")
    build.set_finish_point("chat")
    build.set_finish_point("grade")

    # Finally, compile and return the graph, with a Memory Checkpointer
    return build.compile(checkpointer=MemorySaver())


# Create a singleton instance of the graph for use in the router endpoint
agentic_graph = build_agentic_graph()
