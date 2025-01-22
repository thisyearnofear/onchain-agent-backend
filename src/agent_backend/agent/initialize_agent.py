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
    
    # Development mode
    logger.info("Development mode: Managing development wallet")
    
    # Try to load existing development wallet
    try:
        current_dir = Path(__file__).parent.parent.parent.parent
        seed_path = current_dir / "dev_wallet_seed.json"
        
        if seed_path.exists():
            logger.info("Found existing development wallet seed")
            # Load wallet data to get ID
            with open(current_dir / "wallet_credentials.json") as f:
                creds = json.load(f)
                wallet_id = creds["wallet_id"]
            
            # First fetch the unhydrated wallet
            wallet = Wallet.fetch(wallet_id)
            # Then hydrate it with the saved seed
            wallet.load_seed_from_file(str(seed_path))
            logger.info(f"Successfully loaded development wallet: {wallet.id}")
            return wallet
            
    except Exception as e:
        logger.info(f"Could not load existing development wallet: {e}")
    
    # Create new development wallet
    logger.info("Creating new development wallet")
    wallet = Wallet.create()
    
    # Save development wallet data
    try:
        # Save the seed
        seed_path = current_dir / "dev_wallet_seed.json"
        wallet.save_seed_to_file(str(seed_path), encrypt=True)
        
        # Save wallet credentials
        creds = {
            "wallet_id": wallet.id,
            "network": wallet.network_id,
            "default_address": wallet.default_address.address_id,
            "addresses": [addr.address_id for addr in wallet.addresses]
        }
        with open(current_dir / "wallet_credentials.json", "w") as f:
            json.dump(creds, f, indent=2)
            
        logger.info(f"Saved new development wallet: {wallet.id}")
    except Exception as e:
        logger.warning(f"Failed to save development wallet data: {e}")
    
    return wallet

def initialize_agent() -> AgentExecutor:
    """Initialize the agent with the CDP configuration and tools."""
    settings = get_settings()
    
    # Get the absolute path to the JSON file
    current_dir = Path(__file__).parent.parent.parent.parent
    json_path = current_dir / "cdp_api_key.json"
    logger.info(f"Loading CDP config from: {json_path}")

    # Read and parse the JSON file
    with open(json_path) as f:
        config = json.load(f)

    # Configure CDP SDK
    logger.info("Configuring CDP SDK...")
    Cdp.configure(config["name"], config["privateKey"])
    logger.info("CDP SDK configured successfully")

    # Initialize wallet
    wallet = initialize_wallet(config)
    logger.info(f"Using wallet:")
    logger.info(f"- ID: {wallet.id}")
    logger.info(f"- Network: {wallet.network_id}")
    logger.info(f"- Default Address: {wallet.default_address.address_id}")

    # Initialize the CDP Agentkit wrapper with the wallet
    values = {
        "cdp_api_key_name": config['name'],
        "cdp_api_key_private_key": config['privateKey'],
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