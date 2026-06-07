from fastapi import FastAPI

from app.controller.agent_controller import (
    router
)

import uvicorn

app = FastAPI()

app.include_router(
    router
)


def main():

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8005,
        reload=False
    )


if __name__ == "__main__":

    main()