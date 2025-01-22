"""Utility functions for the application."""

import json
from typing import List, Optional

def format_sse(content: str, event_type: str, functions: Optional[List[str]] = None) -> str:
    """Format a message for SSE transmission"""
    data = {
        "type": event_type,
        "content": content,
    }
    if functions:
        data["functions"] = functions
    
    return f"data: {json.dumps(data)}\n\n"