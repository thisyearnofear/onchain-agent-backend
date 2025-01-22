import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from cdp import Cdp, Wallet
from cdp_langchain.utils import CdpAgentkitWrapper
from cdp_langchain.tools.cdp_tool import CdpTool
from cdp_langchain.agent_toolkits.cdp_toolkit import CDP_ACTIONS
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function
from langchain_openai import ChatOpenAI

from agent_backend.config import get_settings
from agent_backend.constants import AGENT_MODEL, AGENT_PROMPT, WALLET_ID_ENV_VAR, WALLET_SEED_ENV_VAR
from agent_backend.db.wallet import save_wallet_info, get_wallet_info

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def initialize_wallet(config: Dict[str, str]) -> Wallet:
    """Initialize wallet based on environment (development or production)."""
    # Check for production wallet configuration
    wallet_id = os.getenv(WALLET_ID_ENV_VAR)
    
    if wallet_id:
        logger.info(f"Production mode: Loading wallet {wallet_id}")
        try:
            wallet = Wallet.fetch(wallet_id)
            logger.info(f"Successfully loaded production wallet")
            return wallet
        except Exception as e:
            logger.error(f"Failed to load production wallet: {e}")
            raise
    
    # Development mode - create a new wallet if none exists
    logger.info("Development mode: Creating new wallet")
    try:
        wallet = Wallet.create()
        logger.info(f"Created new development wallet: {wallet.id}")
        
        # Save wallet info to database
        wallet_info = {
            "wallet_id": wallet.id,
            "network": wallet.network_id,
            "default_address": wallet.default_address.address_id,
            "addresses": [addr.address_id for addr in wallet.addresses]
        }
        save_wallet_info(wallet.id, wallet_info)
        logger.info("Saved wallet info to database")
        
        return wallet
    except Exception as e:
        logger.error(f"Failed to create development wallet: {e}")
        raise

def format_private_key(key: str) -> str:
    """Format the private key with proper PEM headers and line breaks."""
    # Remove any existing headers/footers and whitespace
    clean_key = key.replace("-----BEGIN EC PRIVATE KEY-----", "")
    clean_key = clean_key.replace("-----END EC PRIVATE KEY-----", "")
    clean_key = clean_key.replace("\\n", "")
    clean_key = clean_key.replace("\n", "")
    clean_key = clean_key.strip()
    
    # Format with proper headers and line breaks
    formatted_key = "-----BEGIN EC PRIVATE KEY-----\n"
    # Split the key into 64-character chunks
    chunks = [clean_key[i:i+64] for i in range(0, len(clean_key), 64)]
    formatted_key += "\n".join(chunks)
    formatted_key += "\n-----END EC PRIVATE KEY-----"
    
    return formatted_key

def initialize_agent() -> AgentExecutor:
    """Initialize the agent with the CDP configuration and tools."""
    settings = get_settings()
    
    # Get CDP configuration from environment variables
    cdp_api_key_name = os.getenv("CDP_API_KEY_NAME")
    cdp_api_key_private_key = os.getenv("CDP_API_KEY_PRIVATE_KEY")
    
    if not cdp_api_key_name or not cdp_api_key_private_key:
        raise ValueError("CDP_API_KEY_NAME and CDP_API_KEY_PRIVATE_KEY environment variables must be set")

    # Format the private key
    try:
        logger.info("Formatting CDP private key...")
        formatted_key = format_private_key(cdp_api_key_private_key)
        logger.info("Private key formatted successfully")
        logger.debug(f"Formatted key preview: {formatted_key[:50]}...")
        
        # Configure CDP SDK
        logger.info("Configuring CDP SDK...")
        Cdp.configure(cdp_api_key_name, formatted_key)
        logger.info("CDP SDK configured successfully")
            
    except Exception as e:
        logger.error(f"Failed to configure CDP SDK: {str(e)}")
        logger.error(f"CDP API Key Name: {cdp_api_key_name}")
        # Log the first and last 10 characters of the key for debugging
        if cdp_api_key_private_key:
            key_preview = f"{cdp_api_key_private_key[:10]}...{cdp_api_key_private_key[-10:]}"
            logger.error(f"Private Key Preview: {key_preview}")
        raise

    # Initialize wallet
    wallet = initialize_wallet({"name": cdp_api_key_name, "privateKey": formatted_key})
    logger.info(f"Using wallet:")
    logger.info(f"- ID: {wallet.id}")
    logger.info(f"- Network: {wallet.network_id}")
    logger.info(f"- Default Address: {wallet.default_address.address_id}")

    # Initialize the CDP Agentkit wrapper with the wallet
    values = {
        "cdp_api_key_name": cdp_api_key_name,
        "cdp_api_key_private_key": formatted_key,
        "wallet": wallet
    }
    
    logger.info("Initializing CDP Agentkit wrapper...")
    agentkit = CdpAgentkitWrapper(**values)
    logger.info("CDP Agentkit wrapper initialized successfully")

    # Initialize LLM
    llm = ChatOpenAI(
        model=AGENT_MODEL,
        temperature=0
    )

    # Create tools from CDP actions
    tools = []
    for action in CDP_ACTIONS:
        tool = CdpTool(
            name=action.name,
            description=action.description,
            func=action.func,
            args_schema=action.args_schema,
            cdp_agentkit_wrapper=agentkit
        )
        tools.append(tool)
    
    logger.info(f"Created {len(tools)} tools from CDP actions")
    
    # Format tools for OpenAI functions
    tool_functions = [format_tool_to_openai_function(t) for t in tools]
    
    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", AGENT_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create the agent with tools as functions
    llm_with_tools = llm.bind(functions=tool_functions)
    
    # Create the agent
    agent = (
        {
            "messages": lambda x: x["messages"],
            "agent_scratchpad": lambda x: format_to_openai_function_messages(
                x.get("intermediate_steps", [])
            ),
        }
        | prompt
        | llm_with_tools
        | OpenAIFunctionsAgentOutputParser()
    )

    # Create the AgentExecutor
    return AgentExecutor(agent=agent, tools=tools, verbose=True)