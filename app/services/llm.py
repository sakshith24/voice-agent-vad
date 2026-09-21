from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.client = OpenAI()
    def generate_response(self,user_text:str) -> str:
        response  = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role":"system",
                    "content":"You are a helpful voice assistant. Keep responses concise."
                },
                {
                    "role":"user",
                    "content":user_text
                }
            ]
        )
        return response.choices[0].message.content