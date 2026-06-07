import uvicorn


def main():

    uvicorn.run(
        "app.server.api_server:app",
        host="0.0.0.0",
        port=8004
    )


if __name__ == "__main__":

    main()