import numpy as np
import torch
import torchaudio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.services.vad import VADService
from app.pipeline import VoicePipeline

load_dotenv()
pipeline = VoicePipeline()

app = FastAPI(title="Interruptible Voice Agent")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def get_index():
    return {
        "status": "Voice agent server running",
        "frontend": "/static/index.html"
    }


@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()
    print("Client connected via WebSocket")

    vad = VADService()

    # Browser microphone sample rate
    input_sample_rate = 48000
    chunk_size = 512

    # Persistent Audio Buffer initialized per WebSocket session
    audio_buffer = torch.zeros(0, dtype=torch.float32)

    try:
        while True:

            data = await websocket.receive_bytes()

            # 1. PCM bytes → Int16 NumPy array
            audio_int16 = np.frombuffer(data, dtype=np.int16).copy()

            # 2. Int16 → Float32
            audio = torch.from_numpy(audio_int16).float() / 32768.0

            # 3. 48 kHz → 16 kHz
            if input_sample_rate != 16000:
                audio = torchaudio.functional.resample(
                    audio,
                    input_sample_rate,
                    16000
                )

            # 4. Append converted incoming audio to persistent buffer
            audio_buffer = torch.cat((audio_buffer, audio))

            # 5. Extract fixed 512-sample chunks while sufficient audio exists
            while len(audio_buffer) >= chunk_size:
                # Slice out the first 512 samples
                chunk = audio_buffer[:chunk_size]

                # Update the buffer to hold remaining leftover samples
                audio_buffer = audio_buffer[chunk_size:]

                audio_file = await pipeline.process_chunk(
                    chunk,
                    sample_rate=16000
                )
                if audio_file is not None:
                    print("🔊 Sending audio:: ", audio_file)
                    with open(audio_file,"rb") as f:
                        audio_data = f.read()
                    await websocket.send_bytes(audio_data)

    except WebSocketDisconnect:
        print("Client disconnected")