from fastapi import FastAPI

from pydantic import BaseModel

from app.pipeline.speaker_pipeline import (
    SpeakerPipeline
)

app = FastAPI()

speaker_pipeline = (
    SpeakerPipeline()
)


class SpeakRequest(
    BaseModel
):

    text: str


@app.post("/speak")
def speak(
    request: SpeakRequest
):

    speaker_pipeline.speak(
        request.text
    )

    return {
        "status": "completed"
    }