/**
 * Hierarchical Tag and Category Tree Parser for Calibre Tag Browser.
 * Supports splitting tags by '.' or '/' into nested tree structures with aggregate counts.
 */

import type { TagTreeNode } from '../types';

export interface RawCategoryItem {
  name: string;
  count: number;
}

/**
 * Builds a hierarchical tree from a flat list of tags with counts.
 * Delimiters supported: '.' and '/' (e.g. "Fiction.Sci-Fi.Cyberpunk" or "History / Ancient Rome")
 */
export function buildHierarchicalTagTree(
  items: RawCategoryItem[],
  category: string = 'tags'
): TagTreeNode[] {
  interface InternalNode {
    id: string;
    name: string;
    fullPath: string;
    directCount: number;
    category: string;
    children: Map<string, InternalNode>;
  }

  const rootNodes = new Map<string, InternalNode>();

  for (const item of items) {
    if (!item.name || !item.name.trim()) continue;

    // Split on either '.' or '/'
    const parts = item.name
      .split(/[./]/)
      .map((p) => p.trim())
      .filter(Boolean);

    if (parts.length === 0) continue;

    let currentLevel = rootNodes;
    let accumulatedPath = '';

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      accumulatedPath = accumulatedPath ? `${accumulatedPath}.${part}` : part;
      const isLeaf = i === parts.length - 1;

      let node = currentLevel.get(part);
      if (!node) {
        node = {
          id: `${category}:${accumulatedPath}`,
          name: part,
          fullPath: accumulatedPath,
          directCount: 0,
          category,
          children: new Map(),
        };
        currentLevel.set(part, node);
      }

      if (isLeaf) {
        node.directCount += item.count;
      }

      currentLevel = node.children;
    }
  }

  // Convert map hierarchy to recursive TagTreeNode array with aggregated counts
  function convertNode(internal: InternalNode): TagTreeNode {
    const childrenList = Array.from(internal.children.values()).map(convertNode);
    const childrenSum = childrenList.reduce((acc, c) => acc + c.count, 0);
    const totalCount = internal.directCount + childrenSum;

    return {
      id: internal.id,
      name: internal.name,
      fullPath: internal.fullPath,
      count: totalCount,
      category: internal.category,
      children: childrenList.length > 0 ? childrenList : undefined,
    };
  }

  return Array.from(rootNodes.values()).map(convertNode);
}

/**
 * Sorts tree nodes either alphabetically by name or descending by book count.
 */
export function sortTagTreeNodes(
  nodes: TagTreeNode[],
  sortBy: 'name' | 'count' = 'name'
): TagTreeNode[] {
  const sorted = [...nodes].sort((a, b) => {
    if (sortBy === 'count') {
      const diff = b.count - a.count;
      if (diff !== 0) return diff;
    }
    return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
  });

  return sorted.map((node) => ({
    ...node,
    children: node.children ? sortTagTreeNodes(node.children, sortBy) : undefined,
  }));
}

/**
 * Filters a tree node array by a search query (retaining nodes whose name or descendants match).
 */
export function filterTagTreeNodes(
  nodes: TagTreeNode[],
  query: string
): TagTreeNode[] {
  if (!query.trim()) return nodes;

  const q = query.toLowerCase().trim();

  function matchNode(node: TagTreeNode): TagTreeNode | null {
    const isSelfMatch = node.name.toLowerCase().includes(q) || node.fullPath.toLowerCase().includes(q);
    const matchedChildren = node.children
      ? node.children.map(matchNode).filter((c): c is TagTreeNode => c !== null)
      : undefined;

    if (isSelfMatch || (matchedChildren && matchedChildren.length > 0)) {
      return {
        ...node,
        children: matchedChildren && matchedChildren.length > 0 ? matchedChildren : node.children,
      };
    }
    return null;
  }

  return nodes.map(matchNode).filter((n): n is TagTreeNode => n !== null);
}
