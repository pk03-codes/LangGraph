from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
import operator
from langchain_google_genai import ChatGoogleGenerativeAI
import sqlite3

# (Assume LLM setup is here, e.g., ChatGoogleGenerativeAI or ChatOpenAI)
llm=ChatGoogleGenerativeAI(model='gemini-3.5-flash-lite')

# 1. State Schema
class State(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

# 2. Node Definition
def chat_node(state: State):
    #In reality, this invokes your LLM. 
    response = llm.invoke(state["messages"])
    return {"messages": [response]}
     

# 3. Graph Building
workflow = StateGraph(State)
workflow.add_node("chat_node", chat_node)
workflow.set_entry_point("chat_node")
workflow.add_edge("chat_node", END)

conn=sqlite3.connect(database='chatbot.db',check_same_thread=False)
# 4. Compile with Persistence
memory = SqliteSaver(conn=conn)
chatbot = workflow.compile(checkpointer=memory)

def retreive_all_threads():
    all_threads=set()
    for c in memory.list(None):
        all_threads.add(c.config['configurable']['thread_id'])

    return list(all_threads)