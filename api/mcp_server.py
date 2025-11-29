import os
import sys
import logging
import asyncio
from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# Import necessary components from DeepWiki
# Adjust path to include api root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.rag import RAG
from api.api import get_adalflow_default_root_path

# Initialize MCP Server
mcp = FastMCP("DeepWiki")

@mcp.tool()
async def list_available_wikis() -> List[str]:
    """
    Lists all available generated wikis in the cache.
    Returns a list of strings formatted as "owner/repo (type) - language"
    """
    cache_dir = os.path.join(get_adalflow_default_root_path(), "wikicache")
    if not os.path.exists(cache_dir):
        return []

    wikis = []
    for filename in os.listdir(cache_dir):
        if filename.startswith("deepwiki_cache_") and filename.endswith(".json"):
             parts = filename.replace("deepwiki_cache_", "").replace(".json", "").split('_')
             if len(parts) >= 4:
                 repo_type = parts[0]
                 owner = parts[1]
                 language = parts[-1]
                 repo = "_".join(parts[2:-1])
                 wikis.append(f"{owner}/{repo} ({repo_type}) - {language}")
    return wikis

@mcp.tool()
async def query_wiki(query: str, owner: str, repo: str, repo_type: str = "github") -> str:
    """
    Queries a specific repository wiki using RAG.

    Args:
        query: The question to ask.
        owner: Repository owner.
        repo: Repository name.
        repo_type: Repository type (default: github).

    Returns:
        The answer from the RAG system.
    """
    try:
        # Construct repo identifier compatible with RAG
        # Note: RAG.prepare_retriever expects a repo URL or path.
        # If the repo is already indexed in ~/.adalflow/repos, we can point to the local path.

        # We need to reconstruct the path where the repo is stored.
        # Assuming standard naming convention used in API
        repo_path = os.path.join(get_adalflow_default_root_path(), "repos", f"{owner}_{repo}")

        # If not found, try fuzzy or simple name
        if not os.path.exists(repo_path):
             repo_path_alt = os.path.join(get_adalflow_default_root_path(), "repos", repo)
             if os.path.exists(repo_path_alt):
                 repo_path = repo_path_alt

        if not os.path.exists(repo_path):
            return f"Error: Repository {owner}/{repo} not found locally. Please generate the wiki first."

        # Initialize RAG
        # We might want to cache RAG instances or initialize lighter version
        rag = RAG(provider="openai") # Defaulting to openai for now, or read from env

        # Prepare retriever (should load from existing index if available)
        # Note: This might be slow if it re-indexes.
        # Ideally RAG class should support loading existing index quickly.
        # Based on RAG code, prepare_retriever calls db_manager.prepare_database which handles caching.
        rag.prepare_retriever(repo_path, type=repo_type)

        # Call RAG
        result, _ = rag.call(query)
        return result.answer

    except Exception as e:
        logger.error(f"Error querying wiki: {e}")
        return f"Error processing query: {str(e)}"

if __name__ == "__main__":
    mcp.run()
