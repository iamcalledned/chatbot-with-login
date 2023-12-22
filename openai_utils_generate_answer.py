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
from process_recipe import process_recipe


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

async def generate_answer(pool,username, message, user_ip, uuid):  # Add db_pool parameter
    # Use database to get userID
        recipe_id = None
        
        userID = await get_user_id(pool, username)
        print("userID", userID, "username", username)
    
    
        active_thread = await get_active_thread_for_user(pool, userID)

        if active_thread:
            thread_id_n = active_thread['ThreadID']  # Use .get() method to safely access the key
            if thread_id_n:
                if await is_thread_valid(thread_id_n):
                    print("Thread is valid. Continuing with Thread ID:", thread_id_n)
                else:
                    
                    thread_id_n = await create_thread_in_openai()
                    current_time = datetime.datetime.now().isoformat()
                    await insert_thread(pool, thread_id_n, userID, True, current_time)
            else:
                print("Key 0 is not present in active_thread.")
        else:
            print("No active thread found for userID:", userID, "Creating a new thread.")
            thread_id_n = await create_thread_in_openai()
            current_time = datetime.datetime.now().isoformat()
            await insert_thread(pool, thread_id_n, userID, True, current_time)

        if thread_id_n:
            response_text = await send_message(thread_id_n, message)
            

            # Create the run on OpenAI
            run = client.beta.threads.runs.create(
                thread_id=thread_id_n,
                assistant_id="asst_ODqZJkwekTSZwZT554Sabqm2"
            )
            

            if run is not None:
                # Now we have a run ID, we can log the user's message
                await insert_conversation(pool, userID, thread_id_n, run.id, message, 'user', user_ip)  # Replace 'user_ip' with actual IP if available

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

                    await asyncio.sleep(1)   # Wait for 1 second before the next status check

                messages = client.beta.threads.messages.list(
                    thread_id=thread_id_n
                )
                message_content = messages.data[0].content[0].text.value
            
            
                content_type = await classify_content(message_content)
                if content_type == 'recipe':
                    save_result, recipe_id = await process_recipe(pool, message_content, userID)
                    print("done processing recipe")
                    


                
                
            
                

                # Log OpenAI's response
                await insert_conversation(pool, userID, thread_id_n, run.id, message_content, 'bot', None)  # Same here for IP
                print("saved conversations for user:", userID)
            else:
                print("Failed to create a run object in OpenAI.")
                return "Error: Failed to create a run object."

            return message_content, content_type, recipe_id
        else:
            return "Error: Failed to create a new thread in OpenAI."
