import os
import asyncio
import aiomysql
import datetime
import uuid
from config import Config
import pymysql
import base64
import hashlib
import jwt
from jwt.algorithms import RSAAlgorithm
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Define the DB_CONFIG directly here or use a separate configuration file
DB_CONFIG = {
    "host": Config.DB_HOST,
    "port": Config.DB_PORT,
    "user": Config.DB_USER,
    "password": Config.DB_PASSWORD,
    "db": Config.DB_NAME,
}

pool = None

async def create_db_pool():
    return await aiomysql.create_pool(
        host=Config.DB_HOST, port=Config.DB_PORT,
        user=Config.DB_USER, password=Config.DB_PASSWORD,
        db=Config.DB_NAME, charset='utf8',
        cursorclass=aiomysql.DictCursor, autocommit=True
    )

async def get_user_info_by_session_id(session_id, pool):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM user_data WHERE current_session_id = %s", (session_id,))
            result = await cur.fetchone()
            return result
        
async def clear_user_session_id(pool, session_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Update the user_data table to clear the current_session_id
            sql_update = "UPDATE user_data SET current_session_id = NULL WHERE current_session_id = %s"
            await cursor.execute(sql_update, (session_id,))
            await conn.commit()
            print("Cleared session ID for user")

       


async def insert_thread(pool, thread_id, userID, is_active, created_time):
    """Insert a new thread into the threads table"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            sql = '''INSERT INTO threads(ThreadID, UserID, IsActive, CreatedTime)
                     VALUES(%s, %s, %s, %s)'''
            await cur.execute(sql, (thread_id, userID, is_active, created_time))
            await conn.commit()

async def get_active_thread_for_user(pool, userID):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            sql = '''SELECT ThreadID FROM threads WHERE UserID = %s'''
            await cur.execute(sql, (userID,))
            return await cur.fetchone()

async def deactivate_thread(pool, thread_id):
    """Mark a thread as inactive"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            sql = '''UPDATE threads SET IsActive = 0 WHERE ThreadID = %s'''
            await cur.execute(sql, (thread_id,))
            await conn.commit()

async def insert_conversation(pool, userID, thread_id, run_id, message, message_type, ip_address):
    """Insert a new conversation record into the conversations table"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            sql = '''INSERT INTO conversations(UserID, ThreadID, RunID, Message, MessageType, IPAddress)
                     VALUES(%s, %s, %s, %s, %s, %s)'''
            await cur.execute(sql, (userID, thread_id, run_id, message, message_type, ip_address))
            await conn.commit()

async def get_conversations_by_run(pool, run_id):
    """Fetch all conversations for a given RunID"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            sql = '''SELECT * FROM conversations WHERE RunID = %s'''
            await cur.execute(sql, (run_id,))
            return await cur.fetchall()

async def update_conversation_status(pool, conversation_id, new_status):
    """Update the status of a conversation"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            sql = '''UPDATE conversations SET Status = %s WHERE ConversationID = %s'''
            await cur.execute(sql, (new_status, conversation_id))
            await conn.commit()

async def start_new_run(pool, userID, thread_id):
    """Start a new run and return its RunID"""
    run_id = str(uuid.uuid4())
    current_time = datetime.datetime.now().isoformat()
    await insert_thread(pool, thread_id, userID, True, current_time)
    return run_id

async def end_run(pool, run_id):
    """Mark a run as completed"""
    # Logic to mark a run as completed, e.g., updating a runs table or updating conversation statuses
    pass


async def get_user_id(pool, username):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT userID FROM user_data WHERE username = %s", (username,))
            result = await cur.fetchone()
            return result['userID'] if result else None


async def save_recipe_to_db(pool, userID, recipe_data):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            save_result = None
            # Insert into recipes table
            add_recipe = """
                INSERT INTO recipes (userID, title, servings, prep_time, cook_time, total_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            await cur.execute(add_recipe, (userID, recipe_data["title"], recipe_data["servings"], 
                                           recipe_data["prep_time"], recipe_data["cook_time"], recipe_data["total_time"]))
            recipe_id = cur.lastrowid  # Get the ID of the inserted recipe

            # Insert ingredients
            add_ingredient = "INSERT INTO ingredients (recipe_id, item, category) VALUES (%s, %s, %s)"
            for ingredient in recipe_data["ingredients"]:
                await cur.execute(add_ingredient, (recipe_id, ingredient["item"], ingredient.get("category")))

            # Insert instructions
            add_instruction = "INSERT INTO instructions (recipe_id, step_number, description) VALUES (%s, %s, %s)"
            for index, step in enumerate(recipe_data["instructions"], start=1):
                await cur.execute(add_instruction, (recipe_id, index, step))

            await conn.commit()
            save_result = 'success'
        return save_result, recipe_id
            
async def favorite_recipe(pool, userID, recipe_id):
    print("called favorite_recipe")
    current_time = datetime.datetime.now().isoformat()
    save_result = None
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            sql = '''INSERT INTO favorite_recipes (userID, recipe_id, saved_time)
                     VALUES(%s, %s, %s)'''
            await cur.execute(sql, (userID, recipe_id, current_time))
            await conn.commit()
            save_result = 'success'
            return save_result
        
async def un_favorite_recipe(pool, userID, recipe_id):
    print("hit the pool")
    current_time = datetime.datetime.now().isoformat()
    save_result = None
    async with pool.acquire() as conn:
   
        async with conn.cursor() as cur:
            sql = '''INSERT INTO favorite_recipes (userID, recipe_id, saved_time)
                     VALUES(%s, %s, %s)'''
            await cur.execute(sql, (userID, recipe_id, current_time))
            await conn.commit()
            return save_result
        

async def get_recipe_for_printing(pool, recipe_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Query the recipe details
            query_recipe = "SELECT title, servings, prep_time, cook_time, total_time FROM recipes WHERE recipe_id = %s"
            await cur.execute(query_recipe, (recipe_id,))
            recipe_details = await cur.fetchone()

            # Query the ingredients
            query_ingredients = "SELECT item, category FROM ingredients WHERE recipe_id = %s"
            await cur.execute(query_ingredients, (recipe_id,))
            ingredients = await cur.fetchall()

            # Query the instructions
            query_instructions = "SELECT step_number, description FROM instructions WHERE recipe_id = %s ORDER BY step_number"
            await cur.execute(query_instructions, (recipe_id,))
            instructions = await cur.fetchall()

    # Format the data into a printer-friendly format
    formatted_recipe = format_recipe_for_printing(recipe_details, ingredients, instructions)
    return formatted_recipe

def format_recipe_for_printing(details, ingredients, instructions):
    # Start with the HTML structure for the recipe
    formatted_html = f"<h1>{details['title']}</h1>"
    formatted_html += f"<p><strong>Servings:</strong> {details['servings']}</p>"
    formatted_html += f"<p><strong>Prep Time:</strong> {details['prep_time']}</p>"
    formatted_html += f"<p><strong>Cook Time:</strong> {details['cook_time']}</p>"
    formatted_html += f"<p><strong>Total Time:</strong> {details['total_time']}</p>"

   # Add ingredients in an HTML list
    formatted_html += "<h2>Ingredients</h2><ul>"
    for ingredient in ingredients:
        if ingredient['category'] is not None:
            formatted_html += f"<li>{ingredient['item']} ({ingredient['category']})</li>"
        else:
            formatted_html += f"<li>{ingredient['item']}</li>"
    formatted_html += "</ul>"

    # Add instructions in an ordered list
    formatted_html += "<h2>Instructions</h2><ol>"
    for step in instructions:
        formatted_html += f"<li>{step['description']}</li>"
    formatted_html += "</ol>"

    return formatted_html


