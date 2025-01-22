"""Script to manage CDP wallets with proper persistence and security."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from cdp import Cdp, Wallet, MnemonicSeedPhrase

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

def configure_cdp():
    """Configure CDP SDK with API credentials."""
    config = load_cdp_config()
    logger.info("Configuring CDP SDK...")
    Cdp.configure(config["name"], config["privateKey"])
    logger.info("CDP SDK configured successfully")

def create_developer_wallet(network_id: str = "base-sepolia") -> Wallet:
    """Create a new developer-managed (1-of-1) wallet."""
    # Ensure CDP is configured
    configure_cdp()
    
    logger.info(f"Creating new wallet on {network_id}...")
    wallet = Wallet.create(network_id=network_id)
    
    logger.info(f"Created wallet:")
    logger.info(f"Wallet ID: {wallet.id}")
    logger.info(f"Network: {wallet.network_id}")
    logger.info(f"Default Address: {wallet.default_address.address_id}")
    
    return wallet

def save_wallet_securely(wallet: Wallet, encrypt: bool = True):
    """Save wallet data securely."""
    try:
        # Export wallet data (includes seed and ID)
        wallet_data = wallet.export_data().to_dict()
        
        # Save encrypted seed file (for development)
        seed_path = Path(__file__).parent.parent / "dev_wallet_seed.json"
        wallet.save_seed(str(seed_path), encrypt=encrypt)
        logger.info(f"Development seed file saved to: {seed_path}")
        
        # Save wallet credentials (excluding sensitive data) for reference
        credentials = {
            "wallet_id": wallet.id,
            "network": wallet.network_id,
            "default_address": wallet.default_address.address_id,
            "addresses": [addr.address_id for addr in wallet.addresses]
        }
        
        creds_path = Path(__file__).parent.parent / "wallet_credentials.json"
        with open(creds_path, "w") as f:
            json.dump(credentials, f, indent=2)
        logger.info(f"Wallet credentials saved to: {creds_path}")
        
        # Create production environment template
        env_template = f"""# Production Environment Variables
CDP_API_KEY_NAME="{os.getenv('CDP_API_KEY_NAME', 'your-cdp-key-name')}"
CDP_API_KEY_PRIVATE_KEY="{os.getenv('CDP_API_KEY_PRIVATE_KEY', 'your-cdp-private-key')}"
OPENAI_API_KEY="{os.getenv('OPENAI_API_KEY', 'your-openai-key')}"
NETWORK_ID="{wallet.network_id}"

# CDP Wallet Configuration
CDP_WALLET_ID="{wallet.id}"
"""
        
        env_path = Path(__file__).parent.parent / ".env.production"
        with open(env_path, "w") as f:
            f.write(env_template)
        logger.info(f"Production environment template saved to: {env_path}")
        
        return wallet_data
        
    except Exception as e:
        logger.error(f"Error saving wallet data: {str(e)}")
        raise

def load_existing_wallet() -> Optional[Wallet]:
    """Load an existing wallet from saved credentials."""
    try:
        # Ensure CDP is configured
        configure_cdp()
        
        seed_path = Path(__file__).parent.parent / "dev_wallet_seed.json"
        if not seed_path.exists():
            logger.info("No existing wallet seed found")
            return None
            
        # First fetch the unhydrated wallet
        creds_path = Path(__file__).parent.parent / "wallet_credentials.json"
        with open(creds_path) as f:
            credentials = json.load(f)
            
        wallet = Wallet.fetch(credentials["wallet_id"])
        
        # Hydrate the wallet with the saved seed
        wallet.load_seed(str(seed_path))
        
        logger.info(f"Loaded existing wallet:")
        logger.info(f"Wallet ID: {wallet.id}")
        logger.info(f"Network: {wallet.network_id}")
        logger.info(f"Default Address: {wallet.default_address.address_id}")
        
        return wallet
        
    except Exception as e:
        logger.error(f"Error loading wallet: {str(e)}")
        return None

def import_external_wallet(mnemonic: str, network_id: str = "base-sepolia") -> Wallet:
    """Import an external wallet using a mnemonic seed phrase."""
    try:
        # Ensure CDP is configured
        configure_cdp()
        
        wallet = Wallet.import_wallet(MnemonicSeedPhrase(mnemonic), network_id=network_id)
        logger.info(f"Imported external wallet:")
        logger.info(f"Wallet ID: {wallet.id}")
        logger.info(f"Network: {wallet.network_id}")
        logger.info(f"Default Address: {wallet.default_address.address_id}")
        return wallet
    except Exception as e:
        logger.error(f"Error importing wallet: {str(e)}")
        raise

def main():
    """Main function to manage wallets."""
    # Try to load existing wallet first
    wallet = load_existing_wallet()
    
    if not wallet:
        # Create new wallet if none exists
        wallet = create_developer_wallet()
        wallet_data = save_wallet_securely(wallet)
        
        logger.info("\nIMPORTANT: Wallet data has been saved!")
        logger.info("For production:")
        logger.info("1. Keep the seed file secure")
        logger.info("2. Use environment variables for wallet configuration")
        logger.info("3. Consider using Coinbase-Managed (2-of-2) wallets for additional security")
    
    # Request testnet funds
    logger.info("\nRequesting testnet funds...")
    
    # Request ETH
    eth_tx = wallet.faucet()
    eth_tx.wait()
    logger.info(f"ETH faucet transaction: {eth_tx.transaction_hash}")
    
    # Request USDC
    usdc_tx = wallet.faucet(asset_id="usdc")
    usdc_tx.wait()
    logger.info(f"USDC faucet transaction: {usdc_tx.transaction_hash}")
    
    # Show balances
    logger.info("\nCurrent balances:")
    for asset, balance in wallet.balances().items():
        logger.info(f"{asset}: {balance}")

if __name__ == "__main__":
    main() 