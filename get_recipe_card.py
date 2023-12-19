# generate_answer.py
import time
import sys
import os
# Get the directory of the current script
current_script_path = os.path.dirname(os.path.abspath(__file__))
# Set the path to the parent directory (one folder up)
parent_directory = os.path.dirname(current_script_path)
# Add the config directory to sys.path
sys.path.append(os.path.join(parent_directory, 'database'))
sys.path.append(os.path.join(parent_directory, 'config'))
from openai_utils_new_thread import create_thread_in_openai, is_thread_valid
from openai_utils_send_message import send_message
from openai import OpenAI

from chat_bot_database import get_active_thread_for_user, insert_thread, insert_conversation, create_db_pool ,get_user_id
import datetime
import logging
import asyncio
import aiomysql 
from config import Config
from classify_content import classify_content
import re


# Other imports as necessary
OPENAI_API_KEY = Config.OPENAI_API_KEY


log_file_path = '/home/ubuntu/whattogrill-backend/logs/generate_answer_logs.txt'
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,  # Adjust the log level as needed (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize OpenAI client

openai_client = OpenAI()
openai_client.api_key = Config.OPENAI_API_KEY
client = OpenAI()

async def get_recipe_card(pool, message):  # Add db_pool parameter
    # Use your new database module to create a connection
    print("made it to get recipe card")       
    
    thread_id_n = await create_thread_in_openai()
    print("thread id n", thread_id_n)
    print("message", message)
    if thread_id_n:
        message = await send_message(thread_id_n, message)
        

        # Create the run on OpenAI
        run = client.beta.threads.runs.create(
            thread_id=thread_id_n,
            assistant_id="asst_1cQYQ91vErRgWrhrQXuw5aIo"
        )
        print("run", run)

        if run is not None:
            while True:
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread_id_n,
                    run_id=run.id
                )
        
                if run.status == "completed":
                    print("Run completed. Message:", run.status)
                    break
                elif run.status == "error":
                    print("Run error", run.status)
                    break
                print("waiting...")
                await asyncio.sleep(1)   # Wait for 1 second before the next status check

            messages = client.beta.threads.messages.list(
                thread_id=thread_id_n
            )
            recipe_card = messages.data[0].content[0].text.value
        
        
            
            
            

        return recipe_card
    else:
        return "Error: Failed to create a new thread in OpenAI."
