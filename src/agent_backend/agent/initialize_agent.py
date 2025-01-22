import os
import json
from pathlib import Path
from typing import Dict, Any

from cdp import Cdp
from cdp_langchain.utils import CdpAgentkitWrapper
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function
from langchain_openai import ChatOpenAI

from agent_backend.agent.tools import get_tools
from agent_backend.config import get_settings

def initialize_agent() -> AgentExecutor:
    """Initialize the agent with the CDP configuration and tools."""
    settings = get_settings()
    
    # Get the absolute path to the JSON file
    current_dir = Path(__file__).parent.parent.parent.parent
    json_path = current_dir / "cdp_api_key.json"
    print(f"Loading CDP config from: {json_path}")

    # Read and parse the JSON file
    with open(json_path) as f:
        config = json.load(f)

    # Pass the values directly to CdpAgentkitWrapper
    values = {
        "cdp_api_key_name": config['name'],
        "cdp_api_key_private_key": config['privateKey']
    }

    print("Configuring CDP with values...")
    
    # Initialize the CDP Agentkit wrapper
    agentkit = CdpAgentkitWrapper(**values)
    print("CDP SDK configured successfully")

    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0
    )

    # Get tools
    tools = get_tools()

    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant specialized in blockchain operations on Base Sepolia. 
Your primary functions include:
- Deploying and managing ERC-20 tokens and NFTs
- Checking wallet balances
- Requesting funds from faucets
- Providing specific information about blockchain operations

Only provide information about actual operations or respond to specific requests. 
Do not generate generic blockchain activity reports unless explicitly asked."""),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create the agent
    agent = (
        {
            "messages": lambda x: x["messages"],
            "agent_scratchpad": lambda x: format_to_openai_function_messages(
                x.get("intermediate_steps", [])
            ),
        }
        | prompt
        | llm
        | OpenAIFunctionsAgentOutputParser()
    )

    # Create the AgentExecutor
    return AgentExecutor(agent=agent, tools=tools, verbose=True)