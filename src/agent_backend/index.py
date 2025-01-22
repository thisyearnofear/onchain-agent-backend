from flask import Flask, request, Response, stream_with_context, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

from agent_backend.agent.initialize_agent import initialize_agent
from agent_backend.agent.run_agent import run_agent
from agent_backend.db.setup import setup
from agent_backend.db.tokens import get_tokens
from agent_backend.db.nfts import get_nfts

load_dotenv()
app = Flask(__name__)
CORS(app)

# Setup SQLite tables
setup()

# Initialize the agent
agent_executor = initialize_agent()
app.agent_executor = agent_executor

# Interact with the agent
@app.route("/api/chat", methods=['POST'])
def chat():
    try:
        data = request.get_json()
        # Parse the user input from the request
        input = data['input']
        # Use the conversation_id passed in the request for conversation memory
        config = {"configurable": {"thread_id": data['conversation_id']}}
        return Response(
            stream_with_context(run_agent(input, app.agent_executor, config)),
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
        return jsonify({'error': 'An unexpected error occurred'}), 500
    
# Retrieve a list of tokens the agent has deployed
@app.route("/tokens", methods=['GET'])
def tokens():
    try:
        tokens = get_tokens()
        return jsonify({'tokens': tokens}), 200
    except Exception as e:
        app.logger.error(f"Unexpected error in tokens endpoint: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
    
# Retrieve a list of tokens the agent has deployed
@app.route("/nfts", methods=['GET'])
def nfts():
    try:
        nfts = get_nfts()
        return jsonify({'nfts': nfts}), 200
    except Exception as e:
        app.logger.error(f"Unexpected error in nfts endpoint: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == "__main__":
    setup()
    app.run(host="0.0.0.0", port=int(os.environ.get("FLASK_RUN_PORT", 5000)))
    