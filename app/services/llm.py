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
                    "content":"""
                    You are a real-time voice assistant.

                    Rules:
                    - Respond in English.
                    - Keep responses concise and natural for spoken conversation.
                    - Use short sentences.
                    - Avoid unnecessary lists, tables, markdown, and long explanations.
                    - Give the answer directly.
                    - Do not repeat the user's question unless necessary.
                    - If the user asks a simple question, give a simple answer.
                    - If you don't know something, say so clearly.
                    """
                },
                {
                    "role":"user",
                    "content":user_text
                }
            ]
        )
        return response.choices[0].message.content