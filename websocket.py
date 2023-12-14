import asyncio
import json
import logging
import ssl
from uuid import uuid4
import traceback

from fastapi import FastAPI, WebSocket
from openai_utils_generate_answer import generate_answer
from chat_bot_database import create_db_pool, get_user_info_by_session_id
from config import Config

# Initialize FastAPI app
app = FastAPI()

# Configuration and logging setup
OPENAI_API_KEY = Config.OPENAI_API_KEY
log_file_path = '/home/ubuntu/whattogrill-backend/logs/chat_bot_logs.txt'
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Dictionary to store user_id: WebSocket mapping
connections = {}

# Async function to create a connection pool
@app.on_event("startup")
async def startup():
    app.state.pool = await create_db_pool()
    logging.info("Database pool created")

# FastAPI WebSocket route
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str = None):
    await websocket.accept()
    userID = None
    try:
        logging.info(f"New WebSocket connection request from {websocket.client}")
        if session_id:
            user_info = await get_user_info_by_session_id(session_id, app.state.pool)
            if user_info:
                userID = user_info['username']
                connections[userID] = websocket
                logging.info(f"User {userID} connected with WebSocket from {websocket.client}")
            else:
                logging.error(f"Invalid session ID: {session_id}")
                await websocket.send_json({'error': 'Invalid session'})
                return
        else:
            await websocket.send_json({'error': 'Session ID required'})
            return

        while True:
            data = await websocket.receive_text()
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                logging.error(f"Received malformed data from {websocket.client}")
                continue

            userID = user_info.get('username', '')
            uuid = str(uuid4())
            message = data.get('message', '')
            user_ip = websocket.client.host

            response_text = await generate_answer(app.state.pool, userID, message, user_ip, uuid)
            response = {'response': response_text}
            await websocket.send_json(response)

            logging.info(f"Processed message from user {userID} at IP {user_ip}")
    except Exception as e:
        logging.error(f"Unhandled exception in websocket_endpoint for user {userID}: {e}")
        logging.error("Exception Traceback: " + traceback.format_exc())
    finally:
        logging.info(f"WebSocket disconnected for user {userID}")
        if userID in connections:
            del connections[userID]

# Run the app with Uvicorn
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='172.31.91.113', port=8055, ssl_keyfile='/home/ubuntu/whattogrill-backend/bot/privkey.pem', ssl_certfile='/home/ubuntu/whattogrill-backend/bot/fullchain.pem')
