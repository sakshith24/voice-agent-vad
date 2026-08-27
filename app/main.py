import os
from fastapi import FastAPI, WebSocket,WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

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
