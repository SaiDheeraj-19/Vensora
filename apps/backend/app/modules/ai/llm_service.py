import logging
import os
from typing import List, Dict

logger = logging.getLogger(__name__)

class GroqService:
    """
    Service to handle LLM inferences via Groq.
    Built for ultra-low latency voice responses.
    """
    def __init__(self):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=os.getenv("GROQ_API_KEY", "mock_key")
            )
            self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
            self.enabled = True
        except ImportError:
            logger.warning("groq library not installed. LLM service will use mock mode.")
            self.client = None
            self.enabled = False

    async def generate_response(self, system_prompt: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Generate a conversational response, automatically handling tool calls if the model requests them.
        """
        if not self.enabled or not self.client:
            return "I am a mock AI response since the Groq API key or library is missing."

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        
        from app.modules.ai.tools import AVAILABLE_TOOLS, execute_tool_call
        
        try:
            # 1. Initial LLM Call with Tools
            chat_completion = await self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.5,
                max_tokens=250,
                tools=AVAILABLE_TOOLS,
                tool_choice="auto"
            )
            
            response_message = chat_completion.choices[0].message
            
            # 2. Check if the model wants to call a tool
            if response_message.tool_calls:
                logger.info("LLM requested tool calls.")
                # Append the assistant's tool call request to the history
                messages.append(response_message)
                
                for tool_call in response_message.tool_calls:
                    # Execute the tool
                    tool_result_json = await execute_tool_call(tool_call.function.name, tool_call.function.arguments)
                    
                    # Append the tool result to the history
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": tool_result_json,
                    })
                
                # 3. Final LLM Call to generate the response based on the tool output
                final_completion = await self.client.chat.completions.create(
                    messages=messages,
                    model=self.model,
                    temperature=0.5,
                    max_tokens=150
                )
                return final_completion.choices[0].message.content or ""

            # Normal text response
            return response_message.content or ""
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return "I'm sorry, I'm having trouble processing that right now."

llm_service = GroqService()
