import asyncio
from app.services.stt import STTService
from app.services.vad import VADService

# Initialize services
vad = VADService()
stt = STTService()


async def process_speech_async(speech_audio, sample_rate=16000):
    """Offload blocking HTTP request to an async thread pool."""
    loop = asyncio.get_running_loop()
    # Runs the synchronous stt.transcribe call in a background thread
    text = await loop.run_in_executor(
        None, stt.transcribe, speech_audio, sample_rate
    )
    print("User said:", text)
    return text


async def run_pipeline():
    sample_rate = 16000

    while True:
        chunk = await get_next_audio_chunk()  # Replace with your mic/stream reader

        # VAD accumulates audio frames until speech ends
        speech_audio = vad.process_chunk(chunk)

        if speech_audio is not None:
            # Dispatch transcription without stopping the audio reading loop
            asyncio.create_task(
                process_speech_async(speech_audio, sample_rate)
            )


# asyncio.run(run_pipeline())