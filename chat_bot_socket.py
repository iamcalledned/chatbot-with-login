#chat_bot_soceket
import sys
import os
# Get the directory of the current script
current_script_path = os.path.dirname(os.path.abspath(__file__))
# Set the path to the parent directory (one folder up)
parent_directory = os.path.dirname(current_script_path)
# Add the config directory to sys.path
sys.path.append(os.path.join(parent_directory, 'database'))
sys.path.append(os.path.join(parent_directory, 'config'))
import redis
import asyncio
import json
import websockets
import ssl
import logging
from uuid import uuid4
from datetime import datetime, timezone
from openai_utils_generate_answer import generate_answer
from config import Config
import pymysql
import aiomysql



# Other imports as necessary
OPENAI_API_KEY = Config.OPENAI_API_KEY


log_file_path = '/home/ubuntu/whattogrill-backend/logs/chat_bot_logs.txt'
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,  # Adjust the log level as needed (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Initialize Redis client
redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=0)


# get user info by session_id
async def get_user_info_by_sesion_id(session_id, db_pool):
    print("")
    """
    Asynchronously retrieve user information from the database using the session_id.
    """
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM login WHERE session_id = %s", (session_id,))
            result = await cur.fetchone()
            return result

# Async function to create a connection pool
async def create_db_pool():
    return await aiomysql.create_pool(
        host=Config.DB_HOST, port=Config.DB_PORT,
        user=Config.DB_USER, password=Config.DB_PASSWORD,
        db=Config.DB_NAME, charset='utf8', 
        cursorclass=aiomysql.DictCursor, autocommit=True
    )


# Dictionary to store user_id: websocket mapping
connections = {}

#add function to send direct message to users via websocket
async def send_direct_message(user_id, message):
    print(f"Sending message to user {user_id}: {message}")
    if user_id in connections:
        await connections[user_id].send(message)
    else:
        print(f"User {user_id} not connected")

#add message listener
async def message_listener(redis_client, channel):
    print("message listener")
    
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)
    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True)
        if message:
            data = json.loads(message['data'])
            user_id = data['user_id']
            msg = data['message']
            await send_direct_message(user_id, msg)
        await asyncio.sleep(0.01)  # Prevent busy waiting


async def chatbot_handler(websocket, path):
    logging.info(f"New WebSocket connection from {websocket.remote_address}")
    print(f"New WebSocket connection from {websocket.remote_address}")
    try:    
        initial_data = await websocket.recv()
        initial_data = json.loads(initial_data)
        session_id = initial_data.get('session_id', '')
        print("session_id", session_id)
        print("in tring session")
        if session_id:
            user_info = await get_user_info_by_session_id(session_id, app_state.db_pool)
            if user_info:
                userID = user_info['username']
                connections[userID] = websocket
            else:
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
                logging.warning(f"Received malformed data from {websocket.remote_address}")
                continue

            userID = user_info.get('username', '')
            uuid = str(uuid4())
            message = data.get('message', '')
            user_ip = websocket.remote_address[0]

            response_text = await generate_answer(userID, message, user_ip, uuid)
            response = {'response': response_text}
            await websocket.send(json.dumps(response))

            logging.info(f"Processed message from {user_ip}")
    except websockets.exceptions.ConnectionClosed as e:
        logging.error(f"Connection closed with exception: {e}")
        print(f"Connection closed with exception: {e}")
        if userID in connections:
            del connections[userID]
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")

if __name__ == '__main__':
    server_address = '172.31.91.113'
    server_port = 8055
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain('/home/ubuntu/whattogrill-backend/bot/fullchain.pem', '/home/ubuntu/whattogrill-backend/bot/privkey.pem')

    db_pool = asyncio.get_event_loop().run_until_complete(create_db_pool())
    app_state = type('obj', (object,), {'db_pool': db_pool})


    start_server = websockets.serve(chatbot_handler, server_address, server_port, ssl=ssl_context)

    logging.info('Starting WebSocket server...')
    print('Starting WebSocket server...')
    asyncio.get_event_loop().create_task(message_listener(redis_client, 'direct_messages'))
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
    