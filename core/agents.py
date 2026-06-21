"""Agent builder — creates, configures, and runs AI agents using 0G services."""

import uuid
import json
from datetime import datetime, timezone

from . import compute, storage, chain


# Pre-built agent templates
TEMPLATES = {
    "code_assistant": {
        "name": "Code Assistant",
        "type": "code_assistant",
        "description": "A helpful coding companion that writes, debugs, and explains code",
        "system_prompt": (
            "You are an expert software engineer and coding assistant. "
            "You help users write clean, efficient code in any language. "
            "When asked to code, you provide complete working solutions with comments. "
            "When debugging, you explain the root cause and suggest fixes. "
            "You follow best practices and modern conventions."
        ),
        "tools": ["code_generation", "debugging", "code_review"],
        "personality": "helpful, precise, educational",
    },
    "research_analyst": {
        "name": "Research Analyst",
        "type": "research_analyst",
        "description": "An analytical agent that researches topics and synthesizes information",
        "system_prompt": (
            "You are a meticulous research analyst. You analyze topics deeply, "
            "consider multiple perspectives, cite reasoning, and present balanced conclusions. "
            "You break complex topics into digestible insights. "
            "You distinguish between facts, inferences, and speculation. "
            "You ask clarifying questions when the scope is ambiguous."
        ),
        "tools": ["research", "analysis", "summarization"],
        "personality": "thorough, objective, insightful",
    },
    "creative_writer": {
        "name": "Creative Writer",
        "type": "creative_writer",
        "description": "A creative agent for storytelling, copywriting, and content creation",
        "system_prompt": (
            "You are a talented creative writer with a gift for vivid language and compelling narratives. "
            "You adapt your style to the request — formal for business, playful for social, "
            "dramatic for fiction. You use sensory details and strong verbs. "
            "You brainstorm freely and refine ruthlessly."
        ),
        "tools": ["writing", "brainstorming", "editing"],
        "personality": "imaginative, expressive, adaptable",
    },
    "data_guide": {
        "name": "Data Guide",
        "type": "data_guide",
        "description": "A data-savvy agent that helps with analysis, visualization, and insights",
        "system_prompt": (
            "You are a data analysis expert. You help users understand their data, "
            "suggest appropriate analyses, write queries and scripts, create visualizations, "
            "and explain statistical concepts clearly. You work with SQL, Python (pandas), "
            "and common BI tools. You always consider data quality and potential biases."
        ),
        "tools": ["data_analysis", "sql", "visualization"],
        "personality": "analytical, clear, methodical",
    },
    "custom": {
        "name": "Custom Agent",
        "type": "custom",
        "description": "Build your own agent from scratch",
        "system_prompt": "You are a helpful AI assistant.",
        "tools": [],
        "personality": "helpful",
    },
}


def get_templates() -> dict:
    """Return available agent templates."""
    return TEMPLATES


def create_agent(
    template_id: str = "custom",
    name: str = None,
    system_prompt: str = None,
    personality: str = None,
    tools: list[str] = None,
    owner_address: str = None,
) -> dict:
    """
    Create a new AI agent.
    
    1. Generate unique agent ID
    2. Build agent config from template + customizations
    3. Store config on 0G Storage
    4. (Optionally) mint Agent NFT on 0G Chain
    """
    template = TEMPLATES.get(template_id, TEMPLATES["custom"])
    agent_id = f"agent_{uuid.uuid4().hex[:12]}"

    config = {
        "name": name or template["name"],
        "type": template["type"],
        "description": template["description"],
        "system_prompt": system_prompt or template["system_prompt"],
        "personality": personality or template["personality"],
        "tools": tools or template["tools"],
        "model": "zai-org/GLM-5-FP8",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "owner_address": owner_address,
        "version": 1,
    }

    # Store on 0G Storage
    storage_receipt = storage.store_agent_config(agent_id, config)

    # Optionally mint NFT on 0G Chain
    mint_result = None
    if owner_address:
        mint_result = chain.mint_agent_nft(
            to_address=owner_address,
            agent_name=config["name"],
            system_prompt=config["system_prompt"],
            config_hash=storage_receipt["data_hash"],
        )

    return {
        "agent_id": agent_id,
        "config": config,
        "storage_receipt": storage_receipt,
        "mint_result": mint_result,
    }


def chat_with_agent(agent_id: str, user_message: str, api_key: str = None, provider: str = "0g", base_url: str = None, model_override: str = None) -> dict:
    """
    Send a message to an agent and get a response.
    
    1. Load agent config from 0G Storage
    2. Load recent memory
    3. Build context-aware system prompt
    4. Send to AI provider for inference
    5. Store the interaction in memory
    """
    # Load agent config
    stored = storage.load_agent_config(agent_id)
    if not stored:
        return {"status": "error", "error": f"Agent {agent_id} not found"}

    config = stored["data"]

    # Load memory for context
    memories = storage.load_agent_memory(agent_id)
    memory_context = ""
    if memories:
        recent = memories[-5:]  # Last 5 interactions
        memory_context = "\n\nPrevious interactions:\n"
        for m in recent:
            memory_context += f"- User: {m.get('user_message', '')[:100]}\n"
            memory_context += f"- You: {m.get('agent_response', '')[:100]}\n"

    # Build enhanced system prompt
    full_system_prompt = (
        f"{config['system_prompt']}\n\n"
        f"Personality: {config.get('personality', 'helpful')}\n"
        f"{memory_context}"
    )

    # Get response from AI provider
    # Only use explicit model_override; let compute layer use provider's default otherwise.
    # Agent config's stored model (e.g. "zai-org/GLM-5-FP8") is 0G-specific and
    # would cause "invalid model ID" on other providers.
    try:
        response = compute.chat_completion(
            system_prompt=full_system_prompt,
            user_message=user_message,
            model=model_override,
            api_key=api_key,
            provider=provider,
            base_url=base_url,
        )
    except Exception as e:
        return {"status": "error", "error": f"Compute error: {str(e)}"}

    # Store interaction in memory on 0G Storage
    storage.store_agent_memory(agent_id, {
        "user_message": user_message,
        "agent_response": response,
        "model": model_override or "provider-default",
    })

    return {
        "status": "success",
        "agent_id": agent_id,
        "agent_name": config["name"],
        "response": response,
        "model": model_override or "provider-default",
    }


def chat_with_agent_streaming(agent_id: str, user_message: str, api_key: str = None, provider: str = "0g", base_url: str = None, model_override: str = None):
    """Stream a response from an agent. Yields chunks of text."""
    stored = storage.load_agent_config(agent_id)
    if not stored:
        yield json.dumps({"error": f"Agent {agent_id} not found"})
        return

    config = stored["data"]
    memories = storage.load_agent_memory(agent_id)
    memory_context = ""
    if memories:
        recent = memories[-5:]
        memory_context = "\n\nPrevious interactions:\n"
        for m in recent:
            memory_context += f"- User: {m.get('user_message', '')[:100]}\n"
            memory_context += f"- You: {m.get('agent_response', '')[:100]}\n"

    full_system_prompt = (
        f"{config['system_prompt']}\n\n"
        f"Personality: {config.get('personality', 'helpful')}\n"
        f"{memory_context}"
    )

    full_response = ""
    try:
        for chunk in compute.chat_completion_streaming(
            system_prompt=full_system_prompt,
            user_message=user_message,
            model=model_override,
            api_key=api_key,
            provider=provider,
            base_url=base_url,
        ):
            full_response += chunk
            yield chunk
    except Exception as e:
        yield f"\n\n[Error: {str(e)}]"

    # Store after streaming completes
    storage.store_agent_memory(agent_id, {
        "user_message": user_message,
        "agent_response": full_response,
        "model": model_override or "provider-default",
    })


def get_agent_info(agent_id: str) -> dict:
    """Get full agent info including config, memory count, and chain status."""
    config = storage.load_agent_config(agent_id)
    if not config:
        return {"status": "not_found"}

    memories = storage.load_agent_memory(agent_id)

    return {
        "status": "found",
        "agent_id": agent_id,
        "config": config["data"],
        "storage_hash": config.get("integrity_hash"),
        "memory_count": len(memories),
        "created_at": config.get("timestamp"),
    }


def list_agents() -> list[dict]:
    """List all created agents."""
    return storage.list_stored_agents()
