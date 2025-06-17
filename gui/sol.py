import os
import solara
import solara.lab
import asyncio
from typing import cast
from typing import List
from copy import deepcopy
from openai import OpenAI
from functools import partial
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionMessageParam
from typing_extensions import TypedDict

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from azure.identity import get_bearer_token_provider

load_dotenv('.env.dev', override=True)

class MessageDict(TypedDict):
    role: str  # "user" or "assistant"
    content: str
    is_contains_sql: bool
    is_end_of_stream: bool

with open("db/prompt/system.txt", "r") as file:
    SYSTEM_PROMPT = file.read()

with open("db/prompt/sqlcheck.txt", "r") as file:
    SQL_CHECK_PROMPT = file.read()

messages: solara.Reactive[List[MessageDict]] = solara.reactive([
    {"role": "system", "content": SYSTEM_PROMPT}
])

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), 
    "https://cognitiveservices.azure.com/.default"
)

AZURE_OPENAI_MODEL_DEPLOYMENT = os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT")

openai_client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_ad_token_provider=token_provider
)

def store_feedback(reaction, user_input, chatbot_answer):
    print(reaction, user_input, chatbot_answer)


def contains_sql(text):
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

def create_system_message():
    return {
        "role": "assistant", 
        "content": "", 
        "is_end_of_stream": False, 
        "is_contains_sql": False
    }

def run_query(text):
    pass

@solara.lab.task
async def promt_ai(message: str):
    messages.value = [
        *messages.value,
        {"role": "user", "content": message},
    ]
    
    # Create system prompt message
    CONTEXT_LENGTH = 3
    
    if len(messages.value) <= CONTEXT_LENGTH:
        turn_messages = messages.value
    else:
        turn_messages = deepcopy([messages.value[0], *messages.value[-(CONTEXT_LENGTH-1):]])
    
    response = openai_client.chat.completions.create(
        messages=turn_messages,
        max_tokens=256,
        temperature=0.75,
        top_p=1.0,
        model=AZURE_OPENAI_MODEL_DEPLOYMENT,
        stream=True,
        stop=[";"],
    )

    messages.value = [*messages.value, create_system_message()]

    for chunk in response:
        if (not chunk.choices) or (len(chunk.choices) == 0):
            continue
        
        if chunk.choices[0].finish_reason == "stop":
            messages.value[-1]['is_end_of_stream'] = True
            break

        # replace the last message element with the appended content
        delta = chunk.choices[0].delta.content
        assert delta is not None
        
        updated_message: MessageDict = {
            "role": "assistant",
            "content": messages.value[-1]["content"] + delta,
        }
        # replace the last message element with the appended content which will update the UI
        messages.value = [*messages.value[:-1], updated_message]
    
    if contains_sql(messages.value[-1].get('content', '')) == True:
        messages.value[-1]['is_contains_sql'] = True
    
    return


@solara.component
def Page():
    with solara.Column(
        style={
            "width": "100%",
            "height": "95%",
            "border": "1px solid #e0e0e0",           
            "borderRadius": "12px",                   
            "boxShadow": "0 4px 16px rgba(0,0,0,0.07)", 
            "padding": "24px",               
            "backgroundColor": "#fff",                
        }
    ):
        with solara.lab.ChatBox():
            for i, item in enumerate(messages.value):
                if (item["role"] == "system"):
                    continue

                with solara.lab.ChatMessage(
                    user=item["role"] == "user",
                    avatar=False,
                    name="ChatBot" if item["role"] == "assistant" else "User",
                    color="#e9e9e9" if item["role"] == "assistant" else "#abe0f7",
                    avatar_background_color="primary" if item["role"] == "assistant" else None,
                    border_radius="20px",
                ):
                    solara.Markdown(item["content"])
                
                    if (item["role"] == "assistant"):
                        # Get the previous (user) message index for using it in feedback
                        user_message_idx = i - 1
                        user_message = messages.value[user_message_idx] if user_message_idx >= 0 else None 

                        with solara.Row(
                            style={"backgroundColor": "#e9e9e9"}
                        ): 
                            if item.get('is_end_of_stream', False):
                                solara.Button(
                                    label="like", 
                                    icon_name="mdi-thumb-up",
                                    outlined=True,
                                    color="primary",
                                    on_click=partial(store_feedback, "like", user_message, item),
                                )
                                solara.Button(
                                    label="dislike", 
                                    outlined=True, 
                                    color="primary",
                                    icon_name="mdi-thumb-down",
                                    on_click=partial(store_feedback, "dislike", user_message, item),
                                )

                            if item.get('is_contains_sql', False):
                                solara.Button(
                                    label="run query", 
                                    outlined=True,
                                    color="primary", 
                                    icon_name="mdi-play",
                                    on_click=partial(run_query, item.get('content', ''))
                                ) 
        
        # Show progress bar while generation an answer
        if promt_ai.pending:
            solara.Text("...", style={"font-size": "1rem", "padding-left": "20px"})
            solara.ProgressLinear()
        
        # if we don't call .key(..) with a unique key, the ChatInput component will 
        # be re-created and we'll lose what we typed.
        solara.lab.ChatInput(
            send_callback=promt_ai, 
            disabled=promt_ai.pending, 
            disabled_input=promt_ai.pending, 
            disabled_send=promt_ai.pending, 
            autofocus=True
        ).key("input")
