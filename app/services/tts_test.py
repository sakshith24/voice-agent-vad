from app.services.tts import TTSService


tts = TTSService()

audio_file = tts.synthesize(
    "C++ is a general-purpose programming language."
)

print("🔊 Audio generated:")
print(audio_file)