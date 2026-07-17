// Phoenix Stadium — client JS.
// Single file, no build step, no framework. Vanilla JS throughout.

const RTL = new Set([]);

// ── Language change → sync html[lang] and html[dir] (WCAG 3.1.2) ───────────
const langSel = document.getElementById("lang");
if (langSel) {
  langSel.addEventListener("change", () => {
    const lang = langSel.value;
    document.documentElement.lang  = lang;
    document.documentElement.dir   = RTL.has(lang) ? "rtl" : "ltr";
  });
}

/**
 * Handles submission of the fan assistant query form.
 * Sanitizes input and fetches phrased responses from the backend assistant.
 * @param {Event} e - Submit event
 */
async function handleAssistSubmit(e) {
  e.preventDefault();
  const form = e.currentTarget;
  const btn     = form.querySelector(".btn-ask");
  const replyEl = document.getElementById("reply");
  const factsEl = document.getElementById("facts");
  const lang    = document.getElementById("lang").value;

  const payload = {
    persona:            "fan",
    language:           lang,
    raw_text:           document.getElementById("q").value.trim(),
    accessibility_need: document.getElementById("need").value,
  };

  if (!payload.raw_text) return;

  btn.disabled    = true;
  btn.textContent = "Asking…";
  replyEl.className   = "reply-box";
  replyEl.textContent = "Thinking…";

  try {
    const res = await fetch("/api/assist", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    replyEl.className = "reply-box has-answer";
    replyEl.setAttribute("lang", lang);
    replyEl.setAttribute("dir",  RTL.has(lang) ? "rtl" : "ltr");
    replyEl.textContent = data.reply;

    factsEl.innerHTML = "";
    (data.grounded_facts || []).forEach((f) => {
      const chip = document.createElement("span");
      chip.className   = "chip";
      chip.textContent = f;
      factsEl.appendChild(chip);
    });
  } catch {
    replyEl.className   = "reply-box has-answer";
    replyEl.textContent = "⚠ Couldn't reach the assistant — please try again.";
  } finally {
    btn.disabled    = false;
    btn.textContent = "Ask →";
  }
}

const assistForm = document.getElementById("assist-form");
if (assistForm) {
  assistForm.addEventListener("submit", handleAssistSubmit);
}

// ═══════════════════════════════════════════════════════════════════════════
// OPS DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════

// Store latest gate snapshot so the simulator can read it without extra fetches
let latestGates = [];

/**
 * Standard factorial calculation helper.
 * @param {number} n
 * @returns {number} factorial value
 */
function factorial(n) {
  if (n <= 1) return 1;
  let r = 1;
  for (let i = 2; i <= n; i++) r *= i;
  return r;
}

/**
 * Erlang-C: probability all c servers are busy.
 * @param {number} lambda  - arrival rate (fans/min)
 * @param {number} mu      - service rate per server (fans/min)
 * @param {number} c       - number of servers open
 * @returns {number} - probability 0..1 (1 if system unstable)
 */
function erlangC(lambda, mu, c) {
  const a   = lambda / mu;          // offered load (Erlangs)
  const rho = a / c;                // utilisation per server
  if (rho >= 1) return 1;           // unstable — infinite queue

  let sumTerms = 0;
  for (let k = 0; k < c; k++) {
    sumTerms += Math.pow(a, k) / factorial(k);
  }
  const lastTerm = Math.pow(a, c) / factorial(c);
  const C = lastTerm / (lastTerm + sumTerms * (1 - rho));
  return C;
}

/**
 * Expected wait time in queue (minutes) using Erlang-C solver.
 * @param {number} lambda
 * @param {number} mu
 * @param {number} c
 * @returns {number} predicted wait time
 */
function predictWait(lambda, mu, c) {
  if (c <= 0 || lambda <= 0) return 0;
  const rho = lambda / (c * mu);
  if (rho >= 1) return 999;                            // overloaded
  const C  = erlangC(lambda, mu, c);
  const Wq = C / (c * mu - lambda);                   // minutes
  return Math.max(0, Math.round(Wq * 10) / 10);
}

/**
 * Renders the live gate snapshot into the operations table.
 * @param {object} data - Live gates payload from backend
 */
function renderOpsTable(data) {
  const tbody = document.getElementById("gate-table");
  if (!tbody) return;

  latestGates = data.gates || [];

  const best = latestGates.reduce((a, b) =>
    a.predicted_wait_minutes < b.predicted_wait_minutes ? a : b,
    latestGates[0]);

  tbody.innerHTML = "";
  latestGates.forEach((g) => {
    const util      = g.utilization ?? 0;
    const pct       = Math.round(util * 100);
    const fillClass = util >= 0.85 ? "crit" : util >= 0.65 ? "warn" : "";
    const isBest    = g.gate_id === best?.gate_id;

    const tr = document.createElement("tr");
    if (isBest) tr.classList.add("best");
    tr.dataset.gateId = g.gate_id;

    const alertCell = g.incident
      ? `<td class="color-red text-sm">${g.incident}</td>`
      : `<td class="color-mist">—</td>`;

    tr.innerHTML = `
      <td><strong>${g.name || g.gate_id}</strong></td>
      <td><strong>${g.predicted_wait_minutes}</strong> min</td>
      <td>
        <progress class="${fillClass}" value="${pct}" max="100" aria-label="Utilization"></progress>
        ${pct}%
      </td>
      <td>${typeof g.arrivals_per_min === "number"
            ? g.arrivals_per_min.toFixed(1) : "—"}</td>
      <td>
        <span class="dot ${g.congestion_level}" aria-hidden="true"></span>
        ${g.congestion_level}
      </td>
      ${alertCell}
    `;
    tbody.appendChild(tr);
  });

  // Summary
  const summary = document.getElementById("ops-summary");
  if (summary && best) {
    const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    summary.textContent =
      `Fastest: ${best.name || best.gate_id} · ` +
      `${data.critical_count} critical · updated ${now}`;
  }

  updateSustainability(latestGates);
  refreshSimulator();          // re-run simulator with fresh data
  populateSimGateOptions();    // keep dropdown in sync
}

/**
 * Calculates and updates sustainability metric cards on the page.
 * @param {Array} gates - List of gate status objects
 */
function updateSustainability(gates) {
  if (!gates?.length) return;
  const totalArrivals = gates.reduce((s, g) => s + (g.arrivals_per_min || 0), 0);
  const fans          = Math.round(totalArrivals * 60 * 0.4);
  const recycling     = gates.filter(g => g.congestion_level !== "critical").length * 2;
  const co2           = Math.round(fans * 0.12);
  const water         = gates.length * 3;

  const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  set("s-fans",      fans.toLocaleString());
  set("s-recycling", recycling);
  set("s-co2",       co2.toLocaleString());
  set("s-water",     water);
}

// ═══════════════════════════════════════════════════════════════════════════
// WHAT-IF SERVER SIMULATOR
// ═══════════════════════════════════════════════════════════════════════════

let simServers = 0;   // current simulated server count
let simGate    = null; // current gate object

/**
 * Populates the simulator gate selection dropdown.
 */
function populateSimGateOptions() {
  const sel = document.getElementById("sim-gate");
  if (!sel || !latestGates.length) return;
  const current = sel.value;
  sel.innerHTML = `<option value="">— select a gate —</option>`;
  latestGates.forEach((g) => {
    const opt   = document.createElement("option");
    opt.value   = g.gate_id;
    opt.textContent = g.name || g.gate_id;
    sel.appendChild(opt);
  });
  if (current) sel.value = current;
}

/**
 * Selects a gate in the simulator and re-runs queue model.
 * @param {string} gateId
 */
function selectSimGate(gateId) {
  simGate = latestGates.find(g => g.gate_id === gateId) || null;
  if (!simGate) {
    simServers = 0;
    resetSimDisplay();
    return;
  }
  simServers = simGate.servers_open ?? 1;
  renderSimResult();
}

/**
 * Resets the simulator display when no gate is selected.
 */
function resetSimDisplay() {
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  set("sim-count",    "—");
  set("sim-cur-wait", "—");
  set("sim-new-wait", "—");
  set("sim-delta",    "—");
  document.getElementById("sim-note").textContent = "";
  const el = document.getElementById("sim-new-wait");
  if (el) el.className = "sim-val";
}

/**
 * Solves the Erlang-C wait time for current simulated servers and updates results.
 */
function renderSimResult() {
  if (!simGate) return;

  const lambda   = simGate.arrivals_per_min   ?? 0;
  const mu       = simGate.capacity_per_min   ?? 1;
  const baseSrv  = simGate.servers_open       ?? 1;
  const curWait  = simGate.predicted_wait_minutes ?? predictWait(lambda, mu, baseSrv);
  const newWait  = predictWait(lambda, mu, simServers);
  const delta    = Math.round((curWait - newWait) * 10) / 10;

  const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  set("sim-count",    simServers);
  set("sim-cur-wait", `${curWait} min`);
  set("sim-new-wait", newWait >= 999 ? "∞" : `${newWait} min`);

  const deltaEl = document.getElementById("sim-delta");
  const noteEl  = document.getElementById("sim-note");

  if (simServers === baseSrv) {
    set("sim-delta", "No change");
    if (deltaEl) deltaEl.className = "sim-val color-mist";
    noteEl.textContent = "Adjust servers to see the impact.";
  } else if (delta > 0) {
    set("sim-delta", `−${delta} min`);
    if (deltaEl) deltaEl.className = "sim-val color-green";
    noteEl.textContent =
      `Opening ${simServers - baseSrv} extra server${simServers - baseSrv > 1 ? "s" : ""} ` +
      `at ${simGate.name || simGate.gate_id} would cut the queue by ${delta} min.`;
  } else if (delta < 0) {
    set("sim-delta", `+${Math.abs(delta)} min`);
    if (deltaEl) deltaEl.className = "sim-val color-red";
    noteEl.textContent =
      `Closing ${baseSrv - simServers} server${baseSrv - simServers > 1 ? "s" : ""} ` +
      `at ${simGate.name || simGate.gate_id} would add ${Math.abs(delta)} min to the queue.`;
  }

  if (newWait >= 999) {
    if (deltaEl) deltaEl.className = "sim-val color-red";
    set("sim-delta", "Queue unstable");
    noteEl.textContent = "⚠ Too few servers for current arrivals — queue will grow without limit.";
  }

  // Disable − button at minimum of 1 server
  const minusBtn = document.getElementById("sim-minus");
  if (minusBtn) minusBtn.disabled = simServers <= 1;
}

/**
 * Re-reads current simulated gate from the fresh snapshot.
 */
function refreshSimulator() {
  const sel = document.getElementById("sim-gate");
  if (sel?.value) selectSimGate(sel.value);
}

// Wire simulator controls
const simGateSel = document.getElementById("sim-gate");
if (simGateSel) {
  simGateSel.addEventListener("change", (e) => selectSimGate(e.target.value));
}

const simMinus = document.getElementById("sim-minus");
if (simMinus) {
  simMinus.addEventListener("click", () => {
    if (simServers > 1) { simServers--; renderSimResult(); }
  });
}

const simPlus = document.getElementById("sim-plus");
if (simPlus) {
  simPlus.addEventListener("click", () => {
    simServers++;
    renderSimResult();
  });
}

/**
 * Loads the initial ops gate snapshot.
 */
async function loadSnapshot() {
  try {
    const res  = await fetch("/api/ops/snapshot");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    renderOpsTable(await res.json());
  } catch {
    const tbody = document.getElementById("gate-table");
    if (tbody) tbody.innerHTML =
      `<tr><td colspan="6" class="color-mist" style="padding:1rem;">⚠ Snapshot unavailable — retrying…</td></tr>`;
  }
}

// ── Bootstrap ─────────────────────────────────────────────────────────────
if (document.getElementById("gate-table")) {
  loadSnapshot();

  const es = new EventSource("/api/ops/live");
  es.onmessage = (e) => {
    try { renderOpsTable(JSON.parse(e.data)); } catch { /* ignore */ }
  };
  es.onerror = () => {
    console.warn("SSE closed — switching to 15 s polling");
    es.close();
    loadSnapshot();
    setInterval(loadSnapshot, 15000);
  };
}
