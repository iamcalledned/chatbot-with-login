import os
from dotenv import load_dotenv

# Specify the path to your .env file
dotenv_path = '/home/ubuntu/chatbot-with-login/.evn/.env'

# Load environment variables from the specified .env file
load_dotenv(dotenv_path)

class Config:
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
    COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
    COGNITO_APP_CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID')
    COGNITO_DOMAIN = os.getenv('COGNITO_DOMAIN')
    REDIRECT_URI = os.getenv('REDIRECT_URI')
    ANOTHER_APP_URI = os.getenv('ANOTHER_APP_URI')
    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = os.getenv('REDIS_PORT')
    ASSISTANT_ID = os.getenv('ASSISTANT_ID')
    DB_PATH = os.getenv('DB_PATH')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    LOG_PATH = os.getenv('LOG_PATH')