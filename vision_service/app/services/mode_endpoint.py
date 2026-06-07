from fastapi import FastAPI

app = FastAPI()

current_mode = "PASSIVE"

@app.post("/mode")
async def change_mode(data: dict):

    global current_mode

    current_mode = data["mode"]

    print(f"[VISION] MODE CHANGED TO: {current_mode}")

    return {
        "success": True,
        "mode": current_mode
    }