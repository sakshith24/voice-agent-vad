import io

import torchaudio
from openai import OpenAI


class STTService:

    def __init__(self):
        self.client = OpenAI()

    def transcribe(self, speech_audio, sample_rate: int = 16000) -> str:

        # VAD returns [samples]
        # torchaudio.save expects [channels, samples]
        if speech_audio.dim() == 1:
            waveform = speech_audio.unsqueeze(0)
        else:
            waveform = speech_audio

        # Create WAV in memory
        audio_buffer = io.BytesIO()
        audio_buffer.name = "audio.wav"

        torchaudio.save(
            audio_buffer,
            waveform,
            sample_rate,
            format="wav"
        )

        audio_buffer.seek(0)

        # Send audio to OpenAI
        response = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_buffer
        )

        return response.text