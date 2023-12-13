#process_handler.py
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
import httpx
import os
import base64
import hashlib
import aiomysql
import asyncio
from config import Config  # Import the Config class from your config module
import jwt 
import json
import pymysql
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from jwt.algorithms import RSAAlgorithm
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from fastapi.responses import JSONResponse

app = FastAPI()

# Define session middleware
app.add_middleware(SessionMiddleware, secret_key=Config.SESSION_SECRET_KEY)



@app.on_event("startup")
async def startup():
    app.state.db_pool = await create_pool()

async def generate_code_verifier_and_challenge():
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8').replace('=', '').replace('+', '-').replace('/', '_')
    return code_verifier, code_challenge


async def generate_code_verifier_and_challenge():
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8').replace('=', '').replace('+', '-').replace('/', '_')
    return code_verifier, code_challenge

################################################################## 
######!!!!       Routes                !!!!!######################
##################################################################

################################################################## 
######!!!!     Start login endpoint    !!!!!######################
##################################################################

@app.get("/login")
async def login(request: Request):
    print("start of login")

    # Getting the client's IP address
    client_ip = request.client.host
    print(f"Client IP: {client_ip}")
    
    #get code_verifier and code_challenge
    code_verifier, code_challenge = await generate_code_verifier_and_challenge()
    print("code_verifier: ", code_verifier)
    print("code_challenge: ", code_challenge)

    # generate a state code to link things later
    state = os.urandom(24).hex()  # Generate a random state value
    print("state: ", state)
    
    await save_code_verifier(state, code_verifier, client_ip)  # Corrected function name

    cognito_login_url = (
        f"{Config.COGNITO_DOMAIN}/login?response_type=code&client_id={Config.COGNITO_APP_CLIENT_ID}"
        f"&redirect_uri={Config.REDIRECT_URI}&state={state}&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )
    print("redirecting out of login")
    return RedirectResponse(cognito_login_url)

################################################################## 
######!!!!     End login endpoint      !!!!!######################
##################################################################

################################################################## 
######!!!!     Start callback  endpoint!!!!!######################
##################################################################

@app.get("/callback")

async def callback(request: Request, code: str, state: str):
    print("start of callback")
     # Extract query parameters
    query_params = request.query_params
    code = query_params.get('code')
    state = query_params.get('state')
    print("code: ", code)
    print("state: ", state)
    
    if not code:
        raise HTTPException(status_code=400, detail="Code parameter is missing")

    # Retrieve the code_verifier using the state
    code_verifier = await get_code_verifier(state)
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Invalid state or code_verifier missing")

    
    tokens = await exchange_code_for_token(code, code_verifier)
    if tokens:
        id_token = tokens['id_token']
        decoded_token = await validate_token(id_token)

        # Retrieve session data
        session = request.session

        # Store user information in session
        session['email'] = decoded_token.get('email', 'unknown')
        session['username'] = decoded_token.get('cognito:username', 'unknown')
        session['name'] = decoded_token.get('name', 'unknown')
        session['session_id'] = state
        print("session: ", session)
        
        


        

        # Save user information to MySQL
        mysql_connection = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            db=Config.DB_NAME,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )

        with mysql_connection.cursor() as cursor:
            # Create a SQL statement to insert user information into the MySQL table
            sql = "INSERT INTO login (username, email, name, session_id) VALUES (%s, %s, %s, %s)"
            values = (session['username'], session['email'], session['name'], session['session_id'])
            cursor.execute(sql, values)
            print("User information saved to MySQL")

        # Close the MySQL connection
        mysql_connection.close()

           # Prepare the URL with query parameters
        chat_html_url = '/chat.html'  # Replace with the actual URL of your chat.html
        redirect_url = f"{chat_html_url}?sessionId={session['session_id']}"

        # Redirect the user to the chatbot interface with query parameters
        return RedirectResponse(url=redirect_url, status_code=302)
    else:
        return 'Error during token exchange.', 400
    

##################################################################
######!!!!     End callback endpoint   !!!!!######################
##################################################################


##################################################################
######!!!!     start get ssession endpoint!!######################
##################################################################

@app.get("/get_session_data")
async def get_session_data(request: Request):
    print("at /get_session_data")
    # Retrieve session data
    session_id = request.session.get('session_id')
    nonce = request.session.get('nonce')
    user_info = request.session.get('user_info')  # Adjust as per your actual session keys

    # If session_id is not available, return an error
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID not found in session data")

    print("user info from get session data", user_info)

    # Retrieve additional data from the database using the session_id
    db_data = await get_data_from_db(session_id, app.state.db_pool)

    # You can merge the user_info with db_data if needed
    # user_info.update(db_data)  # Uncomment this line if you want to merge

    # Return the combined data
    return JSONResponse(content={
        "sessionId": session_id,
        "nonce": nonce,
        "userInfo": user_info  # or db_data if you have merged them
    })


##################################################################
######!!!!     end get ssession endpoint  !!######################
##################################################################



##################################################################
######!!!!     Start Functions           !!!!!####################
##################################################################

# Save the code_verifier and state in the database
async def save_code_verifier(state: str, code_verifier: str, client_ip: str):
    async with app.state.db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("INSERT INTO verifier_store (state, code_verifier, client_ip) VALUES (%s, %s, %s)", (state, code_verifier, client_ip))


# Retrieve the code_verifier using the state
async def get_code_verifier(state: str) -> str:
    async with app.state.db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT code_verifier FROM verifier_store WHERE state = %s", (state,))
            result = await cur.fetchone()
            return result['code_verifier'] if result else None

# exhange code for token
async def exchange_code_for_token(code, code_verifier):
    token_url = f"{Config.COGNITO_DOMAIN}/oauth2/token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'authorization_code',
        'client_id': Config.COGNITO_APP_CLIENT_ID,
        'code': code,
        'redirect_uri': Config.REDIRECT_URI,
        'code_verifier': code_verifier
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        print("response.json()", response.json())  
        return response.json()
        
    else:
        return None

# Initialize the connection pool
async def create_pool():
    return await aiomysql.create_pool(
        host=Config.DB_HOST, port=Config.DB_PORT,
        user=Config.DB_USER, password=Config.DB_PASSWORD,
        db=Config.DB_NAME, charset='utf8', 
        cursorclass=aiomysql.DictCursor, autocommit=True
    )
# validate token
async def validate_token(id_token):
    COGNITO_USER_POOL_ID = Config.COGNITO_USER_POOL_ID
    COGNITO_APP_CLIENT_ID = Config.COGNITO_APP_CLIENT_ID
    jwks_url = f"https://cognito-idp.us-east-1.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    #jwks_response = requests.get(jwks_url)
    with httpx.Client() as client:
        jwks_response = client.get(jwks_url)
    jwks = jwks_response.json()

    headers = jwt.get_unverified_header(id_token)
    kid = headers['kid']
    key = [k for k in jwks['keys'] if k['kid'] == kid][0]
    pem = RSAAlgorithm.from_jwk(json.dumps(key))

    decoded_token = jwt.decode(
        id_token,
        pem,
        algorithms=['RS256'],
        audience=COGNITO_APP_CLIENT_ID
    )
    return decoded_token

######   Sessions

def get_session(request: Request):
    return request.session

##################################################################



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
