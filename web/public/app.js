const state = { rows: [], years: [], selectedReport: "all" };

const $ = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
const numberValue = (value) => Number.isFinite(Number(value)) ? Number(value) : 0;
const displayYear = (value) => value && value !== "" ? String(value).replace(/\.0$/, "") : "—";

async function getJson(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
  return payload;
}

function statusLabel(status) {
  return String(status || "unknown").replaceAll("_", " ");
}

function countBy(rows, key) {
  return rows.reduce((counts, row) => {
    const value = row[key] || "Unknown";
    counts[value] = (counts[value] || 0) + 1;
    return counts;
  }, {});
}

function renderBars(target, counts, teal = false) {
  const entries = Object.entries(counts);
  const max = Math.max(...entries.map(([, value]) => value), 1);
  target.classList.toggle("teal", teal);
  target.innerHTML = entries.length ? entries.map(([label, value]) => `
    <div class="bar-row"><span class="bar-label">${escapeHtml(statusLabel(label))}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(value / max) * 100}%"></div></div>
      <span class="bar-value">${value}</span>
    </div>`).join("") : '<div class="muted">No data yet.</div>';
}

function renderOverview() {
  const rows = state.rows;
  const total = rows.length;
  const valid = rows.filter((row) => row.temporal_status === "valid").length;
  const review = rows.filter((row) => ["review", "unresolved"].includes(row.temporal_status)).length;
  const included = rows.filter((row) => ["true", "True", true, 1, "1"].includes(row.included_in_corpus)).length;
  $("metricDocuments").textContent = total.toLocaleString();
  $("metricValid").textContent = valid.toLocaleString();
  $("metricValidRate").textContent = total ? `${Math.round((valid / total) * 100)}% of total` : "—";
  $("metricReview").textContent = review.toLocaleString();
  $("metricIncluded").textContent = included.toLocaleString();
  $("emptyState").classList.toggle("hidden", total > 0);

  renderBars($("statusChart"), countBy(rows, "temporal_status"));
  renderBars($("methodChart"), countBy(rows, "extraction_method"), true);
  const extracted = rows.filter((row) => row.detected_enactment_year !== "").length;
  const coverage = total ? (extracted / total) * 100 : 0;
  const coverageBox = $("coverage");
  coverageBox.classList.toggle("warning", coverage < 50 && total > 0);
  coverageBox.innerHTML = total
    ? `<strong>Enactment signal coverage: ${coverage.toFixed(1)}%</strong><br><span>Target: at least 50% before trusting temporal results.</span>`
    : "Run an audit to calculate parser health.";

  const manifest = window.latestManifest;
  $("manifestNote").textContent = manifest
    ? `Last run: ${manifest.generated_at_utc || "unknown"} · revision ${(manifest.git_revision || "unknown").slice(0, 10)} · ${manifest.pdf_backend || "unknown"} backend`
    : "No reproducibility manifest recorded yet.";
}

function populateControls() {
  const yearSelect = $("year");
  yearSelect.innerHTML = state.years.map((year) => `<option value="${year}">${year}</option>`).join("");
  $("rawCount").textContent = window.statusData.rawPdfCount.toLocaleString();
  $("year").disabled = $("scope").value !== "single" || !state.years.length;

  const statusFilter = $("statusFilter");
  const statuses = [...new Set(state.rows.map((row) => row.temporal_status).filter(Boolean))].sort();
  statusFilter.innerHTML = '<option value="All">All</option>' + statuses.map((status) => `<option value="${escapeHtml(status)}">${escapeHtml(statusLabel(status))}</option>`).join("");
  const yearFilter = $("yearFilter");
  const years = [...new Set(state.rows.map((row) => displayYear(row.folder_year)).filter((year) => year !== "—"))].sort();
  yearFilter.innerHTML = '<option value="All">All</option>' + years.map((year) => `<option value="${year}">${year}</option>`).join("");
  $("reportSelect").innerHTML = '<option value="all">Corpus</option>' + state.years.map((year) => `<option value="${year}">${year}</option>`).join("");
}

function renderDocuments() {
  const status = $("statusFilter").value;
  const year = $("yearFilter").value;
  const search = $("searchFilter").value.trim().toLowerCase();
  const rows = state.rows.filter((row) => {
    const haystack = `${row.filename || ""} ${row.title || ""}`.toLowerCase();
    return (status === "All" || row.temporal_status === status)
      && (year === "All" || displayYear(row.folder_year) === year)
      && (!search || haystack.includes(search));
  });
  $("documentCount").textContent = `${rows.length.toLocaleString()} of ${state.rows.length.toLocaleString()}`;
  $("documentRows").innerHTML = rows.map((row) => {
    const included = ["true", "True", true, 1, "1"].includes(row.included_in_corpus);
    const confidence = row.confidence_score === "" ? "—" : Number(row.confidence_score).toFixed(2);
    return `<tr><td title="${escapeHtml(row.title || "")}">${escapeHtml(row.filename)}</td><td>${displayYear(row.folder_year)}</td><td>${displayYear(row.corpus_year)}</td><td><span class="status ${escapeHtml(row.temporal_status)}">${escapeHtml(statusLabel(row.temporal_status))}</span></td><td>${confidence}</td><td class="${included ? "yes" : "no"}">${included ? "Yes" : "No"}</td><td>${escapeHtml(row.extraction_method || "—")}</td></tr>`;
  }).join("") || '<tr><td colspan="7" class="muted">No matching documents.</td></tr>';
}

function renderReport(markdown) {
  $("reportContent").textContent = markdown || "No report is available yet.";
}

async function loadData(year = "all") {
  const payload = await getJson(`/api/data?year=${encodeURIComponent(year)}`);
  state.rows = payload.rows || [];
  window.latestManifest = payload.manifest;
  renderOverview();
  populateControls();
  renderDocuments();
  renderReport(payload.report);
}

async function executeAudit(yearOverride = undefined, quiet = false) {
  const button = $("runAudit");
  const status = $("runState");
  const start = Number($("windowMin").value);
  const end = Number($("windowMax").value);
  const year = yearOverride !== undefined
    ? yearOverride
    : $("scope").value === "single" ? Number($("year").value) : null;
  if (start > end) { status.textContent = "Start year must not exceed end year."; return false; }
  button.disabled = true;
  status.textContent = quiet ? "Refreshing the database…" : "Running audit…";
  try {
    const payload = await getJson("/api/audit", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ year, windowMin: start, windowMax: end, useOcr: $("useOcr").checked, useCache: $("useCache").checked, syncObsidian: $("syncObsidian").checked }) });
    status.textContent = payload.ok ? "Audit completed." : "Audit failed.";
    if (!payload.ok && !quiet) alert(payload.output || "The audit failed.");
    await refresh();
    return payload.ok;
  } catch (error) {
    status.textContent = "Audit failed.";
    if (!quiet) alert(error.message);
    return false;
  } finally { button.disabled = false; }
}

async function runAudit() {
  await executeAudit();
}

async function uploadPdf(event) {
  event.preventDefault();
  const file = $("pdfFile").files[0];
  const year = Number($("uploadYear").value);
  const status = $("uploadState");
  if (!file) { status.textContent = "Choose a PDF first."; return; }
  status.textContent = "Uploading PDF…";
  const form = new FormData();
  form.append("year", String(year));
  form.append("replace", String($("replaceExisting").checked));
  form.append("file", file, file.name);
  try {
    const payload = await getJson("/api/upload", { method: "POST", body: form });
    status.textContent = `${payload.message} Refreshing reports and Obsidian notes…`;
    $("pdfFile").value = "";
    await executeAudit(null, true);
    status.textContent = `${payload.message} Database updated.`;
  } catch (error) {
    status.textContent = error.message;
  }
}

async function loadChecklist() {
  try { $("checklistContent").textContent = (await getJson("/api/checklist")).markdown; } catch (error) { $("checklistContent").textContent = error.message; }
}

async function refresh() {
  window.statusData = await getJson("/api/status");
  state.years = window.statusData.years || [];
  populateControls();
  await loadData("all");
}

function setup() {
  document.querySelectorAll(".tab").forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll(".tab, .panel").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    $(button.dataset.tab).classList.add("active");
  }));
  $("scope").addEventListener("change", () => { $("year").disabled = $("scope").value !== "single"; });
  $("runAudit").addEventListener("click", runAudit);
  $("uploadForm").addEventListener("submit", uploadPdf);
  ["statusFilter", "yearFilter", "searchFilter"].forEach((id) => $(id).addEventListener("input", renderDocuments));
  $("reportSelect").addEventListener("change", async (event) => {
    const payload = await getJson(`/api/data?year=${encodeURIComponent(event.target.value)}`);
    renderReport(payload.report);
  });
  loadChecklist();
  refresh().catch((error) => { $("runState").textContent = error.message; });
}

document.addEventListener("DOMContentLoaded", setup);
