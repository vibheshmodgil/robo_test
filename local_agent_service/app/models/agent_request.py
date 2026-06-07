from pydantic import BaseModel
from typing import Optional

class AgentRequest(
    BaseModel
):

    user_input: str

    mode: Optional[str] = None

    method: Optional[str] = None

    phase: Optional[str] = None

    description: Optional[str] = None

    title: Optional[str] = None