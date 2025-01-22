import re
from agent_backend.constants import DEPLOY_TOKEN, DEPLOY_NFT
from agent_backend.db.tokens import add_token
from agent_backend.db.nfts import add_nft

def handle_agent_action(agent_action: str, content: str) -> None:
    """
    Adds handling for the agent action.
    In our sample app, we just add deployed tokens and NFTs to the database.
    """
    if agent_action == DEPLOY_TOKEN:
        # Search for contract address from output
        address = re.search(r'0x[a-fA-F0-9]{40}', content).group()
        # Add token to database
        add_token(address)
    if agent_action == DEPLOY_NFT:
        # Search for contract address from output
        address = re.search(r'0x[a-fA-F0-9]{40}', content).group()
        # Add NFT to database
        add_nft(address)