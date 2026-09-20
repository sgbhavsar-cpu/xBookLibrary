import React, { useMemo, useState } from 'react';
import {
  Bookmark,
  ChevronDown,
  ChevronRight,
  Filter,
  Layers,
  Tag,
  User,
  XCircle,
} from 'lucide-react';
import { useStore } from '../store/useStore';
import type { TaxonomyNode } from '../types';

export const FilterSidebar: React.FC = () => {
  const {
    books,
    taxonomyTree,
    selectedTaxonomyPath,
    setSelectedTaxonomyPath,
    selectedAuthor,
    setSelectedAuthor,
    selectedFormat,
    setSelectedFormat,
    selectedSeries,
    setSelectedSeries,
  } = useStore();

  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});

  const toggleExpand = (path: string) => {
    setExpandedNodes((prev) => ({ ...prev, [path]: !prev[path] }));
  };

  // Derive unique authors and counts
  const authorsList = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const b of books) {
      for (const a of b.authors) {
        counts[a] = (counts[a] || 0) + 1;
      }
    }
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 15);
  }, [books]);

  // Derive unique formats and counts
  const formatsList = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const b of books) {
      for (const f of b.formats) {
        counts[f.format] = (counts[f.format] || 0) + 1;
      }
    }
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [books]);

  // Derive unique series and counts
  const seriesWithCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const b of books) {
      if (b.series) {
        counts[b.series] = (counts[b.series] || 0) + 1;
      }
    }
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [books]);

  const hasActiveFilter = Boolean(
    selectedTaxonomyPath || selectedAuthor || selectedFormat || selectedSeries
  );

  const clearAllFilters = () => {
    setSelectedTaxonomyPath(null);
    setSelectedAuthor(null);
    setSelectedFormat(null);
    setSelectedSeries(null);
  };

  const renderTaxonomyNode = (node: TaxonomyNode) => {
    const isExpanded = expandedNodes[node.path];
    const isSelected = selectedTaxonomyPath === node.path;
    const hasChildren = node.children && node.children.length > 0;

    return (
      <div key={node.path} style={{ marginLeft: '12px' }}>
        <div
          onClick={() => setSelectedTaxonomyPath(isSelected ? null : node.path)}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '4px 8px',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            fontSize: '12.5px',
            background: isSelected ? 'var(--accent-surface)' : 'transparent',
            color: isSelected ? 'var(--accent-primary)' : 'var(--text-primary)',
            fontWeight: isSelected ? 600 : 400,
            transition: 'background var(--transition-fast)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', overflow: 'hidden' }}>
            {hasChildren && (
              <span
                onClick={(e) => {
                  e.stopPropagation();
                  toggleExpand(node.path);
                }}
                style={{ cursor: 'pointer', display: 'flex' }}
              >
                {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </span>
            )}
            <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
              {node.name}
            </span>
          </div>
          {node.book_count !== undefined && (
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              {node.book_count}
            </span>
          )}
        </div>

        {hasChildren && isExpanded && (
          <div>
            {node.children!.map((child) => renderTaxonomyNode(child))}
          </div>
        )}
      </div>
    );
  };

  return (
    <aside style={{
      width: 'var(--sidebar-width)',
      height: 'calc(100vh - var(--header-height) - var(--status-bar-height))',
      background: 'var(--bg-surface)',
      borderRight: '1px solid var(--border-default)',
      display: 'flex',
      flexDirection: 'column',
      overflowY: 'auto',
      padding: '1rem',
      gap: '1.25rem',
      userSelect: 'none',
    }}>
      {/* Sidebar Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600, fontSize: '13px' }}>
          <Filter size={15} color="var(--accent-primary)" />
          <span>Catalog Filters</span>
        </div>
        {hasActiveFilter && (
          <button
            onClick={clearAllFilters}
            className="btn btn-ghost"
            style={{ padding: '2px 6px', fontSize: '11px', gap: '4px' }}
          >
            <XCircle size={12} />
            <span>Clear</span>
          </button>
        )}
      </div>

      {/* Formats Badges */}
      <div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '12px',
          fontWeight: 600,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginBottom: '8px',
        }}>
          <Tag size={13} />
          <span>Formats</span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {formatsList.map(([fmt, count]) => {
            const active = selectedFormat === fmt;
            return (
              <button
                key={fmt}
                onClick={() => setSelectedFormat(active ? null : fmt)}
                style={{
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-full)',
                  border: active ? '1px solid var(--accent-primary)' : '1px solid var(--border-default)',
                  background: active ? 'var(--accent-surface)' : 'var(--bg-surface-elevated)',
                  color: active ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  fontSize: '11.5px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <span>{fmt}</span>
                <span style={{ fontSize: '10px', opacity: 0.7 }}>({count})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Taxonomy Tree */}
      <div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '12px',
          fontWeight: 600,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginBottom: '8px',
        }}>
          <Layers size={13} />
          <span>Taxonomies</span>
        </div>
        {taxonomyTree.length === 0 ? (
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic', paddingLeft: '8px' }}>
            No taxonomies configured
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            {taxonomyTree.map((rootNode) => renderTaxonomyNode(rootNode))}
          </div>
        )}
      </div>

      {/* Authors Filter */}
      <div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '12px',
          fontWeight: 600,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginBottom: '8px',
        }}>
          <User size={13} />
          <span>Top Authors</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {authorsList.map(([author, count]) => {
            const isSelected = selectedAuthor === author;
            return (
              <div
                key={author}
                onClick={() => setSelectedAuthor(isSelected ? null : author)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '4px 8px',
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                  fontSize: '12.5px',
                  background: isSelected ? 'var(--accent-surface)' : 'transparent',
                  color: isSelected ? 'var(--accent-primary)' : 'var(--text-primary)',
                  fontWeight: isSelected ? 600 : 400,
                  transition: 'background var(--transition-fast)',
                }}
              >
                <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                  {author}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {count}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Series Filter */}
      {seriesWithCounts.length > 0 && (
        <div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '12px',
              fontWeight: 600,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: '8px',
            }}
          >
            <Bookmark size={13} />
            <span>Series</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            {seriesWithCounts.map(([series, count]) => {
              const isSelected = selectedSeries === series;
              return (
                <div
                  key={series}
                  onClick={() => setSelectedSeries(isSelected ? null : series)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '4px 8px',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer',
                    fontSize: '12.5px',
                    background: isSelected ? 'var(--accent-surface)' : 'transparent',
                    color: isSelected ? 'var(--accent-primary)' : 'var(--text-primary)',
                    fontWeight: isSelected ? 600 : 400,
                    transition: 'background var(--transition-fast)',
                  }}
                >
                  <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                    {series}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {count}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </aside>
  );
};
