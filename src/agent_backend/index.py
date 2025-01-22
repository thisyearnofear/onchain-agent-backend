from flask import Flask, request, Response, stream_with_context, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import ValidationError
from dotenv import load_dotenv
import os
import json
import time
import threading
from datetime import datetime
from sqlalchemy import text
import concurrent.futures
import logging

from agent_backend.agent.initialize_agent import initialize_agent
from agent_backend.agent.run_agent import run_agent
from agent_backend.db.setup import setup_database, get_engine
from agent_backend.db.tokens import get_tokens
from agent_backend.db.nfts import get_nfts
from agent_backend.schemas import chat_request_schema
from agent_backend.config import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__)
CORS(app)

# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

@app.before_first_request
def setup():
    """Set up the application before the first request."""
    logger.info("Setting up database...")
    setup_database()
    logger.info("Database setup complete")
    
    logger.info("Starting agent initialization...")
    global agent_executor
    agent_executor = initialize_agent()
    logger.info("Agent initialization complete")

# Initialize the agent in a background thread with timeout
agent_executor = None
initialization_error = None
initialization_complete = threading.Event()

def init_agent():
    global agent_executor, initialization_error
    try:
        app.logger.info("Starting agent initialization...")
        agent_executor = initialize_agent()
        app.logger.info("Agent initialization complete")
        initialization_complete.set()
    except Exception as e:
        app.logger.error(f"Failed to initialize agent: {str(e)}")
        initialization_error = str(e)
        initialization_complete.set()

# Start initialization in a background thread
init_thread = threading.Thread(target=init_agent)
init_thread.daemon = True  # Make thread daemon so it doesn't block shutdown
init_thread.start()

# Error handlers
@app.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handle marshmallow validation errors."""
    return jsonify({"error": "Validation error", "messages": error.messages}), 400

@app.errorhandler(429)
def handle_rate_limit_error(error):
    """Handle rate limit exceeded errors."""
    return jsonify({
        "error": "Rate limit exceeded",
        "message": str(error.description)
    }), 429

@app.errorhandler(500)
def handle_internal_error(error):
    """Handle internal server errors."""
    app.logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

# Interact with the agent
@app.route("/api/chat", methods=['GET', 'POST'])
@limiter.limit("100/day;30/hour;1/second")
def chat():
    # Check if initialization is complete
    if not initialization_complete.is_set():
        return jsonify({"error": "Agent is still initializing"}), 503
    
    # Check if initialization failed
    if initialization_error:
        return jsonify({"error": f"Agent initialization failed: {initialization_error}"}), 500
    
    # Check if agent is ready
    if not agent_executor:
        return jsonify({"error": "Agent is not properly initialized"}), 500
        
    if request.method == 'GET':
        def generate():
            while True:
                # Send a heartbeat every 15 seconds
                yield 'data: {"type": "heartbeat"}\n\n'
                time.sleep(15)
                
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Content-Type': 'text/event-stream',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
        
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        
        validated_data = chat_request_schema.load(data)
        
        def generate():
            try:
                for chunk in run_agent(validated_data['input'], agent_executor, {"configurable": {"thread_id": validated_data['conversation_id']}}):
                    if chunk.strip():
                        app.logger.debug(f"Sending SSE message: {chunk}")
                        yield chunk
            except Exception as e:
                app.logger.error(f"Error during agent execution: {str(e)}")
                error_data = {
                    "type": "error",
                    "content": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Content-Type': 'text/event-stream',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        app.logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Retrieve a list of tokens the agent has deployed
@app.route("/tokens", methods=['GET'])
@limiter.limit("1000/day;100/hour")
def tokens():
    try:
        tokens = get_tokens()
        return jsonify({'tokens': tokens}), 200
    except Exception as e:
        app.logger.error(f"Unexpected error in tokens endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
# Retrieve a list of tokens the agent has deployed
@app.route("/nfts", methods=['GET'])
@limiter.limit("1000/day;100/hour")
def nfts():
    try:
        nfts = get_nfts()
        return jsonify({'nfts': nfts}), 200
    except Exception as e:
        app.logger.error(f"Unexpected error in nfts endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
@limiter.exempt
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Check database connection
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Check agent initialization status
        agent_status = "initializing"
        if initialization_complete.is_set():
            if agent_executor:
                agent_status = "ready"
            elif initialization_error:
                agent_status = f"failed: {initialization_error}"
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "agent": agent_status,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

if __name__ == "__main__":
    setup()
    app.run(host="0.0.0.0", port=int(os.environ.get("FLASK_RUN_PORT", 5000)))