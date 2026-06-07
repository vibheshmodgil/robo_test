import requests


class CommandService:

    def notify_wakeword(self):

        try:

            response = requests.post(
                "http://localhost:8080/wakeword"
            )

            print(
                "\n[BACKEND RESPONSE]\n"
            )

            print(
                response.text
            )

        except Exception as exception:

            print(exception)

    def handle_command(
        self,
        text: str
    ):

        try:

            response = requests.post(
                "http://localhost:8080/commands",
                json={
                    "command": text
                }
            )

            print(
                "\n[COMMAND RESPONSE]\n"
            )

            print(
                response.text
            )

        except Exception as exception:

            print(exception)