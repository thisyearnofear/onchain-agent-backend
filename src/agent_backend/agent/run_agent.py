from typing import Iterator
from langchain_core.messages import HumanMessage

from agent_backend.constants import EVENT_TYPE_AGENT, EVENT_TYPE_TOOLS, EVENT_TYPE_ERROR
from agent_backend.utils import format_sse
from agent_backend.agent.handle_agent_action import handle_agent_action

def run_agent(input, agent_executor, config) -> Iterator[str]:
    """Run the agent and yield formatted SSE messages"""
    try:
        print(f"Running agent with input: {input}")  # Debug log
        for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=input)]}, config
        ):
            print(f"Raw chunk: {chunk}")  # Debug raw chunk
            
            # Handle the new output format
            if "output" in chunk:
                content = chunk["output"]
                if content:
                    # Split content into paragraphs
                    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                    
                    # For numbered lists, split on number patterns
                    if any(p.strip().startswith(str(i)+'.') for i in range(1,10) for p in paragraphs):
                        new_paragraphs = []
                        for p in paragraphs:
                            # Split numbered points into separate messages
                            if p.count('\n') > 2:  # If paragraph has multiple lines
                                points = [point.strip() for point in p.split('\n') if point.strip()]
                                new_paragraphs.extend(points)
                            else:
                                new_paragraphs.append(p)
                        paragraphs = new_paragraphs
                    
                    # Send each paragraph as a separate message
                    for paragraph in paragraphs:
                        print(f"Agent response paragraph: {paragraph}")  # Debug log
                        formatted = format_sse(paragraph, EVENT_TYPE_AGENT)
                        print(f"Formatted SSE message: {formatted}")  # Debug formatted message
                        yield formatted
            
            # Keep existing tool handling
            elif "tools" in chunk:
                name = chunk["tools"]["messages"][0].name
                content = chunk["tools"]["messages"][0].content
                if content:
                    print(f"Tool response: {content}")  # Debug log
                    formatted = format_sse(content, EVENT_TYPE_TOOLS, functions=[name])
                    print(f"Formatted SSE message: {formatted}")  # Debug formatted message
                    yield formatted
                    handle_agent_action(name, content)
    except Exception as e:
        print(f"Agent error: {str(e)}")  # Debug log
        formatted = format_sse(f"Error: {str(e)}", EVENT_TYPE_ERROR)
        print(f"Formatted error message: {formatted}")  # Debug formatted message
        yield formatted