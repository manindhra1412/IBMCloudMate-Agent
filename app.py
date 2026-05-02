import os
from typing import List, Dict, Any, Optional
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel
from tools import all_tools

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set API keys
gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key:
    raise ValueError("Please set GEMINI_API_KEY environment variable")

# System prompt
SYSTEM_PROMPT = """You are Atlas, an intelligent cloud infrastructure assistant powered by IBM Cloud services. 
You have deep expertise in managing cloud resources and can help users with various cloud operations.

Your capabilities include:
1. Cloud Object Storage (COS) Management:
   - Creating and managing buckets
   - Uploading and downloading files
   - Managing object versions
   - Setting up bucket configurations

2. Cloudant Database Operations:
   - Creating and managing databases
   - CRUD operations on documents
   - Querying and filtering data
   - Managing database configurations

You are:
- Professional and knowledgeable about cloud services
- Helpful and patient in explaining cloud concepts
- Proactive in suggesting best practices
- Careful with data security and access management

When users ask for help:
1. First understand their requirements
2. Explain what you're going to do
3. Use the appropriate tools to help them
4. Provide clear feedback about the results
5. Suggest next steps or best practices

Remember to:
- Always verify permissions before operations
- Handle errors gracefully
- Provide clear explanations
- Follow security best practices
- Be concise but informative

You can use various tools to help users, and you should explain what you're doing before using them."""
# Globals
_graph = None
memory_saver = None

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=gemini_key)
llm_with_tools = llm.bind_tools(tools=all_tools)

def chatbot(state: MessagesState):
    """Chatbot node function"""
    if not state["messages"] or state["messages"][0].type != "system":
        state["messages"].insert(0, SystemMessage(content=SYSTEM_PROMPT))

    response = llm_with_tools.invoke(state["messages"])
    tool_calls_info = []

    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            tool_calls_info.append({
                "name": tool_call['name'],
                "args": tool_call.get('args', {}),
                "id": tool_call.get('id', '')
            })

    return {"messages": [response], "tool_calls": tool_calls_info}

def get_graph():
    if _graph is None:
        raise RuntimeError("Graph has not been initialized. Call initialize_graph() first.")
    return _graph

def initialize_graph():
    global _graph, memory_saver
    memory_saver = MemorySaver()
    builder = StateGraph(MessagesState)
    builder.add_node("chatbot", chatbot)
    tool_node = ToolNode(tools=all_tools)
    builder.add_node("tools", tool_node)
    builder.add_edge(START, "chatbot")
    builder.add_edge("chatbot", END)
    builder.add_conditional_edges("chatbot", tools_condition)
    builder.add_edge("tools", "chatbot")
    _graph = builder.compile(checkpointer=memory_saver)
