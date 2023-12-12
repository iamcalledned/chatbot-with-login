from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
import httpx
import os
import base64
import hashlib
import config  # Your AWS Cognito and other configuration settings

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

    cognito_login_url = (
        f"{config.COGNITO_DOMAIN}/login?response_type=code&client_id={config.COGNITO_APP_CLIENT_ID}"
        f"&redirect_uri={config.REDIRECT_URI}&state={state}&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )
    return RedirectResponse(cognito_login_url)

@app.get("/callback")
async def callback(code: str, state: str):
    if not code:
        raise HTTPException(status_code=400, detail="Code parameter is missing")

    # Exchange code for token
    tokens = await exchange_code_for_token(code, session.get('code_verifier'))
    if tokens:
        # Process tokens (e.g., store them in session or database)
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=400, detail="Error exchanging code for tokens")

async def exchange_code_for_token(code, code_verifier):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            # Your existing token exchange logic here
        )
    if response.status_code == 200:
        return response.json()
    else:
        # Handle error
        return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
