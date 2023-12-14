import asyncio
import json
import websockets
import ssl
import logging
from uuid import uuid4
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from openai_utils_generate_answer import generate_answer
from config import Config

# Importing database functions from database.py
from chat_bot_database import create_db_pool, get_user_info_by_session_id

OPENAI_API_KEY = Config.OPENAI_API_KEY

app = FastAPI()

log_file_path = '/home/ubuntu/whattogrill-backend/logs/chat_bot_logs.txt'
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,  # Use logging.INFO instead of print for logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

connections = {}

# Async function to create a connection pool
@app.websocket("/ws")
async def chatbot_handler(websocket: WebSocket):
    userID = None  # Initialize userID to None
    try:
        await websocket.accept()  # Accept the WebSocket connection
        print(f"New WebSocket connection request from {websocket.client.host}")

        initial_data = await websocket.receive_text()
        initial_data = json.loads(initial_data)
        session_id = initial_data.get('session_id', '')

        if session_id:
            user_info = await get_user_info_by_session_id(session_id, app_state.pool)
            if user_info:
                userID = user_info['username']
                connections[userID] = websocket
                print(f"User {userID} connected with WebSocket from {websocket.client.host}")
            else:
                print(f"Invalid session ID: {session_id}")
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
                print(f"Received malformed data from {websocket.client.host}")
                continue

            userID = user_info.get('username', '')
            uuid = str(uuid4())
            message = data.get('message', '')
            user_ip = websocket.client.host

            response_text = await generate_answer(app_state.pool, userID, message, user_ip, uuid)
            response = {'response': response_text}
            await websocket.send_json(response)

            print(f"Processed message from user {userID} at IP {user_ip}")
    except WebSocketDisconnect as e:
        print(f"WebSocket connection closed for user {userID}: {e}")
        if userID in connections:
            del connections[userID]
    except Exception as e:
        print(f"Unhandled exception in chatbot_handler for user {userID}: {e}")
        logging.exception(f"Exception occurred for user {userID}")
    finally:
        print(f"WebSocket disconnected for user {userID}")

if __name__ == '__main__':
    server_address = '172.31.91.113'
    server_port = 8055
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain('/home/ubuntu/whattogrill-backend/bot/fullchain.pem', '/home/ubuntu/whattogrill-backend/bot/privkey.pem')

    pool = asyncio.get_event_loop().run_until_complete(create_db_pool())
    print("created db pool")
    app_state = type('obj', (object,), {'pool': pool})

    start_server = websockets.serve(chatbot_handler, server_address, server_port, ssl=ssl_context)

    print('Starting WebSocket server...')
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
