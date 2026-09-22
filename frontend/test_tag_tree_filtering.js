/**
 * Test script for Calibre Tag Tree & Tri-State filtering logic.
 */
import assert from 'node:assert';
import { buildHierarchicalTagTree, sortTagTreeNodes, filterTagTreeNodes } from './src/utils/tagTreeParser.ts';
import { matchesBookFilter, filterBooks, getRatingBucket } from './src/utils/filterBooks.ts';

console.log('--- Testing Tag Tree Parser & Hierarchy ---');

const sampleTags = [
  { name: 'Fiction.Sci-Fi.Cyberpunk', count: 2 },
  { name: 'Fiction.Sci-Fi.Space Opera', count: 3 },
  { name: 'Fiction.Fantasy', count: 4 },
  { name: 'Non-Fiction / Biography', count: 1 },
];

const tree = buildHierarchicalTagTree(sampleTags, 'tags');
assert.strictEqual(tree.length, 2, 'Should have 2 root nodes (Fiction, Non-Fiction)');

const fictionNode = tree.find((n) => n.name === 'Fiction');
assert.ok(fictionNode, 'Fiction node should exist');
assert.strictEqual(fictionNode.count, 9, 'Fiction node total count should aggregate 2+3+4 = 9');
assert.strictEqual(fictionNode.children?.length, 2, 'Fiction should have 2 children (Sci-Fi, Fantasy)');

const sciFiNode = fictionNode.children?.find((n) => n.name === 'Sci-Fi');
assert.ok(sciFiNode, 'Sci-Fi node should exist');
assert.strictEqual(sciFiNode.count, 5, 'Sci-Fi should aggregate 2+3 = 5');

// Test tree sorting
const sortedByCount = sortTagTreeNodes(tree, 'count');
assert.strictEqual(sortedByCount[0].name, 'Fiction', 'Fiction (9) should be first by count');

// Test tree search filtering
const filteredTree = filterTagTreeNodes(tree, 'cyber');
assert.strictEqual(filteredTree.length, 1, 'Should find Fiction branch containing cyberpunk');
console.log('✓ Tag Tree Parser & Hierarchy tests passed!');

console.log('--- Testing Calibre Tri-State Filter Engine ---');

const book1 = {
  id: 1,
  title: 'Dune',
  authors: ['Frank Herbert'],
  series: 'Dune',
  formats: [{ format: 'EPUB', name: 'Dune', uncompressed_size: 1000 }],
  tags: ['Fiction.Sci-Fi.Space Opera', 'Classic'],
  publisher: 'Chilton Books',
  rating: 5,
  identifiers: { isbn: '12345' },
};

const book2 = {
  id: 2,
  title: 'Foundation',
  authors: ['Isaac Asimov'],
  series: 'Foundation',
  formats: [{ format: 'PDF', name: 'Foundation', uncompressed_size: 2000 }],
  tags: ['Fiction.Sci-Fi', 'Classic'],
  publisher: 'Gnome Press',
  rating: 4,
  identifiers: { isbn: '67890' },
};

const book3 = {
  id: 3,
  title: 'Neuromancer',
  authors: ['William Gibson'],
  formats: [{ format: 'EPUB', name: 'Neuromancer', uncompressed_size: 1500 }],
  tags: ['Fiction.Sci-Fi.Cyberpunk'],
  rating: 5,
  identifiers: { amazon: 'B000' },
};

const allBooks = [book1, book2, book3];

// 1. Positive Include Author
const herbOnly = filterBooks(allBooks, {
  tagTreeFilter: {
    authors: { 'Frank Herbert': 'include' },
  },
});
assert.strictEqual(herbOnly.length, 1);
assert.strictEqual(herbOnly[0].title, 'Dune');
console.log('✓ Include author filter passed');

// 2. Negative Exclude Author
const noAsimov = filterBooks(allBooks, {
  tagTreeFilter: {
    authors: { 'Isaac Asimov': 'exclude' },
  },
});
assert.strictEqual(noAsimov.length, 2);
assert.ok(!noAsimov.some((b) => b.title === 'Foundation'));
console.log('✓ Exclude author filter passed');

// 3. Hierarchical Tag Include (Fiction matches all 3 books)
const allFiction = filterBooks(allBooks, {
  tagTreeFilter: {
    tags: { 'Fiction': 'include' },
  },
});
assert.strictEqual(allFiction.length, 3, 'Fiction should hierarchically match Dune, Foundation, Neuromancer');
console.log('✓ Hierarchical tag include passed');

// 4. Hierarchical Tag Exclude (Exclude Cyberpunk should exclude Neuromancer)
const noCyberpunk = filterBooks(allBooks, {
  tagTreeFilter: {
    tags: { 'Fiction.Sci-Fi.Cyberpunk': 'exclude' },
  },
});
assert.strictEqual(noCyberpunk.length, 2);
assert.ok(!noCyberpunk.some((b) => b.title === 'Neuromancer'));
console.log('✓ Hierarchical tag exclude passed');

// 5. Conjunction Across Multiple Categories:
// Include EPUB (+), Exclude Cyberpunk (-), Include 5 Stars (+) -> only Dune!
const combo = filterBooks(allBooks, {
  tagTreeFilter: {
    formats: { 'EPUB': 'include' },
    tags: { 'Fiction.Sci-Fi.Cyberpunk': 'exclude' },
    ratings: { '5 Stars': 'include' },
  },
});
assert.strictEqual(combo.length, 1);
assert.strictEqual(combo[0].title, 'Dune');
console.log('✓ Multi-category conjunction (Include format + Exclude tag + Include rating) passed');

console.log('ALL CALIBRE TAG BROWSER TESTS PASSED SUCCESSFULLY!');
