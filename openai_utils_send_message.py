# openai_utils_send_message.py
from openai import AsyncOpenAI
import sys
import os
from config import Config

# Fix Python pathing
current_script_path = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.dirname(current_script_path)
sys.path.append(os.path.join(parent_directory, 'database'))
sys.path.append(os.path.join(parent_directory, 'config'))

# Async OpenAI client
openai_client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

# Send message to thread
async def send_message(thread_id_n, message):
    try:
        response = await openai_client.beta.threads.messages.create(
            thread_id=thread_id_n,
            role="user",
            content=message
        )
        return response.content[0].text.value
    except Exception as e:
        print(f"Error in sending message: {e}")
        return "Error in sending message."
