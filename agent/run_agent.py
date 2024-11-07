import re
from typing import Iterator
from langchain_core.messages import HumanMessage
import constants
from utils import format_sse
from db.tokens import add_token
from db.nfts import add_nft

def run_agent(input, agent_executor, config) -> Iterator[str]:
    """Run the agent and yield formatted SSE messages"""
    try:
        for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=input)]}, config
        ):
            if "agent" in chunk:
                content = chunk["agent"]["messages"][0].content
                if content:
                    yield format_sse(content, constants.EVENT_TYPE_AGENT)
            elif "tools" in chunk:
                name = chunk["tools"]["messages"][0].name
                content = chunk["tools"]["messages"][0].content
                if content:
                    yield format_sse(content, constants.EVENT_TYPE_TOOLS, functions=[name])
                if name == constants.DEPLOY_TOKEN:
                    # Search for contract address from output
                    address = re.search(r'0x[a-fA-F0-9]{40}', content).group()
                    # Add token to database
                    add_token(address)
                if name == constants.DEPLOY_NFT:
                    # Search for contract address from output
                    address = re.search(r'0x[a-fA-F0-9]{40}', content).group()
                    # Add NFT to database
                    add_nft(address)
    except Exception as e:
        yield format_sse(f"Error: {str(e)}", constants.EVENT_TYPE_ERROR)