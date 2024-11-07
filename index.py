from flask import Flask, request, Response, stream_with_context, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from agent.initialize_agent import initialize_agent
from agent.run_agent import run_agent

load_dotenv()
app = Flask(__name__)
CORS(app)

# Initialize the agent
agent_executor, config = initialize_agent()
app.agent_executor = agent_executor
app.agent_config = config


@app.route("/api/chat", methods=['POST'])
def chat():
    try:
        data = request.get_json()

        return Response(
            stream_with_context(run_agent(data['input'], app.agent_executor, app.agent_config)),
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

if __name__ == "__main__":
    app.run()
    