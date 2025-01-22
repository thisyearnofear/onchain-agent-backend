from flask import Flask, request, Response, stream_with_context, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import ValidationError
from dotenv import load_dotenv
import os
import json
import time
from datetime import datetime
from sqlalchemy import text

from agent_backend.agent.initialize_agent import initialize_agent
from agent_backend.agent.run_agent import run_agent
from agent_backend.db.setup import setup, get_engine
from agent_backend.db.tokens import get_tokens
from agent_backend.db.nfts import get_nfts
from agent_backend.schemas import chat_request_schema

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

# Setup SQLite tables
setup()

# Initialize the agent
agent_executor = initialize_agent()
app.agent_executor = agent_executor

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
                for chunk in run_agent(validated_data['input'], app.agent_executor, {"configurable": {"thread_id": validated_data['conversation_id']}}):
                    if chunk.strip():
                        print(f"Sending SSE message: {chunk}")  # Debug log
                        yield chunk
            except Exception as e:
                # Handle any errors during generation
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
        app.logger.info("Attempting database connection check...")
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            app.logger.info("Database connection successful")
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": "production" if os.getenv('RENDER') else "development"
        }), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "environment": "production" if os.getenv('RENDER') else "development"
        }), 500

if __name__ == "__main__":
    setup()
    app.run(host="0.0.0.0", port=int(os.environ.get("FLASK_RUN_PORT", 5000)))