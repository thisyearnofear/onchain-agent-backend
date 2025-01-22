"""Script to generate a CDP wallet and save its credentials."""

import json
import os
from pathlib import Path
from cdp import Cdp
from cdp_langchain.utils import CdpAgentkitWrapper
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_cdp_config():
    """Load CDP configuration from JSON file."""
    current_dir = Path(__file__).parent.parent
    json_path = current_dir / "cdp_api_key.json"
    
    with open(json_path) as f:
        config = json.load(f)
    
    return config

def generate_wallet():
    """Generate a new CDP wallet and save its credentials."""
    try:
        # Load CDP config
        config = load_cdp_config()
        
        # Initialize CDP SDK
        values = {
            "cdp_api_key_name": config['name'],
            "cdp_api_key_private_key": config['privateKey']
        }
        
        logger.info("Initializing CDP SDK...")
        agentkit = CdpAgentkitWrapper(**values)
        
        # Generate wallet
        wallet = agentkit.wallet
        logger.info(f"Generated new wallet:")
        logger.info(f"Wallet ID: {wallet.id}")
        logger.info(f"Network: {wallet.network_id}")
        logger.info(f"Default Address: {wallet.default_address.address_id}")
        
        # Save credentials to a secure file
        credentials = {
            "wallet_id": wallet.id,
            "network": wallet.network_id,
            "default_address": wallet.default_address.address_id,
            # Add any additional wallet info that's available
            **{k: str(v) for k, v in vars(wallet).items() if not k.startswith('_')}
        }
        
        output_path = Path(__file__).parent.parent / "wallet_credentials.json"
        with open(output_path, "w") as f:
            json.dump(credentials, f, indent=2)
        
        logger.info(f"\nCredentials saved to: {output_path}")
        logger.info("\nIMPORTANT: Please save these credentials in a secure location!")
        logger.info("You will need them to set up the production environment.")
        
        # Create .env.production template
        env_template = f"""# Production Environment Variables
CDP_API_KEY_NAME="{config['name']}"
CDP_API_KEY_PRIVATE_KEY="{config['privateKey']}"
OPENAI_API_KEY="{os.getenv('OPENAI_API_KEY', 'your-openai-key')}"
NETWORK_ID="base-sepolia"

# CDP Wallet Configuration
CDP_WALLET_ID="{wallet.id}"
# Add CDP_WALLET_SEED when available
"""
        
        env_path = Path(__file__).parent.parent / ".env.production"
        with open(env_path, "w") as f:
            f.write(env_template)
        
        logger.info(f"\nProduction environment template saved to: {env_path}")
        
    except Exception as e:
        logger.error(f"Error generating wallet: {str(e)}")
        raise

if __name__ == "__main__":
    generate_wallet() 