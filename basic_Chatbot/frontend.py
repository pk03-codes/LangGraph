
import streamlit as st
from langchain_core.messages import HumanMessage
from backend import chatbot, retreive_all_threads
import uuid


# **************** -UTILITY FUNCTIONS- ****************

def generate_thread_id():
    return str(uuid.uuid4())


def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


def reset_chat():
    thread_id = generate_thread_id()

    st.session_state["thread_id"] = thread_id
    st.session_state["message_history"] = []

    


def format_message_content(content):

    if isinstance(content, str):
        return content

    elif isinstance(content, list):

        text_parts = []

        for item in content:

            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))

        return "\n".join(text_parts)

    return str(content)


def load_conversation(thread_id):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    state = chatbot.get_state(config)

    messages = state.values.get("messages", [])

    history = []

    for message in messages:

        if message.type == "human":
            role = "user"

        elif message.type == "ai":
            role = "assistant"

        else:
            continue

        content = format_message_content(message.content)

        history.append({
            "role": role,
            "content": content
        })

    return history

def get_thread_title(thread_id):
    config={
        "configurable":{
        "thread_id":thread_id}
    }
    state=chatbot.get_state(config)
    messages=state.values.get("messages",[])
    for message in messages:
        if message.type =="human":
            content=format_message_content(message.content)

            if len(content)>35:
                return content[:35]+"..."

            return content
    return "New Conversation"


# **************** -INITIALIZATION- ****************

st.title("ChatBOT")

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retreive_all_threads()




# **************** -SIDEBAR UI- ****************

st.sidebar.title("LangGraph Chatbot")


# New Chat Button

if st.sidebar.button("New Chat", key="new_chat"):

    reset_chat()

    st.rerun()


# Conversation History

# **************** -CONVERSATION HISTORY- ****************

st.sidebar.header("My Conversations")

for thread_id in st.session_state["chat_threads"][::-1]:

    title = get_thread_title(thread_id)

    if st.sidebar.button(
        title,
        key=f"thread_{thread_id}",
        use_container_width=True
    ):

        st.session_state["thread_id"] = thread_id

        messages = load_conversation(thread_id)

        st.session_state["message_history"] = messages

        st.rerun()


# **************** -CONFIGURATION- ****************

CONFIG = {
    "configurable": {
        "thread_id": st.session_state["thread_id"]
    }
}


# **************** -DISPLAY CHAT HISTORY- ****************

for message in st.session_state["message_history"]:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# **************** -USER INPUT- ****************

user_input = st.chat_input("Type your message here...")


if user_input:
    if st.session_state["thread_id"] not in st.session_state["chat_threads"]:
        add_thread(st.session_state["thread_id"])

    # Display user message

    with st.chat_message("user"):

        st.markdown(user_input)

    st.session_state["message_history"].append({
        "role": "user",
        "content": user_input
    })


    # Convert input into LangChain message

    input_message = HumanMessage(content=user_input)


    # Generate assistant response

    with st.chat_message("assistant"):

        message_placeholder = st.empty()

        full_response = ""


        for msg, metadata in chatbot.stream(
            {"messages": [input_message]},
            CONFIG,
            stream_mode="messages"
        ):

            if (
                metadata.get("langgraph_node") == "chat_node"
                and hasattr(msg, "content")
                and msg.content
            ):

                chunk_content = msg.content

                if isinstance(chunk_content, list):

                    text_chunk = "".join(
                        item.get("text", "")
                        for item in chunk_content
                        if isinstance(item, dict)
                        and item.get("type") == "text"
                    )

                else:
                    text_chunk = chunk_content


                full_response += text_chunk

                message_placeholder.markdown(full_response + "▌")


        # Final response

        message_placeholder.markdown(full_response)


    # Save assistant response in Streamlit session state

    st.session_state["message_history"].append({
        "role": "assistant",
        "content": full_response
    })
