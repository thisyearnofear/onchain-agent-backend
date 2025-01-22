import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import datetime

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
from agent_backend.constants import AGENT_MODEL, AGENT_PROMPT, WALLET_ID_ENV_VAR
from agent_backend.db.wallet import save_wallet_info, get_wallet_info

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def save_development_wallet(wallet: Wallet) -> None:
    """Save development wallet information to database and persist seed."""
    # Export wallet data (includes seed and ID)
    data = wallet.export_data()
    
    # Save wallet info to database
    wallet_info = {
        "wallet_id": wallet.id,
        "network": wallet.network_id,
        "default_address": wallet.default_address.address_id,
        "addresses": [addr.address_id for addr in wallet.addresses],
        "created_at": datetime.datetime.utcnow().isoformat(),
        "last_validated": datetime.datetime.utcnow().isoformat(),
        "validation_count": 1
    }
    save_wallet_info(wallet.id, wallet_info)
    
    # Save encrypted seed file for development
    seed_path = Path("dev_wallet_seed.json")
    wallet.save_seed(str(seed_path), encrypt=True)
    logger.info(f"Development seed saved to: {seed_path}")

def initialize_wallet(config: Dict[str, str]) -> Wallet:
    """Initialize wallet based on environment (development or production)."""
    wallet_id = os.getenv(WALLET_ID_ENV_VAR)
    
    if wallet_id:
        logger.info(f"Production mode: Loading wallet {wallet_id}")
        try:
            # First fetch the unhydrated wallet
            wallet = Wallet.fetch(wallet_id)
            logger.info(f"Fetched wallet {wallet_id} from server")
            
            # Get stored wallet info from our database
            stored_info = get_wallet_info(wallet_id)
            if not stored_info:
                raise ValueError(f"No stored info found for wallet {wallet_id}")
            
            # Validate wallet network matches our expected network
            if wallet.network_id != stored_info.get('network'):
                raise ValueError(f"Wallet network mismatch. Expected: {stored_info.get('network')}, Got: {wallet.network_id}")
            
            # Check if we need to hydrate the wallet
            if not wallet.can_sign():
                logger.info("Wallet needs hydration")
                # Try to load seed from development file first
                seed_path = Path("dev_wallet_seed.json")
                if seed_path.exists():
                    logger.info("Loading seed from development file")
                    wallet.load_seed(str(seed_path))
                else:
                    # For production, you would fetch the seed from your secure storage
                    logger.warning("No seed file found - wallet will be read-only")
            
            logger.info(f"Wallet status - Can sign: {wallet.can_sign()}")
            logger.info(f"Network: {wallet.network_id}")
            logger.info(f"Default Address: {wallet.default_address.address_id}")
            
            return wallet
            
        except Exception as e:
            logger.error(f"Failed to load production wallet: {e}")
            raise
    
    # Create a new Developer-Managed (1-of-1) wallet for testing
    logger.info("Creating new Developer-Managed wallet for testing")
    try:
        # Create wallet on Base Sepolia testnet
        wallet = Wallet.create(network_id="base-sepolia")
        logger.info(f"Created new Developer-Managed wallet: {wallet.id}")
        
        # Save wallet info and seed
        save_development_wallet(wallet)
        
        # Important security notices
        logger.info("\nIMPORTANT SECURITY NOTICES:")
        logger.info("1. This is a Developer-Managed (1-of-1) wallet - suitable for testing only")
        logger.info("2. For production, consider upgrading to Coinbase-Managed wallets with Server-Signer")
        logger.info("3. Ensure your CDP API keys are stored securely")
        logger.info("4. Enable IP whitelisting in the CDP Portal for additional security")
        logger.info(f"5. Save this wallet ID securely: {wallet.id}")
        logger.info(f"6. Seed is encrypted and saved to dev_wallet_seed.json")
        
        return wallet
    except Exception as e:
        logger.error(f"Failed to create Developer-Managed wallet: {e}")
        raise

def initialize_agent() -> AgentExecutor:
    """Initialize the agent with the CDP configuration and tools."""
    settings = get_settings()
    
    # Get CDP configuration from environment variables
    cdp_api_key_name = os.getenv("CDP_API_KEY_NAME")
    cdp_api_key_private_key = os.getenv("CDP_API_KEY_PRIVATE_KEY")
    
    if not cdp_api_key_name or not cdp_api_key_private_key:
        raise ValueError("CDP_API_KEY_NAME and CDP_API_KEY_PRIVATE_KEY environment variables must be set")

    # Configure CDP SDK with API key name and raw private key
    try:
        logger.info("Configuring CDP SDK...")
        # Pass the private key directly to the SDK
        Cdp.configure(cdp_api_key_name, cdp_api_key_private_key)
        logger.info("CDP SDK configured successfully")
            
    except Exception as e:
        logger.error(f"Failed to configure CDP SDK: {str(e)}")
        logger.error(f"CDP API Key Name: {cdp_api_key_name}")
        raise

    # Initialize wallet and create agent components
    wallet = initialize_wallet({})
    logger.info("Using wallet:")
    logger.info(f"- ID: {wallet.id}")
    logger.info(f"- Network: {wallet.network_id}")
    logger.info(f"- Default Address: {wallet.default_address.address_id}")

    values = {
        "cdp_api_key_name": cdp_api_key_name,
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