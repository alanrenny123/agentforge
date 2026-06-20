// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AgentForgeNFT
 * @notice ERC-721 contract for minting AI Agent NFTs on 0G Chain
 * @dev Each NFT represents an AI agent with its config stored on 0G Storage
 */
contract AgentForgeNFT {
    string public name = "AgentForge Agent";
    string public symbol = "AFAGENT";

    uint256 private _tokenIdCounter;

    struct Agent {
        string agentName;
        string systemPrompt;
        string configHash;    // Hash pointing to full config on 0G Storage
        address creator;
        uint256 createdAt;
    }

    mapping(uint256 => Agent) public agents;
    mapping(uint256 => address) private _owners;
    mapping(address => uint256) private _balances;
    mapping(uint256 => address) private _tokenApprovals;

    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event AgentMinted(uint256 indexed tokenId, string name, address indexed creator);

    modifier onlyOwner(uint256 tokenId) {
        require(_owners[tokenId] == msg.sender, "Not token owner");
        _;
    }

    function totalAgents() public view returns (uint256) {
        return _tokenIdCounter;
    }

    function ownerOf(uint256 tokenId) public view returns (address) {
        address owner = _owners[tokenId];
        require(owner != address(0), "Token does not exist");
        return owner;
    }

    function balanceOf(address owner) public view returns (uint256) {
        require(owner != address(0), "Zero address");
        return _balances[owner];
    }

    /**
     * @notice Mint a new Agent NFT
     * @param to Address to receive the NFT
     * @param agentName Name of the AI agent
     * @param systemPrompt Agent's system prompt (truncated for on-chain storage)
     * @param configHash SHA-256 hash of full config stored on 0G Storage
     */
    function mintAgent(
        address to,
        string calldata agentName,
        string calldata systemPrompt,
        string calldata configHash
    ) external returns (uint256) {
        require(to != address(0), "Mint to zero address");

        uint256 tokenId = _tokenIdCounter++;

        _owners[tokenId] = to;
        _balances[to]++;

        agents[tokenId] = Agent({
            agentName: agentName,
            systemPrompt: systemPrompt,
            configHash: configHash,
            creator: msg.sender,
            createdAt: block.timestamp
        });

        emit Transfer(address(0), to, tokenId);
        emit AgentMinted(tokenId, agentName, msg.sender);

        return tokenId;
    }

    /**
     * @notice Get agent data by token ID
     */
    function getAgent(uint256 tokenId) external view returns (
        string memory agentName,
        string memory systemPrompt,
        string memory configHash,
        address creator,
        uint256 createdAt
    ) {
        require(_owners[tokenId] != address(0), "Token does not exist");
        Agent storage agent = agents[tokenId];
        return (
            agent.agentName,
            agent.systemPrompt,
            agent.configHash,
            agent.creator,
            agent.createdAt
        );
    }

    /**
     * @notice Get token URI (returns config hash for metadata resolution)
     */
    function tokenURI(uint256 tokenId) external view returns (string memory) {
        require(_owners[tokenId] != address(0), "Token does not exist");
        return string(abi.encodePacked("ipfs://", agents[tokenId].configHash));
    }

    function approve(address to, uint256 tokenId) external onlyOwner(tokenId) {
        _tokenApprovals[tokenId] = to;
        emit Approval(msg.sender, to, tokenId);
    }

    function transferFrom(address from, address to, uint256 tokenId) external {
        require(_owners[tokenId] == from, "Not owner");
        require(to != address(0), "Transfer to zero address");

        _tokenApprovals[tokenId] = address(0);
        _balances[from]--;
        _balances[to]++;
        _owners[tokenId] = to;

        emit Transfer(from, to, tokenId);
    }
}
