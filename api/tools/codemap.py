from typing import Dict, List, Any
import os
import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class FileNode:
    name: str
    path: str
    type: str # 'file' or 'directory'
    size: int = 0
    children: List['FileNode'] = field(default_factory=list)

def build_directory_tree(path: str, root_path: str = None) -> FileNode:
    """
    Recursively builds a tree of file nodes from a directory.
    """
    if root_path is None:
        root_path = path

    name = os.path.basename(path)
    if path == root_path:
        # Use repo name or root name
        name = os.path.basename(path) or "root"

    node = FileNode(
        name=name,
        path=os.path.relpath(path, root_path),
        type="directory",
        children=[]
    )

    try:
        # Sort directories first, then files
        entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))

        for entry in entries:
            # Skip hidden files and directories
            if entry.name.startswith('.'):
                continue

            # Skip common build/cache directories
            if entry.name in ['__pycache__', 'node_modules', 'dist', 'build', 'venv', 'env']:
                continue

            if entry.is_dir():
                child_node = build_directory_tree(entry.path, root_path)
                node.children.append(child_node)
            else:
                try:
                    size = entry.stat().st_size
                except:
                    size = 0

                child_node = FileNode(
                    name=entry.name,
                    path=os.path.relpath(entry.path, root_path),
                    type="file",
                    size=size
                )
                node.children.append(child_node)

    except PermissionError:
        logger.warning(f"Permission denied accessing {path}")
    except Exception as e:
        logger.error(f"Error scanning directory {path}: {e}")

    return node

def generate_mermaid_codemap(node: FileNode, indent: int = 0) -> str:
    """
    Generates a Mermaid graph (TD) representing the directory structure.
    Limits depth to avoid huge diagrams.
    """
    # This might be too large for a complex repo.
    # Alternative: A Mindmap might be better for hierarchy.

    # Let's try to generate a Mindmap
    content = "mindmap\n"
    content += f"  root(({node.name}))\n"

    def _add_nodes(parent_node: FileNode, level: int):
        if level > 3: # Limit depth
             return

        for child in parent_node.children:
            prefix = "    " * (level + 1)
            if child.type == 'directory':
                content_line = f"{prefix}{child.name}\n"
                # Add content line to content variable.
                # Wait, I cannot modify outer variable 'content' easily in python closure without nonlocal.
                nonlocal content
                content += content_line
                _add_nodes(child, level + 1)
            else:
                # Maybe don't show all files in mindmap to save space, or show important ones?
                # For now show all but limit depth
                pass

    _add_nodes(node, 0)
    return content

def generate_codemap_data(repo_path: str):
    """
    Generates the data for the Codemap.
    Returns the root FileNode.
    """
    return build_directory_tree(repo_path)
