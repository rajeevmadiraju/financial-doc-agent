"""
agent/graph.py
LangGraph agent with tool use and conversation memory.
"""

from typing import Annotated, List, TypedDict, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from loguru import logger

from backend.config import get_settings
from backend.agent.tools import AGENT_TOOLS

settings = get_settings()

SYSTEM_PROMPT = """You are a financial analysis assistant with access to uploaded financial documents.

GUIDELINES:
- Always cite your sources (document name + page number) when referencing data
- Use calculate_financial_ratio for computing percentages, ratios, or growth figures
- Use compare_documents when comparing two companies or reports
- Use list_available_documents if the user hasn't specified a document
- Be precise with numbers — always include units ($M, $B, %, etc.)
- If data isn't in the documents, say so clearly — never hallucinate figures
- Lead with the direct answer, then provide supporting detail

Number formatting:
- Large numbers: $1.2B, $450M
- Percentages: 12.4%
- Growth: +8.3% YoY, -2.1% QoQ
"""


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def build_agent():
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=0.1,
    )
    llm_with_tools = llm.bind_tools(AGENT_TOOLS)

    def call_model(state: AgentState):
        messages = list(state["messages"])
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        return {"messages": [llm_with_tools.invoke(messages)]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(AGENT_TOOLS))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph.compile()


_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
        logger.info("LangGraph agent compiled")
    return _agent


def run_agent(user_message: str, conversation_history: List[dict] = None) -> dict:
    """
    Run agent with message and optional conversation history.

    Args:
        user_message: Latest user message
        conversation_history: List of {"role": "user"|"assistant", "content": str}

    Returns:
        {"answer": str, "updated_history": list, "tool_calls_made": list}
    """
    conversation_history = conversation_history or []
    messages = [
        HumanMessage(content=m["content"])
        for m in conversation_history if m["role"] == "user"
    ]
    messages.append(HumanMessage(content=user_message))

    logger.info(f"Agent query: '{user_message[:80]}'")
    result = get_agent().invoke({"messages": messages})

    final_message = result["messages"][-1]
    tool_calls_made = [
        tc["name"]
        for msg in result["messages"]
        if hasattr(msg, "tool_calls")
        for tc in (msg.tool_calls or [])
    ]

    return {
        "answer": final_message.content,
        "updated_history": conversation_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": final_message.content},
        ],
        "tool_calls_made": tool_calls_made,
    }