from typing import Iterator
from langchain_core.messages import HumanMessage

from agent_backend.constants import EVENT_TYPE_AGENT, EVENT_TYPE_TOOLS, EVENT_TYPE_ERROR
from agent_backend.utils import format_sse
from agent_backend.agent.handle_agent_action import handle_agent_action

def run_agent(input, agent_executor, config) -> Iterator[str]:
    """Run the agent and yield formatted SSE messages"""
    try:
        for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=input)]}, config
        ):
            if "agent" in chunk:
                content = chunk["agent"]["messages"][0].content
                if content:
                    yield format_sse(content, EVENT_TYPE_AGENT)
            elif "tools" in chunk:
                name = chunk["tools"]["messages"][0].name
                content = chunk["tools"]["messages"][0].content
                if content:
                    yield format_sse(content, EVENT_TYPE_TOOLS, functions=[name])
                    handle_agent_action(name, content)
    except Exception as e:
        yield format_sse(f"Error: {str(e)}", EVENT_TYPE_ERROR)