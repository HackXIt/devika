"""
    DO NOT REARRANGE THE ORDER OF THE FUNCTION CALLS AND VARIABLE DECLARATIONS
    AS IT MAY CAUSE IMPORT ERRORS AND OTHER ISSUES
"""
from gevent import monkey
monkey.patch_all()
from src.init import init_devika
init_devika()

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from src.socket_instance import socketio, emit_agent
import os
import logging
from threading import Thread
import tiktoken

from src.apis.project import project_bp
from src.config import Config
from src.logger import Logger
from src.project import ProjectManager
from src.state import AgentState
from src.agents import Agent
from src.llm import LLM

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins":
                             [
                                "https://localhost:3000",
                                "http://localhost:3000",
                            ]}}) 
app.register_blueprint(project_bp)
socketio.init_app(app)

log = logging.getLogger("werkzeug")
log.disabled = True

TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")

os.environ["TOKENIZERS_PARALLELISM"] = "false"

manager = ProjectManager()
AgentState = AgentState()
config = Config()
logger = Logger()

# initial socket connection
@socketio.on('socket_connect')
def test_connect(data):
    print("Socket connected :: ", data)
    emit_agent("socket_response", {"data": "Server Connected"})

# Fetch initial data (formerly /api/data)
@socketio.on('fetch_data')
def fetch_data():
    try:
        project = manager.get_project_list()
        models = LLM().list_models()
        search_engines = ["Bing", "Google", "DuckDuckGo"]
        emit('fetch_data_response', {
            "projects": project,
            "models": models,
            "search_engines": search_engines
        })
    except Exception as e:
        emit('fetch_data_error', str(e))

# Fetch messages (formerly /api/messages)
@socketio.on('fetch_messages')
def fetch_messages(data):
    try:
        project_name = data.get("project_name")
        messages = manager.get_messages(project_name)
        emit('fetch_messages_response', {"messages": messages})
    except Exception as e:
        emit('fetch_messages_error', str(e))

# Main WebSocket message handler
@socketio.on('user_message')
def handle_message(data):
    try:
        logger.info(f"User message: {data}")
        message = data.get('message')
        base_model = data.get('base_model')
        project_name = data.get('project_name')
        search_engine = data.get('search_engine').lower()

        agent = Agent(base_model=base_model, search_engine=search_engine)

        state = AgentState.get_latest_state(project_name)
        if not state:
            thread = Thread(target=lambda: agent.execute(message, project_name))
            thread.start()
        else:
            if AgentState.is_agent_completed(project_name):
                thread = Thread(target=lambda: agent.subsequent_execute(message, project_name))
                thread.start()
            else:
                emit_agent("info", {"type": "warning", "message": "previous agent hasn't completed its task."})
                last_state = AgentState.get_latest_state(project_name)
                if last_state["agent_is_active"] or not last_state["completed"]:
                    thread = Thread(target=lambda: agent.execute(message, project_name))
                    thread.start()
                else:
                    thread = Thread(target=lambda: agent.subsequent_execute(message, project_name))
                    thread.start()
    except Exception as e:
        emit('user_message_error', str(e))

# Check if agent is active (formerly /api/is-agent-active)
@socketio.on('is_agent_active')
def is_agent_active(data):
    try:
        project_name = data.get("project_name")
        is_active = AgentState.is_agent_active(project_name)
        emit('is_agent_active_response', {"is_active": is_active})
    except Exception as e:
        emit('is_agent_active_error', str(e))

# Get agent state (formerly /api/get-agent-state)
@socketio.on('get_agent_state')
def get_agent_state(data):
    try:
        project_name = data.get("project_name")
        agent_state = AgentState.get_latest_state(project_name)
        emit('get_agent_state_response', {"state": agent_state})
    except Exception as e:
        emit('get_agent_state_error', str(e))

# Get browser snapshot (formerly /api/get-browser-snapshot)
@socketio.on('get_browser_snapshot')
def get_browser_snapshot(data):
    try:
        snapshot_path = data.get("snapshot_path")
        emit('get_browser_snapshot_response', send_file(snapshot_path, as_attachment=True))
    except Exception as e:
        emit('get_browser_snapshot_error', str(e))

# Get browser session (formerly /api/get-browser-session)
@socketio.on('get_browser_session')
def get_browser_session(data):
    try:
        project_name = data.get("project_name")
        agent_state = AgentState.get_latest_state(project_name)
        browser_session = agent_state["browser_session"] if agent_state else None
        emit('get_browser_session_response', {"browser_session": browser_session})
    except Exception as e:
        emit('get_browser_session_error', str(e))

# Get terminal session (formerly /api/get-terminal-session)
@socketio.on('get_terminal_session')
def get_terminal_session(data):
    try:
        project_name = data.get("project_name")
        agent_state = AgentState.get_latest_state(project_name)
        terminal_state = agent_state["terminal_session"] if agent_state else None
        emit('get_terminal_session_response', {"terminal_state": terminal_state})
    except Exception as e:
        emit('get_terminal_session_error', str(e))

# Run code (formerly /api/run-code)
@socketio.on('run_code')
def run_code(data):
    try:
        project_name = data.get("project_name")
        code = data.get("code")
        # TODO: Implement code execution logic
        emit('run_code_response', {"message": "Code execution started"})
    except Exception as e:
        emit('run_code_error', str(e))

# Calculate tokens (formerly /api/calculate-tokens)
@socketio.on('calculate_tokens')
def calculate_tokens(data):
    try:
        prompt = data.get("prompt")
        tokens = len(TIKTOKEN_ENC.encode(prompt))
        emit('calculate_tokens_response', {"token_usage": tokens})
    except Exception as e:
        emit('calculate_tokens_error', str(e))

# Get token usage (formerly /api/token-usage)
@socketio.on('get_token_usage')
def get_token_usage(data):
    try:
        project_name = data.get("project_name")
        token_count = AgentState.get_latest_token_usage(project_name)
        emit('get_token_usage_response', {"token_usage": token_count})
    except Exception as e:
        emit('get_token_usage_error', str(e))

# Fetch logs (formerly /api/logs)
@socketio.on('fetch_logs')
def fetch_logs():
    try:
        log_file = logger.read_log_file()
        emit('fetch_logs_response', {"logs": log_file})
    except Exception as e:
        emit('fetch_logs_error', str(e))

# Get and set settings (formerly /api/settings)
@socketio.on('get_settings')
def get_settings():
    try:
        configs = config.get_config()
        emit('get_settings_response', {"settings": configs})
    except Exception as e:
        emit('get_settings_error', str(e))

@socketio.on('set_settings')
def set_settings(data):
    try:
        config.update_config(data)
        emit('set_settings_response', {"message": "Settings updated"})
    except Exception as e:
        emit('set_settings_error', str(e))

# Server status (formerly /api/status)
@socketio.on('status')
def status():
    try:
        emit('status_response', {"status": "server is running!"})
    except Exception as e:
        emit('status_error', str(e))

if __name__ == "__main__":
    logger.info("Devika is up and running!")
    socketio.run(app, debug=False, port=1337, host="0.0.0.0")
