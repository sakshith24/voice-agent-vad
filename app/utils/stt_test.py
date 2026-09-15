from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

with open("audio.wav", "rb") as audio_file:
    transcript_response = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )

print(transcript_response.text)