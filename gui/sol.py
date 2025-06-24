import solara
import solara.lab
import pandas as pd
from typing import List
from functools import partial
from typing_extensions import TypedDict
from utils.vanna_client import vn
from utils.llm import find_sql

class MessageDict(TypedDict):
    role: str  # "user" or "assistant"
    content: str
    dataframe: pd.DataFrame
    is_sql_statement: bool
    is_end_of_stream: bool


messages: solara.Reactive[List[MessageDict]] = solara.reactive([])


def store_feedback(reaction, user_input, chatbot_answer):
    """
    Store user feedback regarding the chatbot response.

    Parameters
    ----------
    reaction : str
        The user's reaction, e.g., 'like' or 'dislike'.
    user_input : str
        The message content provided by the user.
    chatbot_answer : MessageDict
        The chatbot's response message dictionary.
    """
    print(reaction, user_input, chatbot_answer)


def create_assistant_message(content="", dataframe=None):
    """
    Create a message dictionary representing the assistant's message.

    Parameters
    ----------
    content : str, optional
        The content of the assistant's message (default is "").
    dataframe : pd.DataFrame or None, optional
        An optional DataFrame included with the message (default is None).
    
    Returns
    -------
    dict
        A dictionary with keys:
        - "role": str, fixed as "assistant"
        - "content": str, the message content
        - "dataframe": pd.DataFrame or None, associated data
        - "is_end_of_stream": bool, False by default
        - "is_sql_statement": bool, False by default
    """
    return {
        "role": "assistant",
        "content": content,
        "dataframe": dataframe,
        "is_end_of_stream": False, 
        "is_sql_statement": False
    }


@solara.lab.task
async def prompt_vanna(message: str):
    """
    Process user message, generate SQL query and response, update message history.

    Parameters
    ----------
    message : str
        The user's input message to the chatbot.

    Returns
    -------
    None
    """
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
        dataframe = None
    else:
        result_message = (
            "```sql \n"
            f"{sql_query} "
            "\n"
            "```"
        )
        dataframe = sql_query_result

    messages.value = [
        *messages.value, 
        create_assistant_message(result_message, dataframe)
    ]

    messages.value[-1]['is_end_of_stream'] = True

    if find_sql(result_message) == True:
        messages.value[-1]['is_sql_statement'] = True

    return


def run_query(text):
    """
    Execute a SQL query generated from the user's message.

    Parameters
    ----------
    text : str
        The SQL query string to be executed.

    Returns
    -------
    None
    """
    pass


def render_buttons_row(item, user_message):
    """
    Render a row of feedback buttons based on the message item state.

    Parameters
    ----------
    item : dict
        The message dictionary containing response data.
    user_message : dict or None
        The user message dictionary preceding this response.
    """
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

        # if item.get('is_sql_statement', False):
        #     solara.Button(
        #         label="run query", 
        #         outlined=True,
        #         color="primary", 
        #         icon_name="mdi-play",
        #         on_click=partial(run_query, item.get('content', ''))
        #     )


def render_chat_message(idx, item):
    """
    Render a chat message with optional embedded DataFrame and feedback buttons.

    Parameters
    ----------
    idx : int
        The index of the message in the messages list.
    item : dict
        The message dictionary containing role, content, dataframe, etc.

    Returns
    -------
    None
    """
    with solara.lab.ChatMessage(
        user=item["role"] == "user",
        avatar=False,
        name="ChatBot" if item["role"] == "assistant" else "User",
        color="#e9e9e9" if item["role"] == "assistant" else "#abe0f7",
        avatar_background_color="primary" if item["role"] == "assistant" else None,
        border_radius="20px",
    ):
        solara.Markdown(item["content"])

        if (item["role"] == "assistant") and (item.get("dataframe", None) is not None):
            solara.DataFrame(item.get("dataframe"), items_per_page=5)
            solara.Markdown("")
    
        if (item["role"] == "assistant"):
            # Get the previous (user) message index for using it in feedback
            user_message_idx = idx - 1
            user_message = messages.value[user_message_idx] if user_message_idx >= 0 else None 

            render_buttons_row(item, user_message)


def render_chatbox():
    """
    Render the chatbox by iterating over the message list and displaying each message.

    Uses:
    - solara.lab.ChatBox() context to encapsulate chat messages.
    - Skips messages with the role 'system'.
    - Delegates rendering each message to `render_chat_message`.

    Returns:
    None
    """
    with solara.lab.ChatBox():
        for i, item in enumerate(messages.value):
            if (item["role"] == "system"):
                continue

            render_chat_message(idx=i, item=item)


def render_progress_bar():
    """
    Render a simple progress indicator as a linear progress bar with placeholder text.

    Returns
    -------
    None
    """
    solara.Text("...", style={"font-size": "1rem", "padding-left": "20px"})
    solara.ProgressLinear()


def render_chat_input():
    """
    Render the chat input box with an associated callback to handle user input.

    Uses:
    - solara.lab.ChatInput() component for user message input.
    - Sets callback `prompt_vanna` to process submitted messages.
    - Controls input and send button disable states based on `prompt_vanna.pending`.
    - Enables autofocus on the input field.
    - Assigns a unique key to the component for React-style reactivity.

    Returns
    -------
    None
    """
    solara.lab.ChatInput(
        send_callback=prompt_vanna, 
        disabled=prompt_vanna.pending, 
        disabled_input=prompt_vanna.pending, 
        disabled_send=prompt_vanna.pending, 
        autofocus=True
    ).key("input")


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
        solara.Title("Solara SQL Chatbot")
        
        # Show Chatbox
        render_chatbox()
        
        # Show progress bar while generation an answer
        if prompt_vanna.pending:
            render_progress_bar()
        
        render_chat_input()
