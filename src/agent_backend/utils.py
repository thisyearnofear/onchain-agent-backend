"""Utility functions for the application."""

import json
from typing import List, Optional

def format_sse(data: str, event: str, functions: Optional[List[str]] = None) -> str:
    """Format data for Server-Sent Events (SSE)."""
    message = {
        "data": data,
        "functions": functions or []
    }
    return f"event: {event}\ndata: {json.dumps(message)}\n\n"