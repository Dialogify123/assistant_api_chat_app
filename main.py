from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect
from constants import INSTRUCTION, FUNCTION
from services import chat_service
from services.vector_db import getTemplate


ASSISTANT = chat_service.Assistant(INSTRUCTION, FUNCTION, getTemplate)

app = FastAPI()

origins = [
    '*'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key="secret-d")

@app.websocket("/message")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        ASSISTANT.createThread(userId=1)
        try:
            while True:
                data = await websocket.receive_text()
                system_response = ASSISTANT.runAssistant(1, data)
                await websocket.send_text(system_response)
        except WebSocketDisconnect:
            ASSISTANT.deleteThread(1)
    except:
        pass