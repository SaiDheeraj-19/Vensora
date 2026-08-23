import logging
from typing import TypedDict, Annotated, Sequence, Dict
import operator

logger = logging.getLogger(__name__)

# Try to import LangGraph safely for Phase 1 Audit
try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("langgraph or langchain-core is not installed. Agent will use mock mode.")

from .llm_service import llm_service
from .qdrant_client import qdrant_service

class AgentState(TypedDict):
    """The state of the conversation graph."""
    messages: Annotated[Sequence[Dict[str, str]], operator.add]
    context: str

async def retrieve_node(state: AgentState) -> dict:
    """Retrieve context from Qdrant based on the latest human message."""
    logger.debug("Entering retrieve_node")
    last_message = state["messages"][-1]
    
    if last_message["role"] == "user":
        results = qdrant_service.search(last_message["content"])
        context = "\n".join([r["payload"]["text"] for r in results])
        return {"context": context}
        
    return {"context": ""}

async def generate_node(state: AgentState) -> dict:
    """Generate a response using Groq."""
    logger.debug("Entering generate_node")
    
    system_prompt = f"""You are Vensora, an intelligent enterprise AI assistant.
Keep your answers brief and conversational, as they will be spoken over the phone.
Context retrieved from knowledge base:
{state.get('context', 'None')}
"""
    
    response = await llm_service.generate_response(system_prompt, state["messages"])
    
    return {"messages": [{"role": "assistant", "content": response}]}

def build_graph():
    """Build the LangGraph state machine for the conversation."""
    if not LANGGRAPH_AVAILABLE:
        return None
        
    workflow = StateGraph(AgentState)
    
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)
    
    # Simple static routing for Phase 1: Always retrieve then generate
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()

# Compile the graph globally
conversational_agent = build_graph()

async def process_utterance(call_id: str, utterance: str) -> str:
    """
    Main entry point called by the Telephony module when a user finishes speaking.
    """
    logger.info(f"[{call_id}] Processing user utterance: '{utterance}'")
    
    if not conversational_agent:
        # Fallback if LangGraph isn't installed during audit
        return await llm_service.generate_response("You are Vensora.", [{"role": "user", "content": utterance}])
        
    # Execute the graph
    inputs = {"messages": [{"role": "user", "content": utterance}], "context": ""}
    
    # LangGraph returns an async generator for node execution
    final_state = None
    async for output in conversational_agent.astream(inputs):
        for key, value in output.items():
            final_state = value
            
    if final_state and "messages" in final_state:
        last_message = final_state["messages"][-1]
        if last_message["role"] == "assistant":
            return last_message["content"]
            
    return "I'm sorry, I couldn't process that."
