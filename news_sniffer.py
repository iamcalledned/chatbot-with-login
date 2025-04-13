import openai
import os
from dotenv import load_dotenv

# Optional: use a .env file to store your key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def run_news_sniffer(query):
    print(f"🔍 Searching for: {query}\n")

    # Step 1: Run a live web search via OpenAI tool
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a web intelligence agent named NewsSniffer. "
                    "You search the internet for the latest news articles or headlines about a given query. "
                    "Return your results as a list of concise bullet points with title, source, summary, and link. "
                    "Focus on financial, economic, political, or macro events. Be concise and avoid fluff."
                )
            },
            {
                "role": "user",
                "content": f"Find the most relevant news headlines about: {query}"
            }
        ],
        tools=[{"type": "web_search"}],  # <-- this uses OpenAI's built-in web access
        tool_choice="auto",
    )

    reply = response.choices[0].message.content
    print("🧠 NewsSniffer Report:\n")
    print(reply)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python news_sniffer.py \"your search query here\"")
    else:
        query = " ".join(sys.argv[1:])
        run_news_sniffer(query)
