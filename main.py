import redis

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from typing import List

app = FastAPI()
templates = Jinja2Templates(directory="templates")
db = redis.Redis(host='127.0.0.1', port='6379')
class User:
    id: int
    name: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)


    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, type: str, data: str, id:int):
        for connection in self.active_connections:
            await connection.send_json({'type': type, 'data': data, 'id': id})

    async def add_users(self):
        self.list_users: List[User] = []


manager = ConnectionManager()

@app.get('/')
def index(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, 'id':12})

@app.get('/room')
def room(request: Request):
    return templates.TemplateResponse("room.html", {"request": request})

@app.websocket("/ws/{client_id}/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_id: int, client_name: str):

    await manager.connect(websocket)
    try:
        await manager.broadcast('JOIN', client_name, client_id)
        #await manager.add_users()
        db.set('id', 1)
        db.append('id', 2)
        print(db.get('id'))
        await manager.broadcast('SEND_MESSAGE', f"{client_name} присойденился к Мужикам", client_id)

        while True:
            data = await websocket.receive_text()
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            # await manager.broadcast(f"Мужик {client_name} сказал: {data}")
            await manager.broadcast('SEND_MESSAGE', f"Мужик {client_name} написал: {data}", client_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast('SEND_MESSAGE', f"Мужик {client_name} покинул мужской чат", client_id)
        await manager.broadcast('LEAVE', client_name, client_id)
