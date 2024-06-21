import asyncio
import json
import logging
from uuid import uuid4
import traceback

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter, Request
from config import Config
from chat_bot_database import create_db_pool, get_user_id, get_recent_messages
from handlers import (
    handle_chat_message,
    handle_save_recipe,
    handle_get_user_recipes,
    handle_load_more_messages,
    handle_print_recipe,
    handle_remove_recipe,
)
from utilities import clear_session_data_after_timeout

import redis

# Initialize Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Initialize FastAPI app
app = FastAPI()
router = APIRouter()

log_file_path = Config.LOG_PATH
LOG_FORMAT = 'WEBSOCKET - %(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s'

logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format=LOG_FORMAT
)

# Async function to create a connection pool
async def create_pool():
    return await create_db_pool()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    cookies = websocket.cookies
    session_id_from_cookies = cookies.get('session_id')
    client_host, client_port = websocket.client
    client_ip = client_host
    print(f"Client IP: {client_ip}")
    print("connections at websocket_endpoint:", connections)
    
    username = None
    
    async def ping_client():
        while True:
            try:
                await websocket.send_text(json.dumps({'action': 'ping'}))
                await asyncio.sleep(30)  # Send a ping every 30 seconds
            except Exception as e:
                print(f"Error sending ping: {e}")
                break
    ping_task = asyncio.create_task(ping_client())

    try:
        initial_data = await websocket.receive_text()
        initial_data = json.loads(initial_data)
        session_id = session_id_from_cookies

        if session_id:
            session_data = redis_client.get(session_id)
            if session_data:
                session_data = json.loads(session_data)
                username = session_data['username']
                # Renew the session expiry time upon successful connection
                redis_client.expire(session_id, 3600)  # Reset expiry to another hour
                # Get and send recent messages
                userID = await get_user_id(app.state.pool, username)
                recent_messages = await get_recent_messages(app.state.pool, userID)
                await websocket.send_text(json.dumps({
                    'action': 'recent_messages',
                    'messages': recent_messages
                }))
            else:
                await websocket.send_text(json.dumps({'action': 'redirect_login', 'error': 'Invalid session'}))
                return
        else:
            await websocket.send_text(json.dumps({'action': 'redirect_login', 'error': 'Session ID required'}))
            return

        while True:
            data = await websocket.receive_text()
            data_dict = json.loads(data)
            await dispatch_action(websocket, data_dict, app.state.pool, username, client_ip)
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {username}")
        print(f"Connections: {connections}")
        print(f"sessionid:", session_id)
        if session_id:
            task = asyncio.create_task(clear_session_data_after_timeout(session_id, username, redis_client, app.state.pool))
            tasks[session_id] = task
        connections.pop(username, None)

    except Exception as e:
        print(f"Unhandled exception for user {username}: {e}")
        print("Exception Traceback: " + traceback.format_exc())
    finally:
        ping_task.cancel()

async def dispatch_action(websocket, data_dict, pool, username, client_ip):
    action = data_dict.get('action')
    if action == 'save_recipe':
        await handle_save_recipe(websocket, data_dict, pool, username)
    elif action == 'get_user_recipes':
        await handle_get_user_recipes(websocket, pool, username)
    elif action == 'load_more_messages':
        await handle_load_more_messages(websocket, data_dict, pool, username)
    elif action == 'print_recipe':
        await handle_print_recipe(websocket, data_dict, pool)
    elif action == 'remove_recipe':
        await handle_remove_recipe(data_dict, pool, username)
    elif action == 'chat_message':
        await handle_chat_message(websocket, data_dict, pool, username, client_ip)
    elif action == 'pong':
        redis_client.expire(data_dict.get('session_id'), 3600)  # Reset expiry to another hour

@router.post("/validate_session")
async def validate_session(request: Request):
    session_id = request.json().get('session_id', '')
    if session_id and redis_client.exists(session_id):
        return {"status": "valid"}
    else:
        return {"status": "invalid"}

@router.post("/logout")
async def logout(request: Request):
    session_id = request.json().get('session_id', '')
    if session_id:
        # Remove session data from Redis
        redis_client.delete(session_id)

        # Additional cleanup if necessary
        username = connections.pop(session_id, None)
        if username:
            print(f"User {username} logged out and disconnected.")

    return {"message": "Logged out successfully"}

@app.on_event("startup")
async def startup_event():
    app.state.pool = await create_pool()
    print("Database pool created")
    print("connections at startup:", connections)

# Run with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
