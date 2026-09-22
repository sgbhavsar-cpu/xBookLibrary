import React, { useMemo, useState } from 'react';
import {
  ArrowDownAZ,
  ArrowDownWideNarrow,
  Bookmark,
  Building,
  ChevronDown,
  ChevronRight,
  Folder,
  FolderOpen,
  Hash,
  HardDrive,
  Layers,
  Minus,
  Plus,
  Search,
  Settings,
  Star,
  Tag as TagIcon,
  User,
  X,
  XCircle,
} from 'lucide-react';
import { useStore } from '../store/useStore';
import type { TagTreeNode } from '../types';
import { getRatingBucket } from '../utils/filterBooks';
import {
  buildHierarchicalTagTree,
  filterTagTreeNodes,
  sortTagTreeNodes,
} from '../utils/tagTreeParser';

export const FilterSidebar: React.FC = () => {
  const {
    books,
    taxonomyTree,
    customColumns,
    tagTreeFilter,
    tagTreeSearchQuery,
    tagTreeSortBy,
    cycleTagFilter,
    setTagFilter,
    clearTagTreeFilters,
    setTagTreeSearchQuery,
    setTagTreeSortBy,
  } = useStore();

  // Category collapsed state
  const [collapsedCategories, setCollapsedCategories] = useState<Record<string, boolean>>({
    taxonomies: true, // collapsed by default to keep authors/tags/formats visible
    identifiers: true,
    publishers: true,
  });

  // Expanded sub-tree paths for hierarchical tags
  const [expandedTagPaths, setExpandedTagPaths] = useState<Record<string, boolean>>({});

  const toggleCategory = (cat: string) => {
    setCollapsedCategories((prev) => ({ ...prev, [cat]: !prev[cat] }));
  };

  const toggleTagExpand = (path: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedTagPaths((prev) => ({ ...prev, [path]: !prev[path] }));
  };

  const collapseAll = () => {
    setCollapsedCategories({
      authors: true,
      series: true,
      tags: true,
      formats: true,
      publishers: true,
      ratings: true,
      identifiers: true,
      taxonomies: true,
    });
  };

  const expandAll = () => {
    setCollapsedCategories({});
  };

  const safeBooks = Array.isArray(books) ? books : [];

  // --- Aggregate Category Data ---

  // 1. Authors
  const authorsData = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const b of safeBooks) {
      for (const a of b.authors || []) {
        if (!a) continue;
        counts[a] = (counts[a] || 0) + 1;
      }
    }
    return Object.entries(counts).map(([name, count]) => ({
      id: `authors:${name}`,
      name,
      fullPath: name,
      count,
      category: 'authors',
    }));
  }, [safeBooks]);

  // 2. Series
  const seriesData = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const b of safeBooks) {
      if (b.series && b.series.trim()) {
        counts[b.series] = (counts[b.series] || 0) + 1;
      }
    }
    return Object.entries(counts).map(([name, count]) => ({
      id: `series:${name}`,
      name,
      fullPath: name,
      count,
      category: 'series',
    }));
  }, [safeBooks]);

  // 3. Formats
  const formatsData = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const b of safeBooks) {
      for (const f of b.formats || []) {
        const fmt = f.format.toUpperCase();
        counts[fmt] = (counts[fmt] || 0) + 1;
      }
    }
    return Object.entries(counts).map(([name, count]) => ({
      id: `formats:${name}`,
      name,
      fullPath: name,
      count,
      category: 'formats',
    }));
  }, [safeBooks]);

  // 4. Publishers
  const publishersData = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const b of safeBooks) {
      if (b.publisher && b.publisher.trim()) {
        counts[b.publisher] = (counts[b.publisher] || 0) + 1;
      }
    }
    return Object.entries(counts).map(([name, count]) => ({
      id: `publishers:${name}`,
      name,
      fullPath: name,
      count,
      category: 'publishers',
    }));
  }, [safeBooks]);

  // 5. Ratings
  const ratingsData = useMemo(() => {
    const counts: Record<string, number> = {
      '5 Stars': 0,
      '4 Stars': 0,
      '3 Stars': 0,
      '2 Stars': 0,
      '1 Star': 0,
      'Unrated': 0,
    };
    for (const b of safeBooks) {
      const bucket = getRatingBucket(b.rating);
      counts[bucket] = (counts[bucket] || 0) + 1;
    }
    return Object.entries(counts)
      .filter(([_, count]) => count > 0)
      .map(([name, count]) => ({
        id: `ratings:${name}`,
        name,
        fullPath: name,
        count,
        category: 'ratings',
      }));
  }, [safeBooks]);

  // 6. Tags (Hierarchical Tree)
  const tagsTree = useMemo(() => {
    const rawCounts: Record<string, number> = {};
    for (const b of safeBooks) {
      for (const t of b.tags || []) {
        if (!t) continue;
        rawCounts[t] = (rawCounts[t] || 0) + 1;
      }
    }
    const rawItems = Object.entries(rawCounts).map(([name, count]) => ({ name, count }));
    return buildHierarchicalTagTree(rawItems, 'tags');
  }, [safeBooks]);

  // 7. Identifiers
  const identifiersData = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const b of safeBooks) {
      if (b.isbn) counts['isbn'] = (counts['isbn'] || 0) + 1;
      for (const idKey of Object.keys(b.identifiers || {})) {
        const k = idKey.toLowerCase();
        counts[k] = (counts[k] || 0) + 1;
      }
    }
    return Object.entries(counts).map(([name, count]) => ({
      id: `identifiers:${name}`,
      name,
      fullPath: name,
      count,
      category: 'identifiers',
    }));
  }, [safeBooks]);

  // 8. Custom Columns
  const customColumnsData = useMemo(() => {
    const result: Record<string, { label: string; name: string; items: TagTreeNode[] }> = {};
    for (const col of customColumns) {
      const counts: Record<string, number> = {};
      for (const b of safeBooks) {
        const val = b.custom_values?.[col.label];
        if (val !== undefined && val !== null && val !== '') {
          const str = String(val);
          counts[str] = (counts[str] || 0) + 1;
        }
      }
      const items = Object.entries(counts).map(([name, count]) => ({
        id: `cc:${col.label}:${name}`,
        name,
        fullPath: name,
        count,
        category: `cc:${col.label}`,
      }));
      if (items.length > 0) {
        result[col.label] = {
          label: col.label,
          name: col.name,
          items,
        };
      }
    }
    return result;
  }, [safeBooks, customColumns]);

  // Active Filter Pills
  const activePills = useMemo(() => {
    const pills: { category: string; value: string; state: 'include' | 'exclude' }[] = [];
    for (const [cat, map] of Object.entries(tagTreeFilter)) {
      for (const [val, state] of Object.entries(map)) {
        pills.push({ category: cat, value: val, state });
      }
    }
    return pills;
  }, [tagTreeFilter]);

  // Calculate total active filters count per category
  const activeCountPerCategory = useMemo(() => {
    const map: Record<string, { include: number; exclude: number }> = {};
    for (const [cat, items] of Object.entries(tagTreeFilter)) {
      let inc = 0;
      let exc = 0;
      for (const state of Object.values(items)) {
        if (state === 'include') inc++;
        if (state === 'exclude') exc++;
      }
      map[cat] = { include: inc, exclude: exc };
    }
    return map;
  }, [tagTreeFilter]);

  // Render a single tree node row
  const renderItemRow = (node: TagTreeNode, depth = 0) => {
    const currentCatMap = tagTreeFilter[node.category] || {};
    const filterState = currentCatMap[node.fullPath]; // 'include' | 'exclude' | undefined
    const hasChildren = Boolean(node.children && node.children.length > 0);
    const isExpanded = expandedTagPaths[node.fullPath] ?? true;

    return (
      <div key={node.id}>
        <div
          onClick={() => cycleTagFilter(node.category, node.fullPath)}
          title={`Click to cycle: Neutral -> Include (+) -> Exclude (-) -> Neutral`}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '3px 6px',
            paddingLeft: `${depth * 14 + 6}px`,
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            fontSize: '12px',
            background: filterState === 'include'
              ? 'rgba(16, 185, 129, 0.12)'
              : filterState === 'exclude'
              ? 'rgba(239, 68, 68, 0.12)'
              : 'transparent',
            color: filterState === 'include'
              ? '#10b981'
              : filterState === 'exclude'
              ? '#ef4444'
              : 'var(--text-secondary)',
            fontWeight: filterState ? 600 : 400,
            transition: 'all var(--transition-fast)',
            borderLeft: filterState === 'include'
              ? '2px solid #10b981'
              : filterState === 'exclude'
              ? '2px solid #ef4444'
              : '2px solid transparent',
          }}
          className="tag-tree-row"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflow: 'hidden' }}>
            {/* Hierarchical Folder Expander */}
            {hasChildren ? (
              <span
                onClick={(e) => toggleTagExpand(node.fullPath, e)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                }}
              >
                {isExpanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                {isExpanded ? <FolderOpen size={12} style={{ marginLeft: 2 }} /> : <Folder size={12} style={{ marginLeft: 2 }} />}
              </span>
            ) : null}

            {/* Tri-State Indicator Badge */}
            <span
              style={{
                width: '15px',
                height: '15px',
                borderRadius: '3px',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '10px',
                fontWeight: 700,
                background: filterState === 'include'
                  ? '#10b981'
                  : filterState === 'exclude'
                  ? '#ef4444'
                  : 'var(--bg-card)',
                color: filterState ? '#ffffff' : 'var(--text-muted)',
                border: filterState ? 'none' : '1px solid var(--border-default)',
                flexShrink: 0,
              }}
            >
              {filterState === 'include' ? (
                <Plus size={10} strokeWidth={3} />
              ) : filterState === 'exclude' ? (
                <Minus size={10} strokeWidth={3} />
              ) : null}
            </span>

            <span
              style={{
                textOverflow: 'ellipsis',
                overflow: 'hidden',
                whiteSpace: 'nowrap',
              }}
            >
              {node.name}
            </span>
          </div>

          <span
            style={{
              fontSize: '10.5px',
              color: filterState ? 'inherit' : 'var(--text-muted)',
              padding: '1px 5px',
              borderRadius: 'var(--radius-full)',
              background: filterState ? 'transparent' : 'var(--bg-card)',
              marginLeft: '4px',
              flexShrink: 0,
            }}
          >
            {node.count}
          </span>
        </div>

        {/* Children Sub-tree */}
        {hasChildren && isExpanded && (
          <div>
            {node.children!.map((child) => renderItemRow(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  // Render a Category Section
  const renderCategorySection = (
    catKey: string,
    title: string,
    icon: React.ReactNode,
    nodes: TagTreeNode[]
  ) => {
    if (nodes.length === 0) return null;

    const isCollapsed = Boolean(collapsedCategories[catKey]);
    const filteredNodes = filterTagTreeNodes(nodes, tagTreeSearchQuery);
    const sortedNodes = sortTagTreeNodes(filteredNodes, tagTreeSortBy);

    if (tagTreeSearchQuery && sortedNodes.length === 0) return null;

    const catCounts = activeCountPerCategory[catKey];
    const totalActive = (catCounts?.include || 0) + (catCounts?.exclude || 0);

    return (
      <div style={{ marginBottom: '10px' }} key={catKey}>
        {/* Category Header */}
        <div
          onClick={() => toggleCategory(catKey)}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '5px 8px',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-default)',
            fontSize: '11.5px',
            fontWeight: 600,
            color: 'var(--text-primary)',
            userSelect: 'none',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: 'var(--text-muted)' }}>
              {isCollapsed ? <ChevronRight size={13} /> : <ChevronDown size={13} />}
            </span>
            <span style={{ color: 'var(--accent-primary)', display: 'flex', alignItems: 'center' }}>
              {icon}
            </span>
            <span>{title}</span>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
              ({nodes.length})
            </span>
          </div>

          {/* Active status indicator badge */}
          {totalActive > 0 && (
            <div style={{ display: 'flex', gap: '3px' }}>
              {catCounts.include > 0 && (
                <span
                  style={{
                    fontSize: '9.5px',
                    padding: '0 4px',
                    borderRadius: '3px',
                    background: '#10b981',
                    color: '#fff',
                    fontWeight: 700,
                  }}
                >
                  +{catCounts.include}
                </span>
              )}
              {catCounts.exclude > 0 && (
                <span
                  style={{
                    fontSize: '9.5px',
                    padding: '0 4px',
                    borderRadius: '3px',
                    background: '#ef4444',
                    color: '#fff',
                    fontWeight: 700,
                  }}
                >
                  -{catCounts.exclude}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Category Items List */}
        {!isCollapsed && (
          <div
            style={{
              marginTop: '4px',
              display: 'flex',
              flexDirection: 'column',
              gap: '1px',
              paddingLeft: '2px',
            }}
          >
            {sortedNodes.map((node) => renderItemRow(node, 0))}
          </div>
        )}
      </div>
    );
  };

  return (
    <aside
      style={{
        width: 'var(--sidebar-width)',
        height: 'calc(100vh - var(--header-height) - var(--status-bar-height))',
        background: 'var(--bg-surface)',
        borderRight: '1px solid var(--border-default)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        userSelect: 'none',
      }}
    >
      {/* 1. Header Toolbar */}
      <div
        style={{
          padding: '0.75rem',
          borderBottom: '1px solid var(--border-default)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          background: 'var(--bg-surface-elevated)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600, fontSize: '13px' }}>
            <TagIcon size={14} color="var(--accent-primary)" />
            <span>Tag Browser</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {/* Sort Toggle */}
            <button
              onClick={() => setTagTreeSortBy(tagTreeSortBy === 'name' ? 'count' : 'name')}
              title={`Sorting by ${tagTreeSortBy === 'name' ? 'Name (A-Z)' : 'Count (descending)'}. Click to switch.`}
              className="btn btn-ghost"
              style={{ padding: '2px 6px', fontSize: '11px', gap: '3px' }}
            >
              {tagTreeSortBy === 'name' ? <ArrowDownAZ size={13} /> : <ArrowDownWideNarrow size={13} />}
            </button>

            {/* Expand / Collapse All */}
            <button
              onClick={expandAll}
              title="Expand All Categories"
              className="btn btn-ghost"
              style={{ padding: '2px 4px' }}
            >
              <ChevronDown size={13} />
            </button>
            <button
              onClick={collapseAll}
              title="Collapse All Categories"
              className="btn btn-ghost"
              style={{ padding: '2px 4px' }}
            >
              <ChevronRight size={13} />
            </button>

            {/* Clear All */}
            {activePills.length > 0 && (
              <button
                onClick={clearTagTreeFilters}
                title="Reset all filters"
                className="btn btn-ghost"
                style={{
                  padding: '2px 6px',
                  fontSize: '11px',
                  color: '#ef4444',
                  gap: '3px',
                }}
              >
                <XCircle size={12} />
                <span>Clear ({activePills.length})</span>
              </button>
            )}
          </div>
        </div>

        {/* Tree Quick Search Input */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-sm)',
            padding: '2px 6px',
            gap: '6px',
          }}
        >
          <Search size={12} color="var(--text-muted)" />
          <input
            type="text"
            value={tagTreeSearchQuery}
            onChange={(e) => setTagTreeSearchQuery(e.target.value)}
            placeholder="Filter categories / tags..."
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '11.5px',
              width: '100%',
            }}
          />
          {tagTreeSearchQuery && (
            <button
              onClick={() => setTagTreeSearchQuery('')}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
            >
              <X size={11} />
            </button>
          )}
        </div>
      </div>

      {/* 2. Active Filter Chips Bar */}
      {activePills.length > 0 && (
        <div
          style={{
            padding: '6px 8px',
            background: 'rgba(255, 255, 255, 0.02)',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '4px',
            maxHeight: '90px',
            overflowY: 'auto',
          }}
        >
          {activePills.map((pill) => {
            const isInc = pill.state === 'include';
            return (
              <span
                key={`${pill.category}:${pill.value}`}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '3px',
                  padding: '1px 6px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '10.5px',
                  fontWeight: 600,
                  background: isInc ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: isInc ? '#10b981' : '#ef4444',
                  border: isInc ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
                }}
              >
                <span>{isInc ? '+' : '-'} {pill.value}</span>
                <button
                  onClick={() => setTagFilter(pill.category, pill.value, null)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'inherit',
                    padding: 0,
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <X size={10} />
                </button>
              </span>
            );
          })}
        </div>
      )}

      {/* 3. Scrollable Tree Body */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0.75rem',
        }}
      >
        {/* Authors */}
        {renderCategorySection('authors', 'Authors', <User size={13} />, authorsData)}

        {/* Series */}
        {renderCategorySection('series', 'Series', <Bookmark size={13} />, seriesData)}

        {/* Tags (Hierarchical) */}
        {renderCategorySection('tags', 'Tags', <TagIcon size={13} />, tagsTree)}

        {/* Formats */}
        {renderCategorySection('formats', 'Formats', <HardDrive size={13} />, formatsData)}

        {/* Publishers */}
        {renderCategorySection('publishers', 'Publishers', <Building size={13} />, publishersData)}

        {/* Ratings */}
        {renderCategorySection('ratings', 'Rating', <Star size={13} />, ratingsData)}

        {/* Identifiers */}
        {renderCategorySection('identifiers', 'Identifiers', <Hash size={13} />, identifiersData)}

        {/* Custom Columns */}
        {Object.entries(customColumnsData).map(([colKey, colObj]) =>
          renderCategorySection(
            `cc:${colKey}`,
            colObj.name,
            <Settings size={13} />,
            colObj.items
          )
        )}

        {/* Classification / Taxonomies (BISAC / DDC) */}
        {taxonomyTree.length > 0 &&
          renderCategorySection(
            'taxonomies',
            'Taxonomies',
            <Layers size={13} />,
            taxonomyTree.map((t) => ({
              id: `taxonomies:${t.path}`,
              name: t.name,
              fullPath: t.path,
              count: t.book_count || 0,
              category: 'taxonomies',
            }))
          )}
      </div>
    </aside>
  );
};
