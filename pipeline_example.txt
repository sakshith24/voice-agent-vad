import asyncio
import time

from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService


class VoicePipeline:

    def __init__(self):
        self.stt = STTService()
        self.llm = LLMService()
        self.tts = TTSService()

    async def process_audio(
        self,
        speech_audio,
        sample_rate=16000
    ):
        print("✅ Processing complete speech segment")
        print("Tensor shape:", speech_audio.shape)
        print("Samples:", speech_audio.numel())

        # Make absolutely sure STT receives 1-D audio
        speech_audio = speech_audio.flatten()

        loop = asyncio.get_running_loop()

        # -------------------------
        # STT
        # -------------------------

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

        if not text.strip():
            print("⚠️ Empty transcription")
            return None

        # -------------------------
        # LLM
        # -------------------------

        start = time.perf_counter()

        response = await loop.run_in_executor(
            None,
            self.llm.generate_response,
            text
        )

        llm_time = time.perf_counter() - start

        print("🤖 AI:", response)
        print(f"⏱️ LLM time: {llm_time:.2f}s")

        # -------------------------
        # TTS
        # -------------------------

        start = time.perf_counter()

        audio_file = await loop.run_in_executor(
            None,
            self.tts.synthesize,
            response
        )

        tts_time = time.perf_counter() - start

        print("🔊 Audio:", audio_file)
        print(f"⏱️ TTS time: {tts_time:.2f}s")

        return audio_file