# AgentForge ⚡

**Build, deploy, and interact with AI agents powered by 0G's decentralized infrastructure.**

AgentForge is a full-stack dApp that lets users create AI agents from templates, chat with them in real-time (streaming), and optionally mint them as NFTs on 0G Chain. All agent configurations and memory are stored on 0G Storage, and all inference runs through 0G Compute.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (HTML/CSS/JS)                    │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Templates │  │  Agent Chat  │  │  Network Status Panel │  │
│  └──────────┘  └──────────────┘  └───────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API + SSE Streaming
┌────────────────────────┴────────────────────────────────────┐
│                   Flask Backend (app.py)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ agents.py│  │compute.py│  │storage.py│  │ chain.py   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘  │
└───────┼──────────────┼──────────────┼──────────────┼─────────┘
        │              │              │              │
   ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐   ┌────▼────┐
   │  Agent  │   │ 0G Compute│  │0G Store │   │0G Chain │
   │ Builder │   │  Router   │  │ Indexer │   │  EVM    │
   └─────────┘   └───────────┘  └─────────┘   └─────────┘
```

## 0G Integration

| Service | How It's Used |
|---------|--------------|
| **0G Compute** | Runs LLM inference for agent chat via OpenAI-compatible Router API |
| **0G Storage** | Persists agent configs and conversation memory on decentralized storage |
| **0G Chain** | Mints Agent NFTs (ERC-721) for on-chain provenance and ownership |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your 0G Compute API key
```

**Required:**
- `OG_COMPUTE_API_KEY` — Your 0G Compute Router API key

**Optional (for NFT minting):**
- `WALLET_PRIVATE_KEY` — Private key with 0G tokens
- `AGENT_NFT_CONTRACT_ADDRESS` — Deployed AgentForgeNFT contract address

### 3. Run

```bash
python app.py
```

Open http://localhost:5000

## Agent Templates

| Template | Description |
|----------|-------------|
| 💻 Code Assistant | Writes, debugs, and explains code |
| 🔬 Research Analyst | Deep analysis with balanced perspectives |
| ✍️ Creative Writer | Storytelling, copywriting, content creation |
| 📊 Data Guide | Data analysis, SQL, visualization help |
| 🤖 Custom | Build your own from scratch |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/templates` | List agent templates |
| GET | `/api/agents` | List all created agents |
| POST | `/api/agents` | Create a new agent |
| GET | `/api/agents/:id` | Get agent details |
| POST | `/api/agents/:id/chat` | Chat with agent (JSON) |
| POST | `/api/agents/:id/chat/stream` | Chat with agent (SSE streaming) |
| GET | `/api/status` | Check 0G service connectivity |
| GET | `/api/models` | List available models |

## Deploying the NFT Contract

To enable on-chain agent minting, deploy the Solidity contract to 0G Chain:

1. Use Remix, Hardhat, or Foundry to deploy `contracts/AgentForgeNFT.sol`
2. Set `AGENT_NFT_CONTRACT_ADDRESS` in `.env`
3. Set `WALLET_PRIVATE_KEY` with a funded wallet
4. When creating agents, provide an owner wallet address

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** Vanilla HTML/CSS/JS (no framework dependency)
- **AI:** OpenAI SDK → 0G Compute Router
- **Blockchain:** web3.py → 0G Chain (EVM, Chain ID 16661)
- **Storage:** 0G Storage Indexer API
- **Smart Contract:** Solidity ^0.8.20 (ERC-721)

## License

MIT
