import asyncio

import numpy as np
import torch
import torchaudio

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from app.pipeline import VoicePipeline
from app.services.vad import VADService


load_dotenv()


app = FastAPI(
    title="Interruptible Voice Agent"
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


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

    # --------------------------------
    # Per-session services
    # --------------------------------

    vad = VADService()
    pipeline = VoicePipeline()

    # --------------------------------
    # Audio configuration
    # --------------------------------

    input_sample_rate = 48000
    target_sample_rate = 16000
    chunk_size = 512

    audio_buffer = torch.zeros(
        0,
        dtype=torch.float32
    )

    # --------------------------------
    # Response state
    # --------------------------------

    active_response_task = None

    is_agent_speaking = False

    # --------------------------------
    # Outgoing message queue
    # --------------------------------

    outgoing_queue = asyncio.Queue()

    # --------------------------------
    # Send loop
    # --------------------------------

    async def send_loop():

        try:

            while True:

                message = await outgoing_queue.get()

                try:

                    if isinstance(message, bytes):

                        await websocket.send_bytes(
                            message
                        )

                    elif isinstance(message, dict):

                        await websocket.send_json(
                            message
                        )

                finally:

                    outgoing_queue.task_done()

        except asyncio.CancelledError:

            print("Send loop stopped")

    send_task = asyncio.create_task(
        send_loop()
    )

    # --------------------------------
    # Cancel active AI response
    # --------------------------------

    async def interrupt_agent():

        nonlocal active_response_task
        nonlocal is_agent_speaking

        print("⚡ INTERRUPT")

        # Stop server-side processing
        if (
            active_response_task
            and not active_response_task.done()
        ):

            active_response_task.cancel()

            try:

                await active_response_task

            except asyncio.CancelledError:

                pass

            print(
                "🛑 Active response cancelled"
            )

        active_response_task = None

        is_agent_speaking = False

        # Tell browser to stop audio
        await outgoing_queue.put(
            {
                "type": "interrupt"
            }
        )

    # --------------------------------
    # Generate AI response
    # --------------------------------

    async def generate_response(
        speech_audio
    ):

        nonlocal is_agent_speaking

        try:

            print(
                "🚀 Starting AI pipeline..."
            )

            audio_file = await pipeline.process_audio(
                speech_audio,
                sample_rate=target_sample_rate
            )

            # If task was cancelled, don't send audio
            if asyncio.current_task().cancelled():

                print(
                    "🛑 Response was cancelled"
                )

                return

            if audio_file is None:

                return

            print(
                "🔊 Sending audio:",
                audio_file
            )

            with open(
                audio_file,
                "rb"
            ) as audio:

                audio_bytes = audio.read()

            # Tell browser that AI audio is coming
            await outgoing_queue.put(
                {
                    "type": "audio_start"
                }
            )

            # Send audio
            await outgoing_queue.put(
                audio_bytes
            )

            # Browser will tell us when playback finishes

        except asyncio.CancelledError:

            print(
                "🛑 AI response task cancelled"
            )

            raise

        except Exception as error:

            print(
                "❌ Pipeline error:",
                error
            )

        finally:

            # Don't set is_agent_speaking=False here.
            #
            # The browser may still be playing the
            # generated audio.
            pass

    # --------------------------------
    # Receive loop
    # --------------------------------

    try:

        while True:

            message = await websocket.receive()

            # ==================================
            # BINARY AUDIO FROM MICROPHONE
            # ==================================

            if "bytes" in message:

                data = message["bytes"]

                if data is None:
                    continue

                # ------------------------------
                # PCM bytes → Int16
                # ------------------------------

                audio_int16 = np.frombuffer(
                    data,
                    dtype=np.int16
                ).copy()

                # ------------------------------
                # Int16 → Float32
                # ------------------------------

                audio = (
                    torch.from_numpy(
                        audio_int16
                    ).float()
                    / 32768.0
                )

                # ------------------------------
                # 48kHz → 16kHz
                # ------------------------------

                if (
                    input_sample_rate
                    != target_sample_rate
                ):

                    audio = (
                        torchaudio.functional.resample(
                            audio,
                            input_sample_rate,
                            target_sample_rate
                        )
                    )

                # ------------------------------
                # Add to persistent buffer
                # ------------------------------

                audio_buffer = torch.cat(
                    (
                        audio_buffer,
                        audio
                    )
                )

                # ------------------------------
                # Process 512 samples at a time
                # ------------------------------

                while (
                    len(audio_buffer)
                    >= chunk_size
                ):

                    chunk = audio_buffer[
                        :chunk_size
                    ]

                    audio_buffer = audio_buffer[
                        chunk_size:
                    ]

                    # --------------------------
                    # VAD
                    # --------------------------

                    event = vad.process_chunk(
                        chunk
                    )

                    if event is None:
                        continue

                    # ==========================
                    # USER STARTED SPEAKING
                    # ==========================

                    if (
                        event["type"]
                        == "speech_start"
                    ):

                        print(
                            "🎤 User started speaking"
                        )

                        # If AI is currently
                        # speaking/processing,
                        # interrupt it.
                        if (
                            is_agent_speaking
                            or (
                                active_response_task
                                and not active_response_task.done()
                            )
                        ):

                            await interrupt_agent()

                    # ==========================
                    # USER FINISHED SPEAKING
                    # ==========================

                    elif (
                        event["type"]
                        == "speech_end"
                    ):

                        print(
                            "🔇 User finished speaking"
                        )

                        speech_audio = event[
                            "audio"
                        ]

                        # Start new AI response
                        # WITHOUT blocking
                        # WebSocket receiving.
                        active_response_task = (
                            asyncio.create_task(
                                generate_response(
                                    speech_audio
                                )
                            )
                        )

            # ==================================
            # JSON MESSAGE FROM BROWSER
            # ==================================

            elif "text" in message:

                text = message["text"]

                if not text:
                    continue

                import json

                try:

                    command = json.loads(text)

                except json.JSONDecodeError:

                    continue

                # ------------------------------
                # Browser finished playback
                # ------------------------------

                if (
                    command.get("type")
                    == "playback_finished"
                ):

                    print(
                        "🔊 Browser finished AI audio"
                    )

                    is_agent_speaking = False

    except WebSocketDisconnect:

        print(
            "Client disconnected"
        )

    except Exception as error:

        print(
            "❌ WebSocket error:",
            error
        )

    finally:

        # Cancel AI response
        if (
            active_response_task
            and not active_response_task.done()
        ):

            active_response_task.cancel()

        # Stop sender
        send_task.cancel()

        try:

            await send_task

        except asyncio.CancelledError:

            pass

        print(
            "🔌 WebSocket session closed"
        )