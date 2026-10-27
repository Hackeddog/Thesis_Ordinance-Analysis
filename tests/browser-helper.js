// Native Bun WebSocket/CDP avoids Node pipe/ws compatibility issues on Windows.
// Playwright is used only to locate its managed Chromium executable.
import { chromium } from 'playwright';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

export async function connectCDP(url) {
  const socket = new WebSocket(url);
  const pending = new Map();
  const listeners = new Map();
  let sequence = 0;
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const call = pending.get(message.id);
      if (!call) return;
      clearTimeout(call.timer); pending.delete(message.id);
      if (message.error) call.reject(new Error(JSON.stringify(message.error)));
      else call.resolve(message.result);
    } else {
      for (const fn of listeners.get(message.method) || []) fn(message.params);
    }
  });
  socket.addEventListener('close', () => {
    for (const call of pending.values()) { clearTimeout(call.timer); call.reject(new Error('CDP socket closed')); }
    pending.clear();
  });
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Native CDP WebSocket timeout')), 10000);
    socket.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
    socket.addEventListener('error', () => { clearTimeout(timer); reject(new Error('Native CDP WebSocket failed')); }, { once: true });
  });
  return {
    send(method, params = {}, timeout = 15000) {
      return new Promise((resolve, reject) => {
        const id = ++sequence;
        const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, timeout);
        pending.set(id, { resolve, reject, timer });
        socket.send(JSON.stringify({ id, method, params }));
      });
    },
    on(method, callback) { listeners.set(method, [...(listeners.get(method) || []), callback]); },
    close() { socket.close(); },
  };
}

export async function launchTestBrowser() {
  const profile = await mkdtemp(join(tmpdir(), 'ordinance-dashboard-browser-'));
  const child = Bun.spawn([
    chromium.executablePath(), '--headless=new', '--disable-gpu', '--no-sandbox',
    '--disable-dev-shm-usage', '--disable-background-networking', '--no-first-run', '--no-default-browser-check',
    '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0',
    `--user-data-dir=${profile}`, 'about:blank',
  ], { stdout: 'ignore', stderr: 'pipe' });
  const diagnostics = new Response(child.stderr).text();
  let cdp;
  async function close() {
    if (cdp) {
      await cdp.send('Browser.close', {}, 2000).catch(() => {});
      cdp.close();
    }
    if (child.exitCode === null) child.kill();
    await child.exited;
    await diagnostics;
    await rm(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
  }
  try {
    let port;
    for (let attempt = 0; attempt < 200; attempt++) {
      try { port = Number((await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]); }
      catch { /* Browser is still starting. */ }
      if (port) break;
      if (child.exitCode !== null) throw new Error('Chromium exited before opening CDP: ' + (await diagnostics).slice(-1500));
      await Bun.sleep(100);
    }
    if (!port) throw new Error('Chromium did not open its loopback debugging port in 20 seconds.');
    const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    cdp = await connectCDP(targets.find(target => target.type === 'page').webSocketDebuggerUrl);
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    return { cdp, close };
  } catch (error) {
    await close();
    throw error;
  }
}
