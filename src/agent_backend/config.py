from typing import Dict, Any

def get_settings() -> Dict[str, Any]:
    """Get the application settings."""
    return {
        "network_id": "base-sepolia",  # Default network ID
        "openai_api_key": None,  # Will be loaded from environment variable
    } 