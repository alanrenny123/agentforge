"""0G Chain integration — mint agent NFTs on 0G mainnet."""

import os
import json
from web3 import Web3
from eth_account import Account


# Minimal ERC-721 ABI for minting
AGENT_NFT_ABI = json.loads('''[
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "string", "name": "name", "type": "string"},
            {"internalType": "string", "name": "systemPrompt", "type": "string"},
            {"internalType": "string", "name": "configHash", "type": "string"}
        ],
        "name": "mintAgent",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "getAgent",
        "outputs": [
            {"internalType": "string", "name": "name", "type": "string"},
            {"internalType": "string", "name": "systemPrompt", "type": "string"},
            {"internalType": "string", "name": "configHash", "type": "string"},
            {"internalType": "address", "name": "creator", "type": "address"},
            {"internalType": "uint256", "name": "createdAt", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalAgents",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    }
]''')


def get_web3() -> Web3:
    """Connect to 0G mainnet."""
    rpc_url = os.getenv("OG_RPC_URL", "https://evmrpc.0g.ai")
    return Web3(Web3.HTTPProvider(rpc_url))


def get_account():
    """Get the wallet account from private key."""
    private_key = os.getenv("WALLET_PRIVATE_KEY", "")
    if not private_key or private_key == "your_private_key_here":
        return None
    return Account.from_key(private_key)


def get_contract():
    """Get the Agent NFT contract instance."""
    w3 = get_web3()
    contract_address = os.getenv("AGENT_NFT_CONTRACT_ADDRESS", "")
    if not contract_address or contract_address == "0x0000000000000000000000000000000000000000":
        return None
    return w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=AGENT_NFT_ABI,
    )


def mint_agent_nft(
    to_address: str,
    agent_name: str,
    system_prompt: str,
    config_hash: str,
) -> dict:
    """
    Mint an Agent NFT on 0G Chain.
    
    This creates an on-chain record of the agent with its name,
    system prompt, and a hash pointing to its full config on 0G Storage.
    """
    account = get_account()
    contract = get_contract()

    if not account:
        return {"status": "no_wallet", "message": "No wallet configured. Set WALLET_PRIVATE_KEY in .env"}
    
    if not contract:
        return {"status": "no_contract", "message": "No contract deployed. Set AGENT_NFT_CONTRACT_ADDRESS in .env"}

    w3 = get_web3()

    try:
        # Build transaction
        tx = contract.functions.mintAgent(
            Web3.to_checksum_address(to_address),
            agent_name,
            system_prompt[:500],  # Truncate for on-chain storage
            config_hash,
        ).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 500000,
            "gasPrice": w3.eth.gas_price,
            "chainId": int(os.getenv("OG_CHAIN_ID", "16661")),
        })

        # Sign and send
        signed_tx = w3.eth.account.sign_transaction(tx, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        # Get the minted token ID from logs
        token_id = None
        for log in receipt.logs:
            try:
                decoded = contract.events.Transfer().process_log(log)
                token_id = decoded["args"]["tokenId"]
                break
            except Exception:
                continue

        return {
            "status": "minted",
            "tx_hash": tx_hash.hex(),
            "token_id": token_id,
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "agent_name": agent_name,
            "config_hash": config_hash,
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_agent_from_chain(token_id: int) -> dict:
    """Retrieve agent data from the on-chain contract."""
    contract = get_contract()
    if not contract:
        return {"status": "no_contract"}

    try:
        agent_data = contract.functions.getAgent(token_id).call()
        return {
            "status": "found",
            "token_id": token_id,
            "name": agent_data[0],
            "system_prompt": agent_data[1],
            "config_hash": agent_data[2],
            "creator": agent_data[3],
            "created_at": agent_data[4],
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_chain_status() -> dict:
    """Check 0G Chain connectivity."""
    try:
        w3 = get_web3()
        connected = w3.is_connected()
        block = w3.eth.block_number if connected else 0
        chain_id = w3.eth.chain_id if connected else 0

        account = get_account()
        balance = None
        if account and connected:
            balance_wei = w3.eth.get_balance(account.address)
            balance = str(w3.from_wei(balance_wei, "ether"))

        return {
            "status": "connected" if connected else "disconnected",
            "chain_id": chain_id,
            "block_number": block,
            "wallet_address": account.address if account else None,
            "balance_0g": balance,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
