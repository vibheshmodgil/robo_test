from fastapi import FastAPI

import uvicorn

import threading

from app.audio_controller import (
    router
)

from app.pipeline.audio_pipeline import (
    AudioPipeline
)

app = FastAPI()

app.include_router(router)


def start_pipeline():

    pipeline = AudioPipeline()

    pipeline.start()


def main():

    # START AUDIO PIPELINE THREAD
    pipeline_thread = threading.Thread(
        target=start_pipeline,
        daemon=True
    )

    pipeline_thread.start()

    # START FASTAPI SERVER
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002
    )


if __name__ == "__main__":

    main()