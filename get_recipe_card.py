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

from chat_bot_database import get_active_thread_for_user, insert_thread, insert_conversation, create_db_pool
import datetime
import logging
import asyncio
import aiomysql 
from config import Config
from classify_content import classify_content
import re
import json
from get_recipe_card import get_recipe_card


# Other imports as necessary
OPENAI_API_KEY = Config.OPENAI_API_KEY


# Initialize OpenAI client

openai_client = OpenAI()
openai_client.api_key = Config.OPENAI_API_KEY
client = OpenAI()

def name_recipe(recipe_text):
    prompt = """You are a wiz at turning a block of text that contains a recipe with a name, ingredients, directions/instructions, prep, cook, and total times into a format that can be injected into a database in the following JSON format.  {
  "recipe_name": "",
"servings":"",
  "prepTime": "",
  "cookTime": "",
  "totalTime": "",
  "parts": [
    {
      "part_name": "xxxt",
      "ingredients": [],
      "instructions": []
    },  The JSON format is important, if something is missing, put "N/A".  You make sure that all steps and ingredients are included in the output  You know that some recipes have multiple components like pies for filling and crust.  In order to account for this in the database, even recopies with one component must be set as a part"""

    # Append the prompt to the recipe text
    modified_message = f"{prompt}{recipe_text}"

    print("creating recipe card")
    response = openai_client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "user", "content": modified_message},
        ],
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=0.7,
        frequency_penalty=0.7,
        presence_penalty=0.7
    )
    recipe_card = response.choices[0].message.content
    print("recipe card", recipe_card)
    return recipe_card
    
