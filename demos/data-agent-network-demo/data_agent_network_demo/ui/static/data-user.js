(() => {
  "use strict";

  // Reduced directly from the FinMAS Data User UI. The interaction boundary,
  // rendering vocabulary, and Pulse names remain the same; production-only
  // settings, persistence, ratings, credentials, and comparison flows are absent.
  const byId = (id) => document.getElementById(id);
  const appShell = byId("appShell");
  const conversation = byId("conversation");
  const emptyState = byId("emptyState");
  const messageStream = byId("messageStream");
  const composer = byId("composer");
  const queryInput = byId("queryInput");
  const sendButton = byId("sendButton");
  const preferencePanel = byId("preferencePanel");
  const preferenceButton = byId("preferenceButton");
  const detailDialog = byId("detailDialog");
  const dialogBody = byId("dialogBody");
  const dialogTitle = byId("dialogTitle");
  const dialogEyebrow = byId("dialogEyebrow");
  const howDialog = byId("howDialog");

  const singleSourceDefaults = {
    slug: "single-source",
    number: "1",
    title: "Data Agent / Single Source",
    mode: "single-source",
    enable_live_fetch: true,
    api_base: "/api",
    source_catalog_label: "YFinance",
    source_network_label: "the YFinance Data Source",
    source_direct_label: "YFinance Data Source",
    participant_summary: "Data User, Data Consultant, and the YFinance Data Source",
    empty_copy: "Describe the data you need. Data User asks Data Consultant to search its synchronized YFinance endpoint catalog, then lets you inspect and call the selected Data Source directly.",
    query_placeholder: "Ask which YFinance data fits your work…",
    network_note: "Catalog advice is deterministic and uses no LLM. Live fetches go directly from Data User to the YFinance Data Source Pulse.",
    how_eyebrow: "Three agents, one Plaza",
    how_memory_copy: "Data Consultant retrieves matching endpoint and field documentation synchronized from YFinance. No provider observations are fetched and no LLM is called.",
    how_direct_copy: "Data User resolves YFinance through Consultant status, then uses data_spec or data_fetch on the Data Source.",
    suggestions: [
      { label: "Price history", title: "Daily AAPL prices and volume", query: "I need daily prices and volume for AAPL. Which YFinance endpoint and fields should I use?" },
      { label: "Current quote", title: "MSFT snapshot fields", query: "Which YFinance endpoint returns a current quote snapshot for MSFT?" },
      { label: "Company profile", title: "AAPL fundamentals and metadata", query: "What company profile and fundamental fields can I retrieve for AAPL?" },
      { label: "Endpoint contract", title: "Historical OHLCV parameters", query: "I need historical OHLCV data for an equity research prototype. What parameters are required?" },
    ],
  };

  const multipleSourceDefaults = {
    ...singleSourceDefaults,
    slug: "multiple-sources",
    number: "2",
    title: "Data Agent / Multiple Sources",
    mode: "catalog",
    enable_live_fetch: false,
    api_base: "/api/multiple-sources",
    source_catalog_label: "YFinance, Alpha Vantage, and FRED",
    source_network_label: "the three Data Source agents",
    source_direct_label: "selected Data Source",
    participant_summary: "Data User, Data Consultant, YFinance, Alpha Vantage, and FRED",
    empty_copy: "Describe the data you need. Data User asks Data Consultant to search synchronized catalogs from YFinance, Alpha Vantage, and FRED, then lets you inspect the selected source contract.",
    query_placeholder: "Ask which source data fits your work…",
    network_note: "This view is catalog-only: advice is deterministic, uses no LLM, and performs no provider fetch. Demo 3 exercises the existing live source Pulses.",
    how_eyebrow: "Five agents, one Plaza",
    how_memory_copy: "Data Consultant retrieves matching endpoint and field documentation synchronized from YFinance, Alpha Vantage, and FRED. No provider observations are fetched and no LLM is called.",
    how_direct_copy: "Data User resolves the selected source through Consultant status, then inspects data_spec on that Data Source. Demo 3 exposes the existing data_fetch path.",
    suggestions: [
      { label: "Equity history", title: "Compare daily AAPL routes", query: "Which sources provide daily AAPL prices and volume, and how do their contracts differ?" },
      { label: "Macro series", title: "U.S. CPI observations + revisions", query: "Which source provides U.S. CPI observations and revision vintage dates?" },
      { label: "Company profile", title: "Compare AAPL profile fields", query: "Compare AAPL company profile, sector, industry, and market-cap data across sources." },
      { label: "Source boundary", title: "Inspect a provider contract", query: "Which documented source route should I inspect before fetching data?" },
    ],
  };

  const realDataDefaults = {
    ...multipleSourceDefaults,
    slug: "real-data",
    number: "3",
    title: "Data Agent / Real Data",
    mode: "real-data",
    enable_live_fetch: true,
    api_base: "/api/real-data",
    empty_copy: "Run three guided samples against the same Data Agent Network. Each call goes from Data User directly to one source agent, and every provider result remains separate.",
    query_placeholder: "Ask the Consultant, or run a live sample above…",
    network_note: "Live samples call each selected Data Source Pulse directly. Provider keys stay in the server-side .env file and never enter chat or Pulse input.",
    how_eyebrow: "Five agents, live provider boundaries",
    how_memory_copy: "Data Consultant still owns catalog-grounded advice. The guided samples skip advice and exercise the existing data_fetch Pulse on each selected source agent.",
    how_direct_copy: "Data User sends one direct data_fetch call per provider. Results are shown separately; the Consultant and Plaza never proxy or merge provider payloads.",
    suggestions: [
      {
        sample_id: "no-key",
        label: "Sample 1 · baseline",
        title: "YFinance succeeds; Alpha checks its key",
        query: "Fetch one month of daily AAPL data separately from YFinance and Alpha Vantage.",
        description: "Runs both source agents. Without an Alpha key, its explicit authentication error is part of the demo.",
      },
      {
        sample_id: "alpha-key",
        requires_source: "alpha_vantage",
        label: "Sample 2 · bring a key",
        title: "Fetch AAPL from both equity sources",
        query: "Fetch one month of daily AAPL data separately from YFinance and Alpha Vantage with the configured server key.",
        description: "Requires ALPHA_VANTAGE_API_KEY in .env and a server restart.",
      },
      {
        sample_id: "fred",
        requires_source: "fred",
        label: "Sample 3 · macro data",
        title: "Fetch 12 CPI observations from FRED",
        query: "Fetch the 12 most recent CPIAUCSL observations directly from FRED.",
        description: "Requires FRED_API_KEY in .env and a server restart.",
      },
    ],
  };

  function readDemoConfig() {
    const raw = String(document.body.dataset.demoConfig || "").trim();
    let supplied = {};
    if (raw && raw !== "__DATA_USER_DEMO_CONFIG__") {
      try {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) supplied = parsed;
      } catch (_error) {
        supplied = {};
      }
    }
    const realData = supplied.slug === "real-data" || window.location.pathname.includes("/real-data");
    const multiple = supplied.slug === "multiple-sources" || window.location.pathname.includes("/multiple-sources");
    const fallback = realData ? realDataDefaults : multiple ? multipleSourceDefaults : singleSourceDefaults;
    return {
      ...fallback,
      ...supplied,
      suggestions: Array.isArray(supplied.suggestions) && supplied.suggestions.length
        ? supplied.suggestions
        : fallback.suggestions,
    };
  }

  const demoConfig = readDemoConfig();
  const apiBase = `/${String(demoConfig.api_base || "/api").replace(/^\/+|\/+$/g, "")}`;

  function apiUrl(path) {
    return `${apiBase}/${String(path || "").replace(/^\/+/, "")}`;
  }

  function setText(selector, value) {
    document.querySelectorAll(selector).forEach((element) => {
      element.textContent = String(value || "");
    });
  }

  function renderSuggestions(suggestions) {
    const grid = byId("suggestionGrid");
    if (!grid) return;
    grid.textContent = "";
    suggestions.slice(0, 6).forEach((suggestion) => {
      if (!suggestion || typeof suggestion !== "object" || !String(suggestion.query || "").trim()) return;
      const button = document.createElement("button");
      const label = document.createElement("span");
      const title = document.createElement("strong");
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
      button.type = "button";
      button.className = "suggestion";
      button.dataset.query = String(suggestion.query);
      if (suggestion.sample_id) {
        button.classList.add("live-sample");
        button.dataset.sampleId = String(suggestion.sample_id);
      }
      if (suggestion.requires_source) button.dataset.requiresSource = String(suggestion.requires_source);
      label.textContent = String(suggestion.label || "Suggested question");
      title.textContent = String(suggestion.title || suggestion.query);
      use.setAttribute("href", "#icon-chevron");
      svg.appendChild(use);
      button.append(label, title);
      if (suggestion.description) {
        const description = document.createElement("small");
        description.textContent = String(suggestion.description);
        button.appendChild(description);
      }
      if (suggestion.sample_id) {
        const status = document.createElement("i");
        status.className = "sample-readiness";
        status.textContent = "Checking server…";
        button.appendChild(status);
      }
      button.appendChild(svg);
      grid.appendChild(button);
    });
  }

  function applyDemoConfig() {
    document.title = `Data User · ${String(demoConfig.title || "Data Agent Network")}`;
    setText("[data-demo-number]", `Demo ${demoConfig.number || ""}`.trim());
    setText("[data-demo-title]", demoConfig.title);
    setText("[data-empty-copy]", demoConfig.empty_copy);
    setText("[data-network-note]", demoConfig.network_note);
    setText("[data-how-eyebrow]", demoConfig.how_eyebrow);
    setText("[data-how-memory]", demoConfig.how_memory_copy);
    setText("[data-how-direct]", demoConfig.how_direct_copy);
    document.body.dataset.demoMode = String(demoConfig.mode || demoConfig.slug || "");
    document.querySelectorAll("[data-env-help]").forEach((panel) => {
      panel.hidden = demoConfig.mode !== "real-data";
    });
    queryInput.placeholder = String(demoConfig.query_placeholder || "Ask which source data fits your work…");
    renderSuggestions(demoConfig.suggestions);
    document.querySelectorAll("[data-demo-slug]").forEach((link) => {
      const current = link.dataset.demoSlug === demoConfig.slug;
      link.classList.toggle("is-current", current);
      if (current) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
      const stateLabel = link.querySelector(":scope > i");
      if (stateLabel) stateLabel.textContent = current ? "Current" : "Open";
    });
  }

  applyDemoConfig();

  const state = {
    bootstrap: null,
    busy: false,
    requestController: null,
    thinkingTimer: null,
    thinkingElapsedTimer: null,
    specCache: new Map(),
    sourceStatus: null,
    toastTimer: null,
  };

  const liveSamplePlans = {
    "no-key": {
      title: "Sample 1 · Public source and credential boundary",
      prompt: "Fetch one month of daily AAPL data from YFinance and Alpha Vantage as two direct source calls.",
      calls: [
        {
          source_id: "yfinance",
          source_name: "YFinance",
          endpoint_id: "yfinance.ticker.history",
          parameters: { symbol: "AAPL", period: "1mo", interval: "1d", auto_adjust: true },
        },
        {
          source_id: "alpha_vantage",
          source_name: "Alpha Vantage",
          endpoint_id: "alpha_vantage.time_series_daily",
          parameters: { symbol: "AAPL", outputsize: "compact" },
        },
      ],
    },
    "alpha-key": {
      title: "Sample 2 · Two live equity providers",
      prompt: "Use the configured Alpha Vantage key and fetch daily AAPL data separately from both equity source agents.",
      requires_source: "alpha_vantage",
      calls: [
        {
          source_id: "yfinance",
          source_name: "YFinance",
          endpoint_id: "yfinance.ticker.history",
          parameters: { symbol: "AAPL", period: "1mo", interval: "1d", auto_adjust: true },
        },
        {
          source_id: "alpha_vantage",
          source_name: "Alpha Vantage",
          endpoint_id: "alpha_vantage.time_series_daily",
          parameters: { symbol: "AAPL", outputsize: "compact" },
        },
      ],
    },
    fred: {
      title: "Sample 3 · Live macro observations",
      prompt: "Fetch 12 recent CPIAUCSL observations directly from the FRED source agent.",
      requires_source: "fred",
      calls: [
        {
          source_id: "fred",
          source_name: "FRED",
          endpoint_id: "fred.fred_series_observations",
          parameters: { series_id: "CPIAUCSL", limit: 12, sort_order: "desc" },
        },
      ],
    },
  };

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function humanize(value) {
    return String(value || "")
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function truncate(value, length = 120) {
    const text = String(value || "").replace(/\s+/g, " ").trim();
    return text.length > length ? `${text.slice(0, length - 1).trim()}…` : text;
  }

  function compactAge(value) {
    const seconds = Math.max(0, Number(value || 0));
    if (seconds < 60) return "updated now";
    if (seconds < 3600) return `updated ${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `updated ${Math.floor(seconds / 3600)}h ago`;
    return `updated ${Math.floor(seconds / 86400)}d ago`;
  }

  function ageFromTimestamp(value) {
    const milliseconds = Date.parse(String(value || ""));
    if (!Number.isFinite(milliseconds)) return null;
    return Math.max(0, (Date.now() - milliseconds) / 1000);
  }

  function shortUpdateAge(value) {
    const seconds = ageFromTimestamp(value);
    if (seconds === null) return "pending";
    if (seconds < 60) return "now";
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
    return `${Math.floor(seconds / 86400)}d`;
  }

  function icon(name) {
    return `<svg aria-hidden="true"><use href="#icon-${escapeHtml(name)}"></use></svg>`;
  }

  function showToast(message) {
    const toast = byId("toast");
    toast.textContent = message;
    toast.classList.add("visible");
    window.clearTimeout(state.toastTimer);
    state.toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 3200);
  }

  function detailFromError(payload, fallback) {
    if (!payload) return fallback;
    if (typeof payload === "string") return payload;
    if (typeof payload.detail === "string") return payload.detail;
    if (typeof payload.error === "string") return payload.error;
    if (payload.result && typeof payload.result.error === "string") return payload.result.error;
    return fallback;
  }

  async function readJson(response) {
    const text = await response.text();
    if (!text) return {};
    try {
      return JSON.parse(text);
    } catch (_error) {
      throw new Error(`The service returned an unreadable response (${response.status}).`);
    }
  }

  async function callPulse(pulseName, input, signal) {
    if (window.location.protocol === "file:") {
      throw new Error("Start the local demo server and open its http://127.0.0.1 address before calling a Pulse.");
    }
    const response = await fetch(apiUrl("pulse"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pulse_name: pulseName, input }),
      cache: "no-store",
      signal,
    });
    const payload = await readJson(response);
    if (!response.ok) {
      throw new Error(detailFromError(payload, `Pulse request failed (${response.status}).`));
    }
    const result = payload && payload.status === "success" && payload.result !== undefined
      ? payload.result
      : payload;
    if (result && result.error && !result.status) throw new Error(result.error);
    return result || {};
  }

  function sourceInitial(source) {
    const name = String(source.source_name || source.source_id || "D");
    return name.trim().charAt(0).toUpperCase() || "D";
  }

  function sourceRailName(source) {
    const sourceId = String(source && source.source_id || "");
    if (sourceId === "yfinance") return "YFinance";
    if (sourceId === "alpha_vantage") return "Alpha Vantage";
    if (sourceId === "fred") return "FRED";
    return String(source && (source.source_name || source.provider) || humanize(sourceId) || "Data Source");
  }

  function firstBoolean(...values) {
    return values.find((value) => typeof value === "boolean");
  }

  function sourceById(list, sourceId) {
    return (Array.isArray(list) ? list : []).find((source) => String(source.source_id || "") === String(sourceId || ""));
  }

  function sourceAccessState(source) {
    const sourceId = String(source && source.source_id || "");
    const bootstrapSource = sourceById(state.bootstrap && state.bootstrap.sources, sourceId) || {};
    const connectivity = source && source.connectivity && typeof source.connectivity === "object" ? source.connectivity : {};
    const directAccess = source && source.data_access && typeof source.data_access === "object" ? source.data_access : {};
    const nestedAccess = connectivity.data_access && typeof connectivity.data_access === "object" ? connectivity.data_access : {};
    const access = { ...directAccess, ...nestedAccess };
    const credentialRequired = firstBoolean(access.credential_required, source && source.credential_required, bootstrapSource.credential_required);
    const credentialConfigured = firstBoolean(access.credential_configured, source && source.credential_configured, bootstrapSource.credential_configured);
    const fetchReady = firstBoolean(access.fetch_ready, source && source.fetch_ready, bootstrapSource.fetch_ready);
    const verification = String(access.verification || source && source.verification || "");
    return {
      source_id: sourceId,
      credential_required: credentialRequired === undefined ? sourceId !== "yfinance" : credentialRequired,
      credential_configured: Boolean(credentialConfigured),
      fetch_ready: Boolean(fetchReady) || verification === "verified",
      verification,
      reason: String(access.reason || ""),
    };
  }

  function accessPresentation(source) {
    if (source.last_update_error) return { label: "sync error", className: "error" };
    if (source.available === false) return { label: "unavailable", className: "error" };
    const access = sourceAccessState(source);
    if (!access.credential_required) return { label: "public fetch", className: "public" };
    if (access.fetch_ready) return { label: "fetch verified", className: "fetch-verified" };
    if (access.credential_configured) return { label: "key set", className: "key-set" };
    return { label: "key needed", className: "key-needed" };
  }

  function sourceCredentialConfigured(sourceId) {
    const statusSource = sourceById(state.sourceStatus && state.sourceStatus.sources, sourceId);
    const bootstrapSource = sourceById(state.bootstrap && state.bootstrap.sources, sourceId);
    return sourceAccessState(statusSource || bootstrapSource || { source_id: sourceId }).credential_configured;
  }

  function updateLiveSampleControls() {
    document.querySelectorAll("[data-sample-id]").forEach((button) => {
      const sampleId = String(button.dataset.sampleId || "");
      const requirement = String(button.dataset.requiresSource || "");
      const readiness = button.querySelector(".sample-readiness");
      let available = Boolean(state.bootstrap);
      let label = state.bootstrap ? "Ready to run" : "Checking server…";
      if (sampleId === "no-key" && state.bootstrap) {
        available = true;
        label = sourceCredentialConfigured("alpha_vantage")
          ? "Ready · Alpha key detected, both calls may succeed"
          : "Ready · expected Alpha key error";
      } else if (requirement && state.bootstrap) {
        available = sourceCredentialConfigured(requirement);
        label = available
          ? `Ready · ${requirement === "fred" ? "FRED" : "Alpha"} key detected`
          : "Needs .env key + server restart";
      }
      if (state.busy) available = false;
      button.classList.toggle("is-unavailable", !available && Boolean(state.bootstrap));
      button.setAttribute("aria-disabled", available ? "false" : "true");
      if (readiness) readiness.textContent = label;
    });
  }

  function renderSourceNetwork(sources) {
    const target = byId("sourceNetwork");
    const list = Array.isArray(sources) ? sources : [];
    byId("networkCount").textContent = String(list.length);
    target.textContent = "";
    list.forEach((source) => {
      const row = document.createElement("div");
      const status = accessPresentation(source);
      const access = sourceAccessState(source);
      row.className = `source-network-row ${status.className}${source.stale ? " stale" : ""}`;
      row.setAttribute("role", "listitem");
      row.title = source.last_update_error
        ? source.error || "The source catalog could not be synchronized."
        : access.reason || `${source.source_name || source.source_id || "Data Source"} has a synchronized catalog in Plaza.`;
      row.innerHTML = `
        <span class="source-dot"></span>
        <span title="${escapeHtml(source.source_name || source.provider || source.source_id)}">${escapeHtml(sourceRailName(source))}</span>
        <small>${escapeHtml(status.label)}</small>
      `;
      target.appendChild(row);
    });
    if (!list.length) {
      target.innerHTML = '<div class="source-network-row error"><span class="source-dot"></span><span>No source registered</span><small>offline</small></div>';
    }
  }

  async function loadSourceStatus() {
    const liveStatus = byId("liveStatus");
    if (window.location.protocol === "file:") {
      renderSourceNetwork([]);
      liveStatus.className = "live-status error";
      liveStatus.querySelector("span").textContent = "Server required";
      showToast("Run the local demo server, then open the URL it prints.");
      return;
    }
    try {
      const response = await fetch(apiUrl("data-user/bootstrap"), { cache: "no-store" });
      const bootstrap = await readJson(response);
      if (!response.ok) throw new Error(detailFromError(bootstrap, "Unable to reach Data User."));
      state.bootstrap = bootstrap;
      const status = await callPulse("data_source_status", {});
      state.sourceStatus = status;
      const sources = Array.isArray(status.sources)
        ? status.sources
        : Array.isArray(bootstrap.sources)
          ? bootstrap.sources
          : [];
      renderSourceNetwork(sources);
      updateLiveSampleControls();
      if (status.last_update_error || !sources.length) {
        liveStatus.className = "live-status error";
        liveStatus.querySelector("span").textContent = sources.length ? "Source sync issue" : "Source unavailable";
        return;
      }
      const fetchReady = sources.filter((source) => {
        const access = sourceAccessState(source);
        return access.fetch_ready || !access.credential_required;
      }).length;
      liveStatus.className = "live-status ready";
      liveStatus.querySelector("span").textContent = `${sources.length} catalogs · ${fetchReady} fetch-ready`;
      liveStatus.title = `${demoConfig.participant_summary} are registered through Plaza. Provider fetch readiness is shown separately.`;
    } catch (error) {
      renderSourceNetwork([]);
      liveStatus.className = "live-status error";
      liveStatus.querySelector("span").textContent = "Network unavailable";
      showToast(error.message || "Unable to connect to Data User.");
    }
  }

  function formatInline(value) {
    let text = escapeHtml(value);
    text = text.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    return text;
  }

  function renderMarkdown(value) {
    const lines = String(value || "").replace(/\r/g, "").split("\n");
    const output = [];
    let listType = "";
    const closeList = () => {
      if (listType) output.push(`</${listType}>`);
      listType = "";
    };
    lines.forEach((rawLine) => {
      const line = rawLine.trim();
      if (!line) {
        closeList();
        return;
      }
      const heading = line.match(/^(#{2,4})\s+(.+)$/);
      if (heading) {
        closeList();
        const level = Math.min(4, heading[1].length);
        output.push(`<h${level}>${formatInline(heading[2])}</h${level}>`);
        return;
      }
      const bullet = line.match(/^[-*]\s+(.+)$/);
      const ordered = line.match(/^\d+[.)]\s+(.+)$/);
      if (bullet || ordered) {
        const nextType = bullet ? "ul" : "ol";
        if (listType !== nextType) {
          closeList();
          listType = nextType;
          output.push(`<${listType}>`);
        }
        output.push(`<li>${formatInline((bullet || ordered)[1])}</li>`);
        return;
      }
      closeList();
      output.push(`<p>${formatInline(line)}</p>`);
    });
    closeList();
    return output.join("");
  }

  function scrollConversation() {
    window.requestAnimationFrame(() => {
      conversation.scrollTo({ top: conversation.scrollHeight, behavior: "smooth" });
    });
  }

  function renderUserMessage(text) {
    const article = document.createElement("article");
    article.className = "message user-message";
    const bubble = document.createElement("div");
    bubble.className = "user-bubble";
    bubble.textContent = text;
    article.appendChild(bubble);
    messageStream.appendChild(article);
    scrollConversation();
    return article;
  }

  function costLabel(source) {
    const datasets = Array.isArray(source.datasets) ? source.datasets : [];
    const costText = datasets.map((item) => {
      const cost = item && item.cost ? item.cost : {};
      return `${cost.model || ""} ${cost.provider_cost || ""}`.toLowerCase();
    }).join(" ");
    if (costText.includes("free")) return "No direct fee";
    return datasets.length ? "Provider terms" : "Unknown";
  }

  function qualityLabel(source) {
    const datasets = Array.isArray(source.datasets) ? source.datasets : [];
    const caveatCount = datasets.reduce((count, item) => count + (Array.isArray(item.caveats) ? item.caveats.length : 0), 0);
    return caveatCount ? "Provider-dependent" : "Documented";
  }

  function splitValues(value) {
    return String(value || "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function financialFitLabel(source) {
    const matches = (Array.isArray(source.datasets) ? source.datasets : [])
      .map((dataset) => dataset && dataset.financial_match)
      .filter(Boolean);
    if (!matches.length) return "Catalog match";
    const priority = { exact: 4, strong: 3, partial: 2, unconstrained: 1, mismatch: 0 };
    matches.sort((left, right) => (priority[right.level] || 0) - (priority[left.level] || 0));
    const best = matches[0];
    const confidence = Math.round(Number(best.confidence || 0) * 100);
    return `${humanize(best.level)}${best.level === "unconstrained" ? "" : ` · ${confidence}%`}`;
  }

  function financialTags(dataset) {
    const dimensions = dataset && dataset.financial_dimensions ? dataset.financial_dimensions : {};
    const match = dataset && dataset.financial_match ? dataset.financial_match : {};
    const time = dimensions.time || {};
    const matchedAssets = Array.isArray(match.matched_asset_class_tags)
      ? match.matched_asset_class_tags.map((value) => String(value).replace(/^asset_class:/, ""))
      : [];
    const assetTags = matchedAssets.length
      ? matchedAssets.map((value) => `Asset match: ${value}`)
      : (Array.isArray(dimensions.asset_classes) ? dimensions.asset_classes.map((value) => `Asset: ${value}`) : []);
    const values = [
      ...assetTags,
      ...(Array.isArray(time.frequencies) ? time.frequencies : []),
      ...(Array.isArray(time.timeliness) ? time.timeliness : []),
      ...(Array.isArray(dimensions.regions) ? dimensions.regions : []),
      ...(Array.isArray(dimensions.data_types) ? dimensions.data_types : []),
    ];
    return [...new Set(values)].slice(0, 5);
  }

  function datasetRowHtml(source, dataset) {
    const executable = Boolean(dataset.executable);
    const canFetch = Boolean(demoConfig.enable_live_fetch && executable);
    const endpointId = dataset.dataset_id || dataset.endpoint_id || "";
    const match = dataset.financial_match || {};
    const level = String(match.level || "unconstrained");
    const confidence = Math.round(Number(match.confidence || 0) * 100);
    const fitLabel = level === "unconstrained" ? "Catalog match" : `${humanize(level)} fit · ${confidence}%`;
    const tags = financialTags(dataset);
    return `
      <div class="dataset-row">
        <div class="dataset-main">
          <strong title="${escapeHtml(endpointId)}">${escapeHtml(endpointId)}</strong>
          <span><i class="execution-dot${canFetch ? " ready" : ""}"></i>${canFetch ? "Direct source fetch available" : "Specification only"}<b class="fit-label ${escapeHtml(level)}">${escapeHtml(fitLabel)}</b></span>
          ${tags.length ? `<div class="dimension-tags">${tags.map((tag) => `<i>${escapeHtml(humanize(tag))}</i>`).join("")}</div>` : ""}
        </div>
        <div class="dataset-actions">
          <button class="mini-button" type="button" data-action="inspect" data-source-id="${escapeHtml(source.source_id)}" data-endpoint-id="${escapeHtml(endpointId)}">Inspect</button>
          ${canFetch ? `<button class="mini-button primary" type="button" data-action="fetch" data-source-id="${escapeHtml(source.source_id)}" data-endpoint-id="${escapeHtml(endpointId)}">Use</button>` : ""}
        </div>
      </div>
    `;
  }

  function fieldRowHtml(source, field) {
    const routes = Array.isArray(field.access_routes) ? field.access_routes : [];
    const route = routes.find((item) => item && item.executable) || routes[0] || {};
    const canonicalName = field.canonical_name || field.name || "field";
    const vendorNames = Array.isArray(field.vendor_field_names) ? field.vendor_field_names : [];
    const provenance = Array.isArray(field.provider_definitions) && field.provider_definitions.length
      ? "Provider defined"
      : field.inferred ? "Canonical inference" : "Schema mapped";
    const match = field.match || {};
    const pulseDefinition = field.attas_pulse_definition || {};
    const pulseName = pulseDefinition.pulse_name || "data_fetch";
    const canFetch = Boolean(demoConfig.enable_live_fetch && route.executable);
    return `
      <div class="field-row">
        <div class="field-main">
          <div class="field-name-line">
            <strong>${escapeHtml(humanize(canonicalName))}</strong>
            ${match.requested ? '<b class="field-requested">Requested</b>' : match.matched ? '<b class="field-requested relevant">Relevant</b>' : ""}
          </div>
          <p>${escapeHtml(field.definition || "No field definition supplied.")}</p>
          <div class="field-meta">
            <span>${escapeHtml(vendorNames.join(" / ") || field.name || canonicalName)}</span>
            <i>${escapeHtml(field.type || "value")}</i>
            <i>${escapeHtml(field.unit || "provider-defined")}</i>
            <i>${escapeHtml(provenance)}</i>
            <i class="field-contract">${escapeHtml(pulseName)} · canonical</i>
          </div>
        </div>
        ${route.endpoint_id ? `
          <div class="dataset-actions field-actions">
            <button class="mini-button" type="button" data-action="inspect" data-source-id="${escapeHtml(source.source_id)}" data-endpoint-id="${escapeHtml(route.endpoint_id)}">Inspect route</button>
            ${canFetch ? `<button class="mini-button primary" type="button" data-action="fetch" data-source-id="${escapeHtml(source.source_id)}" data-endpoint-id="${escapeHtml(route.endpoint_id)}">Use</button>` : ""}
          </div>
        ` : ""}
      </div>
    `;
  }

  function fieldComparisonItems(result) {
    const direct = Array.isArray(result.field_comparisons) ? result.field_comparisons : [];
    if (direct.length) return direct;
    const sets = Array.isArray(result.comparison_sets) ? result.comparison_sets : [];
    const fieldSet = sets.find((item) => item && item.format === "field_comparison");
    return fieldSet && Array.isArray(fieldSet.items) ? fieldSet.items : [];
  }

  function comparisonDefinitionText(source) {
    const definitions = Array.isArray(source.provider_definitions)
      ? source.provider_definitions.filter(Boolean)
      : [];
    if (definitions.length) return definitions.join(" ");
    return `Canonical definition used · ${humanize(source.definition_source || "canonical mapping")}`;
  }

  function comparisonCostText(source) {
    const cost = source.cost && typeof source.cost === "object" ? source.cost : {};
    if (cost.provider_cost) return String(cost.provider_cost);
    const amount = Number(cost.amount || 0);
    if (amount) return `${amount} ${cost.currency || ""} / ${cost.unit || "request"}`.trim();
    return humanize(cost.model || "provider terms");
  }

  function comparisonQualityText(source) {
    const quality = source.quality && typeof source.quality === "object" ? source.quality : {};
    const notes = Array.isArray(quality.notes) ? quality.notes.filter(Boolean) : [];
    const status = humanize(quality.status || "not stated");
    return notes.length ? `${status} · ${notes[0]}` : status;
  }

  function fieldComparisonHtml(result) {
    const comparisons = fieldComparisonItems(result);
    if (!comparisons.length) return "";
    const visible = comparisons.slice(0, 10);
    return `
      <section class="field-comparison-panel" aria-label="Field comparison">
        <div class="field-comparison-head">
          <div><span>Normalized data dictionary</span><strong>Field-by-field evidence</strong></div>
          <p>${comparisons.length} aligned field${comparisons.length === 1 ? "" : "s"} from the ${escapeHtml(demoConfig.source_catalog_label)} catalog</p>
        </div>
        <div class="field-comparison-list">
          ${visible.map((comparison, index) => {
            const sources = Array.isArray(comparison.sources) ? comparison.sources : [];
            const differences = Array.isArray(comparison.differences) ? comparison.differences.filter(Boolean) : [];
            const compatibility = comparison.compatibility || "single_source";
            const open = comparison.requested || index === 0;
            return `
              <details class="field-comparison-item${comparison.requested ? " requested" : ""}"${open ? " open" : ""}>
                <summary>
                  <span class="comparison-field-name"><strong>${escapeHtml(humanize(comparison.canonical_name))}</strong>${comparison.requested ? '<i class="field-requested">Requested</i>' : ""}</span>
                  <span class="comparison-field-contract">${escapeHtml(comparison.semantic_type || "value")} · ${escapeHtml((comparison.canonical_definition && comparison.canonical_definition.type) || sources[0]?.type || "value")} · ${escapeHtml((comparison.canonical_definition && comparison.canonical_definition.unit) || sources[0]?.unit || "provider-defined")}</span>
                  <span class="comparison-source-count">${sources.length} source${sources.length === 1 ? "" : "s"}</span>
                  <b class="comparison-compatibility ${escapeHtml(compatibility)}">${escapeHtml(humanize(compatibility))}</b>
                </summary>
                <div class="field-comparison-detail">
                  <div class="comparison-canonical-definition"><span>Canonical definition</span><p>${escapeHtml(comparison.definition || "No canonical definition supplied.")}</p></div>
                  <div class="comparison-matrix-scroll">
                    <div class="comparison-matrix" role="table" aria-label="${escapeHtml(humanize(comparison.canonical_name))} source evidence">
                      <div class="comparison-matrix-row comparison-matrix-header" role="row">
                        <span role="columnheader">Source</span><span role="columnheader">Vendor field</span><span role="columnheader">Definition</span><span role="columnheader">Type / unit</span><span role="columnheader">Frequency / access</span><span role="columnheader">Cost / quality</span>
                      </div>
                      ${sources.map((source) => {
                        const vendorNames = Array.isArray(source.vendor_field_names) ? source.vendor_field_names : [];
                        const frequencies = Array.isArray(source.frequencies) ? source.frequencies : [];
                        const routeCount = Number(source.access_route_count || 0);
                        const recommended = source.source_id === comparison.recommended_source_id;
                        return `
                          <div class="comparison-matrix-row" role="row">
                            <span role="cell" class="comparison-source-name"><strong>${escapeHtml(source.source_name || source.source_id)}</strong>${recommended ? "<i>Recommended</i>" : ""}</span>
                            <span role="cell"><strong>${escapeHtml(vendorNames.join(" / ") || comparison.canonical_name)}</strong><small>${escapeHtml(source.provider || source.source_id)}</small></span>
                            <span role="cell"><strong>${escapeHtml(comparisonDefinitionText(source))}</strong><small>${escapeHtml(humanize(source.definition_source || "canonical mapping"))}</small></span>
                            <span role="cell"><strong>${escapeHtml(source.type || "value")}</strong><small>${escapeHtml(source.unit || "provider-defined")}</small></span>
                            <span role="cell"><strong>${escapeHtml(frequencies.join(", ") || "Not stated")}</strong><small>${source.direct_access ? "Direct source access" : "Specification only"} · ${routeCount} route${routeCount === 1 ? "" : "s"}</small></span>
                            <span role="cell"><strong>${escapeHtml(comparisonCostText(source))}</strong><small title="${escapeHtml(comparisonQualityText(source))}">${escapeHtml(comparisonQualityText(source))}</small></span>
                          </div>
                        `;
                      }).join("")}
                    </div>
                  </div>
                  <div class="comparison-findings">
                    <div><span>Observed differences</span>${differences.length ? `<ul>${differences.map((difference) => `<li>${escapeHtml(difference)}</li>`).join("")}</ul>` : "<p>Available from the current source catalog.</p>"}</div>
                    ${comparison.recommendation ? `<p class="comparison-recommendation"><strong>Recommendation</strong>${escapeHtml(comparison.recommendation)}</p>` : ""}
                  </div>
                </div>
              </details>
            `;
          }).join("")}
        </div>
        ${comparisons.length > visible.length ? `<p class="comparison-overflow">${comparisons.length - visible.length} additional field${comparisons.length - visible.length === 1 ? "" : "s"} included in the response.</p>` : ""}
      </section>
    `;
  }

  function sourceHasMatchingResults(source) {
    if (!source || typeof source !== "object") return false;
    if (Array.isArray(source.fields) && source.fields.length) return true;
    if (Array.isArray(source.datasets) && source.datasets.length) return true;
    return (Array.isArray(source.result_sets) ? source.result_sets : []).some((resultSet) => (
      resultSet
      && ["field", "endpoint"].includes(String(resultSet.format || ""))
      && Array.isArray(resultSet.items)
      && resultSet.items.length > 0
    ));
  }

  function sourceCardHtml(source, result, options = {}) {
    const connectivity = source.connectivity || {};
    const datasets = Array.isArray(source.datasets) ? source.datasets : [];
    const fields = Array.isArray(source.fields) ? source.fields : [];
    const showFields = Boolean(options.showFields);
    const visible = fields.slice(0, 4);
    const hidden = fields.slice(4);
    const available = source.available !== false;
    const agentStatus = connectivity.status || (available ? "ready" : "unavailable");
    const facts = [
      ...(showFields ? [`<span class="source-summary-fact"><small>Fields</small><strong>${fields.length}</strong></span>`] : []),
      `<span class="source-summary-fact"><small>Endpoints</small><strong>${datasets.length}</strong></span>`,
      `<span class="source-summary-fact"><small>Cost</small><strong>${escapeHtml(costLabel(source))}</strong></span>`,
      `<span class="source-summary-fact"><small>Quality</small><strong>${escapeHtml(qualityLabel(source))}</strong></span>`,
    ];
    return `
      <details class="source-card${showFields ? " with-field-detail" : " endpoint-focused"}" data-source="${escapeHtml(source.source_id)}" data-rank="${Number(options.rank || 1)}" role="listitem">
        <summary class="source-card-top">
          <span class="source-summary-source">
            <span class="source-symbol">${escapeHtml(sourceInitial(source))}</span>
            <span class="source-title">
              <strong title="${escapeHtml(source.source_name)}"><i class="source-rank">#${Number(options.rank || 1)}</i>${escapeHtml(source.source_name || source.source_id)}</strong>
              <span title="${escapeHtml(source.provider)}">${escapeHtml(source.provider || source.description || "Data source")} · ${escapeHtml(financialFitLabel(source))}</span>
            </span>
          </span>
          <span class="status-pill ${available ? "status-verified" : "status-failed"}" title="${escapeHtml(`Data Source agent status: ${humanize(agentStatus)}.`)}"><span>${escapeHtml(available ? "Source ready" : "Unavailable")}</span></span>
          <span class="source-summary-facts">${facts.join("")}</span>
          <span class="source-card-chevron">${icon("chevron")}</span>
        </summary>
        <div class="source-card-body">
          ${showFields && fields.length ? `
            <div class="field-list">
              ${visible.map((field) => fieldRowHtml(source, field)).join("")}
              ${hidden.length ? `<div class="hidden-fields" hidden>${hidden.map((field) => fieldRowHtml(source, field)).join("")}</div>` : ""}
              ${hidden.length ? `<button class="source-more" type="button" data-action="toggle-source">Show ${hidden.length} more field${hidden.length === 1 ? "" : "s"}</button>` : ""}
            </div>
          ` : ""}
          ${datasets.length ? `
            <details class="access-route-disclosure"${showFields ? "" : " open"}>
              <summary><span>Endpoint access routes</span><b>${datasets.length}</b></summary>
              <div class="dataset-list">${datasets.map((dataset) => datasetRowHtml(source, dataset)).join("")}</div>
            </details>
          ` : ""}
        </div>
      </details>
    `;
  }

  function sourceResultsHtml(sources, result) {
    if (!sources.length) return "";
    const showFields = fieldComparisonItems(result).length > 0;
    return `
      <section class="source-results" data-source-results aria-label="Matched source evidence">
        <header class="source-results-toolbar">
          <div class="source-results-title"><span>Source evidence</span><strong>${sources.length} catalog source${sources.length === 1 ? "" : "s"}</strong></div>
          <div class="source-results-actions"><button class="source-expand-button" type="button" data-action="toggle-source-results" aria-pressed="false">Expand all</button></div>
        </header>
        <div class="source-ledger">
          <div class="source-table-header${showFields ? " with-field-detail" : ""}" role="row" aria-hidden="true">
            <span>Source</span><span>Status</span><span class="source-table-facts">${showFields ? "<i>Fields</i>" : ""}<i>Endpoints</i><i>Cost</i><i>Quality</i></span><span></span>
          </div>
          <div class="source-grid" role="list">${sources.map((source, index) => sourceCardHtml(source, result, { showFields, rank: index + 1 })).join("")}</div>
        </div>
      </section>
    `;
  }

  function durationLabel(milliseconds) {
    const value = Number(milliseconds);
    if (!Number.isFinite(value) || value < 0) return "";
    if (value < 1000) return `${Math.max(0, Math.round(value))} ms`;
    return `${(value / 1000).toFixed(1)} s`;
  }

  function responseTimingHtml(result) {
    const timing = result.timing && typeof result.timing === "object" ? result.timing : {};
    const browserTotal = Number(timing.client_total_ms);
    const consultantTotal = Number(timing.total_ms);
    const totalMs = Number.isFinite(browserTotal) && browserTotal >= 0 ? browserTotal : consultantTotal;
    if (!Number.isFinite(totalMs) || totalMs < 0) return "";
    const memoryLabel = durationLabel(timing.memory_search_ms);
    const detail = [`Browser response: ${durationLabel(totalMs)}`, memoryLabel ? `Catalog search: ${memoryLabel}` : ""].filter(Boolean).join(" · ");
    return `
      <span class="response-timing" title="${escapeHtml(detail)}" aria-label="${escapeHtml(detail)}">
        <span><b>${escapeHtml(durationLabel(totalMs))}</b> total</span>
        ${memoryLabel ? `<span><b>${escapeHtml(memoryLabel)}</b> catalog</span>` : ""}
      </span>
    `;
  }

  function renderAssistantMessage(result) {
    const article = document.createElement("article");
    article.className = "message assistant-message";
    const sources = (Array.isArray(result.sources) ? result.sources : []).filter(sourceHasMatchingResults);
    const warnings = Array.isArray(result.warnings) ? result.warnings.filter(Boolean) : [];
    const memory = result.memory && typeof result.memory === "object" ? result.memory : {};
    const evidenceLabel = memory.mode === "rag_memory"
      ? `Catalog RAG · ${Number(memory.search_ms || 0).toFixed(1)} ms · ${compactAge(memory.age_seconds)} · no LLM`
      : `${demoConfig.source_catalog_label} catalog evidence · no LLM`;
    article.innerHTML = `
      <div class="assistant-avatar"><div class="pulse-mark"><span></span><span></span><span></span><span></span></div></div>
      <div class="assistant-body">
        <p class="assistant-label"><strong>Data Consultant</strong><span>${escapeHtml(evidenceLabel)}</span>${responseTimingHtml(result)}</p>
        <div class="answer-content">${renderMarkdown(result.answer || "No catalog advice was returned.")}</div>
        ${fieldComparisonHtml(result)}
        ${sourceResultsHtml(sources, result)}
        ${warnings.length ? `<div class="warning-panel">${warnings.map((item) => escapeHtml(item)).join("<br>")}</div>` : ""}
      </div>
    `;
    messageStream.appendChild(article);
    scrollConversation();
    return article;
  }

  function renderErrorMessage(message, totalMs = null) {
    return renderAssistantMessage({
      answer: "I couldn’t complete that catalog request.",
      sources: [],
      warnings: [message],
      timing: totalMs !== null && Number.isFinite(Number(totalMs)) ? { client_total_ms: Number(totalMs) } : {},
    });
  }

  function addThinkingMessage(startedAt = window.performance.now()) {
    const article = document.createElement("article");
    article.className = "message assistant-message thinking-message";
    article.innerHTML = `
      <div class="assistant-avatar"><div class="pulse-mark"><span></span><span></span><span></span><span></span></div></div>
      <div class="assistant-body">
        <p class="assistant-label"><strong>Data Consultant</strong><span>working across the Data Agent Network</span></p>
        <div class="thinking-card">
          <div class="thinking-top">
            <span class="thinking-orbit"></span>
            <div class="thinking-copy"><strong data-thinking-title>Routing data_request</strong><span data-thinking-stage>Data User is locating Data Consultant through Plaza…</span></div>
            <span class="thinking-elapsed" data-thinking-elapsed>0.0 s</span>
          </div>
          <div class="thinking-track"><span></span></div>
        </div>
      </div>
    `;
    messageStream.appendChild(article);
    const stages = [
      ["Searching source memory", `Data Consultant is matching ${demoConfig.source_catalog_label} endpoint and field documentation…`],
      ["Preparing catalog evidence", "Returning supported routes without fetching market observations…"],
    ];
    let index = 0;
    state.thinkingTimer = window.setInterval(() => {
      const stage = stages[Math.min(index++, stages.length - 1)];
      const title = article.querySelector("[data-thinking-title]");
      const detail = article.querySelector("[data-thinking-stage]");
      if (title) title.textContent = stage[0];
      if (detail) detail.textContent = stage[1];
    }, 1800);
    const updateElapsed = () => {
      const target = article.querySelector("[data-thinking-elapsed]");
      if (target) target.textContent = durationLabel(window.performance.now() - startedAt);
    };
    updateElapsed();
    state.thinkingElapsedTimer = window.setInterval(updateElapsed, 250);
    scrollConversation();
    return article;
  }

  function removeThinkingMessage(article) {
    window.clearInterval(state.thinkingTimer);
    window.clearInterval(state.thinkingElapsedTimer);
    state.thinkingTimer = null;
    state.thinkingElapsedTimer = null;
    if (article && article.isConnected) article.remove();
  }

  function setBusy(value) {
    state.busy = value;
    composer.classList.toggle("busy", value);
    queryInput.disabled = value;
    sendButton.disabled = !value && !queryInput.value.trim();
    sendButton.setAttribute("aria-label", value ? "Stop request" : "Send question");
    updateLiveSampleControls();
  }

  function requestPayload(query) {
    const fields = splitValues(byId("fieldsInput").value);
    const assetClasses = splitValues(byId("assetClassInput").value);
    const regions = splitValues(byId("regionInput").value);
    const dataTypes = splitValues(byId("dataTypesInput").value);
    const cost = byId("costSelect").value;
    const frequency = byId("frequencySelect").value;
    const timeliness = byId("timelinessSelect").value;
    const time = {};
    if (frequency) time.frequency = frequency;
    if (timeliness) time.timeliness = timeliness;
    return {
      query,
      use_case: byId("useCaseInput").value.trim(),
      preferences: cost ? { cost } : {},
      asset_classes: assetClasses,
      regions,
      data_types: dataTypes,
      time,
      fields,
      limit: 4,
    };
  }

  async function submitQuestion(query) {
    const cleanQuery = String(query || "").trim();
    if (!cleanQuery) return;
    const requestStartedAt = window.performance.now();
    emptyState.classList.add("hidden");
    byId("threadTitle").textContent = truncate(cleanQuery, 44);
    renderUserMessage(cleanQuery);
    queryInput.value = "";
    resizeComposer();
    preferencePanel.hidden = true;
    preferenceButton.classList.remove("active");
    preferenceButton.setAttribute("aria-expanded", "false");

    setBusy(true);
    const thinking = addThinkingMessage(requestStartedAt);
    state.requestController = new AbortController();
    try {
      const result = await callPulse("data_request", requestPayload(cleanQuery), state.requestController.signal);
      result.timing = {
        ...(result.timing && typeof result.timing === "object" ? result.timing : {}),
        client_total_ms: Number((window.performance.now() - requestStartedAt).toFixed(1)),
      };
      removeThinkingMessage(thinking);
      renderAssistantMessage(result);
    } catch (error) {
      removeThinkingMessage(thinking);
      if (error.name === "AbortError") {
        showToast("Request stopped.");
      } else {
        renderErrorMessage(error.message || "Unable to reach Data Consultant.", window.performance.now() - requestStartedAt);
      }
    } finally {
      state.requestController = null;
      setBusy(false);
      queryInput.focus();
    }
  }

  function responseSchemaFields(endpoint) {
    const schema = endpoint.response_schema || {};
    const direct = schema.properties || {};
    const itemProperties = direct.items && direct.items.items && direct.items.items.properties
      ? direct.items.items.properties
      : {};
    const properties = Object.keys(itemProperties).length ? itemProperties : direct;
    return Object.entries(properties).slice(0, 16).map(([name, definition]) => ({
      name,
      type: definition && definition.type ? definition.type : "value",
    }));
  }

  function parameterInputHtml(parameter, advanced) {
    const schema = parameter.schema || {};
    const name = parameter.name || "parameter";
    const type = schema.type || "string";
    const required = Boolean(parameter.required);
    const defaultValue = parameter.default === null || parameter.default === undefined ? "" : parameter.default;
    const label = `<label for="param-${escapeHtml(name)}"><span>${escapeHtml(name)}${required ? " *" : ""}</span><small>${escapeHtml(type)}</small></label>`;
    let control = "";
    if (Array.isArray(schema.enum) && schema.enum.length) {
      control = `<select id="param-${escapeHtml(name)}" data-param-name="${escapeHtml(name)}" data-param-type="${escapeHtml(type)}" ${required ? "required" : ""}>${schema.enum.map((item) => `<option value="${escapeHtml(item)}"${String(item) === String(defaultValue) ? " selected" : ""}>${escapeHtml(item)}</option>`).join("")}</select>`;
    } else if (type === "boolean") {
      return `<div class="parameter-field toggle-field${advanced ? " advanced-parameter" : ""}" ${advanced ? "hidden" : ""}><label for="param-${escapeHtml(name)}"><span>${escapeHtml(name)}</span><input id="param-${escapeHtml(name)}" type="checkbox" data-param-name="${escapeHtml(name)}" data-param-type="boolean" ${defaultValue === true || defaultValue === "true" ? "checked" : ""}></label></div>`;
    } else if (type === "object" || type === "array") {
      control = `<textarea id="param-${escapeHtml(name)}" data-param-name="${escapeHtml(name)}" data-param-type="${escapeHtml(type)}" ${required ? "required" : ""} placeholder='${type === "array" ? "[]" : "{}"}'>${escapeHtml(defaultValue === "" ? "" : JSON.stringify(defaultValue))}</textarea>`;
    } else {
      const inputType = type === "integer" || type === "number" ? "number" : "text";
      const step = type === "number" ? ' step="any"' : "";
      control = `<input id="param-${escapeHtml(name)}" type="${inputType}"${step} data-param-name="${escapeHtml(name)}" data-param-type="${escapeHtml(type)}" value="${escapeHtml(defaultValue)}" ${required ? "required" : ""} placeholder="${escapeHtml(parameter.description || name)}">`;
    }
    return `<div class="parameter-field${advanced ? " advanced-parameter" : ""}" ${advanced ? "hidden" : ""}>${label}${control}</div>`;
  }

  function safeExternalUrl(value) {
    try {
      const url = new URL(String(value || ""));
      return ["http:", "https:"].includes(url.protocol) ? url.href : "";
    } catch (_error) {
      return "";
    }
  }

  function sourceDisplayName(sourceId) {
    const sources = state.bootstrap && Array.isArray(state.bootstrap.sources) ? state.bootstrap.sources : [];
    const match = sources.find((source) => String(source.source_id || "") === String(sourceId || ""));
    return String((match && (match.source_name || match.provider)) || humanize(sourceId) || demoConfig.source_direct_label || "Data Source");
  }

  function providerTermsNotice(sourceId) {
    if (String(sourceId || "").toLowerCase().includes("yfinance")) {
      return "yfinance is unaffiliated with Yahoo. Yahoo Finance data is intended for personal use and remains subject to applicable terms and availability.";
    }
    return `${sourceDisplayName(sourceId)} access remains subject to the provider's terms, limits, credentials, and availability.`;
  }

  function renderSpecDialog(sourceId, endpoint, focusFetch) {
    const parameters = Array.isArray(endpoint.parameters) ? endpoint.parameters : [];
    const publicParameters = parameters.filter((item) => !/api[_-]?key|secret|password|token/i.test(item.name || ""));
    const hiddenDefaults = publicParameters.filter((item) => item.name === "function" && item.default !== null && item.default !== undefined);
    const formParameters = publicParameters.filter((item) => !hiddenDefaults.includes(item));
    const coreParameters = formParameters.filter((item) => item.required).concat(formParameters.filter((item) => !item.required).slice(0, 3));
    const coreNames = new Set(coreParameters.map((item) => item.name));
    const advancedParameters = formParameters.filter((item) => !coreNames.has(item.name));
    const fields = responseSchemaFields(endpoint);
    const fieldMappings = Array.isArray(endpoint.field_mappings) ? endpoint.field_mappings : [];
    const pulseAccess = endpoint.attas_pulse || {};
    const executable = Boolean(endpoint.executable);
    const canFetch = Boolean(demoConfig.enable_live_fetch && executable);
    const docsUrl = safeExternalUrl(endpoint.documentation_url);
    dialogEyebrow.textContent = canFetch ? "Endpoint · Data Source fetch ready" : "Endpoint · specification only";
    dialogTitle.textContent = endpoint.name || endpoint.endpoint_id;
    dialogBody.innerHTML = `
      <div class="spec-meta">
        <span class="spec-chip">${escapeHtml(endpoint.endpoint_id)}</span>
        <span class="spec-chip">${escapeHtml(endpoint.transport || "source")}</span>
        <span class="spec-chip">${escapeHtml(endpoint.category || "uncategorized")}</span>
        <span class="spec-chip pulse">${escapeHtml(pulseAccess.pulse_name || "data_fetch")} · ${escapeHtml(pulseAccess.contract_version || "lite")}</span>
        <span class="spec-chip${canFetch ? " ready" : ""}">${canFetch ? "Fetch ready" : "Specification only"}</span>
      </div>
      <p class="endpoint-description">${escapeHtml(endpoint.description || "No endpoint description is available.")}</p>
      <section class="pulse-contract-panel">
        <div class="pulse-contract-copy">
          <span>Data Source Pulse</span>
          <strong>${escapeHtml(pulseAccess.pulse_name || "data_fetch")}</strong>
          <p>The provider payload remains available as <code>data</code>; mapped fields are returned with canonical names in <code>canonical_data</code>.</p>
        </div>
        <div class="field-map-grid">
          ${fieldMappings.length ? fieldMappings.slice(0, 12).map((mapping) => `
            <span title="${escapeHtml(mapping.definition || "")}"><b>${escapeHtml(humanize(mapping.canonical_name))}</b><i>${escapeHtml(mapping.vendor_field_name)} → ${escapeHtml(mapping.canonical_name)}</i></span>
          `).join("") : "<span><b>Provider-defined</b><i>No canonical mapping supplied</i></span>"}
        </div>
      </section>
      <section class="detail-section">
        <div class="detail-section-head">
          <h3>Provider response schema</h3>
          ${docsUrl ? `<a href="${escapeHtml(docsUrl)}" target="_blank" rel="noreferrer">${escapeHtml(sourceDisplayName(sourceId))} docs ${icon("external")}</a>` : ""}
        </div>
        <div class="schema-fields">${fields.length ? fields.map((field) => `<span class="schema-field">${escapeHtml(field.name)} <i>${escapeHtml(field.type)}</i></span>`).join("") : '<span class="schema-field">Provider-defined object</span>'}</div>
      </section>
      <section class="detail-section">
        <div class="detail-section-head"><h3>${canFetch ? "Direct source fetch" : "Request parameters"}</h3></div>
        ${formParameters.length ? `
          <form class="parameter-form" id="endpointForm">
            ${hiddenDefaults.map((item) => `<input type="hidden" data-param-name="${escapeHtml(item.name)}" data-param-type="string" value="${escapeHtml(item.default)}">`).join("")}
            <div class="parameter-grid">${coreParameters.map((item) => parameterInputHtml(item, false)).join("")}${advancedParameters.map((item) => parameterInputHtml(item, true)).join("")}</div>
            ${advancedParameters.length ? `<button class="advanced-toggle" type="button" id="advancedToggle">Show ${advancedParameters.length} optional parameter${advancedParameters.length === 1 ? "" : "s"}</button>` : ""}
            ${canFetch ? `<div class="fetch-bar"><span class="fetch-note">Calls ${escapeHtml(sourceDisplayName(sourceId))} <code>data_fetch</code> directly through Data User.</span><button class="fetch-button" id="fetchButton" type="submit">Fetch data</button></div>` : ""}
          </form>
        ` : '<p class="endpoint-description">This operation does not declare request parameters.</p>'}
        ${!canFetch ? '<div class="warning-panel">This demo keeps the documented operation in specification mode.</div>' : `<div class="warning-panel">${escapeHtml(providerTermsNotice(sourceId))}</div>`}
        <div id="fetchResult" aria-live="polite"></div>
      </section>
    `;

    const advancedToggle = byId("advancedToggle");
    if (advancedToggle) {
      advancedToggle.addEventListener("click", () => {
        const advanced = [...dialogBody.querySelectorAll(".advanced-parameter")];
        const opening = advanced.some((item) => item.hidden);
        advanced.forEach((item) => { item.hidden = !opening; });
        advancedToggle.textContent = opening ? "Hide optional parameters" : `Show ${advanced.length} optional parameter${advanced.length === 1 ? "" : "s"}`;
      });
    }
    const form = byId("endpointForm");
    if (form && canFetch) form.addEventListener("submit", (event) => fetchEndpoint(event, sourceId, endpoint));
    if (focusFetch && form) {
      window.setTimeout(() => {
        const first = form.querySelector("input:not([type=hidden]), select, textarea");
        if (first) first.focus();
      }, 80);
    }
  }

  async function loadEndpointSpec(sourceId, endpointId) {
    const cacheKey = `${sourceId}:${endpointId}`;
    let endpoint = state.specCache.get(cacheKey);
    if (endpoint) return endpoint;
    const result = await callPulse("data_spec", { source_id: sourceId, endpoint_id: endpointId });
    endpoint = Array.isArray(result.endpoints) ? result.endpoints[0] : null;
    if (!endpoint) throw new Error("The Data Source did not return this endpoint specification.");
    state.specCache.set(cacheKey, endpoint);
    return endpoint;
  }

  async function openEndpoint(sourceId, endpointId, focusFetch = false) {
    dialogEyebrow.textContent = "Endpoint specification";
    dialogTitle.textContent = endpointId;
    dialogBody.innerHTML = '<div class="dialog-loading"><div class="thinking-copy"><strong>Reading source specification</strong><span>Calling the Data Source data_spec Pulse…</span></div></div>';
    if (!detailDialog.open) detailDialog.showModal();
    try {
      const endpoint = await loadEndpointSpec(sourceId, endpointId);
      renderSpecDialog(sourceId, endpoint, focusFetch);
    } catch (error) {
      dialogBody.innerHTML = `<div class="error-panel">${escapeHtml(error.message || "Unable to load endpoint specification.")}</div>`;
    }
  }

  function collectParameters(form) {
    const parameters = {};
    form.querySelectorAll("[data-param-name]").forEach((control) => {
      const name = control.dataset.paramName;
      const type = control.dataset.paramType || "string";
      let value;
      if (type === "boolean") value = Boolean(control.checked);
      else value = control.value.trim();
      if (value === "" && !control.required) return;
      if (type === "integer") value = Number.parseInt(value, 10);
      else if (type === "number") value = Number.parseFloat(value);
      else if (type === "object" || type === "array") {
        try {
          value = JSON.parse(value || (type === "array" ? "[]" : "{}"));
        } catch (_error) {
          throw new Error(`${name} must contain valid JSON.`);
        }
      }
      parameters[name] = value;
    });
    return parameters;
  }

  async function requestEndpointData(sourceId, endpoint, parameters, signal) {
    return callPulse("data_fetch", {
      source_id: sourceId,
      endpoint_id: endpoint.endpoint_id,
      parameters,
      access_mode: "data_source_pulse",
    }, signal);
  }

  function canonicalResultData(result) {
    if (result && result.canonical_data && typeof result.canonical_data === "object") return result.canonical_data;
    return result && result.data !== undefined ? result.data : {};
  }

  function isStructuredData(value) {
    return value !== null && typeof value === "object";
  }

  function dataTreeType(value) {
    if (Array.isArray(value)) return `Array · ${value.length} item${value.length === 1 ? "" : "s"}`;
    const count = isStructuredData(value) ? Object.keys(value).length : 0;
    return `Object · ${count} field${count === 1 ? "" : "s"}`;
  }

  function dataScalarType(value) {
    if (value === null) return "null";
    if (typeof value === "boolean") return "boolean";
    if (typeof value === "number") return "number";
    return "string";
  }

  function dataScalarHtml(value) {
    const type = dataScalarType(value);
    const text = value === null ? "null" : value === "" ? "empty string" : String(value);
    return `<span class="data-tree-value ${type}" title="${escapeHtml(text)}">${escapeHtml(truncate(text, 240))}</span>`;
  }

  function dataTreeNodeHtml(value, label, depth, options) {
    if (!isStructuredData(value)) {
      return `<div class="data-tree-leaf"><span class="data-tree-key">${escapeHtml(label)}</span>${dataScalarHtml(value)}</div>`;
    }
    const entries = Array.isArray(value) ? value.map((item, index) => [String(index), item]) : Object.entries(value);
    const visibleEntries = entries.slice(0, Number(options.maxChildren || 200));
    const open = depth === 0 && options.openRoot;
    const displayLabel = label || (Array.isArray(value) ? "items" : "root");
    if (depth >= Number(options.maxDepth || 10)) {
      return `<div class="data-tree-leaf limited"><span class="data-tree-key">${escapeHtml(displayLabel)}</span><span class="data-tree-value">${escapeHtml(dataTreeType(value))}</span></div>`;
    }
    return `
      <details class="data-tree-node"${open ? " open" : ""}>
        <summary><span class="data-tree-key">${escapeHtml(displayLabel)}</span><span class="data-tree-kind">${escapeHtml(dataTreeType(value))}</span></summary>
        <div class="data-tree-children">
          ${visibleEntries.length ? visibleEntries.map(([key, item]) => {
            const childLabel = Array.isArray(value) ? `[${key}]` : key;
            return isStructuredData(item)
              ? dataTreeNodeHtml(item, childLabel, depth + 1, options)
              : `<div class="data-tree-leaf"><span class="data-tree-key">${escapeHtml(childLabel)}</span>${dataScalarHtml(item)}</div>`;
          }).join("") : '<div class="data-tree-empty">Empty</div>'}
          ${entries.length > visibleEntries.length ? `<div class="data-tree-overflow">${entries.length - visibleEntries.length} more entr${entries.length - visibleEntries.length === 1 ? "y" : "ies"} in the response</div>` : ""}
        </div>
      </details>
    `;
  }

  function dataTreeHtml(value, options = {}) {
    const treeOptions = {
      openRoot: options.openRoot !== false,
      compact: Boolean(options.compact),
      maxChildren: options.maxChildren || 200,
      maxDepth: options.maxDepth || 10,
    };
    return `<div class="data-tree-root${treeOptions.compact ? " compact" : ""}">${dataTreeNodeHtml(value, options.label || "", 0, treeOptions)}</div>`;
  }

  function dataValueHtml(value, options = {}) {
    if (value === undefined) return '<span class="missing-value">—</span>';
    if (isStructuredData(value)) return dataTreeHtml(value, { ...options, openRoot: false, compact: true });
    return dataScalarHtml(value);
  }

  function isIdentifierColumn(name) {
    const normalized = String(name || "").replace(/([a-z0-9])([A-Z])/g, "$1_$2").toLowerCase();
    return /(^|[._\-\s])(id|uuid)$/.test(normalized);
  }

  function compactIdentifierValue(value) {
    if (value === undefined) return "—";
    if (value === null) return "nul";
    if (Array.isArray(value)) return "arr";
    if (isStructuredData(value)) return "obj";
    return String(value).slice(0, 3) || "—";
  }

  function dataTableCellHtml(value, options = {}) {
    const structured = isStructuredData(value);
    const title = structured ? dataTreeType(value) : value === undefined ? "Missing" : String(value);
    const identifier = Boolean(options.identifier);
    const columnIndex = Number.isInteger(options.columnIndex) ? options.columnIndex : -1;
    if (identifier) {
      return `
        <td class="${structured ? "data-tree-cell" : "data-scalar-cell"} identifier-column is-collapsed" data-column-index="${columnIndex}" title="${escapeHtml(title)}" aria-label="${escapeHtml(title)}">
          <span class="identifier-value-compact" aria-hidden="true">${escapeHtml(compactIdentifierValue(value))}</span><span class="identifier-value-full">${dataValueHtml(value)}</span>
        </td>
      `;
    }
    return `<td class="${structured ? "data-tree-cell" : "data-scalar-cell"}" title="${escapeHtml(title)}">${dataValueHtml(value)}</td>`;
  }

  function identifierColumnHeaderHtml(column, columnIndex) {
    return `
      <th class="identifier-column is-collapsed" data-column-index="${columnIndex}" title="${escapeHtml(column)}">
        <button class="identifier-column-toggle" type="button" data-identifier-column-toggle data-column-index="${columnIndex}" aria-expanded="false" aria-label="Expand ${escapeHtml(column)} column">
          <span class="identifier-header-compact">ID</span><span class="identifier-header-full">${escapeHtml(column)}</span>${icon("chevron")}
        </button>
      </th>
    `;
  }

  function toggleIdentifierColumn(button) {
    const table = button.closest(".data-table");
    if (!table) return;
    const columnIndex = String(button.dataset.columnIndex || "");
    const expanded = button.getAttribute("aria-expanded") !== "true";
    table.querySelectorAll(`th[data-column-index="${columnIndex}"], td[data-column-index="${columnIndex}"]`).forEach((cell) => {
      cell.classList.toggle("is-collapsed", !expanded);
      cell.classList.toggle("is-expanded", expanded);
    });
    button.setAttribute("aria-expanded", String(expanded));
    const header = button.closest("th");
    button.setAttribute("aria-label", `${expanded ? "Collapse" : "Expand"} ${header ? header.title : "identifier"} column`);
  }

  function resultTableHtml(items) {
    const rows = items.filter((item) => item && typeof item === "object" && !Array.isArray(item)).slice(0, 20);
    if (!rows.length) return dataTreeHtml(items, { openRoot: true });
    const columns = [...new Set(rows.flatMap((row) => Object.keys(row)))].slice(0, 10);
    const identifierColumns = columns.map(isIdentifierColumn);
    return `
      <div class="data-table-wrap">
        <table class="data-table">
          <thead><tr>${columns.map((column, columnIndex) => identifierColumns[columnIndex] ? identifierColumnHeaderHtml(column, columnIndex) : `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead>
          <tbody>${rows.map((row) => `<tr>${columns.map((column, columnIndex) => dataTableCellHtml(row[column], { identifier: identifierColumns[columnIndex], columnIndex })).join("")}</tr>`).join("")}</tbody>
        </table>
      </div>
    `;
  }

  function renderFetchResult(result) {
    const target = byId("fetchResult");
    if (!target) return;
    if (result.status !== "completed") {
      const detail = result.error || (result.warnings || []).join(" ") || `Source returned ${result.status || "an unknown status"}.`;
      target.innerHTML = `<div class="warning-panel">${escapeHtml(detail)}</div>`;
      return;
    }
    const providerData = result.data || {};
    const canonicalData = canonicalResultData(result);
    const items = Array.isArray(canonicalData) ? canonicalData : Array.isArray(canonicalData.items) ? canonicalData.items : null;
    const fieldCount = canonicalData && typeof canonicalData === "object" && !Array.isArray(canonicalData) ? Object.keys(canonicalData).length : 1;
    const countLabel = items ? `${items.length} row${items.length === 1 ? "" : "s"}` : `${fieldCount} field${fieldCount === 1 ? "" : "s"}`;
    target.innerHTML = `
      <div class="fetch-result">
        <div class="fetch-result-head"><strong>Canonical result · ${escapeHtml(countLabel)} <i>Data Source pulse</i></strong></div>
        ${items ? resultTableHtml(items) : dataTreeHtml(canonicalData, { openRoot: true })}
        <details class="provider-payload-disclosure"><summary>Provider payload</summary>${dataTreeHtml(providerData, { openRoot: true })}</details>
      </div>
    `;
  }

  function liveSamplePreviewHtml(result) {
    const canonicalData = canonicalResultData(result);
    const items = Array.isArray(canonicalData)
      ? canonicalData
      : canonicalData && Array.isArray(canonicalData.items)
        ? canonicalData.items
        : null;
    if (items) {
      const visible = items.slice(0, 6);
      return `${resultTableHtml(visible)}${items.length > visible.length ? `<p class="sample-preview-note">Previewing 6 of ${items.length} canonical rows.</p>` : ""}`;
    }
    if (canonicalData && typeof canonicalData === "object" && Object.keys(canonicalData).length) {
      return dataTreeHtml(canonicalData, { openRoot: true, maxChildren: 18, maxDepth: 4 });
    }
    return '<p class="sample-preview-note">The source returned no canonical rows for these parameters.</p>';
  }

  function renderLiveSampleResult(target, call, result, error) {
    if (!target) return;
    if (error) {
      target.className = "live-provider-result failed";
      target.innerHTML = `
        <header><span>${escapeHtml(call.source_name)}</span><b>Request failed</b></header>
        <p class="live-provider-route">Data User → ${escapeHtml(call.source_name)} · <code>data_fetch</code> · ${escapeHtml(call.endpoint_id)}</p>
        <div class="error-panel" role="alert">${escapeHtml(error.message || "The direct source call failed.")}</div>
      `;
      return;
    }
    const status = String(result && result.status || "unknown");
    const completed = status === "completed";
    const authenticationRequired = status === "authentication_required";
    const detail = String(result && result.error || (result && result.warnings || []).join(" ") || `Source returned ${status}.`);
    target.className = `live-provider-result ${completed ? "completed" : authenticationRequired ? "key-needed" : "failed"}`;
    target.innerHTML = `
      <header>
        <span>${escapeHtml(call.source_name)}</span>
        <b>${escapeHtml(completed ? "Live data received" : authenticationRequired ? "Server key required" : humanize(status))}</b>
      </header>
      <p class="live-provider-route">Data User → ${escapeHtml(call.source_name)} · <code>data_fetch</code> · ${escapeHtml(call.endpoint_id)}</p>
      ${completed ? `<div class="live-provider-preview">${liveSamplePreviewHtml(result)}</div>` : `<div class="${authenticationRequired ? "warning-panel" : "error-panel"}" role="${authenticationRequired ? "status" : "alert"}">${escapeHtml(detail)}</div>`}
    `;
  }

  function liveSampleArticle(plan) {
    const article = document.createElement("article");
    article.className = "message assistant-message live-sample-message";
    const alphaConfigured = sourceCredentialConfigured("alpha_vantage");
    const baselineNote = plan === liveSamplePlans["no-key"]
      ? alphaConfigured
        ? "An Alpha Vantage key is already configured, so both calls may succeed. No failure is simulated."
        : "No Alpha Vantage key was detected. YFinance should return public data while Alpha Vantage should report its real authentication boundary."
      : "Each provider is called independently through the existing Data Source Pulse.";
    article.innerHTML = `
      <div class="assistant-avatar"><div class="pulse-mark"><span></span><span></span><span></span><span></span></div></div>
      <div class="assistant-body">
        <p class="assistant-label"><strong>Data User</strong><span>direct source execution · no proxy · no merged payload</span></p>
        <div class="live-sample-intro">
          <span>LIVE SAMPLE</span>
          <h3>${escapeHtml(plan.title)}</h3>
          <p>${escapeHtml(baselineNote)}</p>
        </div>
        <div class="live-sample-results" role="list" aria-label="Separate provider results">
          ${plan.calls.map((call, index) => `
            <section class="live-provider-result pending" data-sample-result-index="${index}" role="listitem" aria-live="polite">
              <header><span>${escapeHtml(call.source_name)}</span><b>Calling source…</b></header>
              <p class="live-provider-route">Data User → ${escapeHtml(call.source_name)} · <code>data_fetch</code> · ${escapeHtml(call.endpoint_id)}</p>
              <div class="dialog-loading"><span>Waiting for the source-owned provider boundary…</span></div>
            </section>
          `).join("")}
        </div>
      </div>
    `;
    messageStream.appendChild(article);
    scrollConversation();
    return article;
  }

  async function runLiveSample(sampleId) {
    const plan = liveSamplePlans[String(sampleId || "")];
    if (!plan || demoConfig.mode !== "real-data" || state.busy) return;
    if (!state.bootstrap) {
      showToast("The Data Agent Network is still connecting.");
      return;
    }
    if (plan.requires_source && !sourceCredentialConfigured(plan.requires_source)) {
      showToast(`Add ${plan.requires_source === "fred" ? "FRED_API_KEY" : "ALPHA_VANTAGE_API_KEY"} to .env, then restart the server.`);
      const help = document.querySelector("[data-env-help]");
      if (help) help.scrollIntoView({ behavior: "smooth", block: "nearest" });
      return;
    }

    emptyState.classList.add("hidden");
    byId("threadTitle").textContent = truncate(plan.title, 44);
    renderUserMessage(plan.prompt);
    const article = liveSampleArticle(plan);
    setBusy(true);
    state.requestController = new AbortController();
    const signal = state.requestController.signal;
    try {
      await Promise.all(plan.calls.map(async (call, index) => {
        const target = article.querySelector(`[data-sample-result-index="${index}"]`);
        try {
          const result = await callPulse("data_fetch", {
            source_id: call.source_id,
            endpoint_id: call.endpoint_id,
            parameters: { ...call.parameters },
            access_mode: "data_source_pulse",
          }, signal);
          renderLiveSampleResult(target, call, result, null);
        } catch (error) {
          renderLiveSampleResult(target, call, null, error);
        }
      }));
      await loadSourceStatus();
      const firstResult = article.querySelector(".live-provider-result");
      if (firstResult) {
        firstResult.tabIndex = -1;
        firstResult.focus({ preventScroll: true });
      }
      scrollConversation();
    } finally {
      state.requestController = null;
      setBusy(false);
    }
  }

  async function fetchEndpoint(event, sourceId, endpoint) {
    event.preventDefault();
    const form = event.currentTarget;
    const button = byId("fetchButton");
    let parameters;
    try {
      parameters = collectParameters(form);
    } catch (error) {
      showToast(error.message);
      return;
    }
    if (!form.reportValidity()) return;
    button.disabled = true;
    button.textContent = "Fetching…";
    const target = byId("fetchResult");
    if (target) target.innerHTML = `<div class="dialog-loading"><span>Calling ${escapeHtml(sourceDisplayName(sourceId))} data_fetch Pulse…</span></div>`;
    try {
      const result = await requestEndpointData(sourceId, endpoint, parameters);
      renderFetchResult(result);
      await loadSourceStatus();
    } catch (error) {
      if (target) target.innerHTML = `<div class="error-panel">${escapeHtml(error.message || "Data Source fetch failed.")}</div>`;
    } finally {
      button.disabled = false;
      button.textContent = "Fetch data";
    }
  }

  function resizeComposer() {
    queryInput.style.height = "auto";
    queryInput.style.height = `${Math.min(queryInput.scrollHeight, 160)}px`;
    if (!state.busy) sendButton.disabled = !queryInput.value.trim();
  }

  function updateSourceExpansionControl(section) {
    const button = section && section.querySelector('[data-action="toggle-source-results"]');
    const cards = section ? Array.from(section.querySelectorAll(".source-grid > .source-card")) : [];
    if (!button) return;
    const allOpen = cards.length > 0 && cards.every((card) => card.open);
    button.textContent = allOpen ? "Collapse all" : "Expand all";
    button.setAttribute("aria-pressed", String(allOpen));
  }

  composer.addEventListener("submit", (event) => {
    event.preventDefault();
    if (state.busy) {
      if (state.requestController) state.requestController.abort();
      return;
    }
    submitQuestion(queryInput.value);
  });

  queryInput.addEventListener("input", resizeComposer);
  queryInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      composer.requestSubmit();
    }
  });

  preferenceButton.addEventListener("click", () => {
    const opening = preferencePanel.hidden;
    preferencePanel.hidden = !opening;
    preferenceButton.classList.toggle("active", opening);
    preferenceButton.setAttribute("aria-expanded", String(opening));
  });

  document.querySelectorAll(".suggestion").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.sampleId) {
        if (button.getAttribute("aria-disabled") === "true") {
          const source = button.dataset.requiresSource;
          showToast(source
            ? `Add ${source === "fred" ? "FRED_API_KEY" : "ALPHA_VANTAGE_API_KEY"} to .env, then restart the server.`
            : "The Data Agent Network is still connecting.");
          return;
        }
        runLiveSample(button.dataset.sampleId);
        return;
      }
      submitQuestion(button.dataset.query);
    });
  });

  messageStream.addEventListener("toggle", (event) => {
    if (event.target.matches(".source-card")) updateSourceExpansionControl(event.target.closest("[data-source-results]"));
  }, true);

  messageStream.addEventListener("click", (event) => {
    const target = event.target.closest("[data-action]");
    if (!target) return;
    const action = target.dataset.action;
    if (action === "inspect" || action === "fetch") {
      if (action === "fetch" && !demoConfig.enable_live_fetch) return;
      openEndpoint(target.dataset.sourceId, target.dataset.endpointId, action === "fetch");
    } else if (action === "toggle-source-results") {
      const section = target.closest("[data-source-results]");
      const cards = section ? Array.from(section.querySelectorAll(".source-grid > .source-card")) : [];
      const opening = cards.some((card) => !card.open);
      cards.forEach((card) => { card.open = opening; });
      updateSourceExpansionControl(section);
    } else if (action === "toggle-source") {
      const card = target.closest(".source-card");
      const hidden = card && card.querySelector(".hidden-fields");
      if (!hidden) return;
      const opening = hidden.hidden;
      hidden.hidden = !opening;
      target.textContent = opening ? "Show fewer fields" : `Show ${hidden.children.length} more fields`;
    }
  });

  byId("menuButton").addEventListener("click", () => appShell.classList.add("rail-open"));
  byId("railScrim").addEventListener("click", () => appShell.classList.remove("rail-open"));
  [byId("howButton"), byId("topHelpButton")].forEach((button) => {
    button.addEventListener("click", () => howDialog.showModal());
  });
  dialogBody.addEventListener("click", (event) => {
    const button = event.target.closest("[data-identifier-column-toggle]");
    if (button) toggleIdentifierColumn(button);
  });
  byId("closeHowButton").addEventListener("click", () => howDialog.close());
  byId("closeDialogButton").addEventListener("click", () => detailDialog.close());
  [detailDialog, howDialog].forEach((dialog) => {
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
  });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") appShell.classList.remove("rail-open");
  });

  resizeComposer();
  async function initialize() {
    await loadSourceStatus();
    updateLiveSampleControls();
    if (demoConfig.mode !== "real-data") return;
    const requestedSample = new URLSearchParams(window.location.search).get("sample");
    if (["no-key", "alpha-key", "fred"].includes(requestedSample)) {
      await runLiveSample(requestedSample);
    }
  }
  initialize();
})();
