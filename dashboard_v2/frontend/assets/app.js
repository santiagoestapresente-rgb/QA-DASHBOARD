const CHANNELS = ["All", "Phone", "Live Chat"];
const state = { channel: "All", inflight: null };

function ease(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function tween(el, to, fmt) {
  const from = Number(el.dataset.val || 0);
  if (!Number.isFinite(to)) {
    el.textContent = "—";
    return;
  }
  if (Math.abs(from - to) < 0.0005 && el.dataset.ready) {
    el.textContent = fmt(to);
    el.dataset.val = String(to);
    return;
  }
  const start = performance.now();
  const dur = Math.max(650, Math.min(1100, 550 + Math.abs(to - from) * 8));
  function step(now) {
    const p = Math.min(1, (now - start) / dur);
    const v = from + (to - from) * ease(p);
    el.textContent = fmt(v);
    if (p < 1) requestAnimationFrame(step);
    else {
      el.textContent = fmt(to);
      el.dataset.val = String(to);
      el.dataset.ready = "1";
    }
  }
  requestAnimationFrame(step);
}

function pct(n) {
  return `${n.toFixed(2)}%`;
}
function int(n) {
  return Math.round(n).toLocaleString("en-US");
}

function tile(id, title, traffic) {
  return `<article class="tile ${traffic || "neutral"}" id="${id}">
    <h3>${title}</h3>
    <div class="num" data-val="0">—</div>
    <p class="cap"></p>
  </article>`;
}

function renderShell() {
  document.getElementById("chips").innerHTML = CHANNELS.map(
    (c) => `<button type="button" data-ch="${c}" class="${c === state.channel ? "on" : ""}">${c}</button>`
  ).join("");
  document.getElementById("kpis").innerHTML = [
    tile("kpi-qa", "QA Score", "neutral"),
    tile("kpi-csat", "CSAT Score", "neutral"),
    tile("kpi-rc", "Recontact Rate", "neutral"),
    tile("kpi-contacts", "Total Contacts", "neutral"),
    tile("kpi-surveys", "Total Surveys", "neutral"),
    tile("kpi-evals", "QA Evaluations", "neutral"),
  ].join("");
  document.querySelectorAll("#chips button").forEach((b) => {
    b.addEventListener("click", () => {
      state.channel = b.dataset.ch;
      load();
    });
  });
}

function setTile(id, value, cap, traffic, fmt) {
  const root = document.getElementById(id);
  root.className = `tile ${traffic || "neutral"}`;
  root.querySelector(".cap").textContent = cap;
  tween(root.querySelector(".num"), value, fmt);
}

async function load() {
  if (state.inflight) state.inflight.abort();
  state.inflight = new AbortController();
  renderShellChipsOnly();
  try {
    const res = await fetch(`/api/overview?channel=${encodeURIComponent(state.channel)}`, {
      signal: state.inflight.signal,
    });
    if (!res.ok) throw new Error(`overview ${res.status}`);
    const data = await res.json();
    document.getElementById("slice-label").textContent =
      `Channel ${data.channel} · Market All · all weeks`;
    const k = data.kpis;
    setTile("kpi-qa", k.qa, `${k.qa_n.toLocaleString("en-US")} evaluations · goal ≥ ${data.goals.qa}`, k.qa_traffic, pct);
    setTile("kpi-csat", k.csat, `${k.csat_n.toLocaleString("en-US")} surveys · goal ≥ ${data.goals.csat}`, k.csat_traffic, pct);
    setTile("kpi-rc", k.recontact, `${k.recontact_n.toLocaleString("en-US")} contacts · goal ≤ ${data.goals.recontact}`, k.recontact_traffic, pct);
    setTile("kpi-contacts", k.contacts, "Σ Contacts in this slice", "neutral", int);
    setTile("kpi-surveys", k.surveys, "Σ Feedback CNT", "neutral", int);
    setTile("kpi-evals", k.qa_n, "QA audits in this slice", "neutral", int);
    drawChart(data.by_channel);
  } catch (err) {
    if (err.name === "AbortError") return;
    console.error(err);
  }
}

function renderShellChipsOnly() {
  document.querySelectorAll("#chips button").forEach((b) => {
    b.classList.toggle("on", b.dataset.ch === state.channel);
  });
}

function drawChart(rows) {
  const x = rows.map((r) => r.Channel);
  const traces = [
    { name: "QA", x, y: rows.map((r) => r.QA_Score), type: "bar", marker: { color: "#2E9B57" } },
    { name: "CSAT", x, y: rows.map((r) => r.CSAT_Score), type: "bar", marker: { color: "#2E6FBE" } },
    { name: "Recontact", x, y: rows.map((r) => r.Recontact_Rate), type: "bar", marker: { color: "#D64545" } },
  ];
  const layout = {
    barmode: "group",
    margin: { t: 10, r: 10, b: 40, l: 40 },
    paper_bgcolor: "#fff",
    plot_bgcolor: "#fff",
    font: { family: "Inter, Segoe UI, sans-serif", color: "#1a1a1a" },
    legend: { orientation: "h", y: 1.12 },
    yaxis: { title: "%" },
  };
  const el = document.getElementById("chart");
  if (el.data) Plotly.react(el, traces, layout, { displayModeBar: false });
  else Plotly.newPlot(el, traces, layout, { displayModeBar: false });
}

renderShell();
load();
