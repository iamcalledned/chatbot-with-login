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
import database  # Importing the database module
from database import get_active_thread_for_user, insert_user, insert_thread, insert_conversation
import datetime
import logging
import asyncio
import aiomysql 
from config import Config
from database import create_pool, get_active_thread_for_user, insert_user, insert_thread, insert_conversation, pool


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

async def generate_answer(userID, message, user_ip, uuid):
    # Use your new database module to create a connection
    print("in generate answer")
    pool = await create_pool()  # Create the connection pool
    print("pool in genanswer", pool)
    if pool is None:
        return "Error: Failed to connect to the database."
    print("trying to aquire popl")
    async with pool.acquire() as conn:  # Acquire a connection from the pool
        user_id = await insert_user(conn, userID)
        print("Database user_id for userID:", userID, "is", user_id)

        active_thread = await get_active_thread_for_user(conn, user_id)
        if active_thread:
            thread_id_n = active_thread[0]
            print("Active thread found for userID:", userID, "Thread ID:", thread_id_n)

            if await is_thread_valid(thread_id_n):
                print("Thread is valid. Continuing with Thread ID:", thread_id_n)
            else:
                print("Thread is no longer valid. Creating a new thread.")
                thread_id_n = await create_thread_in_openai()
                current_time = datetime.datetime.now().isoformat()
                await insert_thread(conn, thread_id_n, user_id, True, current_time)
        else:
            print("No active thread found for userID:", userID, "Creating a new thread.")
            thread_id_n = await create_thread_in_openai()
            current_time = datetime.datetime.now().isoformat()
            await insert_thread(conn, thread_id_n, user_id, True, current_time)

        if thread_id_n:
            response_text = await send_message(thread_id_n, message)
            print("created message to send")

            # Create the run on OpenAI
            run = client.beta.threads.runs.create(
                thread_id=thread_id_n,
                assistant_id="asst_ODqZJkwekTSZwZT554Sabqm2"
            )
            print("created run on openAI")

            if run is not None:
                # Now we have a run ID, we can log the user's message
                await insert_conversation(conn, user_id, thread_id_n, run.id, message, 'user', user_ip)  # Replace 'user_ip' with actual IP if available

                while True:
                    run = client.beta.threads.runs.retrieve(
                        thread_id=thread_id_n,
                        run_id=run.id
                    )
                    print("checking status...")
                    if run.status == "completed":
                        print("response received for thread:", thread_id_n, run.id)
                        break
                    elif run.status == "error":
                        print("Error encountered in run")
                        break

                    await asyncio.sleep(1)   # Wait for 1 second before the next status check

                messages = client.beta.threads.messages.list(
                    thread_id=thread_id_n
                )
                message_content = messages.data[0].content[0].text.value
                print("messages sent")

                # Log OpenAI's response
                await insert_conversation(conn, user_id, thread_id_n, run.id, message_content, 'bot', None)  # Same here for IP
                print("saved conversations for user:", user_id)
            else:
                print("Failed to create a run object in OpenAI.")
                return "Error: Failed to create a run object."

            return message_content
        else:
            return "Error: Failed to create a new thread in OpenAI."
