import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Read the API key from the environment — never hardcode it.
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise SystemExit("Set the GROQ_API_KEY environment variable first.")

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
   messages=[
    {"role": "user", "content": "What's 17% of 340? Think step by step before answering."}
]
) 

print(response.choices[0].message.content)
