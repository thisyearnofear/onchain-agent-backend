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

def save_development_wallet(wallet: Wallet) -> None:
    """Save development wallet information to database."""
    wallet_info = {
        "wallet_id": wallet.id,
        "network": wallet.network_id,
        "default_address": wallet.default_address.address_id,
        "addresses": [addr.address_id for addr in wallet.addresses]
    }
    save_wallet_info(wallet.id, wallet_info)
    logger.info("Saved wallet info to database")

def initialize_wallet(config: Dict[str, str]) -> Wallet:
    """Initialize wallet based on environment (development or production)."""
    wallet_id = os.getenv(WALLET_ID_ENV_VAR)
    
    if wallet_id:
        logger.info(f"Production mode: Loading wallet {wallet_id}")
        try:
            wallet = Wallet.fetch(wallet_id)
            logger.info("Successfully loaded production wallet")
            return wallet
        except Exception as e:
            logger.error(f"Failed to load production wallet: {e}")
            raise
    
    # Development mode - create a new wallet if none exists
    logger.info("Development mode: Creating new wallet")
    try:
        wallet = Wallet.create()
        logger.info(f"Created new development wallet: {wallet.id}")
        save_development_wallet(wallet)
        return wallet
    except Exception as e:
        logger.error(f"Failed to create development wallet: {e}")
        raise

def format_private_key(key: str) -> str:
    """Format the private key with proper PEM headers and line breaks."""
    logger.debug("Input key length: %d", len(key))
    clean_key = key.strip()
    logger.debug("Stripped key length: %d", len(clean_key))

    # If the key already has headers, extract just the base64 part
    if "-----BEGIN EC PRIVATE KEY-----" in clean_key:
        logger.debug("Key contains PEM headers, extracting base64 part")
        parts = clean_key.split("-----")
        for part in parts:
            if not part.startswith("BEGIN") and not part.startswith("END") and part.strip():
                clean_key = part.strip()
                logger.debug("Extracted base64 part length: %d", len(clean_key))
                break

    # Remove any escaped newlines and actual newlines
    original_length = len(clean_key)
    clean_key = clean_key.replace("\\n", "").replace("\n", "")
    if len(clean_key) != original_length:
        logger.debug("Removed %d newline characters", original_length - len(clean_key))

    # Add padding if needed
    padding_needed = len(clean_key) % 4
    if padding_needed:
        clean_key += "=" * (4 - padding_needed)
        logger.debug("Added %d padding characters", 4 - padding_needed)

    # Validate the key is proper base64
    import base64
    try:
        decoded = base64.b64decode(clean_key)
        logger.debug("Successfully decoded base64 key (length: %d bytes)", len(decoded))
    except Exception as e:
        logger.error(f"Invalid base64 in private key: {str(e)}")
        logger.error("Key content: %s", clean_key)
        raise ValueError("Private key is not valid base64") from e

    # Remove the padding for the final formatted key
    clean_key = clean_key.rstrip("=")
    
    # Build the formatted key with proper PEM structure
    formatted_lines = ["-----BEGIN EC PRIVATE KEY-----"]
    formatted_lines.extend(
        clean_key[i:i + 64] for i in range(0, len(clean_key), 64)
    )
    formatted_lines.append("-----END EC PRIVATE KEY-----")

    result = "\n".join(formatted_lines)
    logger.debug("Final formatted key length: %d", len(result))
    return result

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
        logger.debug("Raw key length: %d", len(cdp_api_key_private_key))
        logger.debug("Raw key starts with: %s", cdp_api_key_private_key[:20])
        
        formatted_key = format_private_key(cdp_api_key_private_key)
        logger.info("Private key formatted successfully")
        logger.debug("Formatted key length: %d", len(formatted_key))
        logger.debug("Formatted key structure:")
        for line in formatted_key.split("\n"):
            logger.debug("  %s", f"{line[:10]}..." if len(line) > 10 else line)
        
        # Configure CDP SDK
        logger.info("Configuring CDP SDK...")
        Cdp.configure(cdp_api_key_name, formatted_key)
        logger.info("CDP SDK configured successfully")
            
    except Exception as e:
        logger.error(f"Failed to configure CDP SDK: {str(e)}")
        logger.error(f"CDP API Key Name: {cdp_api_key_name}")
        if cdp_api_key_private_key:
            key_preview = f"{cdp_api_key_private_key[:10]}...{cdp_api_key_private_key[-10:]}"
            logger.error(f"Private Key Preview: {key_preview}")
        raise

    # Initialize wallet and create agent components
    wallet = initialize_wallet({"name": cdp_api_key_name, "privateKey": formatted_key})
    logger.info("Using wallet:")
    logger.info(f"- ID: {wallet.id}")
    logger.info(f"- Network: {wallet.network_id}")
    logger.info(f"- Default Address: {wallet.default_address.address_id}")

    values = {
        "cdp_api_key_name": cdp_api_key_name,
        "cdp_api_key_private_key": formatted_key,
        "wallet": wallet
    }
    
    logger.info("Initializing CDP Agentkit wrapper...")
    agentkit = CdpAgentkitWrapper(**values)
    logger.info("CDP Agentkit wrapper initialized successfully")

    # Initialize LLM and tools
    llm = ChatOpenAI(model=AGENT_MODEL, temperature=0)
    tools = [
        CdpTool(
            name=action.name,
            description=action.description,
            func=action.func,
            args_schema=action.args_schema,
            cdp_agentkit_wrapper=agentkit
        )
        for action in CDP_ACTIONS
    ]
    
    logger.info(f"Created {len(tools)} tools from CDP actions")
    tool_functions = [format_tool_to_openai_function(t) for t in tools]
    
    # Create the prompt template and agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", AGENT_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    llm_with_tools = llm.bind(functions=tool_functions)
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

    return AgentExecutor(agent=agent, tools=tools, verbose=True)