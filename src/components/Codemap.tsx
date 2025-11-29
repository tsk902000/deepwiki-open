import React, { useState, useEffect } from 'react';
import Mermaid from './Mermaid';

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  children?: FileNode[];
}

interface CodemapProps {
  owner: string;
  repo: string;
  repoType: string;
  onClose: () => void;
}

const Codemap: React.FC<CodemapProps> = ({ owner, repo, repoType, onClose }) => {
  const [data, setData] = useState<FileNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'mindmap' | 'graph'>('mindmap');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Using the same server base URL as the app usually does
        const baseUrl = process.env.NEXT_PUBLIC_SERVER_BASE_URL || 'http://localhost:8001';
        const response = await fetch(`${baseUrl}/api/codemap?owner=${owner}&repo=${repo}&repo_type=${repoType}`);

        if (!response.ok) {
          throw new Error(`Failed to load codemap: ${response.statusText}`);
        }

        const jsonData = await response.json();
        setData(jsonData);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [owner, repo, repoType]);

  const generateMermaidChart = (node: FileNode, mode: 'mindmap' | 'graph'): string => {
    if (mode === 'mindmap') {
      let content = "mindmap\n";
      content += `  root((${node.name}))\n`;

      const addNodes = (parentNode: FileNode, level: number) => {
        if (level > 3) return; // Limit depth

        parentNode.children?.forEach(child => {
          if (child.type === 'directory') {
            const prefix = "    ".repeat(level + 1);
            content += `${prefix}${child.name}\n`;
            addNodes(child, level + 1);
          }
        });
      };

      addNodes(node, 0);
      return content;
    } else {
        // Graph TD
        let content = "graph TD\n";
        content += `  root[/${node.name}/]\n`;
        content += `  style root fill:#f9f,stroke:#333,stroke-width:2px\n`;

        let nodeId = 0;
        const getNewId = () => `node${++nodeId}`;
        const nodeMap = new Map<string, string>();
        nodeMap.set(node.path, "root");

        const addNodes = (parentNode: FileNode, parentId: string, level: number) => {
             if (level > 2) return; // Stricter limit for graph

             parentNode.children?.forEach(child => {
                 if (child.type === 'directory') {
                     const id = getNewId();
                     content += `  ${parentId} --> ${id}[/${child.name}/]\n`;
                     addNodes(child, id, level + 1);
                 }
             });
        };
        addNodes(node, "root", 0);
        return content;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4">
      <div className="bg-[var(--card-bg)] rounded-lg shadow-custom max-w-6xl max-h-[90vh] w-full flex flex-col card-japanese h-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--border-color)]">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-medium text-[var(--foreground)] font-serif">Codemap: {owner}/{repo}</h2>
            <div className="flex bg-[var(--background)] rounded-md border border-[var(--border-color)] overflow-hidden">
                <button
                    onClick={() => setViewMode('mindmap')}
                    className={`px-3 py-1 text-sm ${viewMode === 'mindmap' ? 'bg-[var(--accent-primary)] text-white' : 'text-[var(--foreground)]'}`}
                >
                    Mindmap
                </button>
                <button
                    onClick={() => setViewMode('graph')}
                    className={`px-3 py-1 text-sm ${viewMode === 'graph' ? 'bg-[var(--accent-primary)] text-white' : 'text-[var(--foreground)]'}`}
                >
                    Tree
                </button>
            </div>
          </div>
          <button onClick={onClose} className="text-[var(--foreground)] hover:text-[var(--accent-primary)]">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4 bg-[var(--background)]/50">
          {loading && (
            <div className="flex justify-center items-center h-full">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--accent-primary)]"></div>
            </div>
          )}

          {error && (
            <div className="flex justify-center items-center h-full text-red-500">
              {error}
            </div>
          )}

          {data && (
            <div className="h-full w-full">
                <Mermaid
                    chart={generateMermaidChart(data, viewMode)}
                    zoomingEnabled={true}
                    className="h-full w-full"
                />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Codemap;
