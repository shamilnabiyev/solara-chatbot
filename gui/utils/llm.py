import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from azure.identity import get_bearer_token_provider

load_dotenv('.env.dev', override=True)

AZURE_OPENAI_MODEL_DEPLOYMENT = os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT")

with open("db/prompt/system.txt", "r") as file:
    SYSTEM_PROMPT = file.read()

with open("db/prompt/sqlcheck.txt", "r") as file:
    SQL_CHECK_PROMPT = file.read()

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), 
    "https://cognitiveservices.azure.com/.default"
)

openai_client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_ad_token_provider=token_provider
)


def find_sql(text):
    turn_message = [
        {"role": "system", "content": SQL_CHECK_PROMPT},
        {"role": "user", "content": f"<input>{text}</input>"},
    ]

    response = openai_client.chat.completions.create(
        messages=turn_message,
        max_tokens=2,
        temperature=0.0,
        top_p=1.0,
        model=AZURE_OPENAI_MODEL_DEPLOYMENT,
        stream=False,
        stop=["\n"],
    )
    result = response.choices[0].message.content.strip().lower()
    return result == "true"


def generate_sql(messages):
    return openai_client.chat.completions.create(
        messages=messages,
        max_tokens=256,
        temperature=0.75,
        top_p=1.0,
        model=AZURE_OPENAI_MODEL_DEPLOYMENT,
        stream=True,
    )

def init_messages():
    return {"role": "system", "content": SYSTEM_PROMPT}
