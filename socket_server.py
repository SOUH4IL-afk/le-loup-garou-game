from fastapi import FastAPI
import socketio


sio = socketio.AsyncServer(cors_allowed_origins='*')
app = FastAPI()


sio_app = socketio.ASGIApp(sio, app)


rooms = {}


@sio.event
async def connect(sid, environ):
print('Client connected:', sid)


@sio.event
async def join_room(sid, data):
room = data['room']
sio.enter_room(sid, room)
await sio.emit('system', f'User joined {room}', room=room)


@sio.event
async def chat(sid, data):
room = data['room']
msg = data['msg']
user = data.get('user', 'Anon')
await sio.emit('chat', {'user': user, 'msg': msg}, room=room)


@sio.event
async def vote(sid, data):
room = data['room']
await sio.emit('vote', data, room=room)


@sio.event
async def disconnect(sid):
print('Client disconnected:', sid)


# تشغيل السيرفر:
# uvicorn socket_server:sio_app --host 0.0.0.0 --port 8000