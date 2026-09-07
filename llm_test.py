# Testing model response from vLLM using the OpenAI API client library

# Remeber to set the OPENAI_API_KEY and LLM_API_ENDPOINT in your .env file before running this test.

# Also connect to university VPN if you are off-campus, as the LLM API endpoint is only accessible from the university network.
# Take a look at https://ask.otago.ac.nz/knowledgebase/article/KA-10004411 

import os
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv(".env")

LLM_API_ENDPOINT = os.getenv("LLM_API_ENDPOINT")
print(f"LLM API Endpoint: {LLM_API_ENDPOINT}")

# OpenAI automatically uses the OPENAI_API_KEY from the environment variable, so we don't need to pass it explicitly here.
client = OpenAI(
    base_url=LLM_API_ENDPOINT
)

print("\nSending a test message to vLLM...")

try:
    # 2. Send a basic prompt (Remembering to control max_tokens on the client side)
    response = client.chat.completions.create(
        model="ONCAMPUS/gemma-4-12B-it", 
        messages=[
            {"role": "system", "content": "You are a helpful and concise AI assistant."},
            {"role": "user", "content": "Say hello!"}
        ],
        max_tokens=50,       # Small token limit just for a fast test response
        temperature=0.2     # Adjust the randomness of the response
    )
    
    # 3. Print the output
    print("\n Success! The model responded:")
    print(response.choices[0].message.content)

except Exception as e:
    print(f"\n Connection Failed: {e}")


