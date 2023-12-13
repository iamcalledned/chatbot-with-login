#database.py
import sys
import os
# Get the directory of the current script
current_script_path = os.path.dirname(os.path.abspath(__file__))
# Set the path to the parent directory (one folder up)
parent_directory = os.path.dirname(current_script_path)
# Add the config directory to sys.path
sys.path.append(os.path.join(parent_directory, 'config'))
sys.path.append(os.path.join(parent_directory, 'bot'))
import sqlite3
from sqlite3 import Error
import datetime
from config import Config


# Define the DB_PATH directly here or use a separate configuration file
DB_PATH = Config.DB_PATH

def create_connection(db_file=DB_PATH):
    print("db path", DB_PATH, db_file)
    try:
        conn = sqlite3.connect(db_file)
        #print('Connection to db successful!!')
    except Error as e:
        print(e)
        return None
    return conn


def create_tables(conn):
    """ Create tables """
    create_users_table = """CREATE TABLE IF NOT EXISTS users (
                                UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                                Username TEXT UNIQUE NOT NULL
                            );"""

    create_threads_table = """CREATE TABLE IF NOT EXISTS threads (
                                  ThreadID TEXT PRIMARY KEY,
                                  UserID INTEGER NOT NULL,
                                  IsActive BOOLEAN NOT NULL,
                                  CreatedTime TEXT NOT NULL,
                                  FOREIGN KEY (UserID) REFERENCES users (UserID)
                              );"""
    create_converations_table = """CREATE TABLE IF NOT EXISTS conversations (
                                   ConversationID INTEGER PRIMARY KEY AUTOINCREMENT,    
                                   UserID INTEGER NOT NULL,
                                   ThreadID TEXT NOT NULL,
                                   RunID TEXT NOT NULL,  -- New column for RunID
                                   Message TEXT NOT NULL,
                                   Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                   MessageType TEXT NOT NULL,
                                   IPAddress TEXT,
                                   Status TEXT DEFAULT 'active',
                                   FOREIGN KEY (UserID) REFERENCES users (UserID),
                                   FOREIGN KEY (ThreadID) REFERENCES threads (ThreadID)
                                );"""

    try:
        c = conn.cursor()
        c.execute(create_users_table)
        c.execute(create_threads_table)
        c.execute(create_converations_table)
    except Error as e:
        print(e)

def insert_user(conn, username):
    """Insert a new user into the users table or return existing user ID"""
    # Check if user already exists
    sql_check = '''SELECT UserID FROM users WHERE Username = ?'''
    cur = conn.cursor()
    cur.execute(sql_check, (username,))
    existing_user = cur.fetchone()

    if existing_user:
        print("Existing user", existing_user)
        return existing_user[0]  # Return the existing user's ID

    # Insert new user if not existing
    sql_insert = '''INSERT INTO users(Username) VALUES(?)'''
    cur.execute(sql_insert, (username,))
    conn.commit()
    userID=cur.lastrowid # return the userID
    return userID  # Return the new user's ID



def insert_thread(conn, thread_id, user_id, is_active, created_time):
    """ Insert a new thread into the threads table """
    sql = '''INSERT INTO threads(ThreadID, UserID, IsActive, CreatedTime)
             VALUES(?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, (thread_id, user_id, is_active, created_time))
    conn.commit()
    print("inserted tread:")

def get_active_thread_for_user(conn, user_id):
    print("looking for active thread for user:",user_id)
    """ Fetch the active thread for a given user """
    sql = '''SELECT ThreadID FROM threads 
             WHERE UserID = ? '''
    cur = conn.cursor()
    cur.execute(sql, (user_id,))
    return cur.fetchone()

def deactivate_thread(conn, thread_id):
    """ Mark a thread as inactive """
    sql = '''UPDATE threads SET IsActive = 0 WHERE ThreadID = ?'''
    cur = conn.cursor()
    cur.execute(sql, (thread_id,))
    conn.commit()

def insert_conversation(conn, user_id, thread_id, run_id, message, message_type, ip_address):
    """ Insert a new conversation record into the conversations table """
    sql = '''INSERT INTO conversations(UserID, ThreadID, RunID, Message, MessageType, IPAddress)
             VALUES(?,?,?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, (user_id, thread_id, run_id, message, message_type, ip_address))
    conn.commit()

def get_conversations_by_run(conn, run_id):
    """ Fetch all conversations for a given RunID """
    sql = '''SELECT * FROM conversations WHERE RunID = ?'''
    cur = conn.cursor()
    cur.execute(sql, (run_id,))
    return cur.fetchall()

def update_conversation_status(conn, conversation_id, new_status):
    """ Update the status of a conversation """
    sql = '''UPDATE conversations SET Status = ? WHERE ConversationID = ?'''
    cur = conn.cursor()
    cur.execute(sql, (new_status, conversation_id))
    conn.commit()

def start_new_run(conn, user_id, thread_id):
    """ Start a new run and return its RunID """
    # Generate a new RunID, e.g., using uuid
    run_id = str(uuid.uuid4())
    current_time = datetime.datetime.now().isoformat()
    # Insert a record to signify the start of a new run (optional)
    insert_thread(conn, thread_id, user_id, True, current_time, run_id)
    return run_id

def end_run(conn, run_id):
    """ Mark a run as completed """
    # Logic to mark a run as completed, e.g., updating a runs table or updating conversation statuses
    pass


