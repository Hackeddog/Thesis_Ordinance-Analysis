import { createHash } from "node:crypto";
import { createServer } from "node:http";
import { execFile, spawn } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { basename, extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { URL } from "node:url";

const execFileAsync = promisify(execFile);
const PROJECT_ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const WEB_ROOT = join(PROJECT_ROOT, "web");
const PUBLIC_ROOT = join(WEB_ROOT, "public");
const PORT = Number(process.env.PORT || 3000);
const HOST = process.env.HOST || "127.0.0.1";
const PIPELINE = join(PROJECT_ROOT, "src", "ordinance_eda_pipeline.py");
const SUMMARY_DIR = join(PROJECT_ROOT, "data", "EDA");
const REPORT_DIR = join(PROJECT_ROOT, "outputs", "reports");
const INDEX_PATH = join(PROJECT_ROOT, "data", "processed", "corpus_index.csv");
const RAW_DIR = join(PROJECT_ROOT, "data", "raw");
let auditRunning = false;

function pythonCommand() {
  const candidates = process.platform === "win32"
    ? [join(PROJECT_ROOT, ".venv", "Scripts", "python.exe"), "python"]
    : [join(PROJECT_ROOT, ".venv", "bin", "python"), "python3", "python"];
  for (const candidate of candidates) {
    if (candidate === "python" || candidate === "python3" || existsSync(candidate)) return candidate;
  }
  return "python";
}

function json(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
  });
  res.end(body);
}

function text(res, status, body, contentType = "text/plain; charset=utf-8") {
  res.writeHead(status, { "Content-Type": contentType, "Cache-Control": "no-store" });
  res.end(body);
}

function parseCsv(source) {
  if (!source.trim()) return [];
  const rows = [];
  let row = [];
  let value = "";
  let quoted = false;
  for (let i = 0; i < source.length; i += 1) {
    const char = source[i];
    const next = source[i + 1];
    if (quoted) {
      if (char === '"' && next === '"') {
        value += '"'; i += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        value += char;
      }
    } else if (char === '"' && value === "") {
      quoted = true;
    } else if (char === ",") {
      row.push(value); value = "";
    } else if (char === "\n") {
      row.push(value); value = "";
      if (row.some((item) => item !== "")) rows.push(row);
      row = [];
    } else if (char !== "\r") {
      value += char;
    }
  }
  if (value || row.length) {
    row.push(value);
    if (row.some((item) => item !== "")) rows.push(row);
  }
  if (!rows.length) return [];
  const headers = rows[0];
  return rows.slice(1).map((cells) => Object.fromEntries(
    headers.map((header, index) => [header, cells[index] ?? ""]),
  ));
}

function readCsv(path) {
  return existsSync(path) ? parseCsv(readFileSync(path, "utf8")) : [];
}

function availableYears() {
  if (!existsSync(RAW_DIR)) return [];
  return readdirSync(RAW_DIR)
    .filter((name) => {
      if (!/^\d{4}$/.test(name)) return false;
      try { return statSync(join(RAW_DIR, name)).isDirectory(); } catch { return false; }
    })
    .map(Number)
    .sort((a, b) => a - b);
}

function rawPdfCount() {
  return availableYears().reduce((count, year) => {
    const folder = join(RAW_DIR, String(year));
    return count + readdirSync(folder).filter((name) => name.toLowerCase().endsWith(".pdf")).length;
  }, 0);
}

function readManifest() {
  const path = join(REPORT_DIR, "run_manifest.json");
  if (!existsSync(path)) return null;
  try { return JSON.parse(readFileSync(path, "utf8")); } catch { return null; }
}

function loadRows(year = null) {
  const summaryPath = year === null
    ? join(SUMMARY_DIR, "ordinances_eda_summary_ALL.csv")
    : join(SUMMARY_DIR, `ordinances_eda_summary_${year}.csv`);
  const rows = readCsv(summaryPath);
  const index = readCsv(INDEX_PATH);
  const indexByKey = new Map(index.map((row) => [`${row.filename}|${row.folder_year}`, row]));
  return rows.map((row) => {
    const extra = indexByKey.get(`${row.filename}|${row.folder_year}`) || {};
    return { ...row, ...extra };
  });
}

function readReport(year = null) {
  const path = year === null
    ? join(REPORT_DIR, "eda_report_CORPUS.md")
    : join(REPORT_DIR, `eda_report_${year}.md`);
  return existsSync(path) ? readFileSync(path, "utf8") : null;
}

async function requestBody(req) {
  let data = "";
  for await (const chunk of req) {
    data += chunk;
    if (data.length > 1024 * 1024) throw new Error("Request body too large");
  }
  return data ? JSON.parse(data) : {};
}

async function requestBuffer(req, maxBytes = 50 * 1024 * 1024) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > maxBytes) throw new Error("PDF upload is larger than 50 MB");
    chunks.push(Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}

function parseMultipart(body, contentType) {
  const match = contentType.match(/boundary=(?:"([^\"]+)"|([^;]+))/i);
  if (!match) throw new Error("Missing multipart boundary");
  const boundary = Buffer.from(`--${match[1] || match[2]}`);
  const separator = Buffer.from("\r\n\r\n");
  const parts = [];
  let cursor = 0;
  while (true) {
    const boundaryStart = body.indexOf(boundary, cursor);
    if (boundaryStart < 0) break;
    let start = boundaryStart + boundary.length;
    if (body.subarray(start, start + 2).toString() === "--") break;
    if (body.subarray(start, start + 2).toString() === "\r\n") start += 2;
    const headerEnd = body.indexOf(separator, start);
    if (headerEnd < 0) break;
    const headers = body.subarray(start, headerEnd).toString("utf8");
    const nextBoundary = body.indexOf(boundary, headerEnd + separator.length);
    if (nextBoundary < 0) break;
    const contentEnd = nextBoundary - 2;
    const dispositionLine = headers.split(/\r?\n/).find((line) => /content-disposition/i.test(line)) || "";
    const nameMatch = dispositionLine.match(/\bname="([^"]+)"/i);
    const filenameMatch = dispositionLine.match(/\bfilename="([^"]*)"/i);
    if (nameMatch) {
      parts.push({ name: nameMatch[1], filename: filenameMatch ? filenameMatch[1] : "", data: body.subarray(headerEnd + separator.length, contentEnd) });
    }
    cursor = nextBoundary;
  }
  return parts;
}

function safeUploadName(filename) {
  const name = basename(String(filename || "")).replace(/[^a-zA-Z0-9._() -]/g, "_");
  if (!name || !name.toLowerCase().endsWith(".pdf")) throw new Error("Only PDF files can be uploaded");
  return name;
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

function findExistingHash(hash) {
  for (const year of availableYears()) {
    const folder = join(RAW_DIR, String(year));
    for (const filename of readdirSync(folder).filter((name) => name.toLowerCase().endsWith(".pdf"))) {
      try {
        if (sha256(readFileSync(join(folder, filename))) === hash) return { year, filename };
      } catch { /* ignore a file that disappears during the scan */ }
    }
  }
  return null;
}

function storeUpload(year, filename, data, replaceExisting) {
  if (!Number.isInteger(year) || year < 1900 || year > 2035) throw new Error("Enter a valid ordinance year");
  const targetDir = join(RAW_DIR, String(year));
  mkdirSync(targetDir, { recursive: true });
  const safeName = safeUploadName(filename);
  const target = join(targetDir, safeName);
  const hash = sha256(data);
  const duplicate = findExistingHash(hash);
  if (duplicate) return { duplicate, hash, filename: safeName };
  const replaced = existsSync(target);
  if (replaced && !replaceExisting) return { conflict: true, hash, filename: safeName };
  if (replaced) {
    const backupDir = join(PROJECT_ROOT, "data", "versions", "uploads", new Date().toISOString().replace(/[:.]/g, "-"), String(year));
    mkdirSync(backupDir, { recursive: true });
    copyFileSync(target, join(backupDir, safeName));
  }
  writeFileSync(target, data);
  return { saved: true, hash, filename: safeName, year, replaced };
}

function runPipeline(options) {
  return new Promise((resolveRun, reject) => {
    const python = pythonCommand();
    const args = [PIPELINE, "--window-min", String(options.windowMin), "--window-max", String(options.windowMax)];
    if (options.year === null || options.year === undefined) args.push("--all-years");
    else args.push("--year", String(options.year));
    if (!options.useOcr) args.push("--no-ocr");
    if (!options.useCache) args.push("--no-cache");
    if (options.syncObsidian) args.push("--export-obsidian");

    const child = spawn(python, args, { cwd: PROJECT_ROOT, windowsHide: true });
    let output = "";
    child.stdout.on("data", (chunk) => { output += chunk.toString(); });
    child.stderr.on("data", (chunk) => { output += chunk.toString(); });
    child.on("error", reject);
    child.on("close", (code) => resolveRun({ code: code ?? 1, output }));
  });
}

function staticFile(pathname, res) {
  const requested = pathname === "/" ? "/index.html" : pathname;
  const filePath = resolve(PUBLIC_ROOT, `.${normalize(requested)}`);
  if (!filePath.startsWith(`${PUBLIC_ROOT}${process.platform === "win32" ? "\\" : "/"}`)) {
    return text(res, 403, "Forbidden");
  }
  if (!existsSync(filePath)) return text(res, 404, "Not found");
  const contentTypes = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".json": "application/json" };
  return text(res, 200, readFileSync(filePath), contentTypes[extname(filePath)] || "application/octet-stream");
}

async function handler(req, res) {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  if (url.pathname === "/api/status" && req.method === "GET") {
    return json(res, 200, { years: availableYears(), rawPdfCount: rawPdfCount(), rows: loadRows().length, manifest: readManifest() });
  }
  if (url.pathname === "/api/data" && req.method === "GET") {
    const value = url.searchParams.get("year");
    const year = value && value !== "all" ? Number(value) : null;
    return json(res, 200, { rows: loadRows(year), report: readReport(year), manifest: readManifest() });
  }
  if (url.pathname === "/api/checklist" && req.method === "GET") {
    const path = join(PROJECT_ROOT, "docs", "THESIS_READINESS_CHECKLIST.md");
    return json(res, 200, { markdown: existsSync(path) ? readFileSync(path, "utf8") : "Checklist unavailable." });
  }
  if (url.pathname === "/api/upload" && req.method === "POST") {
    if (auditRunning) return json(res, 409, { error: "Wait for the current audit to finish before uploading." });
    const contentType = String(req.headers["content-type"] || "");
    if (!contentType.toLowerCase().startsWith("multipart/form-data")) {
      return json(res, 415, { error: "Upload must use multipart/form-data." });
    }
    try {
      const parts = parseMultipart(await requestBuffer(req), contentType);
      const fields = Object.fromEntries(parts.filter((part) => !part.filename).map((part) => [part.name, part.data.toString("utf8")]));
      const file = parts.find((part) => part.filename);
      if (!file) return json(res, 400, { error: "Choose a PDF file first." });
      const result = storeUpload(Number(fields.year), file.filename, file.data, fields.replace === "true");
      if (result.duplicate) return json(res, 409, { error: `This PDF is already stored in ${result.duplicate.year}: ${result.duplicate.filename}`, result });
      if (result.conflict) return json(res, 409, { error: `${result.filename} already exists in that year. Enable replace to update it.`, result });
      return json(res, 201, { ok: true, message: `${result.filename} was added to data/raw/${result.year}.`, result });
    } catch (error) {
      return json(res, 400, { error: error.message });
    }
  }
  if (url.pathname === "/api/audit" && req.method === "POST") {
    if (auditRunning) return json(res, 409, { error: "An audit is already running." });
    let options;
    try { options = await requestBody(req); } catch (error) { return json(res, 400, { error: error.message }); }
    const windowMin = Number(options.windowMin);
    const windowMax = Number(options.windowMax);
    if (!Number.isInteger(windowMin) || !Number.isInteger(windowMax) || windowMin > windowMax) {
      return json(res, 400, { error: "Invalid study window." });
    }
    auditRunning = true;
    try {
      const result = await runPipeline({
        year: options.year === null || options.year === undefined ? null : Number(options.year),
        windowMin, windowMax,
        useOcr: options.useOcr !== false,
        useCache: options.useCache !== false,
        syncObsidian: options.syncObsidian === true,
      });
      return json(res, result.code === 0 ? 200 : 500, { ok: result.code === 0, output: result.output });
    } catch (error) {
      return json(res, 500, { error: error.message });
    } finally {
      auditRunning = false;
    }
  }
  if (url.pathname.startsWith("/api/")) return json(res, 404, { error: "API route not found" });
  return staticFile(url.pathname, res);
}

const server = createServer((req, res) => {
  handler(req, res).catch((error) => json(res, 500, { error: error.message }));
});

server.listen(PORT, HOST, () => {
  const address = `http://${HOST}:${PORT}`;
  console.log(`Ordinance Lab is running at ${address}`);
  if (process.env.NO_BROWSER !== "1") {
    const command = process.platform === "win32" ? "cmd" : "open";
    const args = process.platform === "win32" ? ["/c", "start", "", address] : [address];
    execFileAsync(command, args).catch(() => {});
  }
});
