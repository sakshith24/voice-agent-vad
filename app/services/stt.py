import io
import wave

import numpy as np
from openai import OpenAI


class STTService:
    def __init__(self):
        self.client = OpenAI()

    def transcribe(self, speech_audio, sample_rate: int = 16000) -> str:
        # Convert PyTorch tensor → NumPy
        audio = speech_audio.detach().cpu().numpy()

        # Convert float32 [-1, 1] → int16 PCM
        audio_int16 = (audio * 32767).clip(-32768, 32767).astype(np.int16)

        # Create WAV in memory
        audio_buffer = io.BytesIO()

        with wave.open(audio_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # int16 = 2 bytes
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        audio_buffer.seek(0)
        audio_buffer.name = "speech.wav"

        # Send to OpenAI STT
        response = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_buffer
        )

        return response.text