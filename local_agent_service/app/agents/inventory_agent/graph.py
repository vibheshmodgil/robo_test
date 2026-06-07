import json
import re

from typing import TypedDict

from langgraph.graph import StateGraph, END

from app.services.llm_service import LLMService

llm_service = LLMService()


class InventoryState(TypedDict):
    session_id: str
    user_input: str
    mode: str
    method: str
    description: list[str]
    reply: str
    phase: str
    complete: bool


# Intent router: pick the target mode. The orchestrator re-runs this on each
# conversation turn too, which is how it switches talk <-> inventory.
ACTION_PROMPT = """
You are an intent router for a voice assistant.
Classify the user's request into exactly one mode.

Modes:
- INVENTORY: saving/storing/adding/creating an item, OR retrieving/searching/finding an item.
  For INVENTORY also set method: SET (save/add/store/create) or GET (find/search/retrieve) or UNKNOWN.
- CHAT: anything else - general questions, conversation, small talk.

Return ONLY valid JSON:
{ "mode": "INVENTORY|CHAT", "method": "SET|GET|UNKNOWN" }
"""

DESCRIPTION_PROMPT = """
You are an inventory description creation agent.

Rules:
- user prompt will be a long description of an database item
- extract the description and respond in given format
- try to make points of the user prompt for description

Return ONLY valid JSON.

Example:

{
  "description":[
    "it has 4 amp battery",
    "it has 6 watt energy"
  ]
}
"""

# Pull a clean item name out of a spoken phrase, for both the SAVE title and
# the GET search term, before it touches the DB.
ITEM_NAME_PROMPT = """
Extract a short item name from what the user said.
Drop filler like "save it as", "it should be called", "find me", and any punctuation.

Examples:
- "it should be called Anshul" -> {"name": "Anshul"}
- "save it as red toolbox" -> {"name": "red toolbox"}
- "can you find the apple" -> {"name": "apple"}
- "Apple." -> {"name": "Apple"}

Return ONLY valid JSON:
{ "name": "..." }
"""

FALLBACK_PROMPT = """
You are a helpful voice assistant.
Answer the user directly in one or two short, natural sentences.
Do not mention inventory, modes, or JSON.
"""

CHAT_PROMPT = """
You are a helpful voice assistant having a spoken conversation.
You will be given the conversation so far.
Reply to the user's last message in one or two short, natural sentences.
Do not mention inventory, modes, or JSON.
"""


def _parse_json(raw):
    """Parse JSON from an LLM response, tolerating ``` fences / stray text."""
    if not raw or not raw.strip():
        return None

    text = raw.strip()

    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


# =====================================
# EXTRACTION NODE
# =====================================

def extraction_node(state: InventoryState):

    phase = state.get("phase", "GET_ACTION")
    print(f"phase:- {phase}")

    try:

        if phase == "GET_ACTION":
            response = llm_service.chat(ACTION_PROMPT, state["user_input"])
            print("\nGET ACTION RESPONSE\n")
            print(response)

            data = _parse_json(response) or {}
            state["mode"] = data.get("mode", "")
            state["method"] = data.get("method", "")
            return state

        if phase == "GET_DESCRIPTION":
            response = llm_service.chat(DESCRIPTION_PROMPT, state["user_input"])
            print("\nDESCRIPTION RESPONSE\n")
            print(response)

            data = _parse_json(response) or {}
            state["description"] = data.get("description", [])
            return state

        # GET_ITEM_NAME and CHAT are handled by their own nodes.

    except Exception as exception:
        print("\nEXTRACTION ERROR\n")
        print(exception)
        state["reply"] = "Sorry, I could not understand that."
        state["complete"] = False
        return state

    return state


# =====================================
# ROUTER  (after extraction)
# =====================================

def route_after_extraction(state: InventoryState):
    phase = state.get("phase", "GET_ACTION")
    mode = (state.get("mode") or "").upper()

    if phase == "CHAT":
        return "chat"

    if phase == "GET_ITEM_NAME":
        return "item_name"

    if phase == "GET_DESCRIPTION":
        return "validate"

    # GET_ACTION
    if mode == "INVENTORY":
        return "validate"

    # CHAT / anything else -> conversational first reply
    return "fallback"


# =====================================
# ITEM NAME NODE  (clean title / search term)
# =====================================

def item_name_node(state: InventoryState):
    print("\nITEM NAME EXTRACTION\n")

    raw = ""
    try:
        raw = llm_service.chat(ITEM_NAME_PROMPT, state["user_input"]) or ""
        print(raw)
    except Exception as exception:
        print("\nITEM NAME ERROR\n")
        print(exception)

    name = ""

    # Prefer JSON {"name": "..."}.
    data = _parse_json(raw)
    if data and data.get("name"):
        name = str(data["name"]).strip()
    else:
        # Model didn't return JSON: take the last meaningful line, strip junk.
        for line in reversed(raw.strip().splitlines()):
            line = line.strip().strip('"').strip("'").strip()
            low = line.lower()
            if (
                line
                and not line.startswith("{")
                and not low.startswith("here")
                and not low.startswith("the name")
                and "<think>" not in low
                and "</think>" not in low
            ):
                name = line.rstrip(".").strip()
                break

    # Fall back to the raw utterance if extraction failed entirely.
    state["reply"] = name or (state.get("user_input") or "").strip()
    print(f"ITEM NAME -> {state['reply']}")
    state["complete"] = True
    return state


# =====================================
# FALLBACK NODE  (CHAT/unknown -> first conversational reply)
# =====================================

def fallback_node(state: InventoryState):
    print("\nFALLBACK -> conversational reply\n")

    try:
        reply = llm_service.chat(FALLBACK_PROMPT, state["user_input"])
    except Exception as exception:
        print("\nFALLBACK ERROR\n")
        print(exception)
        reply = ""

    state["reply"] = (reply or "").strip() or "Sorry, I didn't catch that. Could you say that again?"

    state["mode"] = ""
    state["method"] = ""
    state["complete"] = False
    return state


# =====================================
# CHAT NODE  (follow-up conversation turns)
# =====================================

def chat_node(state: InventoryState):
    print("\nCHAT TURN\n")

    try:
        reply = llm_service.chat(CHAT_PROMPT, state["user_input"])
    except Exception as exception:
        print("\nCHAT ERROR\n")
        print(exception)
        reply = ""

    state["reply"] = (reply or "").strip() or "Sorry, I didn't catch that."
    state["complete"] = False
    return state


# =====================================
# VALIDATION NODE  (inventory path)
# =====================================

def validation_node(state: InventoryState):

    mode = state.get("mode", "")
    method = state.get("method", "")
    description = state.get("description", [])

    if not mode or mode == "UNKNOWN":
        state["reply"] = "Please tell me which mode you want."
        state["complete"] = False
        return state

    if not method or method == "UNKNOWN":
        state["reply"] = "Would you like to save or retrieve inventory?"
        state["complete"] = False
        return state

    if method == "GET":
        state["reply"] = "What would you like me to find?"
        state["complete"] = True
        return state

    if method == "SET":
        if not description:
            state["phase"] = "GET_DESCRIPTION"
            state["reply"] = "Please describe your item."
            state["complete"] = False
            return state

        state["reply"] = "Inventory item ready to save."
        state["complete"] = True
        return state

    return state


# =====================================
# GRAPH
# =====================================

builder = StateGraph(InventoryState)

builder.add_node("extract", extraction_node)
builder.add_node("validate", validation_node)
builder.add_node("fallback", fallback_node)
builder.add_node("chat", chat_node)
builder.add_node("item_name", item_name_node)

builder.set_entry_point("extract")

builder.add_conditional_edges(
    "extract",
    route_after_extraction,
    {
        "validate": "validate",
        "fallback": "fallback",
        "chat": "chat",
        "item_name": "item_name",
    },
)

builder.add_edge("validate", END)
builder.add_edge("fallback", END)
builder.add_edge("chat", END)
builder.add_edge("item_name", END)

inventory_graph = builder.compile()