// Pure, dependency-free calculations shared by the UI and Bun tests.
export const percent = (value, digits = 1) => Number.isFinite(value) ? `${(value * 100).toFixed(digits)}%` : 'Not available';
export const number = value => Number.isFinite(value) ? value.toLocaleString('en-US') : 'Not available';
export const decimal = value => Number.isFinite(value) ? value.toFixed(4) : 'Not available';

export function validateData(data) {
  if (data.schema_version !== 1 || data.configuration !== 'coarse_grained' || data.seed !== 42 || !data.fresh_encoder_inference || data.fit_count !== 6) throw new Error('Unexpected or incomplete run identity.');
  if (data.years.length !== 10 || data.years.some((year, index) => year !== 2016 + index)) throw new Error('The complete 2016–2025 study window is required.');
  if (data.yearly_documents.length !== 10 || data.yearly_documents.some(n => !Number.isInteger(n) || n <= 0) || data.yearly_documents.reduce((a, b) => a + b, 0) !== data.documents) throw new Error('Invalid corpus denominators.');
  for (const key of ['lexical', 'semantic']) {
    const model = data.models[key];
    if (!model || model.topics.length !== model.metrics.topics_excluding_outliers || model.metrics.sections !== data.units || model.metrics.trial !== data.configuration || model.metrics.seed !== data.seed || model.metrics.status !== 'completed') throw new Error('Model evidence does not match the declared run.');
    if (new Set(model.topics.map(topic => topic.id)).size !== model.topics.length || model.topics.some(topic => !Number.isInteger(topic.id) || topic.id < 0)) throw new Error('Invalid topic identities.');
    const vectors = [...model.topics.map(topic => topic.shares), model.outlier_shares];
    if (vectors.some(shares => shares.length !== 10 || shares.some(n => !Number.isFinite(n) || n < 0 || n > 1))) throw new Error('Invalid temporal values.');
    for (let i = 0; i < 10; i++) if (Math.abs(vectors.reduce((sum, values) => sum + values[i], 0) - 1) > 1e-8) throw new Error('Annual document weights do not sum to one.');
    for (const topic of model.topics) {
      const weight = topic.shares.reduce((sum, share, i) => sum + share * data.yearly_documents[i], 0);
      if (Math.abs(weight - topic.fractional_documents) > 1e-6) throw new Error('Topic ranking weights disagree with annual observations.');
    }
  }
  return data;
}

export function rankTopics(topics) {
  return [...topics].sort((a, b) => b.fractional_documents - a.fractional_documents || a.id - b.id);
}

export function filterTopics(topics, query, category) {
  const search = query.trim().toLowerCase();
  return rankTopics(topics).filter(topic => (category === 'all' || topic.category === category) &&
    (!search || `${topic.id} ${topic.title} ${topic.keywords.join(' ')}`.toLowerCase().includes(search)));
}

export function composition(model, yearIndex, count = 5) {
  const ranked = [...model.topics].sort((a, b) => b.shares[yearIndex] - a.shares[yearIndex] || a.id - b.id);
  return [
    ...ranked.slice(0, count).map(topic => ({ label: `T${topic.id} · ${topic.title}`, share: topic.shares[yearIndex] })),
    { label: 'Other assigned topics', share: ranked.slice(count).reduce((sum, topic) => sum + topic.shares[yearIndex], 0) },
    { label: 'Outliers', share: model.outlier_shares[yearIndex] },
  ];
}

export function topicSummary(topic, years) {
  const peak = Math.max(...topic.shares);
  return { peak, peakYears: years.filter((year, i) => Math.abs(topic.shares[i] - peak) < 1e-12),
    changePoints: (topic.shares.at(-1) - topic.shares[0]) * 100 };
}
