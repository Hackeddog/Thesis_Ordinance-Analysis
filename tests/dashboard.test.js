import { test, expect } from 'bun:test';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { validateData, filterTopics, rankTopics, composition, topicSummary, percent } from '../dashboard/data-utils.js';

const root = resolve(import.meta.dir, '..');
const data = JSON.parse(readFileSync(resolve(root, 'dashboard/data/results.json'), 'utf8'));

test('publication contains complete fresh coarse-grained evidence', () => {
  expect(validateData(data)).toBe(data);
  expect(data.sensitivity_seeds).toEqual([43, 44]);
  expect(data.parameters).toEqual({ neighbors: 30, min_dist: 0.1, min_cluster_size: 60, min_samples: 15, umap_components: 5 });
  for (const key of ['lexical', 'semantic']) {
    const metrics = JSON.parse(readFileSync(resolve(root, 'artifacts/coarse_grained_retrain/evidence/coarse_grained', key, 'metrics.json'), 'utf8'));
    expect(data.models[key].metrics).toEqual(metrics);
    expect(metrics.sections).toBe(data.units);
  }
});
test('download fingerprints match all exported bytes', () => {
  const hashes = JSON.parse(readFileSync(resolve(root, 'dashboard/downloads/checksums.json'), 'utf8'));
  expect(Object.keys(hashes).length).toBeGreaterThan(15);
  for (const [file, sha] of Object.entries(hashes)) {
    expect(createHash('sha256').update(readFileSync(resolve(root, 'dashboard', file))).digest('hex')).toBe(sha);
  }
});
test('every download link resolves to a real local artifact', () => {
  const html = readFileSync(resolve(root, 'dashboard/index.html'), 'utf8');
  for (const match of html.matchAll(/href="(downloads\/[^"#]+)"/g)) expect(existsSync(resolve(root, 'dashboard', match[1]))).toBe(true);
});
test('rejects corrupt, missing or misleading temporal data', () => {
  const bad = structuredClone(data);
  bad.models.semantic.topics[0].shares[0] += .01;
  expect(() => validateData(bad)).toThrow();
  const incomplete = structuredClone(data); incomplete.fit_count = 2;
  expect(() => validateData(incomplete)).toThrow();
  const wrong = structuredClone(data); wrong.configuration = 'conservative';
  expect(() => validateData(wrong)).toThrow();
});
test('all yearly compositions retain 100 percent including outliers', () => {
  for (const model of Object.values(data.models)) for (let i = 0; i < 10; i++) {
    const rows = composition(model, i);
    expect(rows.reduce((sum, row) => sum + row.share, 0)).toBeCloseTo(1, 10);
    expect(rows.at(-1).share).toBe(model.outlier_shares[i]);
  }
});
test('search, categories and rankings include all actual topics', () => {
  for (const model of Object.values(data.models)) {
    expect(filterTopics(model.topics, '', 'all')).toHaveLength(model.topics.length);
    const first = rankTopics(model.topics)[0];
    expect(filterTopics(model.topics, first.keywords[0].toUpperCase(), 'all').some(t => t.id === first.id)).toBe(true);
    expect(filterTopics(model.topics, '', first.category).every(t => t.category === first.category)).toBe(true);
    expect(filterTopics(model.topics, 'zzzz-unmatched', 'all')).toHaveLength(0);
  }
});
test('peak ties and percentage-point changes are not causal claims', () => {
  const stats = topicSummary({ shares: [.1, .2, .2] }, [2020, 2021, 2022]);
  expect(stats.peakYears).toEqual([2021, 2022]);
  expect(stats.changePoints).toBeCloseTo(10);
  expect(percent(null)).toBe('Not available');
  expect(percent(0)).toBe('0.0%');
});
