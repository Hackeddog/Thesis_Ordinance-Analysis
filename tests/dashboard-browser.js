// Real Chromium + native Bun CDP: no Node runtime, frontend framework or mock results.
import assert from 'node:assert/strict';
import { mkdir, readFile, access } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { launchTestBrowser } from './browser-helper.js';
import { createServer } from '../scripts/serve_dashboard.js';

const require = createRequire(import.meta.url);
const axeSource = await readFile(require.resolve('axe-core/axe.min.js'), 'utf8');
const out = resolve(import.meta.dir, '../test-results/dashboard');
await mkdir(out, { recursive: true });
const server = createServer({ port: 0 });
const data = JSON.parse(await readFile(resolve(import.meta.dir, '../dashboard/data/results.json'), 'utf8'));
let session, nested;
try {
  session = await launchTestBrowser();
  const { cdp } = session;
  const errors = [];
  cdp.on('Runtime.exceptionThrown', event => errors.push(event.exceptionDetails.exception?.description || event.exceptionDetails.text));
  console.log('Chromium connected over native Bun CDP.');
  const evaluate = async expression => {
    const result = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true }, 30000);
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
    return result.result.value;
  };
  const query = selector => `document.querySelector(${JSON.stringify(selector)})`;
  async function waitFor(expression, description) {
    for (let i = 0; i < 150; i++) {
      if (await evaluate(expression)) return;
      await Bun.sleep(100);
    }
    throw new Error('Timed out: ' + description);
  }
  async function navigate(url) {
    await cdp.send('Page.navigate', { url });
    await waitFor(`document.readyState === 'complete' && ${query('#dashboard')} && !${query('#dashboard')}.hidden`, 'loaded dashboard');
  }
  async function viewport(width, height = 844) {
    await cdp.send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });
  }
  async function screenshot(name, full = false) {
    const options = { format: 'png', captureBeyondViewport: full };
    if (full) {
      const layout = await cdp.send('Page.getLayoutMetrics');
      options.clip = { x: 0, y: 0, width: layout.cssContentSize.width, height: layout.cssContentSize.height, scale: 1 };
    }
    const shot = await cdp.send('Page.captureScreenshot', options);
    await Bun.write(resolve(out, name), Buffer.from(shot.data, 'base64'));
  }
  async function click(selector) {
    await evaluate(`${query(selector)}.scrollIntoView({block:'center',behavior:'instant'})`);
    await Bun.sleep(50);
    const point = await evaluate(`(()=>{const r=${query(selector)}.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
    await cdp.send('Input.dispatchMouseEvent', { type: 'mousePressed', ...point, button: 'left', clickCount: 1 });
    await cdp.send('Input.dispatchMouseEvent', { type: 'mouseReleased', ...point, button: 'left', clickCount: 1 });
  }
  async function change(selector, value, type = 'change') {
    await evaluate(`(()=>{const e=${query(selector)};e.value=${JSON.stringify(value)};e.dispatchEvent(new Event(${JSON.stringify(type)},{bubbles:true}));})()`);
  }
  async function text(selector) { return evaluate(`${query(selector)}.textContent`); }
  async function catalogMatches(key) {
    const rows = await evaluate(`Array.from(document.querySelectorAll('#catalog-table tbody tr'), row => ({
      id: Number(row.cells[0].textContent), title: row.cells[1].textContent, words: row.cells[2].textContent
    }))`);
    const expected = [...data.models[key].topics].sort((a, b) => a.id - b.id).map(topic => ({
      id: topic.id, title: topic.title, words: topic.keywords.join('; ')
    }));
    assert.deepEqual(rows, expected, `${key}: all original topic IDs, titles and complete keywords`);
    assert.equal(await evaluate(`${query('#catalog-model')}.value`), key);
    assert.match(await text('#catalog-count'), new RegExp(`${expected.length} topics`));
  }
  async function accessibility(label) {
    await evaluate(axeSource);
    const violations = await evaluate(`axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}}).then(r=>r.violations.map(v=>({id:v.id,impact:v.impact,targets:v.nodes.map(n=>n.target)})))`);
    assert.deepEqual(violations, [], label + ' accessibility');
  }

  await viewport(1440, 1000);
  await navigate(server.url.toString());
  assert.equal(await evaluate(`document.querySelectorAll('#heatmap tbody tr').length`), 8);
  await screenshot('desktop-overview.png');
  await screenshot('desktop-full.png', true);
  await accessibility('desktop');
  console.log('PASS: loaded real data and desktop accessibility.');

  await click('.sidebar nav a[href="#topic-catalog"]');
  await catalogMatches('semantic');
  await evaluate(`${query('#topic-catalog')}.scrollIntoView({behavior:'instant'})`);
  await screenshot('desktop-catalog.png');
  await change('#catalog-model', 'lexical');
  await catalogMatches('lexical');
  assert.match(await text('#heatmap-model'), /Lexical/);
  assert.equal(await evaluate(`${query('[data-model="lexical"]')}.getAttribute('aria-pressed')`), 'true');
  await change('#catalog-model', 'semantic');
  await change('#topic-search', 'zzzz-unmatched', 'input');
  await change('#category-filter', 'procedural');
  await catalogMatches('semantic');
  const lastTopic = [...data.models.semantic.topics].sort((a, b) => a.id - b.id).at(-1);
  await click('#catalog-table tbody tr:last-child button');
  assert.equal(await text('#topic-title'), lastTopic.title);
  assert.equal(await text('#topic-id'), `${data.models.semantic.name} · T${lastTopic.id}`);
  assert.equal(await evaluate(`document.activeElement === ${query('#topic-title')}`), true);
  assert.equal(await evaluate(`${query('#topic-search')}.value`), '');
  assert.equal(await evaluate(`${query('#category-filter')}.value`), 'all');
  assert.equal(await evaluate(`${query('.topic-choice[aria-pressed="true"]')}.dataset.topic`), String(lastTopic.id));
  console.log('PASS: full catalog, original IDs/keywords, representation sync, filter independence and annual-pattern links.');

  await click('[data-model="lexical"]');
  await catalogMatches('lexical');
  assert.match(await text('#heatmap-model'), /Lexical/);
  await change('#year-filter', '2025');
  assert.match(await text('#selection-summary'), /32 source documents/);
  assert.match(await text('#composition-year'), /2025/);
  assert.match(await text('#topic-buttons'), /in 2025/);
  await catalogMatches('lexical');
  await change('#topic-search', 'zzzz-unmatched', 'input');
  assert.match(await text('#topic-count'), /0 of/);
  assert.match(await text('#topic-buttons'), /No topics match/);
  await change('#topic-search', '', 'input');
  await change('#category-filter', 'procedural');
  assert.ok(await evaluate(`document.querySelectorAll('#topic-buttons .topic-choice').length > 0`));
  await change('#category-filter', 'all');
  await click('#next-page');
  assert.match(await text('#page-label'), /2 \//);
  await click('#topic-buttons .topic-choice');
  assert.equal(await evaluate(`document.activeElement === document.querySelector('#topic-buttons .topic-choice[aria-pressed="true"]')`), true);
  await evaluate(`${query('.corpus-column[data-year="2020"]')}.focus()`);
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13, text: '\r', unmodifiedText: '\r' });
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
  assert.equal(await evaluate(`document.activeElement === ${query('.corpus-column[data-year="2020"]')}`), true);
  assert.match(await text('#composition-year'), /2020/);
  await click('.topic-detail summary');
  assert.equal(await evaluate(`document.querySelectorAll('#trajectory-table tbody tr').length`), 10);
  await click('#heatmap tbody th button');
  assert.equal(await evaluate(`document.activeElement === ${query('#topic-title')}`), true);
  await Bun.sleep(400);
  await screenshot('desktop-topic.png');
  console.log('PASS: model/year/search/category filters, pagination, exact values and keyboard focus.');

  await cdp.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: out });
  await click('a[href="downloads/Temporal_Topic_Summaries.pdf"]');
  const downloaded = resolve(out, 'Temporal_Topic_Summaries.pdf');
  let found = false;
  for (let i = 0; i < 100; i++) {
    try { await access(downloaded); found = true; break; } catch { await Bun.sleep(100); }
  }
  assert.ok(found, 'PDF download completed');
  assert.deepEqual(await readFile(downloaded), await readFile(resolve(import.meta.dir, '../dashboard/downloads/Temporal_Topic_Summaries.pdf')));

  for (const width of [390, 768]) {
    await viewport(width);
    await navigate(server.url.toString());
    assert.equal(await evaluate('document.documentElement.scrollWidth > innerWidth'), false, `No page overflow at ${width}px`);
    await screenshot(`responsive-${width}.png`);
    await screenshot(`responsive-${width}-full.png`, true);
    await accessibility(`${width}px`);
    await catalogMatches('semantic');
    await evaluate(`${query('#topic-catalog')}.scrollIntoView({behavior:'instant'})`);
    await screenshot(`responsive-${width}-catalog.png`);
    assert.equal(await evaluate(`${query('.catalog-scroll')}.scrollWidth > ${query('.catalog-scroll')}.clientWidth`), true, 'Catalog scrolls inside its panel');
    assert.equal(await evaluate(`getComputedStyle(${query('.catalog-words')}).whiteSpace`), 'normal', 'Keywords wrap without truncation');
  }
  console.log('PASS: PDF bytes, mobile/tablet layouts and accessibility.');

  // A real HTTP prefix proxy simulates GitHub Pages project-subdirectory hosting.
  nested = Bun.serve({ hostname: '127.0.0.1', port: 0, fetch(request) {
    const url = new URL(request.url);
    url.pathname = url.pathname.replace(/^\/Thesis_Ordinance-Analysis\//, '/');
    return fetch(new URL(url.pathname + url.search, server.url));
  } });
  await navigate(new URL('/Thesis_Ordinance-Analysis/index.html', nested.url).toString());
  assert.match(await text('#heatmap-model'), /Legal-BERT/);
  await catalogMatches('semantic');
  const catalogLink = await evaluate(`${query('.catalog-download')}.href`);
  assert.ok(new URL(catalogLink).pathname.startsWith('/Thesis_Ordinance-Analysis/downloads/'));
  const catalogResponse = await fetch(catalogLink);
  assert.equal(catalogResponse.status, 200);
  assert.equal(await catalogResponse.text(), await readFile(resolve(import.meta.dir, '../dashboard/downloads/all_topic_titles.csv'), 'utf8'));
  await cdp.send('Fetch.enable', { patterns: [{ urlPattern: '*/data/results.json', requestStage: 'Request' }] });
  cdp.on('Fetch.requestPaused', event => {
    cdp.send('Fetch.fulfillRequest', { requestId: event.requestId, responseCode: 503, body: btoa('Unavailable') }).catch(error => errors.push(error.message));
  });
  await cdp.send('Page.navigate', { url: server.url.toString() });
  await waitFor(`${query('#load-state')}?.getAttribute('role') === 'alert'`, 'explicit unavailable-data alert');
  assert.match(await text('#load-state'), /No placeholder results/);
  assert.equal(await evaluate(`${query('#dashboard')}.hidden`), true);
  assert.deepEqual(errors, []);
  console.log('PASS: subdirectory hosting, unavailable-data handling and zero uncaught page errors.');
  console.log('Screenshots: test-results/dashboard/');
} finally {
  await session?.close();
  nested?.stop(true);
  server.stop(true);
}
