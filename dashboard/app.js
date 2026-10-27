import { validateData, percent, number, decimal, rankTopics, filterTopics, composition, topicSummary } from './data-utils.js';

const $ = selector => document.querySelector(selector);
const palette = ['#24695e', '#b76034', '#75875a', '#6c83a1', '#997b91', '#c9cebf', '#55635d'];
const state = { model: 'semantic', year: 2024, topic: null, query: '', category: 'all', page: 0 };
const pageSize = 6;
let data;

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function svgEl(tag, attrs = {}, text) {
  const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
}
function replace(selector, ...children) { $(selector).replaceChildren(...children); }
function model() { return data.models[state.model]; }
function yearIndex() { return data.years.indexOf(state.year); }
function stat(label, value, note, accent = false) {
  const card = el('div', `stat-card${accent ? ' accent' : ''}`);
  card.append(el('span', 'stat-label', label), el('strong', '', value), el('small', '', note));
  return card;
}
function setYear(year) {
  const restoreBarFocus = document.activeElement?.classList.contains('corpus-column');
  state.year = year;
  $('#year-filter').value = String(year);
  renderOverview();
  renderTopic();
  if (restoreBarFocus) document.querySelector(`.corpus-column[data-year="${year}"]`)?.focus({ preventScroll: true });
}
function chooseTopic(id, scroll = false) {
  state.topic = id;
  if (scroll) {
    state.query = ''; state.category = 'all';
    $('#topic-search').value = ''; $('#category-filter').value = 'all';
    state.page = Math.floor(rankTopics(model().topics).findIndex(topic => topic.id === id) / pageSize);
  }
  renderTopic();
  if (!scroll) document.querySelector(`.topic-choice[data-topic="${id}"]`)?.focus({ preventScroll: true });
  if (scroll) {
    $('#topics').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
    $('#topic-title').tabIndex = -1;
    $('#topic-title').focus({ preventScroll: true });
  }
}

function renderOverview() {
  const selected = model();
  const totalTopics = Object.values(data.models).reduce((sum, value) => sum + value.topics.length, 0);
  replace('#corpus-stats', stat('Source documents', number(data.documents), 'Distinct included source contents'),
    stat('Modeling units', number(data.units), 'Detected sections + document fallbacks'),
    stat('Topics across both models', number(totalTopics), 'Model-local topics; not unique policy fields'),
    stat(`${selected.name} · topics`, number(selected.topics.length), `${percent(selected.metrics.topic_coverage)} unit assignment coverage`, true));
  $('#selection-summary').textContent = `${state.year}: ${number(data.yearly_documents[yearIndex()])} source documents · ${selected.name}`;
  $('#heatmap-model').textContent = `${selected.name} · seed ${data.seed}`;
  renderHeatmap();
  renderCorpus();
  renderComposition();
}

function renderHeatmap() {
  const leading = rankTopics(model().topics).slice(0, 8);
  // Shared scale across representations, not independently rescaled on each switch.
  const max = Math.max(.05, ...Object.values(data.models).flatMap(m => rankTopics(m.topics).slice(0, 8).flatMap(t => t.shares)));
  const caption = el('caption', 'sr-only', `Leading ${model().name} topics. Annual document-weighted share in percent; common color scale across models.`);
  const head = el('thead'); const headings = el('tr');
  const topicHead = el('th', '', 'TOPIC / DRAFT DESCRIPTION'); topicHead.scope = 'col'; headings.append(topicHead);
  data.years.forEach(year => { const th = el('th', '', year); th.scope = 'col'; headings.append(th); });
  head.append(headings);
  const body = el('tbody');
  leading.forEach(topic => {
    const row = el('tr'); const th = el('th'); th.scope = 'row';
    const button = el('button', '', topic.title); button.type = 'button';
    button.append(el('small', '', `T${topic.id} · ${topic.category}`));
    button.addEventListener('click', () => chooseTopic(topic.id, true));
    th.append(button); row.append(th);
    topic.shares.forEach((share, index) => {
      const ratio = share / max;
      const start = [238, 243, 235], end = [40, 106, 90];
      const rgb = start.map((v, i) => Math.round(v + (end[i] - v) * ratio));
      const td = el('td', data.years[index] === state.year ? 'selected-year' : '', (share * 100).toFixed(1));
      td.style.backgroundColor = `rgb(${rgb.join(',')})`;
      const linear = rgb.map(v => { const s = v / 255; return s <= .04045 ? s / 12.92 : ((s + .055) / 1.055) ** 2.4; });
      const luminance = linear[0] * .2126 + linear[1] * .7152 + linear[2] * .0722;
      td.style.color = luminance < .179 ? '#fff' : '#000';
      td.title = `${topic.title}, ${data.years[index]}: ${percent(share, 3)}`;
      row.append(td);
    });
    body.append(row);
  });
  replace('#heatmap', caption, head, body);
}

function renderCorpus() {
  const max = Math.max(...data.yearly_documents);
  replace('#corpus-chart', ...data.years.map((year, index) => {
    const count = data.yearly_documents[index];
    const button = el('button', 'corpus-column'); button.type = 'button'; button.dataset.year = year;
    button.setAttribute('aria-label', `Inspect ${year}, ${count} source documents`);
    button.setAttribute('aria-pressed', String(year === state.year));
    const bar = el('span', 'bar'); bar.style.height = `${count / max * 115}px`; bar.setAttribute('aria-hidden', 'true');
    button.append(el('span', 'count', count), bar, el('span', 'year', year));
    button.addEventListener('click', () => setYear(year));
    return button;
  }));
}

function renderComposition() {
  $('#composition-year').textContent = `${state.year} · ${model().name.toUpperCase()}`;
  const items = composition(model(), yearIndex());
  const track = el('div', 'composition-track'); track.setAttribute('aria-hidden', 'true');
  const list = el('div');
  items.forEach((item, index) => {
    const part = el('span'); part.style.width = `${item.share * 100}%`; part.style.background = palette[index]; track.append(part);
    const row = el('div', 'composition-row');
    const dot = el('span', 'dot'); dot.style.background = palette[index]; dot.setAttribute('aria-hidden', 'true');
    row.append(dot, el('span', '', item.label), el('strong', '', percent(item.share)));
    list.append(row);
  });
  replace('#composition', track, list);
}

function renderCatalog() {
  const selected = model();
  const topics = [...selected.topics].sort((a, b) => a.id - b.id);
  $('#catalog-model').value = state.model;
  $('#catalog-count').textContent = `${topics.length} topics · ${selected.name} · seed ${data.seed} · full 2016–2025 run`;
  const caption = el('caption', '', `${selected.name}: all ${topics.length} identified topics and their complete clustered_words.`);
  const head = el('thead'), header = el('tr');
  ['Topic number', 'Proposed topic title (draft)', 'clustered_words', 'Dashboard review'].forEach(label => {
    const th = el('th', '', label); th.scope = 'col'; header.append(th);
  });
  head.append(header);
  const body = el('tbody');
  topics.forEach(topic => {
    const row = el('tr'); row.dataset.topic = topic.id;
    const id = el('th', 'catalog-id', topic.id); id.scope = 'row';
    const title = el('td', 'catalog-topic-title', topic.title);
    const words = el('td', 'catalog-words', topic.keywords.join('; '));
    const action = el('td');
    const button = el('button', '', 'View annual pattern');
    button.type = 'button';
    button.setAttribute('aria-label', `View annual pattern for ${selected.name} topic ${topic.id}: ${topic.title}`);
    button.addEventListener('click', () => chooseTopic(topic.id, true));
    action.append(button);
    row.append(id, title, words, action); body.append(row);
  });
  replace('#catalog-table', caption, head, body);
}

function renderTopicList() {
  const filtered = filterTopics(model().topics, state.query, state.category);
  const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
  state.page = Math.min(state.page, pages - 1);
  $('#topic-count').textContent = `${filtered.length} of ${model().topics.length} topics · ranked by total document weight`;
  const shown = filtered.slice(state.page * pageSize, (state.page + 1) * pageSize);
  replace('#topic-buttons', ...(shown.length ? shown.map(topic => {
    const button = el('button', 'topic-choice'); button.type = 'button'; button.dataset.topic = topic.id;
    button.setAttribute('aria-pressed', String(topic.id === state.topic));
    button.append(el('strong', '', topic.title), el('small', '', `T${topic.id} · ${topic.category} · ${percent(topic.shares[yearIndex()])} in ${state.year}`));
    button.addEventListener('click', () => chooseTopic(topic.id));
    return button;
  }) : [el('p', 'footnote', 'No topics match. Try another keyword or select all categories. The current detail remains visible.')]));
  $('#page-label').textContent = `${state.page + 1} / ${pages}`;
  $('#previous-page').disabled = state.page === 0;
  $('#next-page').disabled = state.page >= pages - 1;
}

function renderTopic() {
  const topic = model().topics.find(t => t.id === state.topic);
  if (!topic) return;
  const stats = topicSummary(topic, data.years);
  $('#topic-id').textContent = `${model().name} · T${topic.id}`;
  $('#topic-category').textContent = topic.category;
  $('#topic-title').textContent = topic.title;
  $('#label-method').textContent = `Draft label · ${topic.label_method.replaceAll('_', ' ')} · not expert validated`;
  replace('#keyword-list', ...topic.keywords.map(word => el('span', '', word)));
  const values = [[`${state.year} archive share`, percent(topic.shares[yearIndex()], 2)], ['Peak year(s)', stats.peakYears.join(', ')], ['2016 → 2025 change', `${stats.changePoints >= 0 ? '+' : ''}${stats.changePoints.toFixed(2)} pp`]];
  replace('#topic-stats', ...values.map(([label, value], i) => {
    const item = el('div'); item.append(el('small', '', label), el('strong', i === 1 ? 'peak-years' : '', value)); return item;
  }));
  renderTrajectory(topic);
  const caption = el('caption', '', `${topic.title}: exact shares, including outliers in the annual denominator.`);
  const head = el('thead'), header = el('tr');
  ['Year', 'Source documents', 'Topic share'].forEach(text => { const th = el('th', '', text); th.scope = 'col'; header.append(th); }); head.append(header);
  const body = el('tbody');
  data.years.forEach((year, i) => { const row = el('tr'); row.append(el('td', '', year), el('td', '', number(data.yearly_documents[i])), el('td', '', percent(topic.shares[i], 4))); body.append(row); });
  replace('#trajectory-table', caption, head, body);
  renderTopicList();
}

function renderTrajectory(topic) {
  const width = 580, height = 245, left = 43, right = 14, top = 16, bottom = 32;
  const upper = Math.max(.02, Math.ceil(Math.max(...topic.shares) * 100 / 2) * .02);
  const x = i => left + i / 9 * (width - left - right);
  const y = share => height - bottom - share / upper * (height - top - bottom);
  const svg = svgEl('svg', { viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-labelledby': 'trajectory-title trajectory-description' });
  svg.append(svgEl('title', { id: 'trajectory-title' }, `${model().name} T${topic.id}: ${topic.title}`));
  svg.append(svgEl('desc', { id: 'trajectory-description' }, 'Document-weighted annual shares from 2016 to 2025. Exact values are available in the table below.'));
  for (let i = 0; i <= 4; i++) {
    const value = upper * i / 4;
    svg.append(svgEl('line', { x1: left, x2: width - right, y1: y(value), y2: y(value), class: 'grid-line' }));
    svg.append(svgEl('text', { x: left - 8, y: y(value) + 4, 'text-anchor': 'end' }, percent(value, upper < .04 ? 1 : 0)));
  }
  const points = topic.shares.map((share, i) => `${x(i)},${y(share)}`);
  svg.append(svgEl('polygon', { points: `${x(0)},${y(0)} ${points.join(' ')} ${x(9)},${y(0)}`, fill: '#e5eee3' }));
  svg.append(svgEl('polyline', { points: points.join(' '), fill: 'none', stroke: '#24695e', 'stroke-width': 2.5 }));
  data.years.forEach((year, i) => {
    svg.append(svgEl('text', { x: x(i), y: height - 9, 'text-anchor': 'middle' }, year));
    const dot = svgEl('circle', { cx: x(i), cy: y(topic.shares[i]), r: year === state.year ? 5 : 3.5, fill: '#24695e', tabindex: 0, class: year === state.year ? 'selected-dot' : '', 'aria-label': `${year}: ${percent(topic.shares[i], 3)}` });
    dot.append(svgEl('title', {}, `${year}: ${percent(topic.shares[i], 3)}`)); svg.append(dot);
  });
  replace('#trajectory', svg);
}

function renderModels() {
  replace('#model-cards', ...['lexical', 'semantic'].map(key => {
    const m = data.models[key], metrics = m.metrics;
    const card = el('article', `panel model-card ${key}`);
    card.append(el('p', 'eyebrow', key === 'lexical' ? 'MODEL A · LEXICAL REPRESENTATION' : 'MODEL B · SEMANTIC REPRESENTATION'), el('h3', '', m.name), el('p', 'pipeline', m.pipeline));
    const list = el('dl', 'model-metrics');
    [['Topics (excluding outliers)', number(metrics.topics_excluding_outliers)], ['C_v coherence', decimal(metrics.cv_coherence)], ['Keyword diversity', decimal(metrics.topic_diversity)], ['Assigned unit coverage', percent(metrics.topic_coverage, 2)], ['Outlier units', `${number(metrics.outlier_sections)} · ${percent(metrics.outlier_fraction, 2)}`], ['Mean aligned seed stability', decimal(m.aligned_seed_stability)]].forEach(([label, value]) => {
      const group = el('div'); group.append(el('dt', '', label), el('dd', '', value)); list.append(group);
    });
    card.append(list); return card;
  }));
}

function renderProvenance() {
  const pairs = [
    ['Active configuration', 'Coarse-grained; primary seed 42; sensitivity seeds 43, 44'],
    ['Selection rationale', data.selection_reason],
    ['UMAP', `${data.parameters.neighbors} neighbors · ${data.parameters.umap_components} dimensions · min_dist ${data.parameters.min_dist}`],
    ['HDBSCAN', `min_cluster_size ${data.parameters.min_cluster_size} · min_samples ${data.parameters.min_samples}`],
    ['Frozen encoder', data.encoder], ['Encoder revision', data.encoder_revision],
    ['Training scope', `${data.fit_count} new clustering fits; fresh lexical vectors and frozen-encoder inference; no encoder fine-tuning`],
    ['Run started (UTC)', data.run_started_utc], ['Run completed (UTC)', data.run_finished_utc],
    ['Measured run duration', `${(data.session_wall_seconds / 60).toFixed(2)} minutes`],
    ['Prepared source SHA-256', data.source_sha256], ['Ordered input SHA-256', data.input_units_sha256],
    ['Configuration SHA-256', data.experiment_config_sha256], ['Temporal manifest SHA-256', data.temporal_manifest_sha256],
  ];
  replace('#provenance', ...pairs.flatMap(([label, value]) => [el('dt', '', label), el('dd', '', value)]));
  $('#run-date').textContent = `Run completed ${new Date(data.run_finished_utc).toLocaleDateString('en-GB', { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' })} (UTC)`;
}

function setModel(key) {
  state.model = key; state.page = 0; state.category = 'all'; state.query = '';
  state.topic = rankTopics(model().topics)[0].id;
  $('#topic-search').value = '';
  document.querySelectorAll('[data-model]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.model === key)));
  const all = el('option', '', 'All categories'); all.value = 'all';
  replace('#category-filter', all, ...[...new Set(model().topics.map(topic => topic.category))].sort().map(category => {
    const option = el('option', '', category[0].toUpperCase() + category.slice(1)); option.value = category; return option;
  }));
  renderOverview(); renderTopic(); renderCatalog();
}

function installNavigation() {
  const links = [...document.querySelectorAll('.sidebar nav a')];
  const observer = new IntersectionObserver(entries => {
    const visible = entries.filter(entry => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio);
    if (!visible.length) return;
    links.forEach(link => {
      if (link.hash === `#${visible[0].target.id}`) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }, { rootMargin: '-5% 0px -65% 0px', threshold: 0 });
  document.querySelectorAll('main section').forEach(section => observer.observe(section));
}

async function init() {
  try {
    const response = await fetch(new URL('./data/results.json', import.meta.url));
    if (!response.ok) throw new Error(`Could not load the published data (HTTP ${response.status}).`);
    data = validateData(await response.json());
    replace('#year-filter', ...data.years.map(year => { const option = el('option', '', year); option.value = year; return option; }));
    $('#year-filter').value = String(state.year);
    $('#year-filter').addEventListener('change', event => setYear(Number(event.target.value)));
    document.querySelectorAll('[data-model]').forEach(button => button.addEventListener('click', () => setModel(button.dataset.model)));
    $('#catalog-model').addEventListener('change', event => setModel(event.target.value));
    $('#topic-search').addEventListener('input', event => { state.query = event.target.value; state.page = 0; renderTopicList(); });
    $('#category-filter').addEventListener('change', event => { state.category = event.target.value; state.page = 0; renderTopicList(); });
    $('#previous-page').addEventListener('click', () => { state.page--; renderTopicList(); });
    $('#next-page').addEventListener('click', () => { state.page++; renderTopicList(); });
    setModel(state.model); renderModels(); renderProvenance();
    $('#load-state').hidden = true; $('#dashboard').hidden = false;
    installNavigation();
  } catch (error) {
    $('#load-state').setAttribute('role', 'alert');
    $('#load-state').textContent = `Research results unavailable. ${error.message} Serve the dashboard over HTTP using the VS Code task or bun run dev; do not open index.html as a file. No placeholder results are shown.`;
  }
}
init();
