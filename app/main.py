import os
from fastapi import FastAPI, WebSocket,WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app.services.vad import VADService


load_dotenv()

app = FastAPI(title="Interruptible Voice agent")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
    return{"status":"Voice agent server running" , "frontend":"/static/index.html"}

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket:WebSocket):
    await websocket.accept()
    print("Client connected via Websocket")
    try:
        while True:
            data= await websocket.receive_bytes()
            await websocket.send_text("Audio chunk recieved")
    except WebSocketDisconnect:
        print("Client Disconnected") 

@app.websocket("/ws")
async def websocket_endpoint(websocket):

    await websocket.accept()

    vad = VADService()

    while True:

        audio_chunk = await websocket.receive_bytes()

        speech = vad.process_chunk(audio_chunk)

        if speech is not None:
            print("speech ended")
            print(f"Recived {len(speech)} bytes")
            await websocket.send_text("Audio chunk received")

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    print("Client connected via WebSocket")

    try:
        while True:

            data = await websocket.receive_bytes()

            print("Received PCM :", len(data), "bytes")

    except WebSocketDisconnect:
        print("Client disconnected")