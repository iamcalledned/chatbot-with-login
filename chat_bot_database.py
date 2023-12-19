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


        

async def create_tables(pool):
    """Create tables"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            create_users_table = """CREATE TABLE IF NOT EXISTS users (
                UserID INT AUTO_INCREMENT PRIMARY KEY,
                Username VARCHAR(255) UNIQUE NOT NULL
            );"""

            create_threads_table = """CREATE TABLE IF NOT EXISTS threads (
                ThreadID VARCHAR(36) PRIMARY KEY,
                UserID INT NOT NULL,
                IsActive BOOLEAN NOT NULL,
                CreatedTime DATETIME NOT NULL,
                FOREIGN KEY (UserID) REFERENCES users (UserID)
            );"""

            create_conversations_table = """CREATE TABLE IF NOT EXISTS conversations (
                ConversationID INT AUTO_INCREMENT PRIMARY KEY,
                UserID INT NOT NULL,
                ThreadID VARCHAR(36) NOT NULL,
                RunID VARCHAR(36) NOT NULL,
                Message TEXT NOT NULL,
                Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                MessageType VARCHAR(255) NOT NULL,
                IPAddress VARCHAR(255),
                Status VARCHAR(255) DEFAULT 'active',
                FOREIGN KEY (UserID) REFERENCES users (UserID),
                FOREIGN KEY (ThreadID) REFERENCES threads (ThreadID)
            );"""

            await cur.execute(create_users_table)
            await cur.execute(create_threads_table)
            await cur.execute(create_conversations_table)

#async def insert_user(pool, userID):
#    """Insert a new user into the users table or return existing user ID"""
#    async with pool.acquire() as conn:
#        async with conn.cursor() as cur:
#            # Check if user already exists
#            sql_check = '''SELECT UserID FROM users WHERE Username = %s'''
#            await cur.execute(sql_check, (userID,))
#            existing_user = await cur.fetchone()
#            #print("existing user", existing_user)###
#
#            if existing_user:
#                return existing_user['UserID']  # Return the existing user's ID#
#
#            # Insert new user if not existing
#            sql_insert = '''INSERT INTO users(Username) VALUES(%s)'''
#            await cur.execute(sql_insert, (get_user_info_by_session_id,))
#            await conn.commit()
#            return cur.lastrowid  # Return the new user's ID



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

async def insert_recipe(conn, recipe_data):
    try:
        print("recipe data", recipe_data)
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO Recipes (recipe_name, servings, prepTime, cookTime, totalTime) VALUES (%s, %s, %s, %s, %s)",
                (recipe_data["title"], recipe_data["servings"], recipe_data["prepTime"], recipe_data["cookTime"], recipe_data["totalTime"]))

            await cur.execute("SELECT LAST_INSERT_ID()")
            result = await cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"An error occurred in insert_recipe: {e}")

async def insert_part(conn, recipe_id, part_name):
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO Parts (recipe_id, part_name) VALUES (%s, %s)",
                (recipe_id, part_name))
            await cur.execute("SELECT LAST_INSERT_ID()")
            result = await cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"An error occurred at insert_part: {e}")

async def insert_ingredient(conn, ingredient_name):
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO Ingredients (name) VALUES (%s) ON DUPLICATE KEY UPDATE ingredient_id=LAST_INSERT_ID(ingredient_id)",
            (ingredient_name,))
        await cur.execute("SELECT LAST_INSERT_ID()")
        result = await cur.fetchone()
        return result[0]


async def link_part_ingredient(conn, part_id, ingredient_id, quantity):
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO RecipePartsIngredients (recipe_part_id, ingredient_id, quantity) VALUES (%s, %s, %s)",
            (part_id, ingredient_id, quantity))

async def insert_instruction(conn, part_id, step_number, instruction_text):
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO Instructions (part_id, step_number, instruction_text) VALUES (%s, %s, %s)",
            (part_id, step_number, instruction_text))


async def save_recipe_to_db(pool, recipe_data):
    # Insert the main recipe data
    async with pool.acquire() as conn:
        try:
            await conn.begin()  # Start a transaction
            recipe_id = await insert_recipe(conn, recipe_data)
            if not recipe_id:
                raise Exception("Failed to insert recipe.")

             # Iterate through each part and its details
            for part in recipe_data["parts"]:
                part_id = await insert_part(conn, recipe_id, part["part_name"])

            # Insert each ingredient and link it to the part
            for ingredient in part["ingredients"]:
                ingredient_id = await insert_ingredient(pool, ingredient)
                await link_part_ingredient(conn, part_id, ingredient_id, "some quantity")  # Define logic to extract quantity

            # Insert each instruction
            for step_number, instruction in enumerate(part["instructions"], start=1):
                await insert_instruction(conn, part_id, step_number, instruction)

            await conn.commit()
            return "success"
        except Exception as e:
            print(f"An error occurred: {e}")
            await conn.rollback()  # Rollback the transaction in case of error
            return "failure"

