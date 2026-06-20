"""0G Storage integration — stores agent configs and memory on decentralized storage."""

import os
import json
import hashlib
import requests
from datetime import datetime, timezone


STORAGE_INDEXER = os.getenv("OG_STORAGE_INDEXER", "https://indexer-storage-turbo.0g.ai")
FLOW_CONTRACT = "0x62D4144dB0F0a6fBBaeb6296c785C71B3D57C526"


def _hash_data(data: dict) -> str:
    """Generate a SHA-256 hash of the data for integrity verification."""
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def store_agent_config(agent_id: str, config: dict) -> dict:
    """
    Store an agent's configuration on 0G Storage.
    
    This stores the agent's system prompt, tools, personality, and metadata
    on 0G's decentralized storage network. Returns a storage receipt with
    the data hash for on-chain reference.
    """
    payload = {
        "agent_id": agent_id,
        "type": "agent_config",
        "data": config,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": 1,
    }
    data_hash = _hash_data(payload)
    payload["integrity_hash"] = data_hash

    # In production, this would use the 0G Storage SDK to submit to the flow contract.
    # For the demo, we store locally and simulate the on-chain receipt.
    storage_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
    os.makedirs(storage_dir, exist_ok=True)

    filepath = os.path.join(storage_dir, f"{agent_id}_config.json")
    with open(filepath, "w") as f:
        json.dump(payload, f, indent=2)

    return {
        "status": "stored",
        "agent_id": agent_id,
        "data_hash": data_hash,
        "storage_path": filepath,
        "indexer_url": f"{STORAGE_INDEXER}/file/{data_hash}",
        "timestamp": payload["timestamp"],
    }


def store_agent_memory(agent_id: str, memory_entry: dict) -> dict:
    """
    Append a memory entry to an agent's memory store on 0G Storage.
    
    Memory entries represent conversation history, learned preferences,
    and behavioral adaptations that persist across sessions.
    """
    storage_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
    os.makedirs(storage_dir, exist_ok=True)

    memory_file = os.path.join(storage_dir, f"{agent_id}_memory.json")

    # Load existing memory
    memories = []
    if os.path.exists(memory_file):
        with open(memory_file, "r") as f:
            memories = json.load(f)

    entry = {
        **memory_entry,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "index": len(memories),
    }
    memories.append(entry)

    # Keep last 100 memory entries
    if len(memories) > 100:
        memories = memories[-100:]

    data_hash = _hash_data({"agent_id": agent_id, "memories": memories})

    with open(memory_file, "w") as f:
        json.dump(memories, f, indent=2)

    return {
        "status": "stored",
        "agent_id": agent_id,
        "memory_count": len(memories),
        "data_hash": data_hash,
    }


def load_agent_config(agent_id: str) -> dict | None:
    """Load an agent's configuration from 0G Storage."""
    storage_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
    filepath = os.path.join(storage_dir, f"{agent_id}_config.json")

    if not os.path.exists(filepath):
        return None

    with open(filepath, "r") as f:
        return json.load(f)


def load_agent_memory(agent_id: str) -> list[dict]:
    """Load an agent's memory history from 0G Storage."""
    storage_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
    memory_file = os.path.join(storage_dir, f"{agent_id}_memory.json")

    if not os.path.exists(memory_file):
        return []

    with open(memory_file, "r") as f:
        return json.load(f)


def list_stored_agents() -> list[dict]:
    """List all agents stored in 0G Storage."""
    storage_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
    if not os.path.exists(storage_dir):
        return []

    agents = []
    for filename in os.listdir(storage_dir):
        if filename.endswith("_config.json"):
            agent_id = filename.replace("_config.json", "")
            config = load_agent_config(agent_id)
            if config:
                agents.append({
                    "agent_id": agent_id,
                    "name": config.get("data", {}).get("name", "Unnamed"),
                    "type": config.get("data", {}).get("type", "custom"),
                    "stored_at": config.get("timestamp"),
                    "data_hash": config.get("integrity_hash"),
                })

    return agents
