from enum import Enum


class AudioStates(Enum):

    WAITING_WAKEWORD = (
        "WAITING_WAKEWORD"
    )

    LISTENING_COMMAND = (
        "LISTENING_COMMAND"
    )

    WORKFLOW_RUNNING = (
        "WORKFLOW_RUNNING"
    )