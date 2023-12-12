from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import httpx
import os
import base64
import hashlib
from config import Config  # Import the Config class from your config module

app = FastAPI()

async def generate_code_verifier_and_challenge():
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8').replace('=', '').replace('+', '-').replace('/', '_')
    return code_verifier, code_challenge

@app.get("/login")
async def login():
    code_verifier, code_challenge = await generate_code_verifier_and_challenge()
    state = os.urandom(24).hex()  # Generate a random state value

    # TODO: Securely store the code_verifier indexed by the state
    # e.g., save_to_secure_storage(state, code_verifier)

    cognito_login_url = (
        f"{Config.COGNITO_DOMAIN}/login?response_type=code&client_id={Config.COGNITO_APP_CLIENT_ID}"
        f"&redirect_uri={Config.REDIRECT_URI}&state={state}&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )
    return RedirectResponse(cognito_login_url)

@app.get("/callback")
async def callback(code: str, state: str):
    if not code:
        raise HTTPException(status_code=400, detail="Code parameter is missing")

    # TODO: Retrieve the code_verifier using the state
    # e.g., code_verifier = retrieve_from_secure_storage(state)

    tokens = await exchange_code_for_token(code, code_verifier)
    if tokens:
        # Process tokens (e.g., store them in session or database)
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=400, detail="Error exchanging code for tokens")

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
        return response.json()
    else:
        return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
