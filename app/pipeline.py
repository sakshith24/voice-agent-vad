import asyncio
import time

from app.services.vad import VADService
from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService


class VoicePipeline:

    def __init__(self):
        self.vad = VADService()
        self.stt = STTService()
        self.llm = LLMService()
        self.tts = TTSService()

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

        start = time.perf_counter()

        text = await loop.run_in_executor(
            None,
            self.stt.transcribe,
            speech_audio,
            sample_rate
        )

        stt_time = time.perf_counter() - start

        print("📝 User said:", text)
        print(f"⏱️ STT time: {stt_time:.2f}s")

        start = time.perf_counter()

        response = await loop.run_in_executor(
            None,
            self.llm.generate_response,
            text
        )

        llm_time = time.perf_counter() - start

        print("🤖 AI:", response)
        print(f"⏱️ LLM time: {llm_time:.2f}s")

        print(f"⏱️ Total STT + LLM: {stt_time + llm_time:.2f}s")

        audio_file = await loop.run_in_executor(
            None,
            self.tts.synthesize,
            response
        )
        print("🔊 Audio:", audio_file)

        # return response

# asyncio.run(run_pipeline())