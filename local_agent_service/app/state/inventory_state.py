from typing import TypedDict


class InventoryState(TypedDict):

    session_id: str

    user_input: str

    mode: str

    method: str

    title: str

    description: str

    reply: str

    complete: bool