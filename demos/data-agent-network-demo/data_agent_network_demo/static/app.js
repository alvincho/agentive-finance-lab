const promptField = document.querySelector("#prompt");
const demoForm = document.querySelector("#demo-form");
const runButton = document.querySelector("#run-button");
const offlineToggle = document.querySelector("#simulate-offline");
const exampleButtons = document.querySelector("#example-buttons");
const networkMap = document.querySelector("#network-map");
const consultantNode = document.querySelector("#consultant-node");
const networkStatus = document.querySelector("#network-status");
const emptyState = document.querySelector("#empty-state");
const resultContent = document.querySelector("#result-content");
const resultStatus = document.querySelector("#result-status");
const resultHeadline = document.querySelector("#result-headline");
const resultSummary = document.querySelector("#result-summary");
const resultCaveat = document.querySelector("#result-caveat");
const correlationId = document.querySelector("#correlation-id");
const requirementsStrip = document.querySelector("#requirements-strip");
const recommendations = document.querySelector("#recommendations");
const benefits = document.querySelector("#benefits");
const traceList = document.querySelector("#trace-list");
let registeredNetworkSummary = "Reading the in-memory Plaza directory…";

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function getJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body.detail) message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch (_) {
      // Keep the status-based message when a response is not JSON.
    }
    throw new Error(message);
  }
  return response.json();
}

function renderExamples(prompts) {
  clearNode(exampleButtons);
  prompts.slice(0, 3).forEach((prompt, index) => {
    const shortPrompt = prompt.length > 42 ? `${prompt.slice(0, 39)}…` : prompt;
    const button = element("button", "example-button", `0${index + 1} · ${shortPrompt}`);
    button.type = "button";
    button.title = prompt;
    button.setAttribute("aria-label", `Load example ${index + 1}: ${prompt}`);
    button.addEventListener("click", () => {
      promptField.value = prompt;
      promptField.focus();
    });
    exampleButtons.appendChild(button);
  });
}

function renderRequirements(request) {
  clearNode(requirementsStrip);
  const values = [
    ...(request.needs || []).map((value) => `need:${value}`),
    ...(request.priorities || []).map((value) => `priority:${value}`),
    ...(request.instruments || []).map((value) => `instrument:${value}`),
  ];
  values.forEach((value) => requirementsStrip.appendChild(element("span", "requirement-chip", value)));
}

function renderRecommendations(items) {
  clearNode(recommendations);
  if (!items.length) {
    recommendations.appendChild(
      element("p", "trace-placeholder", "No recommendation was produced. The evidence gap remains explicit."),
    );
    return;
  }

  items.forEach((item, index) => {
    const row = element("article", "recommendation");
    row.appendChild(element("span", "recommendation-rank", String(index + 1).padStart(2, "0")));

    const copy = element("div");
    copy.appendChild(element("strong", "", item.name));
    copy.appendChild(element("p", "", item.rationale));
    copy.appendChild(
      element("small", "", `${item.freshness} · ${item.cost} · ${item.access} · ${item.limitation}`),
    );
    row.appendChild(copy);
    row.appendChild(element("span", "score", `${item.score} pts`));
    recommendations.appendChild(row);
  });
}

function renderBenefits(benefit) {
  clearNode(benefits);
  ["separation", "discoverability", "inspectability", "replaceability"].forEach((key) => {
    if (!benefit[key]) return;
    const group = element("div");
    group.appendChild(element("dt", "", key));
    group.appendChild(element("dd", "", benefit[key]));
    benefits.appendChild(group);
  });
}

function renderTrace(events) {
  clearNode(traceList);
  events.forEach((event, index) => {
    const item = element("li", "trace-item");
    item.style.animationDelay = `${Math.min(index * 70, 700)}ms`;
    item.appendChild(element("span", "trace-sequence", String(event.sequence).padStart(2, "0")));

    const actor = element("div", "trace-actor");
    actor.appendChild(element("strong", "", event.actor));
    actor.appendChild(
      element("small", "", event.target ? `${event.stage} → ${event.target}` : event.stage),
    );
    item.appendChild(actor);
    item.appendChild(element("span", "trace-summary", event.summary));
    item.appendChild(element("span", "trace-time", `+${event.elapsed_ms.toFixed(1)} ms`));

    if (event.detail && Object.keys(event.detail).length) {
      const inspector = element("details", "trace-detail");
      inspector.appendChild(element("summary", "", "Inspect payload summary"));
      inspector.appendChild(element("code", "", JSON.stringify(event.detail, null, 2)));
      item.appendChild(inspector);
    }
    traceList.appendChild(item);
  });
}

function syncConsultantAvailability() {
  const offline = offlineToggle.checked;
  networkMap.classList.toggle("consultant-offline", offline);
  consultantNode.setAttribute("aria-disabled", String(offline));
  networkStatus.textContent = offline
    ? "Simulation armed · Data Consultant will be absent from Plaza for the next run"
    : registeredNetworkSummary;
}

function renderResult(data) {
  emptyState.hidden = true;
  resultContent.hidden = false;
  resultStatus.textContent = data.status;
  resultStatus.classList.toggle("degraded", data.status === "degraded");
  resultHeadline.textContent = data.answer.headline;
  resultSummary.textContent = data.answer.summary;
  resultCaveat.textContent = data.answer.caveat;
  correlationId.textContent = data.correlation_id;
  correlationId.title = data.correlation_id;
  renderRequirements(data.request);
  renderRecommendations(data.consultant.recommendations || []);
  renderBenefits(data.benefit || {});
  renderTrace(data.trace || []);
}

function renderError(error) {
  emptyState.hidden = true;
  resultContent.hidden = false;
  resultStatus.textContent = "error";
  resultStatus.classList.add("degraded");
  resultHeadline.textContent = "The demo could not complete this request.";
  resultSummary.textContent = error.message;
  resultCaveat.textContent = "No external side effect occurred; edit the question and try again.";
  correlationId.textContent = "no correlation id";
  clearNode(requirementsStrip);
  clearNode(recommendations);
  clearNode(benefits);
  clearNode(traceList);
  traceList.appendChild(element("li", "trace-placeholder", "The request failed before a trace was returned."));
}

demoForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  runButton.disabled = true;
  runButton.firstElementChild.textContent = "Routing request…";
  try {
    const data = await getJson("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: promptField.value,
        simulate_consultant_offline: offlineToggle.checked,
      }),
    });
    renderResult(data);
  } catch (error) {
    renderError(error);
  } finally {
    runButton.disabled = false;
    runButton.firstElementChild.textContent = "Run agent network";
  }
});

offlineToggle.addEventListener("change", syncConsultantAvailability);

async function boot() {
  try {
    const [network, examples] = await Promise.all([
      getJson("/api/network"),
      getJson("/api/examples"),
    ]);
    const names = network.pits.map((pit) => pit.name).join(" + ");
    registeredNetworkSummary = `${network.plaza.name} · ${network.pits.length} registered Personas · ${names}`;
    syncConsultantAvailability();
    renderExamples(examples.prompts || []);
  } catch (error) {
    networkStatus.textContent = `Runtime metadata unavailable: ${error.message}`;
  }
}

boot();
