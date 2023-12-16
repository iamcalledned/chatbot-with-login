import asyncio
import json
import logging
import ssl
from uuid import uuid4
import traceback

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.endpoints import WebSocketEndpoint

from openai_utils_generate_answer import generate_answer
from config import Config
from chat_bot_database import create_db_pool, get_user_info_by_session_id, save_recipe_to_db




# Initialize FastAPI app
app = FastAPI()
OPENAI_API_KEY = Config.OPENAI_API_KEY
connections = {}  # Dictionary to store user_id: websocket mapping

log_file_path = Config.LOG_PATH
LOG_FORMAT = 'generate-answer - %(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s'

logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,  # Adjust the log level as needed (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format=LOG_FORMAT
)

# Async function to create a connection pool
async def create_pool():
    return await create_db_pool()


@app.on_event("startup")
async def startup_event():
    app.state.pool = await create_pool()
    print("Database pool created")


@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id = None

    try:
        initial_data = await websocket.receive_text()
        initial_data = json.loads(initial_data)
        session_id = initial_data.get('session_id', '')

        if session_id:
            user_info = await get_user_info_by_session_id(session_id, app.state.pool)
            if user_info:
                user_id = user_info['username']
                connections[user_id] = websocket
                print(f"User {user_id} connected with WebSocket")
            else:
                await websocket.send_text(json.dumps({'error': 'Invalid session'}))
                return
        else:
            await websocket.send_text(json.dumps({'error': 'Session ID required'}))
            return

        while True:
            data = await websocket.receive_text()
            data_dict = json.loads(data)
            #print("data_dict", data_dict)

            if 'action' in data_dict and data_dict['action'] == 'save_recipe':
                # Handle the save recipe action
                recipe_content = data_dict['content']
                print("recipe_content:", recipe_content)
                save_result = await save_recipe_to_db(app.state.pool, user_id, recipe_content)  # Replace with your DB save logic
                
                await websocket.send_text(json.dumps({'action': 'recipe_saved', 'status': save_result}))
            else:
                # Handle regular messages
                message = data_dict.get('message', '')
                user_ip = "User IP"  # Placeholder for user IP
                uuid = str(uuid4())

                response_text, content_type = await generate_answer(app.state.pool, user_id, message, user_ip, uuid)
                response = {
                    'response': response_text,
                    'type': content_type,
                }
                await websocket.send_text(json.dumps(response))

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {user_id}")
        connections.pop(user_id, None)
    except Exception as e:
        print(f"Unhandled exception for user {user_id}: {e}")
        print("Exception Traceback: " + traceback.format_exc())

# Run with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
