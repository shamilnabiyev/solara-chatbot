import solara
import solara.lab

from typing import cast
from typing import List
from openai import OpenAI
from functools import partial
from openai.types.chat import ChatCompletionMessageParam
from typing_extensions import TypedDict



class MessageDict(TypedDict):
    role: str  # "user" or "assistant"
    content: str


messages: solara.Reactive[List[MessageDict]] = solara.reactive([])

ollama_client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama', # required, but unused
)

def store_feedback(reaction, user_input, chatbot_answer):
    print(reaction, user_input, chatbot_answer)

@solara.lab.task
async def promt_ai(message: str):
    messages.value = [
        *messages.value,
        {"role": "user", "content": message},
    ]
    # The part below can be replaced with a call to your own
    response = ollama_client.chat.completions.create(
        model="llama3.2:3b",
        # our MessageDict is compatible with the OpenAI types
        messages=cast(List[ChatCompletionMessageParam], messages.value),
        stream=True,
    )
    # start with an empty reply message, so we render and empty message in the chat
    # while the AI is thinking
    messages.value = [*messages.value, {"role": "assistant", "content": ""}]
    # and update it with the response
    for chunk in response:
        if chunk.choices[0].finish_reason == "stop":  # type: ignore
            return
        # replace the last message element with the appended content
        delta = chunk.choices[0].delta.content
        assert delta is not None
        updated_message: MessageDict = {
            "role": "assistant",
            "content": messages.value[-1]["content"] + delta,
        }
        # replace the last message element with the appended content
        # which will update the UI
        messages.value = [*messages.value[:-1], updated_message]


@solara.component
def Page():
    with solara.Column(
        style={
            "width": "100%",
            "height": "90%",
            "border": "1px solid #e0e0e0",           
            "borderRadius": "12px",                   
            "boxShadow": "0 4px 16px rgba(0,0,0,0.07)", 
            "padding": "24px",               
            "backgroundColor": "#fff",                
        }
    ):
        with solara.lab.ChatBox():
            for i, item in enumerate(messages.value):
                with solara.lab.ChatMessage(
                    user=item["role"] == "user",
                    avatar=False,
                    name="ChatBot" if item["role"] == "assistant" else "User",
                    color="rgba(0,0,0, 0.06)" if item["role"] == "assistant" else "#abe0f7",
                    avatar_background_color="primary" if item["role"] == "assistant" else None,
                    border_radius="20px",
                ):
                    solara.Markdown(item["content"])
                
                if (item["role"] == "assistant") and (not promt_ai.pending):
                    # Get the previous (user) message index
                    user_message_idx = i - 1
                    user_message = messages.value[user_message_idx] if user_message_idx >= 0 else None 
                    with solara.Row(): 
                        solara.Button(
                            label="like", 
                            icon_name="mdi-thumb-up",
                            on_click=partial(store_feedback, "like", user_message, item)
                        )
                        solara.Button(label="dislike", icon_name="mdi-thumb-down")
                        solara.Button(label="comment", icon_name="mdi-comment-text-outline")
                        # 

        if promt_ai.pending:
            solara.Text("...", style={"font-size": "1rem", "padding-left": "20px"})
            solara.ProgressLinear()
        # if we don't call .key(..) with a unique key, the ChatInput component will be re-created
        # and we'll lose what we typed.
        solara.lab.ChatInput(send_callback=promt_ai, disabled_send=promt_ai.pending, autofocus=True).key("input")
