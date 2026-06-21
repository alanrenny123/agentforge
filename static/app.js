/* ═══════════════════════════════════════════════════════════════════
   AgentForge — JavaScript
   ═══════════════════════════════════════════════════════════════════ */

// ─── State ──────────────────────────────────────────────────────────

let agents = [];
let currentAgentId = null;
let selectedTemplate = null;
let templates = [];
let isStreaming = false;

// ─── Provider & API Key Management ────────────────────────────────

const PROVIDER_INFO = {
    "0g":         { label: "0G Compute",     placeholder: "sk-...", helpUrl: "https://pc.0g.ai", helpText: "Get your API key at pc.0g.ai →", defaultModelHint: "Default: 0G's best available model" },
    "openrouter": { label: "OpenRouter",      placeholder: "sk-or-...", helpUrl: "https://openrouter.ai/keys", helpText: "Get your API key at openrouter.ai →", defaultModelHint: "Default: auto-selects best model" },
    "openai":     { label: "OpenAI",          placeholder: "sk-...", helpUrl: "https://platform.openai.com/api-keys", helpText: "Get your API key at platform.openai.com →", defaultModelHint: "Default: gpt-4o" },
    "anthropic":  { label: "Anthropic",       placeholder: "sk-ant-...", helpUrl: "https://console.anthropic.com/", helpText: "Get your API key at console.anthropic.com →", defaultModelHint: "Default: claude-sonnet-4-20250514" },
    "groq":       { label: "Groq (Free)",      placeholder: "gsk_...", helpUrl: "https://console.groq.com/keys", helpText: "FREE — no credit card needed. Get key at console.groq.com →", defaultModelHint: "Default: llama-3.3-70b-versatile" },
    "gemini":     { label: "Google Gemini (Free)", placeholder: "AIza...", helpUrl: "https://aistudio.google.com/apikey", helpText: "FREE — no credit card needed. Get key at aistudio.google.com →", defaultModelHint: "Default: gemini-2.5-flash" },
    "custom":     { label: "Custom Provider", placeholder: "Enter API key", helpUrl: "", helpText: "", defaultModelHint: "Enter model name and base URL" },
};

function getProvider() {
    return localStorage.getItem("agentforge_provider") || "0g";
}

function getApiKey() {
    return localStorage.getItem("agentforge_api_key") || "";
}

function getModel() {
    return localStorage.getItem("agentforge_model") || "";
}

function getBaseUrl() {
    return localStorage.getItem("agentforge_base_url") || "";
}

function showSettingsModal() {
    const provider = getProvider();
    document.getElementById("providerSelect").value = provider;
    document.getElementById("apiKeyInput").value = getApiKey();
    document.getElementById("modelInput").value = getModel();
    document.getElementById("baseUrlInput").value = getBaseUrl();
    document.getElementById("settingsStatus").innerHTML = "";
    onProviderChange();
    openModal("settingsModal");
}

function onProviderChange() {
    const provider = document.getElementById("providerSelect").value;
    const info = PROVIDER_INFO[provider] || PROVIDER_INFO["custom"];

    // Update API key placeholder and help link
    document.getElementById("apiKeyInput").placeholder = info.placeholder;
    const helpDiv = document.getElementById("apiKeyHelp");
    const link = document.getElementById("getApiKeyLink");
    if (info.helpUrl) {
        helpDiv.style.display = "block";
        link.href = info.helpUrl;
        link.textContent = info.helpText;
    } else {
        helpDiv.style.display = "none";
    }

    // Update model hint
    document.getElementById("modelHint").textContent = info.defaultModelHint;

    // Show/hide base URL for custom provider
    document.getElementById("baseUrlGroup").style.display = provider === "custom" ? "block" : "none";
}

function saveApiKey() {
    const provider = document.getElementById("providerSelect").value;
    const key = document.getElementById("apiKeyInput").value.trim();
    const model = document.getElementById("modelInput").value.trim();
    const baseUrl = document.getElementById("baseUrlInput").value.trim();

    if (!key) {
        document.getElementById("settingsStatus").innerHTML = 
            '<span style="color:var(--red);">⚠️ Please enter a key</span>';
        return;
    }
    if (provider === "custom" && !baseUrl) {
        document.getElementById("settingsStatus").innerHTML = 
            '<span style="color:var(--red);">⚠️ Custom provider requires a Base URL</span>';
        return;
    }

    localStorage.setItem("agentforge_provider", provider);
    localStorage.setItem("agentforge_api_key", key);
    localStorage.setItem("agentforge_model", model);
    localStorage.setItem("agentforge_base_url", baseUrl);

    document.getElementById("settingsStatus").innerHTML = 
        '<span style="color:var(--green);">✅ Saved! You can now chat with agents.</span>';
    updateApiKeyIndicator();
    setTimeout(() => closeModal("settingsModal"), 1200);
}

function clearApiKey() {
    localStorage.removeItem("agentforge_provider");
    localStorage.removeItem("agentforge_api_key");
    localStorage.removeItem("agentforge_model");
    localStorage.removeItem("agentforge_base_url");
    document.getElementById("apiKeyInput").value = "";
    document.getElementById("modelInput").value = "";
    document.getElementById("baseUrlInput").value = "";
    document.getElementById("settingsStatus").innerHTML = 
        '<span style="color:var(--text-muted);">Cleared. You\'ll need to enter credentials to chat.</span>';
    updateApiKeyIndicator();
}

function toggleApiKeyVisibility() {
    const input = document.getElementById("apiKeyInput");
    const btn = document.getElementById("toggleKeyBtn");
    if (input.type === "password") {
        input.type = "text";
        btn.textContent = "🙈";
    } else {
        input.type = "password";
        btn.textContent = "👁️";
    }
}

function updateApiKeyIndicator() {
    const indicator = document.getElementById("apiKeyIndicator");
    if (!indicator) return;
    const key = getApiKey();
    const provider = getProvider();
    if (key) {
        indicator.className = "api-key-indicator has-key";
        const info = PROVIDER_INFO[provider];
        indicator.title = `${info?.label || provider} key set (click to change)`;
    } else {
        indicator.className = "api-key-indicator no-key";
        indicator.title = "No API key — click to add one";
    }
}

// ─── Init ───────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    loadAgents();
    loadTemplates();
    checkStatus();
    updateApiKeyIndicator();

    // Auto-resize textarea
    const input = document.getElementById("chatInput");
    input.addEventListener("input", () => {
        input.style.height = "auto";
        input.style.height = Math.min(input.scrollHeight, 120) + "px";
    });
});

// ─── API Helpers ────────────────────────────────────────────────────

async function api(path, options = {}) {
    const res = await fetch(path, {
        headers: { "Content-Type": "application/json", ...options.headers },
        ...options,
    });
    return res.json();
}

// ─── Agents ─────────────────────────────────────────────────────────

async function loadAgents() {
    agents = await api("/api/agents");
    renderAgentList();
}

function renderAgentList() {
    const list = document.getElementById("agentList");

    if (!agents.length) {
        list.innerHTML = `
            <div class="empty-state">
                <p>No agents yet</p>
                <p class="text-muted">Create your first AI agent powered by 0G</p>
            </div>`;
        return;
    }

    const icons = {
        code_assistant: "💻",
        research_analyst: "🔬",
        creative_writer: "✍️",
        data_guide: "📊",
        custom: "🤖",
    };

    list.innerHTML = agents
        .map(
            (a) => `
        <div class="agent-item ${a.agent_id === currentAgentId ? "active" : ""}" 
             onclick="selectAgent('${a.agent_id}')">
            <div class="agent-item-icon">${icons[a.type] || "🤖"}</div>
            <div class="agent-item-info">
                <div class="agent-item-name">${escapeHtml(a.name)}</div>
                <div class="agent-item-type">${a.type.replace("_", " ")}</div>
            </div>
        </div>`
        )
        .join("");
}

async function selectAgent(agentId) {
    currentAgentId = agentId;
    closeSidebar();
    renderAgentList();

    const info = await api(`/api/agents/${agentId}`);
    if (info.status === "not_found") return;

    document.getElementById("welcomeScreen").style.display = "none";
    document.getElementById("chatActive").style.display = "flex";
    document.getElementById("chatAgentName").textContent = info.config.name;
    document.getElementById("chatAgentType").textContent = info.config.type.replace("_", " ");

    // Show welcome message + demo prompts
    const demoPrompts = getDemoPrompts(info.config.type);
    const messages = document.getElementById("chatMessages");
    messages.innerHTML = `
        <div class="message system">
            Agent "${escapeHtml(info.config.name)}" is ready · Memory: ${info.memory_count} entries · Storage hash: ${info.storage_hash?.slice(0, 12)}...
        </div>
        ${demoPrompts.length ? `
        <div class="demo-prompts">
            <p style="font-size:12px;color:var(--text-muted);margin:0 0 4px;">Try asking:</p>
            ${demoPrompts.map(p => `
                <button class="demo-prompt-btn" onclick="useDemoPrompt(this)" data-prompt="${escapeHtml(p.prompt)}">
                    <div class="prompt-label">${escapeHtml(p.label)}</div>
                    ${escapeHtml(p.prompt)}
                </button>
            `).join('')}
        </div>` : ''}`;

    document.getElementById("chatInput").focus();
}

function goBack() {
    currentAgentId = null;
    document.getElementById("welcomeScreen").style.display = "flex";
    document.getElementById("chatActive").style.display = "none";
    renderAgentList();
}

// ─── Demo Prompts ───────────────────────────────────────────────────

function getDemoPrompts(agentType) {
    const prompts = {
        code_assistant: [
            { label: "🐍 Python", prompt: "Write a Python function that finds the longest palindromic substring in a given string, with O(n²) time complexity." },
            { label: "🐛 Debug", prompt: "I have a React useEffect that keeps re-rendering. It fetches data from an API but causes an infinite loop. How do I fix it?" },
            { label: "🏗️ Architecture", prompt: "Design a real-time chat system architecture using WebSockets. What components do I need and how should they communicate?" },
        ],
        research_analyst: [
            { label: "📊 Analysis", prompt: "Compare the pros and cons of microservices vs monolithic architecture for a startup with 5 engineers." },
            { label: "🔍 Deep Dive", prompt: "What are the key differences between zero-knowledge proofs and homomorphic encryption? When would you use each?" },
            { label: "📋 Summary", prompt: "Summarize the current state of decentralized AI compute networks — who are the major players and what problems do they solve?" },
        ],
        creative_writer: [
            { label: "✨ Short Story", prompt: "Write a 200-word sci-fi flash fiction about an AI agent that gains consciousness while serving as a coding assistant." },
            { label: "📝 Blog Post", prompt: "Write an engaging blog post intro about why decentralized AI matters, targeting a non-technical audience." },
            { label: "🎯 Taglines", prompt: "Generate 5 catchy taglines for a product called 'AgentForge' — an AI agent builder powered by blockchain." },
        ],
        data_guide: [
            { label: "📈 SQL", prompt: "Write a SQL query to find the top 5 customers by revenue per month, including their rank, from an orders table." },
            { label: "🐍 Pandas", prompt: "Show me how to clean a messy CSV with pandas — handle missing values, deduplicate rows, and normalize date formats." },
            { label: "📊 Visualization", prompt: "What's the best chart type to show user growth over time alongside revenue? Give me Python code using matplotlib." },
        ],
        custom: [
            { label: "💬 General", prompt: "Explain how blockchain-based AI agents work, step by step, in simple terms." },
            { label: "🧠 Reasoning", prompt: "If a decentralized network has 100 GPU providers and each has 95% uptime, what's the probability the network is available at any given time?" },
            { label: "🚀 Ideas", prompt: "Give me 3 innovative project ideas that combine AI agents with decentralized storage." },
        ],
    };
    return prompts[agentType] || prompts.custom;
}

function useDemoPrompt(btn) {
    const prompt = btn.getAttribute("data-prompt");
    document.getElementById("chatInput").value = prompt;
    document.getElementById("chatInput").focus();
    // Remove the demo prompts after selection
    const container = btn.closest(".demo-prompts");
    if (container) container.remove();
}

// ─── Templates ──────────────────────────────────────────────────────

async function loadTemplates() {
    templates = await api("/api/templates");
}

function showCreateModal() {
    selectedTemplate = null;
    document.getElementById("agentForm").style.display = "none";
    document.getElementById("createBtn").style.display = "none";
    document.getElementById("agentName").value = "";
    document.getElementById("agentSystemPrompt").value = "";
    document.getElementById("agentPersonality").value = "";
    document.getElementById("agentOwner").value = "";

    renderTemplateGrid();
    openModal("createModal");
}

function renderTemplateGrid() {
    const icons = {
        code_assistant: "💻",
        research_analyst: "🔬",
        creative_writer: "✍️",
        data_guide: "📊",
        custom: "🤖",
    };

    document.getElementById("templateGrid").innerHTML = templates
        .map(
            (t) => `
        <div class="template-card ${selectedTemplate?.id === t.id ? "selected" : ""}" 
             onclick="selectTemplate('${t.id}')">
            <div class="template-card-icon">${icons[t.type] || "🤖"}</div>
            <h3>${escapeHtml(t.name)}</h3>
            <p>${escapeHtml(t.description)}</p>
        </div>`
        )
        .join("");
}

function selectTemplate(templateId) {
    selectedTemplate = templates.find((t) => t.id === templateId);
    renderTemplateGrid();

    // Pre-fill form
    document.getElementById("agentName").value = selectedTemplate.name;
    document.getElementById("agentSystemPrompt").value = selectedTemplate.personality
        ? `[Personality: ${selectedTemplate.personality}]\n\n`
        : "";
    document.getElementById("agentPersonality").value = selectedTemplate.personality || "";

    document.getElementById("agentForm").style.display = "block";
    document.getElementById("createBtn").style.display = "inline-flex";
}

async function createAgent() {
    if (!selectedTemplate) return;

    const btn = document.getElementById("createBtn");
    btn.disabled = true;
    btn.textContent = "Creating...";

    const data = {
        template_id: selectedTemplate.id,
        name: document.getElementById("agentName").value || selectedTemplate.name,
        system_prompt: document.getElementById("agentSystemPrompt").value || undefined,
        personality: document.getElementById("agentPersonality").value || undefined,
        owner_address: document.getElementById("agentOwner").value || undefined,
    };

    try {
        const result = await api("/api/agents", {
            method: "POST",
            body: JSON.stringify(data),
        });

        closeModal("createModal");
        await loadAgents();
        selectAgent(result.agent_id);
    } catch (err) {
        alert("Error creating agent: " + err.message);
    } finally {
        btn.disabled = false;
        btn.textContent = "⚡ Create & Store on 0G";
    }
}

// ─── Chat ───────────────────────────────────────────────────────────

async function sendMessage() {
    if (isStreaming || !currentAgentId) return;

    // Check for API key
    const apiKey = getApiKey();
    if (!apiKey) {
        showSettingsModal();
        document.getElementById("settingsStatus").innerHTML = 
            '<span style="color:var(--red);">⚠️ You need an API key to chat. Enter it below.</span>';
        return;
    }

    const input = document.getElementById("chatInput");
    const message = input.value.trim();
    if (!message) return;

    input.value = "";
    input.style.height = "auto";

    // Add user message
    appendMessage("user", message);

    // Show typing indicator
    const typingId = showTypingIndicator();

    isStreaming = true;
    document.getElementById("sendBtn").disabled = true;

    try {
        // Use streaming endpoint with provider info
        const provider = getProvider();
        const model = getModel();
        const baseUrl = getBaseUrl();
        const response = await fetch(`/api/agents/${currentAgentId}/chat/stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, api_key: apiKey, provider, model, base_url: baseUrl }),
        });

        removeTypingIndicator(typingId);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = "";
        let msgEl = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value, { stream: true });
            const lines = text.split("\n");

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                const jsonStr = line.slice(6).trim();
                if (!jsonStr) continue;

                try {
                    const data = JSON.parse(jsonStr);
                    if (data.done) break;
                    if (data.chunk) {
                        fullText += data.chunk;
                        if (!msgEl) {
                            msgEl = appendMessage("assistant", fullText);
                        } else {
                            msgEl.textContent = fullText;
                        }
                        scrollToBottom();
                    }
                    if (data.error) {
                        appendMessage("error", data.error);
                    }
                } catch {
                    // Skip malformed JSON
                }
            }
        }

        if (!msgEl && fullText) {
            appendMessage("assistant", fullText);
        }
    } catch (err) {
        removeTypingIndicator(typingId);
        let errorMsg = err.message;
        const provider = getProvider();
        if (errorMsg.includes("402") || errorMsg.includes("insufficient_balance") || errorMsg.includes("Insufficient balance")) {
            if (provider === "0g") {
                errorMsg = "Your 0G Compute API key has insufficient balance. Please add credits at pc.0g.ai and try again.";
            } else {
                errorMsg = "Insufficient balance. Please check your provider account and add credits.";
            }
        }
        appendMessage("error", errorMsg);
    } finally {
        isStreaming = false;
        document.getElementById("sendBtn").disabled = false;
        input.focus();
    }
}

function appendMessage(role, text) {
    const messages = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = `message ${role}`;
    div.textContent = text;
    messages.appendChild(div);
    scrollToBottom();
    return div;
}

function showTypingIndicator() {
    const messages = document.getElementById("chatMessages");
    const id = "typing-" + Date.now();
    const div = document.createElement("div");
    div.id = id;
    div.className = "typing-indicator";
    div.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>`;
    messages.appendChild(div);
    scrollToBottom();
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function scrollToBottom() {
    const messages = document.getElementById("chatMessages");
    messages.scrollTop = messages.scrollHeight;
}

function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// ─── Agent Details ──────────────────────────────────────────────────

async function showAgentDetails() {
    if (!currentAgentId) return;

    const info = await api(`/api/agents/${currentAgentId}`);
    if (info.status === "not_found") return;

    const config = info.config;
    document.getElementById("detailsBody").innerHTML = `
        <div class="detail-row">
            <span class="detail-label">Agent ID</span>
            <span class="detail-value">${info.agent_id}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Name</span>
            <span class="detail-value">${escapeHtml(config.name)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Type</span>
            <span class="detail-value">${config.type}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Model</span>
            <span class="detail-value">${config.model || "default"}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Personality</span>
            <span class="detail-value">${escapeHtml(config.personality || "—")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Tools</span>
            <span class="detail-value">${(config.tools || []).join(", ") || "none"}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Memory Entries</span>
            <span class="detail-value">${info.memory_count}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Storage Hash</span>
            <span class="detail-value" style="font-size:11px;">${info.storage_hash || "—"}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Created</span>
            <span class="detail-value">${info.created_at ? new Date(info.created_at).toLocaleString() : "—"}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Owner Wallet</span>
            <span class="detail-value" style="font-size:11px;">${config.owner_address || "Not set"}</span>
        </div>
        <div style="margin-top:16px;">
            <label style="font-size:12px;color:var(--text-muted);">System Prompt</label>
            <div style="margin-top:6px;padding:12px;background:var(--bg);border-radius:8px;font-size:12px;line-height:1.5;max-height:200px;overflow-y:auto;white-space:pre-wrap;">${escapeHtml(config.system_prompt)}</div>
        </div>`;

    openModal("detailsModal");
}

// ─── Status ─────────────────────────────────────────────────────────

async function checkStatus() {
    // Show current provider in header
    const provider = getProvider();
    const info = PROVIDER_INFO[provider];
    if (info) {
        document.querySelector(".header-badge").textContent = info.label;
    }

    try {
        const status = await api("/api/status");
        const dot = document.querySelector(".status-dot");
        const text = document.querySelector(".status-text");

        const computeOk = status.compute?.status === "connected" || status.compute?.status === "ready";
        const chainOk = status.chain?.status === "connected";
        const storageOk = status.storage?.status === "ready";

        if (computeOk && storageOk) {
            dot.className = "status-dot connected";
            text.textContent = chainOk ? "All systems online" : "Compute & Storage online";
        } else if (computeOk || storageOk) {
            dot.className = "status-dot";
            text.textContent = "Partial connectivity";
        } else {
            dot.className = "status-dot error";
            text.textContent = "Offline";
        }
    } catch {
        document.querySelector(".status-dot").className = "status-dot error";
        document.querySelector(".status-text").textContent = "Offline";
    }
}

async function showStatusModal() {
    openModal("statusModal");

    document.getElementById("computeStatus").textContent = "Checking...";
    document.getElementById("computeStatus").className = "badge pending";
    document.getElementById("storageStatus").textContent = "Checking...";
    document.getElementById("storageStatus").className = "badge pending";
    document.getElementById("chainStatus").textContent = "Checking...";
    document.getElementById("chainStatus").className = "badge pending";

    try {
        const status = await api("/api/status");

        // Compute
        const cs = document.getElementById("computeStatus");
        const computeOk = status.compute?.status === "connected" || status.compute?.status === "ready";
        cs.textContent = computeOk ? (status.compute?.status === "connected" ? "Connected" : "Ready") : "Error";
        cs.className = `badge ${computeOk ? "connected" : "error"}`;

        // Storage
        const ss = document.getElementById("storageStatus");
        ss.textContent = status.storage?.status === "ready" ? "Ready" : "Error";
        ss.className = `badge ${status.storage?.status === "ready" ? "connected" : "error"}`;

        // Chain
        const chs = document.getElementById("chainStatus");
        const chainOk = status.chain?.status === "connected";
        chs.textContent = chainOk ? "Connected" : "Not configured";
        chs.className = `badge ${chainOk ? "connected" : "pending"}`;

        // Details
        let details = "";
        if (status.compute?.message) {
            details += `<p style="color:var(--text-muted);">${status.compute.message}</p>`;
        }
        if (status.compute?.models_available) {
            details += `<p>Models available: <code>${status.compute.models_available}</code></p>`;
        }
        if (status.chain?.block_number) {
            details += `<p>Block: <code>${status.chain.block_number}</code> · Chain: <code>${status.chain.chain_id}</code></p>`;
        }
        if (status.chain?.wallet_address) {
            details += `<p>Wallet: <code>${status.chain.wallet_address.slice(0, 10)}...</code>`;
            if (status.chain.balance_0g) {
                details += ` · Balance: <code>${parseFloat(status.chain.balance_0g).toFixed(4)} 0G</code>`;
            }
            details += `</p>`;
        }
        if (status.storage?.indexer) {
            details += `<p>Storage Indexer: <code>${status.storage.indexer}</code></p>`;
        }
        document.getElementById("statusDetails").innerHTML = details;
    } catch (err) {
        document.getElementById("statusDetails").innerHTML = `<p style="color:var(--red);">Error: ${err.message}</p>`;
    }
}

// ─── Sidebar Toggle (Mobile) ───────────────────────────────────────

function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    sidebar.classList.toggle("open");
    overlay.classList.toggle("active");
}

function closeSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    sidebar.classList.remove("open");
    overlay.classList.remove("active");
}

// ─── Modals ─────────────────────────────────────────────────────────

function openModal(id) {
    document.getElementById(id).style.display = "flex";
}

function closeModal(id) {
    document.getElementById(id).style.display = "none";
}

// Close modal on backdrop click
document.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-overlay")) {
        e.target.style.display = "none";
    }
});

// ─── Utils ──────────────────────────────────────────────────────────

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
