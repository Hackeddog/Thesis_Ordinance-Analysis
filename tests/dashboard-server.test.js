import { test, expect, afterAll } from 'bun:test';
import { createServer } from '../scripts/serve_dashboard.js';
const server = createServer({ port: 0 });
afterAll(() => server.stop(true));
test('serves the plain HTML and scripts without exposing repository files', async () => {
  const response = await fetch(server.url);
  expect(response.status).toBe(200);
  expect(await response.text()).toContain('Davao Ordinance Observatory');
  expect(response.headers.get('X-Content-Type-Options')).toBe('nosniff');
  expect((await fetch(new URL('/app.js', server.url))).status).toBe(200);
  for (const path of ['/missing', '/downloads', '/.git/config', '/configs/coarse_grained_retrain.json', '/%2e%2e%2fREADME.md']) {
    expect((await fetch(new URL(path, server.url))).status).toBe(404);
  }
});
test('rejects writes and supports HEAD and malformed encodings', async () => {
  expect((await fetch(server.url, { method: 'POST' })).status).toBe(405);
  const head = await fetch(server.url, { method: 'HEAD' });
  expect(head.status).toBe(200);
  expect(await head.text()).toBe('');
  expect((await fetch(new URL('/%ZZ', server.url))).status).toBe(400);
});
