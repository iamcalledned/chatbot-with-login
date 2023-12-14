#process_handler_database.py
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


# Save the code_verifier and state in the database
async def save_code_verifier(pool, state: str, code_verifier: str, client_ip: str, login_timestamp ):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("INSERT INTO verifier_store (state, code_verifier, client_ip, login_timestamp) VALUES (%s, %s, %s, %s)", (state, code_verifier, client_ip, login_timestamp))

# Retrieve the code_verifier using the state
async def get_code_verifier(pool, state: str) -> str:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT code_verifier FROM verifier_store WHERE state = %s", (state,))
            result = await cur.fetchone()
            return result['code_verifier'] if result else None

#gnerate code and challenge code
async def generate_code_verifier_and_challenge():
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8').replace('=', '').replace('+', '-').replace('/', '_')
    return code_verifier, code_challenge


#get all data from DB
async def get_data_from_db(session_id, pool):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM login WHERE session_id = %s", (session_id,))
            result = await cur.fetchone()
            return result if result else {}



async def get_user_info_by_session_id(session_id, pool):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM login WHERE session_id = %s", (session_id,))
            result = await cur.fetchone()
            return result


async def save_user_info_to_mysql(pool, session, client_ip, state):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            sql = "INSERT INTO login (username, email, name, session_id, ip_address, state) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (session['username'], session['email'], session['name'], session['session_id'], client_ip, state)
            await cursor.execute(sql, values)
            
            await conn.commit()
            print("User information saved to login table")

async def save_user_info_to_userdata(pool, session, client_ip, state):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            sql_check = "SELECT username FROM user_data WHERE username = %s"
            await cursor.execute(sql_check, (session['username']))
            username = await cursor.fetchone()
            
            if username:
            # If the user exists, update the last_login_date
                sql_update = "UPDATE user_data SET last_login_date = NOW() WHERE username = %s"
                print("updating username")
                await cursor.execute(sql_update, (username['username'],))
            else:
                
                
                sql = "INSERT INTO user_data (username, email, name, setup_date, last_login_date) VALUES (%s, %s, %s, NOW(), NOW())"
                values = (session['username'], session['email'], session['name'],)
                print("inserted new user")
                await cursor.execute(sql, values)
            await conn.commit()
            print("User information saved to MySQL")

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

            create_user_table = """CREATE TABLE IF NOT EXISTS user_data (
                                user_id INT AUTO_INCREMENT PRIMARY KEY,
                                username VARCHAR(255) UNIQUE NOT NULL,
                                email VARCHAR(255),
                                name VARCHAR(255),
                                setup_date DATETIME,
                                last_login_date DATETIME
                                );"""
            
            await cur.execute(create_users_table)
            await cur.execute(create_threads_table)
            await cur.execute(create_conversations_table)
            await cur.execute(create_user_table)

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

