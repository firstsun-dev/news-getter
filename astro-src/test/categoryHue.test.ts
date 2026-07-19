import { test } from 'node:test';
import assert from 'node:assert/strict';
import { categoryHue } from '../src/lib/categoryHue.ts';

test('categoryHue returns a value in [0, 360)', () => {
  for (const name of ['AI', 'Finance', 'Global', 'Technology', 'TW News', '中文類別']) {
    const h = categoryHue(name);
    assert.ok(h >= 0 && h < 360, `${name} -> ${h} out of range`);
  }
});

test('categoryHue is deterministic (same name -> same hue)', () => {
  assert.equal(categoryHue('AI'), categoryHue('AI'));
  assert.equal(categoryHue('Finance'), categoryHue('Finance'));
});

test('categoryHue is stable across runs (snapshot)', () => {
  // Golden-angle hash snapshots — update only if the hash deliberately changes.
  assert.equal(categoryHue('AI'), 164);
  assert.equal(categoryHue('Finance'), 179);
  assert.equal(categoryHue('Global'), 302);
});

test('categoryHue differs for distinct categories', () => {
  const hues = new Set(['AI', 'Finance', 'Global', 'Technology'].map(categoryHue));
  assert.ok(hues.size >= 3, 'expected at least 3 distinct hues');
});