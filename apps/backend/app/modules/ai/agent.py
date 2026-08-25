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

from .guardrails import guardrail_service
from .prompts import prompt_service
from .memory import memory_manager
from .confidence import confidence_evaluator

class AgentState(TypedDict):
    """The state of the conversation graph."""
    call_id: str
    messages: Annotated[Sequence[Dict[str, str]], operator.add]
    context: str
    guardrail_safe: bool
    guardrail_reason: str
    confidence_decision: str
    retrieval_results: list

async def guardrail_node(state: AgentState) -> dict:
    """Check the utterance against prompt injections and business rules."""
    logger.debug("Entering guardrail_node")
    last_message = state["messages"][-1]
    
    if last_message["role"] == "user":
        is_safe, reason = guardrail_service.check_utterance(last_message["content"])
        return {"guardrail_safe": is_safe, "guardrail_reason": reason}
    return {"guardrail_safe": True, "guardrail_reason": ""}

async def retrieve_node(state: AgentState) -> dict:
    """Retrieve context from Qdrant based on the latest human message."""
    logger.debug("Entering retrieve_node")
    if not state.get("guardrail_safe", True):
        return {"retrieval_results": [], "context": ""}
        
    last_message = state["messages"][-1]
    
    if last_message["role"] == "user":
        from app.core.providers.registry import registry
        try:
            qdrant_provider = registry.get("VectorDBProvider")
            results = qdrant_provider.search(last_message["content"])
        except ValueError:
            results = []
        context = "\n".join([r.get("text", "") for r in results])
        return {"retrieval_results": results, "context": context}
        
    return {"retrieval_results": [], "context": ""}

async def evaluate_node(state: AgentState) -> dict:
    """Evaluate confidence to determine next routing."""
    logger.debug("Entering evaluate_node")
    decision, _ = confidence_evaluator.evaluate(
        state.get("call_id", "unknown"),
        state.get("retrieval_results", []),
        state.get("guardrail_safe", True),
        state.get("guardrail_reason", "")
    )
    return {"confidence_decision": decision}

async def generate_node(state: AgentState) -> dict:
    """Generate a response using Groq."""
    logger.debug("Entering generate_node")
    
    # 1. Fetch DB Prompt
    system_prompt = prompt_service.get_system_prompt()
    system_prompt += f"\nContext:\n{state.get('context', 'None')}"
    
    # 2. Token Optimization (Memory Manager)
    # Re-inject the system prompt as the first message
    optimized_messages = memory_manager.optimize_history(state["messages"])
    
    response = await llm_service.generate_response(system_prompt, optimized_messages)
    
    return {"messages": [{"role": "assistant", "content": response}]}
    
async def escalate_node(state: AgentState) -> dict:
    """Handle low confidence / guardrail failures by preparing for human handoff."""
    logger.debug("Entering escalate_node")
    response = "I'm having a little trouble understanding. Please hold while I transfer you to a human agent."
    
    # In a real system, this would fire an event back to the Telephony state machine to trigger Asterisk Dial()
    
    return {"messages": [{"role": "assistant", "content": response}]}

def route_confidence(state: AgentState) -> str:
    """Route based on confidence decision."""
    decision = state.get("confidence_decision", "HIGH")
    if decision == "LOW":
        return "escalate"
    elif decision == "MEDIUM":
        # For phase 1, Medium acts like high but the LLM might ask a clarifying question.
        return "generate"
    return "generate"

def build_graph():
    """Build the LangGraph state machine for the conversation."""
    if not LANGGRAPH_AVAILABLE:
        return None
        
    workflow = StateGraph(AgentState)
    
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("escalate", escalate_node)
    
    workflow.set_entry_point("guardrail")
    workflow.add_edge("guardrail", "retrieve")
    workflow.add_edge("retrieve", "evaluate")
    
    # Conditional routing
    workflow.add_conditional_edges(
        "evaluate",
        route_confidence,
        {
            "generate": "generate",
            "escalate": "escalate"
        }
    )
    
    workflow.add_edge("generate", END)
    workflow.add_edge("escalate", END)
    
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
    inputs = {
        "call_id": call_id,
        "messages": [{"role": "user", "content": utterance}], 
        "context": "",
        "guardrail_safe": True,
        "guardrail_reason": "",
        "confidence_decision": "HIGH",
        "retrieval_results": []
    }

    
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
