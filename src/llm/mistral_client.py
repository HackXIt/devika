from mistralai import Mistral, UserMessage
from src.config import Config


class MistralAi:
    def __init__(self):
        config = Config()
        api_key = config.get_mistral_api_key()
        self.client = Mistral(api_key=api_key)

    def inference(self, model_id: str, prompt: str) -> str:
        print("prompt", prompt.strip())

        # Using the new `Mistral` client and message structure
        chat_completion = self.client.chat.complete(
            model=model_id,
            messages=[
                UserMessage(content=prompt.strip())
            ],
        )
        
        return chat_completion.choices[0].message.content
