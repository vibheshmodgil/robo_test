import requests
import json


class LLMService:

    def chat(
        self,
        system_prompt,
        user_prompt
    ):

        response = requests.post(
            "http://ollama:11434/api/chat",
            json={
                "model": "qwen3:1.7b",

                "messages": [

                    {
                        "role": "system",
                        "content": system_prompt
                    },

                    {
                        "role": "user",
                        "content": user_prompt
                    }

                ],

                "keep_alive": "30m",
                "think": False,

                "options": {
                    "temperature": 0.1,
                    "num_predict": 256
                },

                "stream": False
            },
            timeout=60
        )

        print("\nSTATUS CODE")
        print(response.status_code)

        print("\nRAW RESPONSE TEXT")
        print(response.text)

        data = response.json()

        print("\nRAW RESPONSE JSON")
        print(json.dumps(data, indent=2))

        content = (
            data.get(
                "message",
                {}
            ).get(
                "content",
                ""
            )
        )

        print("\nEXTRACTED CONTENT")
        print(repr(content))

        return content