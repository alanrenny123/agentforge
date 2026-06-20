"""AgentForge — Build & Deploy AI Agents on 0G. Main Flask application."""

import os
import json
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, Response, stream_with_context

load_dotenv()

from core import agents, compute, storage, chain

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")


# ─── Pages ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─── API: Templates ──────────────────────────────────────────────────────────

@app.route("/api/templates")
def api_templates():
    """Return available agent templates."""
    templates = agents.get_templates()
    result = []
    for tid, t in templates.items():
        result.append({
            "id": tid,
            "name": t["name"],
            "type": t["type"],
            "description": t["description"],
            "tools": t["tools"],
            "personality": t["personality"],
        })
    return jsonify(result)


# ─── API: Agent CRUD ─────────────────────────────────────────────────────────

@app.route("/api/agents", methods=["GET"])
def api_list_agents():
    """List all agents."""
    return jsonify(agents.list_agents())


@app.route("/api/agents", methods=["POST"])
def api_create_agent():
    """Create a new agent."""
    data = request.json or {}
    result = agents.create_agent(
        template_id=data.get("template_id", "custom"),
        name=data.get("name"),
        system_prompt=data.get("system_prompt"),
        personality=data.get("personality"),
        tools=data.get("tools"),
        owner_address=data.get("owner_address"),
    )
    return jsonify(result), 201


@app.route("/api/agents/<agent_id>", methods=["GET"])
def api_get_agent(agent_id):
    """Get agent details."""
    info = agents.get_agent_info(agent_id)
    if info.get("status") == "not_found":
        return jsonify(info), 404
    return jsonify(info)


# ─── API: Chat ───────────────────────────────────────────────────────────────

@app.route("/api/agents/<agent_id>/chat", methods=["POST"])
def api_chat(agent_id):
    """Send a message to an agent (non-streaming)."""
    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Message is required"}), 400

    api_key = data.get("api_key", "").strip() or None
    result = agents.chat_with_agent(agent_id, message, api_key=api_key)
    if result.get("status") == "error":
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/agents/<agent_id>/chat/stream", methods=["POST"])
def api_chat_stream(agent_id):
    """Send a message to an agent (streaming SSE)."""
    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Message is required"}), 400

    api_key = data.get("api_key", "").strip() or None

    def generate():
        for chunk in agents.chat_with_agent_streaming(agent_id, message, api_key=api_key):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ─── API: 0G Services Status ────────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    """Check all 0G service connections."""
    return jsonify({
        "compute": compute.test_connection(),
        "chain": chain.get_chain_status(),
        "storage": {"status": "ready", "indexer": os.getenv("OG_STORAGE_INDEXER")},
    })


@app.route("/api/models")
def api_models():
    """List available models on 0G Compute."""
    try:
        return jsonify(compute.list_models())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
