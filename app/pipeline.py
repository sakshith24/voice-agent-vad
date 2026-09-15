import asyncio

from app.services.vad import VADService
from app.services.stt import STTService


class VoicePipeline:

    def __init__(self):
        self.vad = VADService()
        self.stt = STTService()

    async def process_chunk(self, chunk, sample_rate=16000):
        """
        Process one 512-sample audio chunk.

        Audio flow:
        chunk → VAD → complete speech → STT
        """

        speech_audio = self.vad.process_chunk(chunk)

        # VAD has not detected the end of speech yet
        if speech_audio is None:
            return None

        print("✅ Complete speech segment detected")
        print("Samples:", len(speech_audio))

        # STT is a blocking HTTP request,
        # so run it in a background thread.
        loop = asyncio.get_running_loop()

        text = await loop.run_in_executor(
            None,
            self.stt.transcribe,
            speech_audio,
            sample_rate
        )

        print("📝 User said:", text)

        return text

# asyncio.run(run_pipeline())