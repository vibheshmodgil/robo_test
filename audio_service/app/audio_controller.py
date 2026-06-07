from fastapi import APIRouter

from app.manager.audio_mode_manager import (
    audio_mode_manager
)

from app.audio.microphone_manager import (
    microphone_manager
)

router = APIRouter()




@router.post("/audio/active")
def enable_active_mode():

    microphone_manager.clear_queue()

    audio_mode_manager.enable_active_mode()

    return {
        "status": "active"
    }


@router.post("/audio/passive")
def enable_passive_mode():

    microphone_manager.clear_queue()

    audio_mode_manager.enable_passive_mode()

    return {
        "status": "passive"
    }


@router.post("/audio/workflow")
def enable_workflow_mode():

    microphone_manager.clear_queue()

    audio_mode_manager.enable_workflow_mode()

    return {
        "status": "workflow"
    }


@router.post("/audio/workflow/fresh")
def start_fresh_workflow():

    microphone_manager.clear_queue()

    audio_mode_manager.restart_workflow_listening()

    return {
        "status": "fresh workflow listening"
    }


@router.post("/audio/pause")
def pause_audio():

    audio_mode_manager.pause_listening()

    return {
        "status": "paused"
    }


@router.post("/audio/resume")
def resume_audio():

    audio_mode_manager.resume_listening()

    return {
        "status": "resumed"
    }