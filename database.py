import os
import asyncio
import aiomysql
import datetime
import uuid
from config import Config
import pymysql

# Define the DB_CONFIG directly here or use a separate configuration file
DB_CONFIG = {
    "host": Config.DB_HOST,
    "port": Config.DB_PORT,
    "user": Config.DB_USER,
    "password": Config.DB_PASSWORD,
    "db": Config.DB_NAME,
}

conn = None

async def create_pool():
    print("hit create pool in database.py")
    return await aiomysql.create_pool(**DB_CONFIG)
    

async def create_connection():
    try:
        # Create a MySQL connection using the configuration from your Config class
        connection = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            db=Config.DB_NAME,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        return connection
    except Exception as e:
        print("Error creating MySQL connection:", str(e))
        return None



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

async def insert_user(pool, username):
    """Insert a new user into the users table or return existing user ID"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Check if user already exists
            sql_check = '''SELECT UserID FROM users WHERE Username = %s'''
            await cur.execute(sql_check, (username,))
            existing_user = await cur.fetchone()

            if existing_user:
                return existing_user[0]  # Return the existing user's ID

            # Insert new user if not existing
            sql_insert = '''INSERT INTO users(Username) VALUES(%s)'''
            await cur.execute(sql_insert, (username,))
            await conn.commit()
            return cur.lastrowid  # Return the new user's ID

async def insert_thread(pool, thread_id, user_id, is_active, created_time):
    """Insert a new thread into the threads table"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            sql = '''INSERT INTO threads(ThreadID, UserID, IsActive, CreatedTime)
                     VALUES(%s, %s, %s, %s)'''
            await cur.execute(sql, (thread_id, user_id, is_active, created_time))
            await conn.commit()

async def get_active_thread_for_user(pool, user_id):
    """Fetch the active thread for a given user"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            sql = '''SELECT ThreadID FROM threads WHERE UserID = %s'''
            await cur.execute(sql, (user_id,))
            return await cur.fetchone()

async def deactivate_thread(pool, thread_id):
    """Mark a thread as inactive"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            sql = '''UPDATE threads SET IsActive = 0 WHERE ThreadID = %s'''
            await cur.execute(sql, (thread_id,))
            await conn.commit()

async def insert_conversation(pool, user_id, thread_id, run_id, message, message_type, ip_address):
    """Insert a new conversation record into the conversations table"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            sql = '''INSERT INTO conversations(UserID, ThreadID, RunID, Message, MessageType, IPAddress)
                     VALUES(%s, %s, %s, %s, %s, %s)'''
            await cur.execute(sql, (user_id, thread_id, run_id, message, message_type, ip_address))
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

async def start_new_run(pool, user_id, thread_id):
    """Start a new run and return its RunID"""
    run_id = str(uuid.uuid4())
    current_time = datetime.datetime.now().isoformat()
    await insert_thread(pool, thread_id, user_id, True, current_time)
    return run_id

async def end_run(pool, run_id):
    """Mark a run as completed"""
    # Logic to mark a run as completed, e.g., updating a runs table or updating conversation statuses
    pass
