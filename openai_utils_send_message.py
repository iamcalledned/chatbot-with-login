# openai_utils_send_message.py
from openai import AsyncOpenAI
import sys
import os
import markdown2  # pip install markdown2
from config import Config

# Fix Python pathing
current_script_path = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.dirname(current_script_path)
sys.path.append(os.path.join(parent_directory, 'database'))
sys.path.append(os.path.join(parent_directory, 'config'))

# Async OpenAI client
openai_client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

# Send message to thread
async def send_message(thread_id_n, message):
    try:
        response = await openai_client.beta.threads.messages.create(    
            thread_id=thread_id_n,
            role="user",
            content=message
        )
        
        # Extract raw text
        raw_text = response.content[0].text.value
        
        # Convert markdown (if any) to HTML
        html = markdown2.markdown(raw_text)

        # Wrap it in Tailwind/DaisyUI styling (optional)
        styled_html = f'<div class="prose prose-sm max-w-none">{html}</div>'

        return styled_html
    except Exception as e:
        print(f"Error in sending message: {e}")
        return '<p class="text-error">Error in sending message.</p>'
