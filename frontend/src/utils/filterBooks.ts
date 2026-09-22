/**
 * Universal Book Filtering Engine for xBookLibrary.
 * Evaluates text search, Calibre tri-state tag tree filters, virtual libraries, and taxonomies.
 */

import type { Book, TagTreeFilter, VirtualLibrary } from '../types';

export interface FilterOptions {
  searchQuery?: string;
  tagTreeFilter?: TagTreeFilter;
  activeVirtualLibrary?: string | null;
  virtualLibraries?: VirtualLibrary[];
  // Legacy / Direct single filters for backward compatibility
  selectedAuthor?: string | null;
  selectedFormat?: string | null;
  selectedSeries?: string | null;
  selectedTaxonomyPath?: string | null;
}

/**
 * Normalizes rating number (Calibre uses 0-10 or 0-5) into standard star string bucket.
 */
export function getRatingBucket(rating?: number): string {
  if (!rating || rating <= 0) return 'Unrated';
  // If Calibre 10-point scale (e.g. 10 = 5 stars, 8 = 4 stars)
  const normalized = rating > 5 ? Math.round(rating / 2) : Math.round(rating);
  if (normalized >= 5) return '5 Stars';
  if (normalized === 4) return '4 Stars';
  if (normalized === 3) return '3 Stars';
  if (normalized === 2) return '2 Stars';
  if (normalized === 1) return '1 Star';
  return 'Unrated';
}

/**
 * Checks if a book tag matches a filter tag either exactly or hierarchically
 * e.g. filter tag "Fiction" matches book tag "Fiction.Sci-Fi" or "Fiction / Space"
 */
function tagMatchesHierarchical(bookTag: string, filterTag: string): boolean {
  const bLower = bookTag.toLowerCase().trim();
  const fLower = filterTag.toLowerCase().trim();

  if (bLower === fLower) return true;
  if (bLower.startsWith(`${fLower}.`)) return true;
  if (bLower.startsWith(`${fLower}/`)) return true;
  if (bLower.startsWith(`${fLower} / `)) return true;

  return false;
}

/**
 * Evaluates whether a single book satisfies all filter criteria.
 */
export function matchesBookFilter(book: Book, options: FilterOptions): boolean {
  const {
    searchQuery = '',
    tagTreeFilter = {},
    activeVirtualLibrary = null,
    virtualLibraries = [],
    selectedAuthor = null,
    selectedFormat = null,
    selectedSeries = null,
    selectedTaxonomyPath = null,
  } = options;

  // 1. Text Search Query
  if (searchQuery && searchQuery.trim()) {
    const q = searchQuery.toLowerCase().trim();
    const titleMatch = book.title?.toLowerCase().includes(q);
    const authorMatch = book.authors?.some((a) => a.toLowerCase().includes(q));
    const tagMatch = book.tags?.some((t) => t.toLowerCase().includes(q));
    const seriesMatch = book.series?.toLowerCase().includes(q);
    const publisherMatch = book.publisher?.toLowerCase().includes(q);
    const bisacMatch = book.classification?.bisac_heading?.toLowerCase().includes(q);

    if (!titleMatch && !authorMatch && !tagMatch && !seriesMatch && !publisherMatch && !bisacMatch) {
      return false;
    }
  }

  // 2. Legacy / Direct single-select filters (for backward compatibility)
  if (selectedAuthor && !book.authors?.includes(selectedAuthor)) {
    return false;
  }
  if (selectedFormat && !book.formats?.some((f) => f.format.toUpperCase() === selectedFormat.toUpperCase())) {
    return false;
  }
  if (selectedSeries && book.series !== selectedSeries) {
    return false;
  }
  if (selectedTaxonomyPath) {
    const bisac = (book.classification?.bisac_heading || '').toLowerCase();
    if (!bisac.includes(selectedTaxonomyPath.toLowerCase())) {
      return false;
    }
  }

  // 3. Virtual Library Rule Query
  if (activeVirtualLibrary && virtualLibraries.length > 0) {
    const vl = virtualLibraries.find((v) => v.name === activeVirtualLibrary);
    if (vl && vl.query.trim()) {
      const q = vl.query.toLowerCase();
      if (q.includes('#read_status:')) {
        const expected = q.split('#read_status:')[1]?.split(' ')[0]?.replace(/["']/g, '');
        const current = (book.custom_values?.read_status || '').toLowerCase();
        if (expected && !current.includes(expected.toLowerCase())) return false;
      }
      if (q.includes('series:')) {
        const expected = q.split('series:')[1]?.split(' ')[0]?.replace(/["']/g, '');
        const current = (book.series || '').toLowerCase();
        if (expected && !current.includes(expected.toLowerCase())) return false;
      }
      if (q.includes('tag:') || q.includes('tags:')) {
        const match = q.match(/tags?:"?([^"\s]+)"?/);
        const expected = match ? match[1].toLowerCase() : '';
        if (expected && !book.tags?.some((t) => t.toLowerCase().includes(expected))) return false;
      }
    }
  }

  // 4. Calibre Tri-State Tag Tree Filter
  const categories = Object.keys(tagTreeFilter);
  if (categories.length === 0) return true;

  for (const cat of categories) {
    const itemMap = tagTreeFilter[cat];
    if (!itemMap) continue;

    const entries = Object.entries(itemMap);
    if (entries.length === 0) continue;

    const includedItems = entries.filter(([_, state]) => state === 'include').map(([name]) => name);
    const excludedItems = entries.filter(([_, state]) => state === 'exclude').map(([name]) => name);

    // Evaluate Category Rules
    if (cat === 'authors') {
      const bookAuthors = book.authors || [];
      // Excluded: if book has ANY excluded author, reject
      if (excludedItems.some((ex) => bookAuthors.includes(ex))) {
        return false;
      }
      // Included: book must have AT LEAST ONE included author
      if (includedItems.length > 0 && !includedItems.some((inc) => bookAuthors.includes(inc))) {
        return false;
      }
    } else if (cat === 'series') {
      const bookSeries = book.series;
      if (excludedItems.some((ex) => bookSeries === ex)) {
        return false;
      }
      if (includedItems.length > 0 && (!bookSeries || !includedItems.includes(bookSeries))) {
        return false;
      }
    } else if (cat === 'formats') {
      const bookFmts = (book.formats || []).map((f) => f.format.toUpperCase());
      if (excludedItems.some((ex) => bookFmts.includes(ex.toUpperCase()))) {
        return false;
      }
      if (includedItems.length > 0 && !includedItems.some((inc) => bookFmts.includes(inc.toUpperCase()))) {
        return false;
      }
    } else if (cat === 'publishers') {
      const bookPub = book.publisher;
      if (excludedItems.some((ex) => bookPub === ex)) {
        return false;
      }
      if (includedItems.length > 0 && (!bookPub || !includedItems.includes(bookPub))) {
        return false;
      }
    } else if (cat === 'ratings') {
      const bookRatingBucket = getRatingBucket(book.rating);
      if (excludedItems.some((ex) => bookRatingBucket === ex)) {
        return false;
      }
      if (includedItems.length > 0 && !includedItems.includes(bookRatingBucket)) {
        return false;
      }
    } else if (cat === 'tags') {
      const bookTags = book.tags || [];
      // Excluded tags (with hierarchical child matching)
      for (const ex of excludedItems) {
        if (bookTags.some((bt) => tagMatchesHierarchical(bt, ex))) {
          return false;
        }
      }
      // Included tags (with hierarchical child matching)
      if (includedItems.length > 0) {
        const matchesAnyIncluded = includedItems.some((inc) =>
          bookTags.some((bt) => tagMatchesHierarchical(bt, inc))
        );
        if (!matchesAnyIncluded) {
          return false;
        }
      }
    } else if (cat === 'identifiers') {
      const idTypes = Object.keys(book.identifiers || {}).map((k) => k.toLowerCase());
      if (book.isbn) idTypes.push('isbn');

      if (excludedItems.some((ex) => idTypes.includes(ex.toLowerCase()))) {
        return false;
      }
      if (includedItems.length > 0 && !includedItems.some((inc) => idTypes.includes(inc.toLowerCase()))) {
        return false;
      }
    } else if (cat.startsWith('cc:')) {
      // Custom column filter (e.g. cc:read_status)
      const colKey = cat.replace('cc:', '');
      const rawVal = book.custom_values?.[colKey];
      const valStr = rawVal !== undefined && rawVal !== null ? String(rawVal) : 'None';

      if (excludedItems.includes(valStr)) {
        return false;
      }
      if (includedItems.length > 0 && !includedItems.includes(valStr)) {
        return false;
      }
    }
  }

  return true;
}

/**
 * Filter an array of books against the filter options.
 */
export function filterBooks(books: Book[], options: FilterOptions): Book[] {
  if (!Array.isArray(books)) return [];
  return books.filter((b) => matchesBookFilter(b, options));
}
