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

# Initialize these as None first
agent_executor = None
db_initialized = False

def init_app():
    """Initialize the application."""
    global agent_executor, db_initialized
    
    if not db_initialized:
        logger.info("Setting up database...")
        setup_database()
        logger.info("Database setup complete")
        db_initialized = True
    
    if agent_executor is None:
        logger.info("Starting agent initialization...")
        agent_executor = initialize_agent()
        logger.info("Agent initialization complete")

@app.route('/health')
def health():
    """Health check endpoint."""
    # Initialize if not already done
    if not db_initialized or agent_executor is None:
        try:
            init_app()
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return jsonify({
                "status": "unhealthy",
                "database": "unknown",
                "agent": f"failed: {str(e)}",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }), 500
    
    # Check database connection
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"failed: {str(e)}"
    
    # Check agent status
    agent_status = "initialized" if agent_executor else "not initialized"
    
    return jsonify({
        "status": "healthy" if db_status == "connected" and agent_status == "initialized" else "unhealthy",
        "database": db_status,
        "agent": agent_status,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint."""
    # Initialize if not already done
    if not db_initialized or agent_executor is None:
        try:
            init_app()
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return jsonify({"error": f"Failed to initialize: {str(e)}"}), 500
    
    try:
        data = request.json
        if not data or 'input' not in data:
            return jsonify({"error": "Missing required field: input"}), 400
        
        response = agent_executor.invoke({"input": data['input']})
        return jsonify({"response": response['output']})
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return jsonify({"error": str(e)}), 500

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

if __name__ == '__main__':
    # Initialize on startup when running directly
    init_app()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001)))