import logging
import json
from typing import List, Dict, Any
from app.modules.crm.adapter import crm_adapter

logger = logging.getLogger(__name__)

# Define the JSON Schema for the tools as expected by OpenAI / Groq tool calling formats.
# We will use these schemas to bind tools to the LLM.

AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_shipment_status",
            "description": "Get the current tracking status and estimated delivery time for a shipment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tracking_number": {
                        "type": "string",
                        "description": "The alphanumeric tracking number of the shipment (e.g., TRK123456789).",
                    }
                },
                "required": ["tracking_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Create a support ticket for a customer issue that you cannot immediately resolve.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The unique ID of the customer.",
                    },
                    "issue_summary": {
                        "type": "string",
                        "description": "A brief summary of the customer's problem.",
                    }
                },
                "required": ["customer_id", "issue_summary"],
            },
        },
    }
]

async def execute_tool_call(tool_name: str, arguments: str) -> str:
    """
    Executes the requested tool and returns the JSON stringified result.
    """
    logger.info(f"Executing AI Tool: {tool_name} with args: {arguments}")
    try:
        args_dict = json.loads(arguments)
        
        if tool_name == "get_shipment_status":
            result = await crm_adapter.get_shipment_status(args_dict.get("tracking_number"))
            return json.dumps(result)
            
        elif tool_name == "create_support_ticket":
            result = await crm_adapter.create_support_ticket(args_dict.get("customer_id"), args_dict.get("issue_summary"))
            return json.dumps(result)
            
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
            
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return json.dumps({"error": str(e)})
