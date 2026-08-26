"use strict";

const SYMBOL_PATTERN = /^[A-Z0-9^][A-Z0-9.\-=^]{0,19}$/;
const SVG_NS = "http://www.w3.org/2000/svg";

const demoForm = document.querySelector("#demo-form");
const primaryField = document.querySelector("#primary-symbol");
const benchmarkField = document.querySelector("#benchmark-symbol");
const periodField = document.querySelector("#period");
const formError = document.querySelector("#form-error");
const runButton = document.querySelector("#run-button");
const runCopy = runButton.querySelector(".run-copy");
const retryButton = document.querySelector("#retry-button");
const presetButtons = document.querySelector("#preset-buttons");

const runtimeStatus = document.querySelector("#runtime-status");
const runtimeLabel = document.querySelector("#runtime-label");
const idleState = document.querySelector("#idle-state");
const loadingState = document.querySelector("#loading-state");
const loadingLabel = document.querySelector("#loading-label");
const failureState = document.querySelector("#failure-state");
const failureTitle = document.querySelector("#failure-title");
const failureMessage = document.querySelector("#failure-message");
const failureList = document.querySelector("#failure-list");
const failureCorrelation = document.querySelector("#failure-correlation");
const failureTraceList = document.querySelector("#failure-trace-list");
const resultContent = document.querySelector("#result-content");

const resultStatus = document.querySelector("#result-status");
const coverageLabel = document.querySelector("#coverage-label");
const observationLabel = document.querySelector("#observation-label");
const resultHeadline = document.querySelector("#result-headline");
const resultSummary = document.querySelector("#result-summary");
const providerVersion = document.querySelector("#provider-version");
const chartLegend = document.querySelector("#chart-legend");
const performanceChart = document.querySelector("#performance-chart");
const chartDescription = document.querySelector("#chart-description");
const relativeMetrics = document.querySelector("#relative-metrics");
const metricHead = document.querySelector("#metric-head");
const metricBody = document.querySelector("#metric-body");
const qualityCount = document.querySelector("#quality-count");
const qualityList = document.querySelector("#quality-list");
const warningBox = document.querySelector("#warning-box");
const warningList = document.querySelector("#warning-list");
const observationHead = document.querySelector("#observation-head");
const observationBody = document.querySelector("#observation-body");
const provenanceList = document.querySelector("#provenance-list");
const usageNotice = document.querySelector("#usage-notice");
const correlationId = document.querySelector("#correlation-id");
const traceList = document.querySelector("#trace-list");
const resultCaveat = document.querySelector("#result-caveat");

let loadingTimers = [];

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function svgElement(tag, attributes = {}) {
  const node = document.createElementNS(SVG_NS, tag);
  Object.entries(attributes).forEach(([name, value]) => node.setAttribute(name, String(value)));
  return node;
}

function finiteNumber(value) {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatNumber(value, digits = 2) {
  const number = finiteNumber(value);
  if (number === null) return "—";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(number);
}

function formatInteger(value) {
  const number = finiteNumber(value);
  if (number === null) return "—";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(number);
}

function formatSigned(value, suffix = "") {
  const number = finiteNumber(value);
  if (number === null) return "—";
  const sign = number > 0 ? "+" : "";
  return `${sign}${formatNumber(number)}${suffix}`;
}

function formatDate(value) {
  if (!value) return "—";
  const raw = String(value);
  const date = new Date(`${raw.slice(0, 10)}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return raw;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}

function formatTimestamp(value) {
  if (!value) return "—";
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  });
}

function apiDetailMessage(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => {
      if (!item || typeof item !== "object") return String(item);
      const location = Array.isArray(item.loc) ? item.loc.filter((part) => part !== "body").join(".") : "";
      return `${location ? `${location}: ` : ""}${item.msg || "Invalid request"}`;
    });
    return messages.join(" ");
  }
  if (detail && typeof detail === "object") return detail.message || JSON.stringify(detail);
  return "The local API rejected the request.";
}

async function getJson(url, options = {}) {
  const response = await fetch(url, options);
  let body = null;
  try {
    body = await response.json();
  } catch (_) {
    // The status code is enough when an upstream proxy returns non-JSON content.
  }
  if (!response.ok) {
    const message = body && body.detail
      ? apiDetailMessage(body.detail)
      : `Local API request failed (${response.status}).`;
    throw new Error(message);
  }
  return body;
}

function normalizeField(field) {
  field.value = field.value.trim().toUpperCase();
  return field.value;
}

function validateContract() {
  const primary = normalizeField(primaryField);
  const benchmark = normalizeField(benchmarkField);
  primaryField.setAttribute("aria-invalid", "false");
  benchmarkField.setAttribute("aria-invalid", "false");
  formError.hidden = true;

  if (!SYMBOL_PATTERN.test(primary)) {
    primaryField.setAttribute("aria-invalid", "true");
    formError.textContent = "Enter a valid primary Yahoo Finance ticker, such as AAPL, BRK-B, ^GSPC, or BTC-USD.";
    formError.hidden = false;
    primaryField.focus();
    return null;
  }
  if (!SYMBOL_PATTERN.test(benchmark)) {
    benchmarkField.setAttribute("aria-invalid", "true");
    formError.textContent = "Enter a valid benchmark Yahoo Finance ticker, such as SPY or QQQ.";
    formError.hidden = false;
    benchmarkField.focus();
    return null;
  }
  if (primary === benchmark) {
    primaryField.setAttribute("aria-invalid", "true");
    benchmarkField.setAttribute("aria-invalid", "true");
    formError.textContent = "Primary and benchmark symbols must be different.";
    formError.hidden = false;
    benchmarkField.focus();
    return null;
  }
  return {
    primary_symbol: primary,
    benchmark_symbol: benchmark,
    period: periodField.value,
  };
}

function clearLoadingTimers() {
  loadingTimers.forEach((timer) => window.clearTimeout(timer));
  loadingTimers = [];
}

function showLoading() {
  clearLoadingTimers();
  idleState.hidden = true;
  failureState.hidden = true;
  resultContent.hidden = true;
  loadingState.hidden = false;
  document.body.classList.add("is-running");
  runButton.disabled = true;
  runCopy.textContent = "Routing live request";
  loadingLabel.textContent = "Data User is validating the request contract…";
  const messages = [
    [550, "Plaza is discovering the Data Consultant…"],
    [1200, "Data Consultant is requesting adjusted closes from yfinance…"],
    [2600, "Waiting for the upstream Yahoo Finance response…"],
    [5200, "Aligning sessions and calculating descriptive statistics…"],
  ];
  messages.forEach(([delay, message]) => {
    loadingTimers.push(window.setTimeout(() => {
      loadingLabel.textContent = message;
    }, delay));
  });
}

function finishLoading() {
  clearLoadingTimers();
  loadingState.hidden = true;
  document.body.classList.remove("is-running");
  runButton.disabled = false;
  runCopy.textContent = "Run live comparison";
}

function renderPresets(comparisons) {
  if (!Array.isArray(comparisons) || !comparisons.length) return;
  clearNode(presetButtons);
  comparisons.slice(0, 4).forEach((comparison) => {
    if (!comparison || typeof comparison !== "object") return;
    const primary = String(comparison.primary_symbol || "").toUpperCase();
    const benchmark = String(comparison.benchmark_symbol || "").toUpperCase();
    const period = String(comparison.period || "1y");
    if (!SYMBOL_PATTERN.test(primary) || !SYMBOL_PATTERN.test(benchmark)) return;
    const button = element("button", "", `${primary} / ${benchmark}`);
    button.type = "button";
    button.dataset.primary = primary;
    button.dataset.benchmark = benchmark;
    button.dataset.period = period;
    button.setAttribute("aria-label", `Load ${primary} versus ${benchmark} over ${period}`);
    presetButtons.appendChild(button);
  });
}

function applyPreset(button) {
  primaryField.value = button.dataset.primary || "AAPL";
  benchmarkField.value = button.dataset.benchmark || "SPY";
  const period = button.dataset.period || "1y";
  if ([...periodField.options].some((option) => option.value === period)) periodField.value = period;
  formError.hidden = true;
  primaryField.focus();
}

function renderLegend(primary, benchmark) {
  clearNode(chartLegend);
  [
    { symbol: primary, className: "legend-item" },
    { symbol: benchmark, className: "legend-item secondary" },
  ].forEach((item) => {
    const label = element("span", item.className);
    label.appendChild(element("i", "legend-swatch"));
    label.appendChild(element("span", "", item.symbol));
    chartLegend.appendChild(label);
  });
}

function appendSvgText(parent, x, y, text, anchor = "start") {
  const label = svgElement("text", {
    x,
    y,
    class: "chart-axis-text",
    "text-anchor": anchor,
  });
  label.textContent = String(text);
  parent.appendChild(label);
}

function renderChart(series, primary, benchmark) {
  clearNode(performanceChart);
  renderLegend(primary, benchmark);

  const points = (Array.isArray(series) ? series : []).map((row) => ({
    date: String(row.date || ""),
    primary: finiteNumber(row[primary]),
    benchmark: finiteNumber(row[benchmark]),
  })).filter((row) => row.date && row.primary !== null && row.benchmark !== null);

  if (points.length < 2) {
    appendSvgText(performanceChart, 480, 154, "Not enough aligned observations to draw a comparison", "middle");
    chartDescription.textContent = "No chart is available because fewer than two aligned observations were returned.";
    return;
  }

  const width = 960;
  const height = 300;
  const margin = { top: 18, right: 22, bottom: 32, left: 54 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const values = points.flatMap((point) => [point.primary, point.benchmark]);
  let minimum = Math.min(100, ...values);
  let maximum = Math.max(100, ...values);
  const padding = Math.max((maximum - minimum) * 0.1, 2);
  minimum -= padding;
  maximum += padding;

  const x = (index) => margin.left + (index / (points.length - 1)) * plotWidth;
  const y = (value) => margin.top + ((maximum - value) / (maximum - minimum)) * plotHeight;

  for (let index = 0; index < 5; index += 1) {
    const ratio = index / 4;
    const value = maximum - ratio * (maximum - minimum);
    const position = margin.top + ratio * plotHeight;
    performanceChart.appendChild(svgElement("line", {
      x1: margin.left,
      y1: position,
      x2: width - margin.right,
      y2: position,
      class: Math.abs(value - 100) < (maximum - minimum) / 9 ? "chart-baseline" : "chart-grid-line",
    }));
    appendSvgText(performanceChart, margin.left - 9, position + 3, formatNumber(value, 0), "end");
  }

  const xIndices = [...new Set([0, Math.floor((points.length - 1) / 2), points.length - 1])];
  xIndices.forEach((index, labelIndex) => {
    const anchor = labelIndex === 0 ? "start" : labelIndex === xIndices.length - 1 ? "end" : "middle";
    appendSvgText(performanceChart, x(index), height - 10, formatDate(points[index].date), anchor);
  });

  const pathData = (key) => points
    .map((point, index) => `${index === 0 ? "M" : "L"}${x(index).toFixed(2)},${y(point[key]).toFixed(2)}`)
    .join(" ");

  performanceChart.appendChild(svgElement("path", {
    d: pathData("benchmark"),
    class: "chart-path-benchmark",
  }));
  performanceChart.appendChild(svgElement("path", {
    d: pathData("primary"),
    class: "chart-path-primary",
  }));

  const last = points[points.length - 1];
  performanceChart.appendChild(svgElement("circle", {
    cx: x(points.length - 1), cy: y(last.benchmark), r: 4, class: "chart-end-dot-benchmark",
  }));
  performanceChart.appendChild(svgElement("circle", {
    cx: x(points.length - 1), cy: y(last.primary), r: 4, class: "chart-end-dot-primary",
  }));

  chartDescription.textContent = `${primary} ends at ${formatNumber(last.primary)} and ${benchmark} ends at ${formatNumber(last.benchmark)}, with both series normalized to 100 on ${formatDate(points[0].date)}.`;
}

function renderRelativeMetrics(relative, primary, benchmark) {
  clearNode(relativeMetrics);
  const items = [
    {
      label: `${primary} return spread`,
      value: formatSigned(relative.return_spread_pct_points, " pp"),
      note: `versus ${benchmark} over the aligned window`,
    },
    {
      label: "Daily-return correlation",
      value: formatNumber(relative.daily_return_correlation, 3),
      note: "Pearson correlation of aligned daily returns",
    },
    {
      label: `Beta to ${benchmark}`,
      value: formatNumber(relative.beta_to_benchmark, 3),
      note: "sample covariance divided by benchmark variance",
    },
  ];
  items.forEach((item) => {
    const block = element("div", "relative-metric");
    block.appendChild(element("span", "", item.label));
    block.appendChild(element("strong", "", item.value));
    block.appendChild(element("small", "", item.note));
    relativeMetrics.appendChild(block);
  });
}

function metricValue(metric, key, kind) {
  const value = metric ? metric[key] : null;
  if (kind === "percent") return formatSigned(value, "%");
  if (kind === "volume" || kind === "integer") return formatInteger(value);
  if (kind === "price") {
    const formatted = formatNumber(value, 2);
    return formatted === "—" ? formatted : `${formatted} ${metric.currency || ""}`.trim();
  }
  return formatNumber(value, 3);
}

function renderMetricLedger(metrics, primary, benchmark) {
  clearNode(metricHead);
  clearNode(metricBody);

  const headerRow = element("tr");
  const labelHeader = element("th", "", "Metric");
  labelHeader.scope = "col";
  headerRow.appendChild(labelHeader);
  [primary, benchmark].forEach((symbol) => {
    const header = element("th", "", symbol);
    header.scope = "col";
    headerRow.appendChild(header);
  });
  metricHead.appendChild(headerRow);

  const rows = [
    ["Latest adjusted close", "latest_close", "price"],
    ["Total return", "total_return_pct", "percent"],
    ["Annualized volatility", "annualized_volatility_pct", "percent"],
    ["Maximum drawdown", "max_drawdown_pct", "percent"],
    ["Period high", "period_high", "price"],
    ["Period low", "period_low", "price"],
    ["Average volume", "average_volume", "volume"],
    ["Aligned observations", "observations", "integer"],
  ];

  rows.forEach(([label, key, kind]) => {
    const row = element("tr");
    const heading = element("th", "", label);
    heading.scope = "row";
    row.appendChild(heading);
    row.appendChild(element("td", "", metricValue(metrics[primary], key, kind)));
    row.appendChild(element("td", "", metricValue(metrics[benchmark], key, kind)));
    metricBody.appendChild(row);
  });
}

function qualityStatus(raw) {
  const status = String(raw || "").toLowerCase();
  if (status === "pass" || status === "true") return "pass";
  if (status === "warn" || status === "warning") return "warn";
  return "fail";
}

function renderQuality(consultantQuality, acceptance) {
  clearNode(qualityList);
  clearNode(warningList);

  const consultantChecks = Array.isArray(consultantQuality.checks) ? consultantQuality.checks : [];
  const acceptanceChecks = acceptance && Array.isArray(acceptance.checks) ? acceptance.checks : [];
  const checks = [
    ...acceptanceChecks.map((check) => ({
      name: `User · ${check.name || "acceptance"}`,
      status: check.passed ? "pass" : "fail",
      detail: check.passed ? "Accepted by the Data User contract." : "Rejected by the Data User contract.",
    })),
    ...consultantChecks.map((check) => ({
      name: `Data · ${check.name || "quality"}`,
      status: qualityStatus(check.status),
      detail: check.detail || "No detail returned.",
    })),
  ];

  let passed = 0;
  checks.forEach((check) => {
    const status = qualityStatus(check.status);
    if (status === "pass") passed += 1;
    const item = element("li");
    item.appendChild(element("span", `check-mark ${status === "pass" ? "" : status}`.trim(), status === "pass" ? "✓" : status === "warn" ? "~" : "×"));
    item.appendChild(element("span", "check-name", check.name));
    item.appendChild(element("span", "check-detail", check.detail));
    qualityList.appendChild(item);
  });
  if (!checks.length) qualityList.appendChild(element("li", "check-detail", "No quality checks were returned."));
  qualityCount.textContent = `${passed}/${checks.length} pass`;

  const warnings = [
    ...(Array.isArray(consultantQuality.warnings) ? consultantQuality.warnings : []),
    ...(acceptance && Array.isArray(acceptance.warnings) ? acceptance.warnings : []),
  ];
  const uniqueWarnings = [...new Set(warnings.filter(Boolean).map(String))];
  warningBox.hidden = uniqueWarnings.length === 0;
  uniqueWarnings.forEach((warning) => warningList.appendChild(element("li", "", warning)));
}

function renderObservations(observations, primary, benchmark) {
  clearNode(observationHead);
  clearNode(observationBody);
  const headerRow = element("tr");
  ["Date", primary, benchmark].forEach((label) => {
    const heading = element("th", "", label);
    heading.scope = "col";
    headerRow.appendChild(heading);
  });
  observationHead.appendChild(headerRow);

  const rows = Array.isArray(observations) ? [...observations].reverse() : [];
  rows.forEach((observation) => {
    const row = element("tr");
    const dateCell = element("th", "", formatDate(observation.date));
    dateCell.scope = "row";
    row.appendChild(dateCell);
    row.appendChild(element("td", "", formatNumber(observation[primary], 2)));
    row.appendChild(element("td", "", formatNumber(observation[benchmark], 2)));
    observationBody.appendChild(row);
  });
  if (!rows.length) {
    const row = element("tr");
    const cell = element("td", "", "No aligned observations were returned.");
    cell.colSpan = 3;
    row.appendChild(cell);
    observationBody.appendChild(row);
  }
}

function provenanceValues(item) {
  const query = item && typeof item.query === "object" ? item.query : {};
  return [
    ["Name", item.name || "—"],
    ["Exchange", item.exchange || "—"],
    ["Currency", item.currency || "—"],
    ["Instrument", item.instrument_type || "—"],
    ["Method", query.method || "yfinance.Ticker.history"],
    ["Period / interval", `${query.period || "—"} / ${query.interval || "—"}`],
    ["Auto-adjust", query.auto_adjust === true ? "true" : "false"],
    ["Actions / repair", `${query.actions === true ? "true" : "false"} / ${query.repair === true ? "true" : "false"}`],
    ["Rows received / used", `${formatInteger(item.rows_received)} / ${formatInteger(item.rows_used)}`],
    ["Rows dropped", formatInteger(item.rows_dropped)],
    ["Fetched", formatTimestamp(item.fetched_at_utc)],
  ];
}

function renderProvenance(provenance, source) {
  clearNode(provenanceList);
  const records = Array.isArray(provenance) ? provenance : [];
  records.forEach((item) => {
    const card = element("article", "provenance-card");
    const header = element("header");
    header.appendChild(element("h4", "", item.symbol || "Unknown symbol"));
    header.appendChild(element("span", "", "YFINANCE RESPONSE"));
    card.appendChild(header);
    const ledger = element("dl");
    provenanceValues(item).forEach(([label, value]) => {
      const group = element("div");
      group.appendChild(element("dt", "", label));
      const description = element("dd", "", value);
      description.title = String(value);
      group.appendChild(description);
      ledger.appendChild(group);
    });
    card.appendChild(ledger);
    provenanceList.appendChild(card);
  });
  if (!records.length) provenanceList.appendChild(element("p", "check-detail", "No successful provider response produced provenance."));
  usageNotice.textContent = source.usage || "yfinance is used for research and educational purposes. Yahoo Finance data is intended for personal use.";
}

function traceRow(event, compact = false) {
  const item = element("li", compact ? "failure-trace-item" : "trace-item");
  const sequence = finiteNumber(event.sequence);
  item.appendChild(element("span", "trace-sequence", sequence === null ? "—" : String(sequence).padStart(2, "0")));

  const actor = element("div", "trace-actor");
  actor.appendChild(element("strong", "", event.actor || "unknown"));
  const route = event.target ? `${event.stage || "event"} → ${event.target}` : event.stage || "event";
  actor.appendChild(element("small", "", route));
  item.appendChild(actor);
  item.appendChild(element("span", "trace-summary", event.summary || "No summary returned."));

  if (!compact) {
    const elapsed = finiteNumber(event.elapsed_ms);
    item.appendChild(element("span", "trace-time", elapsed === null ? "—" : `+${formatNumber(elapsed, 1)} ms`));
    if (event.detail && typeof event.detail === "object" && Object.keys(event.detail).length) {
      const inspector = element("details", "trace-detail");
      inspector.appendChild(element("summary", "", "Inspect payload summary"));
      inspector.appendChild(element("code", "", JSON.stringify(event.detail, null, 2)));
      item.appendChild(inspector);
    }
  }
  return item;
}

function renderTrace(events, target = traceList, compact = false) {
  clearNode(target);
  const trace = Array.isArray(events) ? events : [];
  trace.forEach((event) => target.appendChild(traceRow(event, compact)));
  if (!trace.length) target.appendChild(element("li", compact ? "failure-trace-item" : "trace-item", "No trace events were returned."));
}

function renderFailureResponse(data, fallbackMessage) {
  idleState.hidden = true;
  resultContent.hidden = true;
  loadingState.hidden = true;
  failureState.hidden = false;

  const consultant = data && data.consultant ? data.consultant : {};
  const answer = data && data.answer ? data.answer : {};
  const errors = Array.isArray(consultant.errors) ? consultant.errors : [];
  failureTitle.textContent = answer.headline || "The live comparison could not be completed.";
  failureMessage.textContent = answer.summary || fallbackMessage || "The Data Consultant returned no usable comparison.";
  clearNode(failureList);
  if (errors.length) {
    errors.forEach((error) => {
      const symbol = error.symbol ? `${error.symbol} · ` : "";
      const code = error.code ? `${error.code} · ` : "";
      failureList.appendChild(element("li", "", `${symbol}${code}${error.message || "Provider request failed."}`));
    });
  } else {
    failureList.appendChild(element("li", "", "No market series were substituted or generated."));
  }
  const id = data && data.correlation_id ? String(data.correlation_id) : "not available";
  failureCorrelation.textContent = `Correlation · ${id}`;
  renderTrace(data && data.trace, failureTraceList, true);
}

function renderRequestError(error) {
  renderFailureResponse(null, error.message || String(error));
  failureTitle.textContent = "The local demo request failed before a comparison returned.";
  clearNode(failureList);
  failureList.appendChild(element("li", "", "No synthetic or cached market prices were used."));
}

function renderResult(data) {
  const request = data.request || {};
  const consultant = data.consultant || {};
  const answer = data.answer || {};
  const source = consultant.source || {};
  const coverage = consultant.coverage || {};
  const primary = String(request.primary_symbol || primaryField.value).toUpperCase();
  const benchmark = String(request.benchmark_symbol || benchmarkField.value).toUpperCase();
  const metrics = consultant.metrics || {};
  const series = Array.isArray(consultant.series) ? consultant.series : [];

  if (["partial", "unavailable"].includes(String(data.status)) || !metrics[primary] || !metrics[benchmark] || series.length < 2) {
    renderFailureResponse(data);
    return;
  }

  idleState.hidden = true;
  failureState.hidden = true;
  loadingState.hidden = true;
  resultContent.hidden = false;

  const status = String(data.status || consultant.status || "needs-review");
  resultStatus.textContent = status.replaceAll("-", " ").toUpperCase();
  resultStatus.className = `status-chip ${status}`;
  coverageLabel.textContent = `${formatDate(coverage.start)} — ${formatDate(coverage.end)}`;
  observationLabel.textContent = `${formatInteger(coverage.observations)} aligned sessions`;
  resultHeadline.textContent = answer.headline || `${primary} compared with ${benchmark}.`;
  resultSummary.textContent = answer.summary || "The Data Consultant returned an aligned adjusted-close comparison.";
  providerVersion.textContent = `version ${source.version || "—"}`;
  resultCaveat.textContent = answer.caveat || "Descriptive educational output only; not investment advice.";

  renderChart(series, primary, benchmark);
  renderRelativeMetrics(consultant.relative || {}, primary, benchmark);
  renderMetricLedger(metrics, primary, benchmark);
  renderQuality(consultant.quality || {}, data.acceptance || {});
  renderObservations(consultant.latest_observations || [], primary, benchmark);
  renderProvenance(consultant.provenance || [], source);
  correlationId.textContent = data.correlation_id || "—";
  correlationId.title = data.correlation_id || "";
  renderTrace(data.trace || []);
}

async function runContract() {
  const contract = validateContract();
  if (!contract) return;
  showLoading();
  try {
    const data = await getJson("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(contract),
    });
    renderResult(data);
  } catch (error) {
    renderRequestError(error);
  } finally {
    finishLoading();
  }
}

demoForm.addEventListener("submit", (event) => {
  event.preventDefault();
  runContract();
});

retryButton.addEventListener("click", () => demoForm.requestSubmit());

presetButtons.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-primary]");
  if (button) applyPreset(button);
});

[primaryField, benchmarkField].forEach((field) => {
  field.addEventListener("blur", () => normalizeField(field));
  field.addEventListener("input", () => {
    field.removeAttribute("aria-invalid");
    formError.hidden = true;
  });
});

async function boot() {
  if (window.location.protocol === "file:") return;
  const [healthResult, examplesResult] = await Promise.allSettled([
    getJson("/health"),
    getJson("/api/examples"),
  ]);

  if (healthResult.status === "fulfilled") {
    const health = healthResult.value || {};
    runtimeStatus.classList.add("online");
    runtimeLabel.textContent = `${health.mode || "live"} · ${health.provider || "yfinance"} ${health.provider_version || ""}`.trim();
  } else {
    runtimeStatus.classList.add("offline");
    runtimeLabel.textContent = "local runtime unavailable";
  }

  if (examplesResult.status === "fulfilled") {
    renderPresets(examplesResult.value && examplesResult.value.comparisons);
  }
}

boot();
