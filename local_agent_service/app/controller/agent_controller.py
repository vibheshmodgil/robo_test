from fastapi import (
    APIRouter
)

from app.models.agent_request import (
    AgentRequest
)

from app.agents.inventory_agent.graph import (
    inventory_graph
)

router = APIRouter()


@router.post(
    "/inventory/process"
)
async def process(
    request: AgentRequest
):

    result = (
        inventory_graph.invoke(

            {

                "user_input":
                    request.user_input,

                "mode":
                    request.mode,

                "method":
                    request.method,
                
                "phase":
                    request.phase,

                "description":
                    request.description,

                "reply": "",

                "complete": False
            }
        )
    )

    return result