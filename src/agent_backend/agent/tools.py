from typing import List
from langchain.tools import BaseTool

def get_tools() -> List[BaseTool]:
    """Get the list of tools available to the agent."""
    return []  # For now, return an empty list of tools 