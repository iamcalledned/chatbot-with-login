import sys
import os
import asyncio
import json
import websockets
import ssl
import logging
from uuid import uuid4
from openai_utils_generate_answer import generate_answer
from config import Config

# Importing database functions from database.py
from chat_bot_database import create_db_pool, get_user_info_by_session_id

# Other imports as necessary
OPENAI_API_KEY = Config.OPENAI_API_KEY

log_file_path = '/home/ubuntu/whattogrill-backend/logs/chat_bot_logs.txt'
logging.basicConfig(
    filename=log_file_path,
    level=print,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# Initialize Redis client
# Make sure you have imported the necessary Redis client library
import redis
redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=0)

# Dictionary to store user_id: websocket mapping
connections = {}

# Function to send direct message to users via websocket
#async def send_direct_message(user_id, message):
#    print(f"Sending message to user {user_id}: {message}")
#    if user_id in connections:
#        await connections[user_id].send(message)
#    else:
#        print(f"User {user_id} not connected")

# Message listener
#async def message_listener(redis_client, channel):
#    print("message listener")
#    
#    pubsub = redis_client.pubsub()
#    await pubsub.subscribe(channel)
#    while True:
##        message = await pubsub.get_message(ignore_subscribe_messages=True)
#        if message:
#            data = json.loads(message['data'])
#            user_id = data['user_id']
#            msg = data['message']
##            await send_direct_message(user_id, msg)
#        await asyncio.sleep(0.01)  # Prevent busy waiting

# Chatbot handler
import traceback  # Import traceback for detailed error logging

# Async function to create a connection pool
async def create_pool():
    return await create_db_pool()

async def chatbot_handler(websocket, path):
    userID = None  # Initialize userID to None
    try:
        print(f"New WebSocket connection from {websocket.remote_address}")
        initial_data = await websocket.recv()
        print(f"Received initial data: {initial_data}")  # Log the received data
        initial_data = json.loads(initial_data)
        session_id = initial_data.get('session_id', '')

        if session_id:
            user_info = await get_user_info_by_session_id(session_id, app_state.db_pool)
            print(f"User info retrieved: {user_info}")  # Log user info
            if user_info:
                userID = user_info['username']
                connections[userID] = websocket
                print(f"User {userID} connected with WebSocket")  # Log successful connection
            else:
                print(f"Invalid session ID: {session_id}")  # Log invalid session
                await websocket.send(json.dumps({'error': 'Invalid session'}))
                return
        else:
            await websocket.send(json.dumps({'error': 'Session ID required'}))
            return

        while True:
            data = await websocket.recv()
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                print(f"Received malformed data from {websocket.remote_address}")
                continue

            userID = user_info.get('username', '')
            uuid = str(uuid4())
            message = data.get('message', '')
            user_ip = websocket.remote_address[0]

            response_text = await generate_answer(app_state.db_pool, userID, message, user_ip, uuid)
            response = {'response': response_text}
            await websocket.send(json.dumps(response))

            print(f"Processed message from user {userID} at IP {user_ip}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"WebSocket connection closed with exception for user {userID}: {e}. Reason: {e.reason}. Code: {e.code}")
        if userID in connections:
            del connections[userID]
    except Exception as e:
        print(f"Unhandled exception in chatbot_handler for user {userID}: {e}")
        print("Exception Traceback: " + traceback.format_exc())
    finally:
        # Log when a WebSocket disconnects
        print(f"WebSocket disconnected for user {userID}")

# Main function
# Main function
async def main():
    db_pool = await create_pool()
    print("created pool in main")

    server_address = '172.31.91.113'
    server_port = 8055
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain('/home/ubuntu/whattogrill-backend/bot/fullchain.pem', '/home/ubuntu/whattogrill-backend/bot/privkey.pem')

    async with websockets.serve(lambda ws, path: chatbot_handler(ws, path, db_pool), server_address, server_port, ssl=ssl_context):
        print('Starting WebSocket server...')
        await asyncio.Future()
    

if __name__ == '__main__':
    asyncio.run(main())