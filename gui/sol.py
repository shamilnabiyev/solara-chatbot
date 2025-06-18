import solara
import solara.lab
from typing import List
from copy import deepcopy
from functools import partial
from typing_extensions import TypedDict
from utils.vanna_client import vn
from utils.llm import (
    find_sql, 
    generate_sql, 
    init_messages
)

COLUMN_STYLE = {
    "width": "100%",
    "height": "95%",
    "border": "1px solid #e0e0e0",           
    "borderRadius": "12px",                   
    "boxShadow": "0 4px 16px rgba(0,0,0,0.07)", 
    "padding": "24px",               
    "backgroundColor": "#fff",                
}

class MessageDict(TypedDict):
    role: str  # "user" or "assistant"
    content: str
    is_sql_statement: bool
    is_end_of_stream: bool


messages: solara.Reactive[List[MessageDict]] = solara.reactive([
    init_messages()
])


def store_feedback(reaction, user_input, chatbot_answer):
    print(reaction, user_input, chatbot_answer)


def create_system_message(content=""):
    return {
        "role": "assistant", 
        "content": content, 
        "is_end_of_stream": False, 
        "is_sql_statement": False
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
    
    response = generate_sql(turn_messages)

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
    
    if find_sql(messages.value[-1].get('content', '')) == True:
        messages.value[-1]['is_sql_statement'] = True
    
    return

@solara.lab.task
async def prompt_vanna(message: str):
    messages.value = [
        *messages.value,
        {"role": "user", "content": message},
    ]

    sql_query, sql_query_result, sql_query_plot = vn.ask(
        question=message,
        visualize=False,
        print_results=False
    )

    if sql_query_result is None:
        result_message = sql_query
    else:
        result_message = f"""```sql\n 
        {sql_query} ```
        """

    messages.value = [*messages.value, create_system_message(result_message)]
    messages.value[-1]['is_end_of_stream'] = True

    if find_sql(result_message) == True:
        messages.value[-1]['is_sql_statement'] = True

    return

@solara.component
def Page():
    with solara.Column(
        style=COLUMN_STYLE
    ):
        solara.Title("Solara SQL Chatbot")
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
                                    label="", 
                                    icon_name="mdi-thumb-up",
                                    outlined=True,
                                    color="primary",
                                    on_click=partial(store_feedback, "like", user_message, item),
                                )
                                solara.Button(
                                    label="", 
                                    outlined=True, 
                                    color="primary",
                                    icon_name="mdi-thumb-down",
                                    on_click=partial(store_feedback, "dislike", user_message, item),
                                )

                            if item.get('is_sql_statement', False):
                                solara.Button(
                                    label="run query", 
                                    outlined=True,
                                    color="primary", 
                                    icon_name="mdi-play",
                                    on_click=partial(run_query, item.get('content', ''))
                                ) 
        
        # Show progress bar while generation an answer
        if prompt_vanna.pending:
            solara.Text("...", style={"font-size": "1rem", "padding-left": "20px"})
            solara.ProgressLinear()
        
        # if we don't call .key(..) with a unique key, the ChatInput component will 
        # be re-created and we'll lose what we typed.
        solara.lab.ChatInput(
            send_callback=prompt_vanna, 
            disabled=prompt_vanna.pending, 
            disabled_input=prompt_vanna.pending, 
            disabled_send=prompt_vanna.pending, 
            autofocus=True
        ).key("input")
