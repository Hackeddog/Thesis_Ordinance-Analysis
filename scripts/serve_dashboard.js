// Local-only static preview. Production is the dashboard/ folder, with no server/API.
import { resolve, relative, sep } from 'node:path';
import { realpath, stat } from 'node:fs/promises';

export const dashboardRoot = resolve(import.meta.dir, '../dashboard');

export function createServer({ port = 3000, root = dashboardRoot } = {}) {
  root = resolve(root);
  return Bun.serve({
    hostname: '127.0.0.1',
    port,
    async fetch(request) {
      const headers = {
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Cache-Control': 'no-cache',
      };
      if (!['GET', 'HEAD'].includes(request.method)) return new Response('Method not allowed', { status: 405, headers: { ...headers, Allow: 'GET, HEAD' } });
      let pathname;
      try { pathname = decodeURIComponent(new URL(request.url).pathname); }
      catch { return new Response('Invalid URL', { status: 400, headers }); }
      if (pathname.includes('\\') || pathname.includes('\0')) return new Response('Invalid path', { status: 400, headers });
      const path = resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
      const rel = relative(root, path);
      if (rel === '..' || rel.startsWith('..' + sep) || resolve(path) === root) return new Response('Not found', { status: 404, headers });
      try {
        const canonical = await realpath(path);
        const canonicalRelative = relative(root, canonical);
        if (canonicalRelative === '..' || canonicalRelative.startsWith('..' + sep) || !(await stat(canonical)).isFile()) return new Response('Not found', { status: 404, headers });
      } catch { return new Response('Not found', { status: 404, headers }); }
      const file = Bun.file(path);
      return new Response(request.method === 'HEAD' ? null : file, { headers: { ...headers, 'Content-Type': file.type, 'Content-Length': String(file.size) } });
    },
  });
}
if (import.meta.main) {
  const server = createServer({ port: Number(process.env.PORT || 3000) });
  console.log('Davao Ordinance Observatory: ' + server.url);
}
