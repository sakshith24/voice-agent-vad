from app.services.stt import STTService
from app.services.llm import LLMService
from pathlib import Path

stt = STTService()
llm = LLMService()

audio_path = Path(__file__).parent/"audio.wav"
with open(audio_path, "rb") as audio_file:
    response = stt.client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )

text = response.text

print("user said : ")
print(text)

ai_response = llm.generate_response(text)

print("\n Ai response: ")
print(ai_response)