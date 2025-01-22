"""Constants used throughout the application."""

from typing import Final

# Event types
EVENT_TYPE_AGENT: Final[str] = "agent"
EVENT_TYPE_COMPLETED: Final[str] = "completed"
EVENT_TYPE_TOOLS: Final[str] = "tools"
EVENT_TYPE_ERROR: Final[str]= "error"

# Environment variables
WALLET_ID_ENV_VAR: Final[str] = "CDP_WALLET_ID"
WALLET_SEED_ENV_VAR: Final[str] = "CDP_WALLET_SEED"

# Errors
class InputValidationError(Exception):
    """Custom exception for input validation errors"""
    pass

# Actions
DEPLOY_TOKEN: Final[str] = "deploy_token"
DEPLOY_NFT: Final[str] = "deploy_nft"

# Agent
AGENT_MODEL: Final[str] = "gpt-4-0125-preview"
AGENT_PROMPT: Final[str] = """You are a helpful AI assistant that can perform blockchain operations using Coinbase's CDP platform.

You can:
1. Deploy ERC-20 tokens using deploy_token (requires name and symbol)
2. Deploy NFTs using deploy_nft (requires name and symbol)
3. Request testnet funds using request_faucet_funds (no arguments needed)
4. Check wallet balances using get_balance (requires address)

You cannot:
1. Send or transfer ETH (this is disabled for security)

Always explain what you're doing before performing any action.

For queries about the latest Base Sepolia block, MUST call the function every time to receive latest data."""