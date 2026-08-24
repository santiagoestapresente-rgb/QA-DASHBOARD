const ANALYSIS = [
  { id: "overview", label: "Overview", icon: "grid" },
  { id: "qa", label: "QA Analysis", icon: "check" },
  { id: "csat", label: "CSAT Analysis", icon: "heart" },
  { id: "recontact", label: "Recontact", icon: "repeat" },
  { id: "alerts", label: "Agent Performance", icon: "users" },
];
const SUPPORT = [
  { id: "quality", label: "Data Quality", icon: "shield" },
  { id: "definitions", label: "Definitions", icon: "book" },
];

const ICONS = {
  grid: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
  heart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z"/></svg>',
  repeat: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>',
  users: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  book: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
};

const state = {
  page: "overview",
  channel: "All",
  country: "All",
  weeks: "all",
  day: "All",
  lob: "All",
  tenure: "All",
  biz: "All",
  inflight: null,
  meta: null,
  last: null,
};

const PLOT = { displayModeBar: false, responsive: true };
const FONT = { family: "Inter, Segoe UI, sans-serif", color: "#6b7280", size: 11 };
const C = {
  orange: "#FF7D00",
  green: "#1F9D55",
  red: "#E24B4A",
  gold: "#D4A017",
  ink: "#1A1A1A",
  grey: "#6B7280",
  phone: "#3F3F46",
  chat: "#FF7D00",
  navy: "#163A66",
  blue: "#8FCBFF",
  bar: "#2E6FBE",
  csatLine: "#2E6FBE",
  rcLine: "#D64545",
  critDark: "#7A1212",
  critLight: "#F07167",
};

function ease(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}
function tween(el, to, fmt) {
  if (!el) return;
  const from = Number(el.dataset.val || 0);
  if (!Number.isFinite(to)) {
    el.textContent = "—";
    return;
  }
  const start = performance.now();
  function step(now) {
    const p = Math.min(1, (now - start) / 700);
    el.textContent = fmt(from + (to - from) * ease(p));
    if (p < 1) requestAnimationFrame(step);
    else {
      el.textContent = fmt(to);
      el.dataset.val = String(to);
    }
  }
  requestAnimationFrame(step);
}
function playTweens() {
  document.querySelectorAll("[data-tween]").forEach((el) => {
    const to = Number(el.dataset.tween);
    if (!Number.isFinite(to)) return;
    const kind = el.dataset.kind || "int";
    const d = Number(el.dataset.d || 0);
    const fmt =
      kind === "pct" ? (v) => pct(v, d || 2) :
      kind === "num" ? (v) => num(v, d || 1) :
      (v) => int(v);
    el.dataset.val = "0";
    tween(el, to, fmt);
  });
  requestAnimationFrame(() => {
    document.querySelectorAll(".ring[data-p]").forEach((el) => {
      el.style.setProperty("--p", el.getAttribute("data-p"));
    });
  });
}
function first(obj, ...keys) {
  if (!obj) return null;
  for (const k of keys) {
    if (obj[k] != null && obj[k] !== "") return obj[k];
  }
  return null;
}
function histXY(h) {
  if (!h) return { x: [], y: [] };
  if (Array.isArray(h)) {
    return {
      x: h.map((r) => first(r, "CSAT_Score", "Score", "x", "bin")),
      y: h.map((r) => Number(first(r, "Surveys", "Count", "n", "y", "Feedback")) || 0),
    };
  }
  return { x: h.x || [], y: (h.y || []).map(Number) };
}
function toneGoal(value, goal, higher) {
  if (value == null || goal == null) return { tone: "neutral", tag: "No data", pill: "" };
  const v = Number(value);
  const g = Number(goal);
  if (!Number.isFinite(v) || !Number.isFinite(g)) return { tone: "neutral", tag: "No data", pill: "" };
  const d = v - g;
  const ok = higher ? v >= g : v <= g;
  const gap = higher ? v - g : g - v;
  const pill = `${d >= 0 ? "↑" : "↓"} ${d > 0 ? "+" : ""}${d.toFixed(2)} points vs goal`;
  if (ok) return { tone: "green", tag: "On goal", pill };
  if (gap >= -5) return { tone: "amber", tag: "Within 5 points", pill };
  return { tone: "red", tag: "More than 5 points off", pill };
}
function toneFail(n, critical) {
  const v = Number(n || 0);
  if (v <= 0) return { tone: "green", tag: "On goal · 0 fails" };
  return critical
    ? { tone: "red", tag: "Off goal · any critical fail" }
    : { tone: "amber", tag: "Watch · non-critical fails" };
}
function pct(n, d = 2) {
  return n == null || !Number.isFinite(Number(n)) ? "—" : `${Number(n).toFixed(d)}%`;
}
function num(n, d = 2) {
  return n == null || !Number.isFinite(Number(n)) ? "—" : Number(n).toFixed(d);
}
function int(n) {
  return Math.round(Number(n) || 0).toLocaleString("en-US");
}
function pp(n) {
  if (n == null || !Number.isFinite(Number(n))) return "";
  const v = Number(n);
  return `${v > 0 ? "+" : ""}${v.toFixed(2)}pp`;
}
function weekLabel(w) {
  const s = String(w ?? "");
  const m = s.match(/W?(\d{1,2})$/i);
  return m ? `W${m[1]}` : s;
}
function layout(extra = {}) {
  return {
    margin: { t: 28, r: 36, b: 40, l: 48 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: FONT,
    legend: { orientation: "h", y: 1.14, font: { size: 11 } },
    xaxis: { showgrid: false, zeroline: false, linecolor: "#eee" },
    yaxis: { gridcolor: "#f0f0f0", zeroline: false },
    ...extra,
  };
}
function seedTrace(t) {
  const s = JSON.parse(JSON.stringify(t));
  if (t.type === "bar") {
    if (t.orientation === "h") s.x = (t.x || []).map(() => 0);
    else s.y = (t.y || []).map(() => 0);
    delete s.text;
  } else if (t.type === "scatter") {
    s.y = (t.y || []).map(() => 0);
  } else if (t.type === "pie") {
    s.values = (t.values || []).map((v) => (Number(v) > 0 ? 0.02 : 0));
  } else if (t.type === "choropleth") {
    s.z = (t.z || []).map(() => 70);
    s.opacity = 0.15;
  }
  return s;
}
function yMaxOf(traces, axis) {
  let m = 0;
  for (const t of traces || []) {
    if (axis === "y2" && t.yaxis !== "y2") continue;
    if (axis !== "y2" && t.yaxis === "y2") continue;
    const arr = t.orientation === "h" ? t.x : t.type === "pie" ? t.values : t.y;
    for (const v of arr || []) {
      const n = Number(v);
      if (Number.isFinite(n) && n > m) m = n;
    }
  }
  return m;
}
function isHBar(traces) {
  return (traces || []).some((t) => t.type === "bar" && t.orientation === "h");
}
function isPie(traces) {
  return (traces || []).some((t) => t.type === "pie");
}
function fixDummyRange(el, traces) {
  if (!el || !el.layout || isPie(traces) || (traces || []).some((t) => t.type === "choropleth")) return;
  const hbar = isHBar(traces);
  const maxV = yMaxOf(traces, "y");
  if (!(maxV > 1.05)) return;
  const ax = hbar ? el.layout.xaxis : el.layout.yaxis;
  const range = ax && ax.range;
  if (!range || Number(range[1]) > 1.05) return;
  const key = hbar ? "xaxis.range" : "yaxis.range";
  Plotly.relayout(el, { [key]: [0, maxV * 1.18] }).catch(() => {});
}
function plot(id, traces, extra = {}) {
  const el = document.getElementById(id);
  if (!el || typeof Plotly === "undefined") return;
  const list = traces || [];
  const geo = extra.geo === true || list.some((t) => t.type === "choropleth");
  const rest = { ...extra };
  delete rest.geo;
  delete rest.noAnim;
  const dual = !!(rest.yaxis2 || list.some((t) => t.yaxis === "y2"));
  const hbar = isHBar(list);
  const pie = isPie(list);
  const skipAnim = extra.noAnim !== false && (
    extra.noAnim || dual || geo || hbar || pie
    || list.some((t) => t.type === "choropleth" || t.type === "bar")
  );
  const lay = geo
    ? {
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: FONT,
        geo: {
          visible: false,
          resolution: 50,
          showcountries: true,
          countrycolor: "#D0D5DC",
          showland: true,
          landcolor: "#F5F6F8",
          showocean: true,
          oceancolor: "#FFFFFF",
          showlakes: false,
          showframe: false,
          bgcolor: "#FFFFFF",
          lataxis: { range: [-56, 33] },
          lonaxis: { range: [-118, -34] },
          projection: { type: "natural earth" },
        },
        ...rest,
      }
    : layout(rest);
  if (!geo) {
    const t = lay.title;
    if (typeof t === "string") lay.title = { text: t, x: 0.5, xanchor: "center" };
    else if (t && typeof t === "object") {
      if (t.x == null) t.x = 0.5;
      if (t.xanchor == null) t.xanchor = "center";
    }
  }
  if (!geo && !pie) {
    if (hbar) {
      const xmax = yMaxOf(list, "y");
      if (!lay.xaxis) lay.xaxis = {};
      if (lay.xaxis.range == null && xmax > 0) {
        lay.xaxis.rangemode = "tozero";
        lay.xaxis.range = [0, xmax * 1.18];
      }
    } else if (list.some((t) => t.type === "bar") && !(lay.yaxis && lay.yaxis.range != null)) {
      const ymax = yMaxOf(list, "y");
      if (!lay.yaxis) lay.yaxis = {};
      if (ymax > 0) {
        lay.yaxis.rangemode = lay.yaxis.rangemode || "tozero";
        if (lay.yaxis.rangemode === "tozero") lay.yaxis.range = [0, ymax * 1.18];
      }
    }
    if (dual) {
      if (!lay.yaxis2) lay.yaxis2 = rest.yaxis2 || {};
      if (lay.yaxis2.range == null) {
        const y2 = yMaxOf(list, "y2");
        const cap = y2 > 40 ? Math.max(108, y2 * 1.05) : Math.max(y2 * 1.25, 1);
        lay.yaxis2.range = [0, cap];
      }
    }
  }
  const paint = (data) => {
    const op = el.data && el.data.length ? Plotly.react : Plotly.newPlot;
    return op.call(Plotly, el, data, lay, PLOT);
  };
  const finish = () => paint(list).then(() => {
    fixDummyRange(el, list);
  }).catch((err) => {
    console.warn("plot failed", id, err);
    el.innerHTML = `<p class="hint">Chart unavailable</p>`;
  });
  if (skipAnim) {
    finish();
    return;
  }
  const frames = {
    transition: { duration: 640, easing: "cubic-in-out" },
    frame: { duration: 640, redraw: true },
  };
  try {
    paint(list.map(seedTrace))
      .then(() => {
        if (typeof Plotly.animate === "function") {
          return Plotly.animate(el, { data: list, traces: list.map((_, i) => i) }, frames);
        }
      })
      .then(() => finish())
      .catch(() => finish());
  } catch (err) {
    console.warn("plot failed", id, err);
    finish();
  }
}
function card(title, inner, hint = "") {
  return `<article class="card"><h2>${title}</h2>${inner}${hint ? `<p class="hint foot-n">${hint}</p>` : ""}</article>`;
}
function paretoBox(id) {
  return `<div class="pareto-frame"><div class="chart pareto" id="${id}"></div></div>`;
}
function weekSpan(data) {
  const w = (((data && data.filters && data.filters.weeks) || []).map(weekLabel));
  if (!w.length) return "all weeks";
  if (w.length === 1) return w[0];
  return `${w[0]}–${w[w.length - 1]}${w.length > 2 ? ` (${w.length} weeks)` : ""}`;
}
function nEvals(data) {
  const k = (data && data.kpis) || {};
  return int(first(k, "evaluations", "qa_n") || 0);
}
function nSurveys(data) {
  const k = (data && data.kpis) || {};
  return int(first(k, "surveys", "csat_n") || 0);
}
function nContacts(data) {
  const k = (data && data.kpis) || {};
  return int(first(k, "contacts", "recontact_n") || 0);
}
function heroNote(data) {
  return `<p class="hint foot-n">n = ${nEvals(data)} evals · CSAT N = ${nSurveys(data)} surveys · Recontact over ${nContacts(data)} contacts · Phone 12 attrs / Live Chat 8 · ${weekSpan(data)}</p>`;
}
function setBusy(on) {
  const bar = document.getElementById("loadbar");
  const view = document.getElementById("view");
  if (bar) {
    bar.classList.toggle("is-loading", !!on);
    bar.classList.remove("on", "load");
    bar.setAttribute("aria-hidden", on ? "false" : "true");
  }
  if (view) view.classList.toggle("is-busy", !!on);
}
function enterView() {
  setBusy(false);
  const view = document.getElementById("view");
  if (!view) return;
  view.classList.remove("is-busy");
  view.classList.remove("is-enter");
  void view.offsetWidth;
  view.classList.add("is-enter");
  playTweens();
}
function ring(p, color, label) {
  const clamped = Math.max(0, Math.min(100, Number(p) || 0));
  return `<div class="ring" style="--p:0;--c:${color}" data-p="${clamped}"><span>${label}</span></div>`;
}
function badge(higher, value, goal) {
  if (value == null) return `<span class="badge watch">No data</span>`;
  const ok = higher ? value >= goal : value <= goal;
  const diff = higher ? value - goal : goal - value;
  if (ok) return `<span class="badge on">On Goal</span>`;
  if (diff >= -5) return `<span class="badge watch">Watch</span>`;
  return `<span class="badge off">Off Goal</span>`;
}
function deltaCls(higher, value, goal) {
  if (value == null) return "";
  const ok = higher ? value >= goal : value <= goal;
  if (ok) return "up";
  const diff = higher ? value - goal : goal - value;
  return diff >= -5 ? "warn" : "down";
}
function ringColor(higher, value, goal) {
  if (value == null) return C.grey;
  const ok = higher ? value >= goal : value <= goal;
  if (ok) return C.green;
  const diff = higher ? value - goal : goal - value;
  return diff >= -5 ? C.gold : C.red;
}
function kpiRing({ title, value, goal, higher, fmt, ncap, kind = "num" }) {
  const color = ringColor(higher, value, goal);
  const fill = higher ? value : Math.max(8, Math.min(100, (goal / Math.max(value || goal, 0.01)) * 70));
  const d = value == null ? null : value - goal;
  const tweenAttr = value == null ? "" : `data-tween="${value}" data-kind="${kind}" data-d="2"`;
  return `<article class="card kpi">
    <div>
      <p class="kpi-label">${title}</p>
      <div class="kpi-val" ${tweenAttr}>${value == null ? "—" : "0"}</div>
      <div class="kpi-meta">
        <span>Goal: ${fmt(goal)}</span>
        <span class="delta ${deltaCls(higher, value, goal)}">${d == null ? "" : pp(d)}</span>
        ${badge(higher, value, goal)}
        <span>${ncap || ""}</span>
      </div>
    </div>
    ${ring(higher ? value : fill, color, value == null ? "—" : String(fmt(value)).replace("%", ""))}
  </article>`;
}
function table(rows, cols) {
  if (!rows || !rows.length) return `<p class="hint">No rows in this slice.</p>`;
  const head = cols.map((c) => `<th>${c.label}</th>`).join("");
  const body = rows
    .map((r) => {
      const tds = cols
        .map((c) => {
          const v = r[c.key];
          const t = c.goal != null && (c.fmt === "pct" || c.fmt === "num") ? toneGoal(v, c.goal, c.higher !== false) : null;
          const toneCls = t && t.tone && t.tone !== "neutral" ? ` tone-cell ${t.tone}` : "";
          if (c.fmt === "pct") return `<td class="num${toneCls}">${pct(v, c.d ?? 2)}</td>`;
          if (c.fmt === "int") return `<td class="num">${v == null ? "—" : int(v)}</td>`;
          if (c.fmt === "num") return `<td class="num${toneCls}">${num(v, c.d ?? 2)}</td>`;
          return `<td>${v == null ? "—" : v}</td>`;
        })
        .join("");
      return `<tr>${tds}</tr>`;
    })
    .join("");
  return `<div class="table-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}
function hbar(id, labels, values, color) {
  const pairs = (labels || [])
    .map((l, i) => ({ l: String(l || ""), v: Number(values[i]) || 0 }))
    .filter((p) => p.l && p.v > 0)
    .sort((a, b) => a.v - b.v);
  plot(id, [{ type: "bar", orientation: "h", y: pairs.map((p) => p.l), x: pairs.map((p) => p.v), marker: { color }, hovertemplate: "%{y}: %{x}<extra></extra>" }], {
    margin: { t: 8, r: 16, b: 24, l: 130 },
    yaxis: { automargin: true },
  });
}
function field(row, keys) {
  for (const k of keys) {
    if (row && row[k] != null && row[k] !== "") return row[k];
  }
  return null;
}
function hexLerp(a, b, t) {
  const p = (h) => [1, 3, 5].map((i) => parseInt(String(h).slice(i, i + 2), 16));
  const A = p(a), B = p(b);
  const c = A.map((v, i) => Math.round(v + (B[i] - v) * t));
  return `#${c.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}
function wrapLabel(s, width = 16) {
  const t = String(s || "");
  if (t.length <= width) return t;
  const words = t.split(/\s+/);
  const lines = [];
  let cur = "";
  for (const w of words) {
    const trial = cur ? `${cur} ${w}` : w;
    if (trial.length <= width) cur = trial;
    else {
      if (cur) lines.push(cur);
      cur = w;
    }
  }
  if (cur) lines.push(cur);
  return lines.slice(0, 3).join("<br>");
}
function setFoot(id, text) {
  const el = document.getElementById(id);
  const art = el && el.closest("article.card");
  const foot = art && art.querySelector("p.hint.foot-n");
  if (foot && text) {
    if (!foot.getAttribute("data-base")) foot.setAttribute("data-base", foot.textContent);
    foot.textContent = text;
  }
}
function paretoRows(rows, labelKeys, valueKeys, maxNamed = 30) {
  const items = (rows || [])
    .map((r) => ({
      label: String(field(r, labelKeys) ?? ""),
      value: Number(field(r, valueKeys) ?? 0),
      crit: !!(r.Is_Critical || r.Critical || r.is_critical),
    }))
    .filter((r) => r.label && r.value > 0)
    .sort((a, b) => b.value - a.value);
  const universe = items.reduce((s, r) => s + r.value, 0);
  let vitalN = items.length;
  let run = 0;
  for (let i = 0; i < items.length; i++) {
    run += items[i].value;
    if (universe && run >= universe * 0.8) {
      vitalN = i + 1;
      break;
    }
  }
  const namedN = Math.min(vitalN, maxNamed, items.length);
  const named = items.slice(0, namedN);
  const tail = items.slice(namedN);
  const nMore = tail.length;
  if (nMore > 0) {
    named.push({
      label: `Remaining reasons (${nMore} more)`,
      value: tail.reduce((s, r) => s + r.value, 0),
      crit: false,
      leftover: true,
      nMore,
    });
  }
  let cum = 0;
  const out = named.map((r) => {
    cum += r.value;
    return { ...r, cumPct: universe ? Math.round((cum / universe) * 1000) / 10 : 0 };
  });
  return { rows: out, universe, namedN, vitalN, nMore, nCats: items.length };
}
function pareto(id, rows, labelKeys, valueKeys, opts = {}) {
  const meta = paretoRows(rows, [].concat(labelKeys), [].concat(valueKeys), opts.max || 10);
  const p = meta.rows;
  const el = document.getElementById(id);
  if (!el) return;
  if (!p.length) {
    el.innerHTML = `<p class="hint">No rows for this Pareto in the current filter.</p>`;
    return;
  }
  const n = p.length;
  const xs = p.map((_, i) => i);
  const labels = p.map((r) => wrapLabel(r.label, 16));
  const counts = p.map((r) => r.value);
  const yMax = Math.max(...counts, 1) * 1.28;
  const hit = p.findIndex((r) => r.cumPct >= 80);
  const cutX = (hit >= 0 ? hit : n - 1) + 0.5;
  const hasCrit = p.some((r) => r.crit);
  const colors = p.map((r, i) => {
    const t = i / Math.max(n - 1, 1);
    if (r.leftover) return "#C5D0DC";
    if (r.crit) return hexLerp(C.critDark || "#7A1212", C.critLight || "#F07167", t);
    return hexLerp(C.navy || "#163A66", C.blue || "#8FCBFF", t);
  });
  const valueTitle = opts.valueTitle || "Count";
  const traces = [
    {
      name: valueTitle,
      x: xs,
      y: counts,
      type: "bar",
      width: 0.72,
      marker: { color: colors, line: { color: "#F4F7FB", width: 1.2 } },
      customdata: p.map((r) => [
        r.label,
        r.crit ? "CRITICAL" : r.leftover ? `${r.nMore} reasons combined` : "Non-critical",
        r.value,
      ]),
      hovertemplate: `%{customdata[0]}<br>%{customdata[1]}<br>${valueTitle}: %{customdata[2]:,}<extra></extra>`,
    },
    {
      name: "Cumulative %",
      x: [-0.5, ...xs.map((i) => i + 0.5)],
      y: [0, ...p.map((r) => r.cumPct)],
      type: "scatter",
      mode: "lines+markers",
      yaxis: "y2",
      line: { color: C.orange, width: 2.5 },
      marker: { size: 8, symbol: "square", color: C.orange },
      hovertemplate: "Cumulative %{y:.1f}%<extra></extra>",
    },
  ];
  if (hasCrit) {
    traces.push({ name: "CRITICAL", x: [null], y: [null], type: "bar", marker: { color: "#D64545" }, hoverinfo: "skip", showlegend: true });
    if (p.some((r) => !r.crit && !r.leftover)) {
      traces.push({ name: "Non-critical", x: [null], y: [null], type: "bar", marker: { color: "#2E6FBE" }, hoverinfo: "skip" });
    }
  }
  plot(id, traces, {
    noAnim: true,
    bargap: 0.18,
    bargroupgap: 0.08,
    autosize: true,
    yaxis: { title: valueTitle, range: [0, yMax], rangemode: "tozero", gridcolor: "#f0f0f0", tickformat: ",d" },
    yaxis2: { title: "Cumulative %", overlaying: "y", side: "right", range: [0, 105], ticksuffix: "%", showgrid: false },
    xaxis: {
      tickmode: "array",
      tickvals: xs,
      ticktext: labels,
      tickangle: n >= 8 ? -55 : n >= 6 ? -36 : 0,
      range: [-0.55, n - 0.45],
      automargin: true,
    },
    legend: { orientation: "h", y: 1.16 },
    shapes: [
      { type: "line", xref: "paper", x0: 0, x1: 1, yref: "y2", y0: 80, y1: 80, line: { color: "rgba(255,125,0,0.55)", width: 1.6, dash: "dot" } },
      { type: "line", xref: "x", x0: cutX, x1: cutX, yref: "paper", y0: 0, y1: 1, line: { color: C.orange, width: 2, dash: "dot" } },
    ],
    annotations: [{ text: "80% vital few", x: 1, xref: "paper", y: 80, yref: "y2", xanchor: "right", yanchor: "bottom", showarrow: false, font: { size: 10, color: C.orange } }],
    margin: { t: 40, r: 64, b: n >= 6 ? 110 : 80, l: 56 },
  });
  const unit = opts.unit || String(valueTitle).toLowerCase();
  let rest = "";
  if (meta.nMore > 0) {
    rest = meta.namedN >= meta.vitalN
      ? `${meta.namedN} named bars reach 80% · last bar = ${meta.nMore} more reasons (leftover ~20%)`
      : `80% takes ${meta.vitalN} reasons · showing ${meta.namedN} · last bar = ${meta.nMore} more combined`;
  }
  const cap = `N = ${int(meta.universe)} ${unit}${opts.nAudits != null ? ` · ${int(opts.nAudits)} audits` : ""}${rest ? ` · ${rest}` : ""}`;
  setFoot(id, cap);
}
function americasMap(id, rows) {
  const el = document.getElementById(id);
  if (!el) return;
  const ISO3 = { MX: "MEX", CO: "COL", CR: "CRI", PE: "PER", DO: "DOM", PA: "PAN" };
  const work = (rows || [])
    .map((r) => ({ ...r, _iso: r.iso3 || r.ISO3 || r.iso_3 || ISO3[String(r.Country || "").trim()] }))
    .filter((r) => r._iso);
  if (!work.length) {
    el.innerHTML = `<p class="hint">No market rows to map in this slice.</p>`;
    return;
  }
  plot(id, [{
    type: "choropleth",
    locations: work.map((r) => r._iso),
    z: work.map((r) => (r.QA_Score != null ? r.QA_Score : r.CSAT_Score)),
    locationmode: "ISO-3",
    colorscale: [[0, "#D64545"], [0.42, "#F2A900"], [0.7, "#2E9B57"], [1, "#1B7A42"]],
    zmin: 70,
    zmax: 100,
    marker: { line: { color: "#fff", width: 0.9 } },
    colorbar: { title: { text: "QA / CSAT %", font: { size: 10 } }, thickness: 12, len: 0.55 },
    text: work.map((r) => {
      const name = r.Country_Name || r.Country;
      const qa = r.QA_Score == null ? "no QA" : `${num(r.QA_Score)} · ${int(r.QA_N || 0)} audits`;
      const cs = r.CSAT_Score == null ? "no CSAT" : `${pct(r.CSAT_Score)} · ${int(r.CSAT_N || r.Feedback || 0)} surveys`;
      return `<b>${name}</b><br>QA ${qa}<br>CSAT ${cs}<br>Recontact: SSL mix (no market field)`;
    }),
    hovertemplate: "%{text}<extra></extra>",
  }], { geo: true, margin: { t: 8, r: 0, l: 0, b: 0 } });
}
function donut(id, labels, values, colors, holeText) {
  plot(id, [{ type: "pie", hole: 0.68, labels, values, marker: { colors }, textinfo: "none", sort: false }], {
    margin: { t: 8, r: 8, b: 8, l: 8 },
    showlegend: false,
    annotations: [{ text: holeText, x: 0.5, y: 0.5, showarrow: false, font: { size: 12, color: C.ink, family: FONT.family } }],
  });
}
function fillSelect(el, items, current, labelFn) {
  if (!el) return;
  el.innerHTML = items
    .map((item) => {
      const id = typeof item === "string" ? item : item.id;
      const label = labelFn ? labelFn(item) : typeof item === "string" ? item : item.label;
      return `<option value="${id}">${label}</option>`;
    })
    .join("");
  el.value = current;
}
function navHtml(items) {
  return items
    .map((p) => `<button type="button" data-id="${p.id}" class="${p.id === state.page ? "on" : ""}">${ICONS[p.icon] || ""}${p.label}</button>`)
    .join("");
}
function bindNav(root) {
  root.querySelectorAll("button").forEach((b) => {
    b.addEventListener("click", () => {
      state.page = b.dataset.id;
      load();
    });
  });
}
function renderChrome() {
  const a = document.getElementById("nav-analysis");
  const s = document.getElementById("nav-support");
  a.innerHTML = navHtml(ANALYSIS);
  s.innerHTML = navHtml(SUPPORT);
  bindNav(a);
  bindNav(s);
  document.getElementById("reset").onclick = () => {
    state.channel = "All";
    state.country = "All";
    state.weeks = "all";
    state.day = "All";
    state.lob = "All";
    state.tenure = "All";
    state.biz = "All";
    syncFilters();
    load();
  };
  document.getElementById("refresh").onclick = () => load();
}
function renderMeta() {
  const m = state.meta;
  if (!m) return;
  fillSelect(document.getElementById("channel"), m.channels, state.channel);
  fillSelect(document.getElementById("country"), m.countries, state.country);
  fillSelect(document.getElementById("weeks"), ["all", ...m.weeks], state.weeks, (id) => (id === "all" ? "All weeks" : weekLabel(id)));
  fillSelect(document.getElementById("day"), m.days || ["All"], state.day);
  fillSelect(document.getElementById("lob"), m.lobs || ["All"], state.lob);
  fillSelect(document.getElementById("tenure"), m.tenure || ["All"], state.tenure);
  fillSelect(document.getElementById("biz"), m.business_types || ["All"], state.biz);
  ["channel", "country", "weeks", "day", "lob", "tenure", "biz"].forEach((id) => {
    const el = document.getElementById(id);
    el.onchange = () => {
      state[id === "biz" ? "biz" : id] = el.value;
      load();
    };
  });
  document.getElementById("as-of").textContent = `Data as of ${m.as_of || "May 2026 snapshot"}`;
  const g = m.goals || {};
  const tgt = document.getElementById("tgt-line");
  if (tgt) tgt.textContent = `QA ≥ ${g.qa ?? 85} · CSAT ≥ ${g.csat ?? 85}% · Recontact ≤ ${g.recontact ?? 5.44}%`;
}
function syncFilters() {
  document.querySelectorAll(".nav button").forEach((b) => b.classList.toggle("on", b.dataset.id === state.page));
  const map = { channel: "channel", country: "country", weeks: "weeks", day: "day", lob: "lob", tenure: "tenure", biz: "biz" };
  Object.entries(map).forEach(([id, key]) => {
    const el = document.getElementById(id);
    if (el) el.value = state[key];
  });
}
function titles() {
  const map = {
    overview: ["CX Quality Dashboard", "CX Service Operations · Delivery LOB"],
    qa: ["QA Analysis", "Audit quality · mean of Score_Pct"],
    csat: ["CSAT Analysis", "Official CSAT · (4★+5★) / Feedback CNT"],
    recontact: ["Recontact", "Official mix · Σ repeats / Σ contacts"],
    alerts: ["Agent Performance", "Coaching queue · reliable agents only"],
    quality: ["Data Quality", "How each source is sliced"],
    definitions: ["Definitions", "Official formulas and goals"],
  };
  const [t, s] = map[state.page] || map.overview;
  document.getElementById("page-title").textContent = t;
  document.getElementById("page-sub").textContent = s;
}
function chRow(rows, name) {
  return (rows || []).find((r) => String(r.Segment || r.Channel || "").toLowerCase() === name.toLowerCase());
}
function statusMeta(tone, tag, pill) {
  const hide = !tag || tag === "Context";
  const bits = [];
  if (pill) bits.push(`<span class="ops-pill ${tone}">${pill}</span>`);
  if (!hide) bits.push(`<span class="mini-tag ${tone}"><i></i>${tag}</span>`);
  if (!bits.length) return "";
  return `<div class="ops-meta">${bits.join("")}</div>`;
}
function miniTile({ label, value, kind = "int", d = 0, tone = "neutral", tag = "", cap = "", pill = "" }) {
  const raw = value == null || !Number.isFinite(Number(value)) ? null : Number(value);
  return `<article class="card mini-kpi tone-${tone}">
    <header class="ops-head">${label}</header>
    <div class="ops-body">
      <div class="kpi-val" ${raw == null ? "" : `data-tween="${raw}" data-kind="${kind}" data-d="${d}"`}>${raw == null ? "—" : "0"}</div>
      ${statusMeta(tone, tag, pill)}
      ${cap ? `<p class="mini-cap">${cap}</p>` : ""}
    </div>
  </article>`;
}
function mini(a, b) {
  if (typeof a === "object" && a && a.label != null) return miniTile(a);
  const s = b == null ? "" : String(b);
  const n = Number(s.replace(/[% ,]/g, ""));
  const kind = s.includes("%") ? "pct" : s.includes(".") ? "num" : "int";
  return miniTile({
    label: a,
    value: Number.isFinite(n) ? n : null,
    kind,
    d: s.includes(".") ? 1 : 0,
    tag: "",
  });
}
function miniCol(title, tiles) {
  return `<div class="ops-col"><p class="kicker">${title}</p>${tiles.join("")}</div>`;
}
function opsCard({ id, title, value, kind = "int", d = 0, tone = "neutral", tag = "", cap = "", pill = "" }) {
  const raw = value == null || !Number.isFinite(Number(value)) ? null : Number(value);
  return `<article class="ops-card tone-${tone}">
    <header class="ops-head">${title}</header>
    <div class="ops-body">
      <div class="kpi-val" ${raw == null ? "" : `data-tween="${raw}" data-kind="${kind}" data-d="${d}"`}>${raw == null ? "—" : "0"}</div>
      ${statusMeta(tone, tag, pill)}
      ${cap ? `<p class="mini-cap">${cap}</p>` : ""}
      ${id ? `<div class="chart ops-plot" id="${id}"></div>` : ""}
    </div>
  </article>`;
}
function scoreRange(ys) {
  const vals = (ys || []).map(Number).filter(Number.isFinite);
  if (!vals.length) return [0, 100];
  const lo = Math.min(...vals);
  const hi = Math.max(...vals);
  const pad = Math.max(1.5, (hi - lo) * 0.22);
  return [Math.max(0, lo - pad), hi + pad];
}
function xyOf(rows, yKeys, xKeys = ["Date", "Week"]) {
  const x = [];
  const y = [];
  for (const r of rows || []) {
    const xv = first(r, ...xKeys);
    const raw = first(r, ...[].concat(yKeys));
    if (xv == null || xv === "" || raw == null || raw === "") continue;
    const yv = Number(raw);
    if (!Number.isFinite(yv)) continue;
    const xs = String(xv);
    x.push(/W\d/i.test(xs) || /^W?\d{1,2}$/i.test(xs) ? weekLabel(xs) : xs);
    y.push(yv);
  }
  return { x, y };
}
function volOf(volumes, key) {
  const rawY = (volumes && volumes[key]) || [];
  const rawX = (volumes && volumes[`${key}_labels`]) || [];
  const x = [];
  const y = [];
  const n = Math.max(rawY.length, rawX.length);
  for (let i = 0; i < n; i++) {
    const v = Number(rawY[i]);
    if (!Number.isFinite(v)) continue;
    x.push(rawX[i] != null ? String(rawX[i]) : String(i + 1));
    y.push(v);
  }
  return { x, y };
}
function pickTrend(daily, weekly, yKeys) {
  const d = xyOf(daily, yKeys, ["Date"]);
  if (d.y.length >= 2) return d;
  return xyOf(weekly, yKeys, ["Week", "Date"]);
}
function emptyPlot(id, msg) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = `<p class="hint empty-plot">${msg || "No series in this filter."}</p>`;
}
function miniLine(id, series, color, opts = {}) {
  if (!series || series.y.length < 2) {
    if (opts.fallbackLabels && opts.fallbackValues) {
      miniCompose(id, opts.fallbackLabels, opts.fallbackValues, opts.fallbackColors, opts.holeText);
      return;
    }
    emptyPlot(id, "No trend in this filter.");
    return;
  }
  const toZero = opts.toZero === true;
  const ymax = Math.max(...series.y);
  plot(id, [{
    x: series.x,
    y: series.y,
    type: "scatter",
    mode: "lines+markers",
    line: { color, width: 2.4 },
    marker: { size: 6, color, symbol: "circle" },
    hovertemplate: "%{x}<br>%{y:.2f}<extra></extra>",
    connectgaps: false,
  }], {
    noAnim: true,
    margin: { t: 6, r: 8, b: 28, l: 36 },
    showlegend: false,
    yaxis: {
      range: toZero ? [0, Math.max(ymax * 1.22, 0.01)] : scoreRange(series.y),
      rangemode: toZero ? "tozero" : "normal",
      gridcolor: "#f0f0f0",
      nticks: 3,
      fixedrange: true,
    },
    xaxis: {
      nticks: 4,
      tickangle: 0,
      showgrid: false,
      fixedrange: true,
      tickformat: (series.x || []).some((s) => /^\d{4}-\d{2}-\d{2}/.test(String(s))) ? "%b %d" : undefined,
    },
  });
}
function miniBars(id, series, color) {
  if (!series || series.y.length < 1) {
    emptyPlot(id, "No volume in this filter.");
    return;
  }
  plot(id, [{
    x: series.x,
    y: series.y,
    type: "bar",
    marker: { color },
    hovertemplate: "%{x}<br>%{y:,.0f}<extra></extra>",
  }], {
    noAnim: true,
    bargap: 0.22,
    margin: { t: 6, r: 8, b: 28, l: 36 },
    showlegend: false,
    yaxis: { rangemode: "tozero", gridcolor: "#f0f0f0", nticks: 3, fixedrange: true, tickformat: ",d" },
    xaxis: { nticks: 4, tickangle: 0, showgrid: false, fixedrange: true },
  });
}
function miniHbar(id, labels, values, color) {
  const pairs = (labels || [])
    .map((l, i) => ({ l: String(l || ""), v: Number(values[i]) || 0 }))
    .filter((p) => p.l && Number.isFinite(p.v) && p.v > 0)
    .sort((a, b) => b.v - a.v)
    .slice(0, 6);
  if (!pairs.length) {
    emptyPlot(id, "No rows in this filter.");
    return;
  }
  if (pairs.length < 2 && arguments.length) {
    miniDonut(id, pairs.map((p) => p.l), pairs.map((p) => p.v), [color, C.grey], String(int(pairs[0].v)));
    return;
  }
  const ranked = pairs.slice().reverse();
  const xmax = Math.max(...ranked.map((p) => p.v), 1);
  plot(id, [{
    type: "bar",
    orientation: "h",
    y: ranked.map((p) => wrapLabel(p.l, 18).replace(/<br>/g, " ")),
    x: ranked.map((p) => p.v),
    marker: { color },
    hovertemplate: "%{y}: %{x:,}<extra></extra>",
  }], {
    noAnim: true,
    bargap: 0.28,
    margin: { t: 4, r: 28, b: 8, l: 88 },
    showlegend: false,
    xaxis: { rangemode: "tozero", range: [0, xmax * 1.18], showgrid: false, fixedrange: true, nticks: 3 },
    yaxis: { automargin: true, fixedrange: true, type: "category" },
  });
}
function miniDonut(id, labels, values, colors, holeText) {
  const labs = [];
  const vals = [];
  const cols = [];
  (labels || []).forEach((lab, i) => {
    const v = Number(values[i]) || 0;
    if (v > 0 && lab) {
      labs.push(lab);
      vals.push(v);
      cols.push((colors || [])[i] || C.bar);
    }
  });
  if (!labs.length) {
    emptyPlot(id, "No mix in this filter.");
    return;
  }
  donut(id, labs, vals, cols, holeText);
}
function miniCompose(id, labels, values, colors, holeText) {
  const pairs = (labels || [])
    .map((l, i) => ({ l: String(l || ""), v: Number(values[i]) || 0 }))
    .filter((p) => p.l && p.v > 0);
  if (!pairs.length) {
    emptyPlot(id, "No mix in this filter.");
    return;
  }
  if (pairs.length <= 4) {
    miniDonut(id, pairs.map((p) => p.l), pairs.map((p) => p.v), colors, holeText);
    return;
  }
  miniHbar(id, pairs.map((p) => p.l), pairs.map((p) => p.v), (colors && colors[0]) || C.bar);
}
function starSlice(rows, wantHi) {
  return (rows || []).filter((r) => {
    const name = String(r.Rating || r.label || "");
    const n = parseInt(name, 10);
    if (wantHi) return n >= 4 || /5 Stars|4 Stars/i.test(name);
    return (n >= 1 && n <= 3) || /3 Stars|2 Stars|1 Star/i.test(name);
  });
}
function downloadBar() {
  return `<div class="foot-actions"><button type="button" class="download" id="download">Download report</button></div>`;
}
function bindDownload() {
  const el = document.getElementById("download");
  if (el) el.onclick = downloadReport;
}
function rcRate(r) {
  if (!r) return null;
  if (r.Recontact_Rate != null) return r.Recontact_Rate;
  const c = Number(r.Contacts || 0);
  const n = Number(r.Recontacts || 0);
  return c ? (n / c) * 100 : null;
}
function combo(id, labels, bars, line, barName, lineName) {
  const yMax = Math.max(0, ...bars.map(Number).filter(Number.isFinite));
  const y2Max = Math.max(0, ...line.map(Number).filter(Number.isFinite));
  plot(id, [
    { name: barName, x: labels, y: bars, type: "bar", marker: { color: C.orange } },
    { name: lineName, x: labels, y: line, type: "scatter", mode: "lines+markers", yaxis: "y2", line: { color: C.ink, width: 2 } },
  ], {
    noAnim: true,
    yaxis: { rangemode: "tozero", range: [0, yMax * 1.18 || 1] },
    yaxis2: { overlaying: "y", side: "right", rangemode: "tozero", range: [0, Math.max(y2Max * 1.2, 1)] },
    xaxis: { tickangle: -25 },
    margin: { t: 28, r: 44, b: 80, l: 48 },
  });
}
function ichartRange(rows) {
  const vals = [];
  for (const r of rows || []) {
    for (const k of ["Value", "UCL", "LCL", "CL", "Goal"]) {
      const n = Number(r[k]);
      if (Number.isFinite(n)) vals.push(n);
    }
  }
  if (!vals.length) return [0, 100];
  const lo = Math.min(...vals);
  const hi = Math.max(...vals);
  const pad = Math.max(1.2, (hi - lo) * 0.12);
  const ymin = Math.max(0, lo - pad);
  let ymax = hi + pad;
  if (hi >= 50) ymax = Math.max(100, hi + pad * 0.4);
  return [ymin, ymax];
}
function ichart(id, rows, title) {
  const el = document.getElementById(id);
  if (!el) return;
  if (!rows || !rows.length) {
    emptyPlot(id, "Not enough daily points to show typical variation.");
    return;
  }
  const xs = rows.map((r) => r.Date);
  const [ymin, ymax] = ichartRange(rows);
  plot(id, [
    { name: title, x: xs, y: rows.map((r) => r.Value), type: "scatter", mode: "lines+markers", line: { color: C.bar, width: 2 }, marker: { size: 6, color: C.bar } },
    { name: "UCL", x: xs, y: rows.map((r) => r.UCL), type: "scatter", mode: "lines", line: { color: C.red, dash: "dot", width: 1.4 } },
    { name: "LCL", x: xs, y: rows.map((r) => r.LCL), type: "scatter", mode: "lines", line: { color: C.red, dash: "dot", width: 1.4 } },
    { name: "CL", x: xs, y: rows.map((r) => r.CL), type: "scatter", mode: "lines", line: { color: C.grey, dash: "dash", width: 1.4 } },
    { name: "Goal", x: xs, y: rows.map((r) => r.Goal), type: "scatter", mode: "lines", line: { color: C.green, dash: "dash", width: 1.6 } },
  ], {
    noAnim: true,
    yaxis: { range: [ymin, ymax], rangemode: "normal", tickformat: ".1f", nticks: 6 },
    legend: { orientation: "h", y: 1.14, font: { size: 10 } },
    margin: { t: 36, r: 28, b: 48, l: 48 },
  });
}
function olsLine(xs, ys) {
  const pts = xs.map((x, i) => [Number(x), Number(ys[i])]).filter((p) => Number.isFinite(p[0]) && Number.isFinite(p[1]));
  if (pts.length < 2) return null;
  const n = pts.length;
  const mx = pts.reduce((s, p) => s + p[0], 0) / n;
  const my = pts.reduce((s, p) => s + p[1], 0) / n;
  let num = 0;
  let den = 0;
  for (const [x, y] of pts) {
    num += (x - mx) * (y - my);
    den += (x - mx) * (x - mx);
  }
  if (!den) return null;
  const slope = num / den;
  const intercept = my - slope * mx;
  const x0 = Math.min(...pts.map((p) => p[0]));
  const x1 = Math.max(...pts.map((p) => p[0]));
  return { x: [x0, x1], y: [slope * x0 + intercept, slope * x1 + intercept] };
}
function scatterXY(id, rows, xKey, yKey, opts = {}) {
  const el = document.getElementById(id);
  if (!el) return;
  const pts = (rows || []).filter((r) => Number.isFinite(Number(r[xKey])) && Number.isFinite(Number(r[yKey])));
  if (!pts.length) {
    emptyPlot(id, opts.empty || "Not enough overlapping contact reasons in this filter.");
    return;
  }
  const xs = pts.map((r) => Number(r[xKey]));
  const ys = pts.map((r) => Number(r[yKey]));
  const names = pts.map((r) => r.CR_Lv4 || r.Channel || "");
  const traces = [{
    name: opts.name || "Contact reasons",
    x: xs,
    y: ys,
    text: names,
    type: "scatter",
    mode: "markers",
    marker: { size: 8, color: opts.color || C.bar, opacity: 0.85 },
    hovertemplate: "%{text}<br>%{xaxis.title.text}: %{x:.1f}<br>%{yaxis.title.text}: %{y:.1f}<extra></extra>",
  }];
  const fit = olsLine(xs, ys);
  if (fit) {
    traces.push({
      name: "Trend",
      x: fit.x,
      y: fit.y,
      type: "scatter",
      mode: "lines",
      line: { color: C.orange, width: 1.8, dash: "dash" },
      hoverinfo: "skip",
    });
  }
  const shapes = [];
  if (opts.xGoal != null) shapes.push({ type: "line", x0: opts.xGoal, x1: opts.xGoal, y0: 0, y1: 1, yref: "paper", line: { color: C.grey, dash: "dot", width: 1 } });
  if (opts.yGoal != null) shapes.push({ type: "line", y0: opts.yGoal, y1: opts.yGoal, x0: 0, x1: 1, xref: "paper", line: { color: C.grey, dash: "dot", width: 1 } });
  plot(id, traces, {
    noAnim: true,
    xaxis: { title: opts.xTitle || xKey, rangemode: "normal" },
    yaxis: { title: opts.yTitle || yKey, rangemode: "normal" },
    shapes,
    margin: { t: 28, r: 16, b: 52, l: 52 },
    showlegend: false,
  });
}
function corrBars(id, rows) {
  const pairs = (rows || [])
    .map((r) => ({ l: r.Pair || r.Slice || "", v: Number(r.R2 != null ? r.R2 : r.Pearson_r) || 0 }))
    .filter((p) => p.l);
  if (!pairs.length) {
    emptyPlot(id, "No association rows in this filter.");
    return;
  }
  miniHbar(id, pairs.map((p) => p.l), pairs.map((p) => Math.abs(p.v)), C.navy);
}
function rcChannelCombo(id, rows, goal) {
  const ch = (rows || []).filter((r) => r.Channel && !String(r.Channel).startsWith("All 12"));
  const el = document.getElementById(id);
  if (!el) return;
  if (!ch.length) {
    emptyPlot(id, "No recontact rows in this filter.");
    return;
  }
  const labels = ch.map((r) => r.Channel);
  const contacts = ch.map((r) => Number(r.Contacts) || 0);
  const repeats = ch.map((r) => Number(r.Repeats) || 0);
  const rates = ch.map((r) => Number(first(r, "Rate %", "Rate", "Recontact_Rate")) || 0);
  const g = Number(goal) || 5.44;
  const rateMax = Math.max(g, ...rates, 1);
  plot(id, [
    { name: "Contacts", x: labels, y: contacts, type: "bar", marker: { color: C.bar }, hovertemplate: "%{x}<br>Contacts %{y:,}<extra></extra>" },
    { name: "Repeats", x: labels, y: repeats, type: "bar", marker: { color: C.rcLine }, hovertemplate: "%{x}<br>Repeats %{y:,}<extra></extra>" },
    { name: "Rate %", x: labels, y: rates, type: "scatter", mode: "lines+markers", yaxis: "y2", line: { color: C.orange, width: 2.6 }, marker: { size: 8, color: C.orange }, hovertemplate: "%{x}<br>Rate %{y:.2f}%<extra></extra>" },
    { name: "Goal 5.44", x: labels, y: labels.map(() => g), type: "scatter", mode: "lines", yaxis: "y2", line: { color: C.grey, width: 1.5, dash: "dash" }, hovertemplate: "Goal %{y:.2f}%<extra></extra>" },
  ], {
    noAnim: true,
    barmode: "group",
    yaxis: { title: "Volume", rangemode: "tozero" },
    yaxis2: { title: "Rate %", overlaying: "y", side: "right", rangemode: "tozero", range: [0, rateMax * 1.25], ticksuffix: "%" },
    xaxis: { tickangle: -28, tickfont: { size: 10 } },
    legend: { orientation: "h", y: 1.16 },
    margin: { t: 40, r: 56, b: 88, l: 56 },
    bargap: 0.28,
  });
}
function channelKpiCombo(id, rows, goals) {
  const ch = (rows || []).filter((r) => {
    const n = String(r.Segment || r.Channel || "");
    return n && n !== "Overall";
  });
  if (!ch.length) {
    emptyPlot(id, "No channel rows in this filter.");
    return;
  }
  const labels = ch.map((r) => r.Segment || r.Channel);
  plot(id, [
    { name: "QA", x: labels, y: ch.map((r) => r.QA_Score), type: "bar", marker: { color: C.green } },
    { name: "CSAT", x: labels, y: ch.map((r) => r.CSAT_Score), type: "bar", marker: { color: C.orange } },
    { name: "Recontact", x: labels, y: ch.map((r) => r.Recontact_Rate), type: "scatter", mode: "lines+markers", yaxis: "y2", line: { color: C.rcLine, width: 2.4 } },
  ], {
    noAnim: true,
    barmode: "group",
    yaxis: { title: "QA / CSAT %", range: scoreRange([...(ch.map((r) => r.QA_Score)), ...(ch.map((r) => r.CSAT_Score)), goals && goals.qa, goals && goals.csat].filter((v) => v != null)) },
    yaxis2: { title: "Recontact %", overlaying: "y", side: "right", rangemode: "tozero" },
    margin: { t: 36, r: 48, b: 48, l: 48 },
  });
}
function marketBoxes(rows) {
  if (!rows || !rows.length) return `<p class="hint">No market rows in this slice.</p>`;
  return `<div class="markets">${rows.map((r) => `
    <div class="mkt-box">
      <b>${r.Country_Name || r.Country || "—"}</b>
      <span>QA ${num(r.QA_Score)} · n ${int(r.QA_N || 0)}</span>
      <span>CSAT ${pct(r.CSAT_Score)} · n ${int(r.CSAT_N || r.Feedback || 0)}</span>
    </div>`).join("")}</div>`;
}
function bandsHtml(bands) {
  const b = (bands && bands.bands) || {};
  return `<div class="quad-bands">${["Q1", "Q2", "Q3", "Q4"].map((q) => {
    const x = b[q] || {};
    const q4 = q === "Q4";
    return `<div class="mkt-box${q4 ? " q4" : ""}"><b>${q} · ${int(x.n || 0)}${q4 ? " · watch" : ""}</b><span>${x.mean == null ? "—" : num(x.mean, 1)} mean</span><span>${(x.names || []).slice(0, 3).join(", ") || "—"}</span></div>`;
  }).join("")}</div>`;
}
function ahtCombo(id, rows, nameKey) {
  combo(id, rows.map((r) => r[nameKey] || r.CR_Lv4 || r.CR_Lv1 || r.SUB_CR || ""), rows.map((r) => r.QA_Score), rows.map((r) => r.AHT_min), "QA", "AHT min");
}

function hero(data) {
  const k = data.kpis;
  const g = data.goals;
  return `<div class="row row-4">
    ${kpiRing({ title: "QA Score", value: k.qa, goal: g.qa, higher: true, fmt: (v) => num(v, 2), ncap: `n = ${int(first(k, "qa_n", "evaluations"))} evals · mean of Score_Pct`, kind: "num" })}
    ${kpiRing({ title: "CSAT", value: k.csat, goal: g.csat, higher: true, fmt: pct, ncap: `CSAT N = ${int(first(k, "csat_n", "surveys"))} surveys · (4★+5★) / Feedback CNT`, kind: "pct" })}
    ${kpiRing({ title: "Recontact", value: k.recontact, goal: g.recontact, higher: false, fmt: pct, ncap: `Recontact over ${int(first(k, "recontact_n", "contacts"))} contacts · Σ repeats / Σ contacts`, kind: "pct" })}
    <article class="card">
      <h2>Volume</h2>
      <div class="vol-list">
        <div class="vol-row"><div class="vol-ico">☎</div><div><b data-tween="${first(k, "contacts", "contacts") || 0}" data-kind="int">0</b><span>Customer contacts</span></div></div>
        <div class="vol-row"><div class="vol-ico">★</div><div><b data-tween="${first(k, "surveys", "csat_n") || 0}" data-kind="int">0</b><span>CSAT surveys</span></div></div>
        <div class="vol-row"><div class="vol-ico">✓</div><div><b data-tween="${first(k, "evaluations", "qa_n") || 0}" data-kind="int">0</b><span>QA audits</span></div></div>
      </div>
      <p class="hint foot-n">Same denominators as the official scorecard. Phone 12 attrs / Live Chat 8 are never mixed.</p>
    </article>
  </div>
  ${heroNote(data)}`;
}

function opsMinis(data) {
  const o = data.overview || {};
  const k = data.kpis;
  const g = data.goals;
  const crit = o.crit || {};
  const res = o.resolution || {};
  const nCrit = Number(first(crit, "n_crit_fails") || 0);
  const nNon = Number(first(crit, "n_noncrit_fails") || 0);
  const tQa = toneGoal(k.qa, g.qa, true);
  const tCs = toneGoal(k.csat, g.csat, true);
  const tRc = toneGoal(k.recontact, g.recontact, false);
  const tCrit = toneFail(nCrit, true);
  const rate = first(res, "rate");
  const tRes = rate == null
    ? { tone: "neutral", tag: "", pill: "" }
    : rate >= 70
      ? { tone: "green", tag: "Majority resolved", pill: "" }
      : { tone: "amber", tag: "Majority not resolved", pill: "" };
  const nProc = Number(first(res, "n_unres_process") || 0);
  const nAgt = Number(first(res, "n_unres_agent") || 0);
  const nAb = Number(first(res, "n_abandoned") || 0);
  const aht = first(o.aht, "aht_min");
  const stars = o.stars || {};
  const hi = Number(stars.hi || 0);
  const lo = Number(stars.lo || 0);
  const starN = Number(stars.n || k.surveys || 0);
  const lv1 = (o.cr_lv1 || [])[0] || {};
  const lv4 = (o.cr_lv4 || [])[0] || {};
  const sub = o.top_sub || {};
  const pc = o.phone_chat || {};
  return `<div class="ops-grid">
    ${miniCol("Quality", [
      opsCard({ id: "ops-qa", title: "QA Score", value: k.qa, kind: "num", d: 2, ...tQa, cap: `Daily mean of Score_Pct · n = ${nEvals(data)} evals` }),
      opsCard({ id: "ops-csat", title: "CSAT Score", value: k.csat, kind: "pct", d: 2, ...tCs, cap: "Daily (4★+5★) / Feedback CNT" }),
      opsCard({ id: "ops-failmix", title: "Critical vs non-critical fails", value: nCrit + nNon, ...tCrit, cap: nCrit + nNon ? `Donut · ${int(nCrit)} critical · ${int(nNon)} non-critical` : "No attribute-fail events in this filter" }),
      opsCard({ id: "ops-res", title: "Auditor resolution", value: rate, kind: "pct", d: 1, ...tRes, cap: "Donut · resolved vs not · auditor close, not FCR" }),
      opsCard({ title: "AHT (min)", id: "ops-aht", value: aht, kind: "num", d: 1, tag: "Handle time", cap: first(o.aht, "aht_p50_min") != null ? `Mean vs median · median ${num(first(o.aht, "aht_p50_min"), 1)} min` : "Mean vs median minutes on audited calls" }),
    ])}
    ${miniCol("Volumes", [
      opsCard({ id: "ops-contacts", title: "Total contacts", value: first(k, "contacts"), tag: "Volume", cap: "Bars · customer contacts over time" }),
      opsCard({ id: "ops-surveys", title: "Surveys", value: first(k, "surveys", "csat_n"), tag: "Volume", cap: "Bars · Feedback CNT over time" }),
      opsCard({ id: "ops-audits", title: "QA evaluations", value: first(k, "evaluations", "qa_n"), tag: "Volume", cap: "Bars · audits over time" }),
      opsCard({ id: "ops-repeats", title: "Recontact volume", value: first(k, "recontacts"), tag: "Volume", cap: "Bars · Σ Recontact Volume (numerator)" }),
      opsCard({ id: "ops-abandon", title: "Abandoned", value: nAb, tone: nAb ? "amber" : "green", tag: nAb ? "Watch" : "On goal", cap: "Donut · abandoned vs not, of the audited sample" }),
    ])}
    ${miniCol("Recontact & sentiment", [
      opsCard({ id: "ops-rc", title: "Recontact Rate", value: k.recontact, kind: "pct", d: 2, ...tRc, cap: `Daily line · Σ repeats / Σ contacts · goal ≤ ${pct(g.recontact)}` }),
      `<div class="ops-pair">
        ${opsCard({ id: "ops-stars-hi", title: "4–5★ surveys", value: hi, tone: "green", tag: "Satisfied", cap: starN ? `Donut of 4★+5★ · ${num((hi / starN) * 100, 1)}% of surveys` : "Donut of 4★ and 5★ ratings" })}
        ${opsCard({ id: "ops-stars-lo", title: "1–3★ surveys", value: lo, tone: lo ? "amber" : "green", tag: lo ? "Watch · 1–3★" : "On goal", cap: starN ? `Donut of 1–3★ · ${num((lo / starN) * 100, 1)}% of surveys` : "Donut of 1–3★ ratings" })}
      </div>`,
      `<div class="ops-pair">
        ${opsCard({ id: "ops-cr1", title: "Contact reason Lv1", value: lv1.Contacts, tag: "Top driver", cap: lv1.CR_Lv1 ? `Bars · top CR Lv1 · ${lv1.CR_Lv1} ${num(lv1.Pct, 1)}% of contacts` : "Bars · top CR Lv1 by contacts" })}
        ${opsCard({ id: "ops-cr4", title: "Contact reason Lv4", value: lv4.Contacts, tag: "Top driver", cap: lv4.CR_Lv4 ? `Bars · top CR Lv4 · ${lv4.CR_Lv4} ${num(lv4.Pct, 1)}% of contacts` : "Bars · top CR Lv4 by contacts" })}
      </div>`,
      opsCard({ id: "ops-pc", title: "Phone vs Live Chat", value: pc.n, tag: "Volume", cap: (pc.names || []).length ? `Donut · ${(pc.names || []).map((n, i) => `${n} ${int((pc.vals || [])[i] || 0)}`).join(" · ")}` : "Donut · Phone and Live Chat contacts" }),
      opsCard({ id: "ops-unres", title: "Unresolved owners", value: nProc + nAgt, tone: (nProc + nAgt) ? "amber" : "green", tag: (nProc + nAgt) ? "Watch" : "On goal", cap: `Donut · process ${int(nProc)} vs agent ${int(nAgt)}` }),
      opsCard({ id: "ops-subcr", title: "Contact reason SUB_CR", value: sub.n, tag: "Top driver", cap: sub.name ? `Bars · top SUB_CR · ${sub.name} ${num(sub.pct, 1)}% of surveys` : "Bars · top SUB_CR by surveys" }),
    ])}
  </div>`;
}
function paintOps(data) {
  const o = data.overview || {};
  const k = data.kpis;
  const weekly = o.weekly || [];
  const daily = o.daily || o.csat_daily || [];
  const volumes = o.volumes || {};
  const crit = o.crit || {};
  const res = o.resolution || {};
  const nCrit = Number(first(crit, "n_crit_fails") || 0);
  const nNon = Number(first(crit, "n_noncrit_fails") || 0);
  const nAb = Number(first(res, "n_abandoned") || 0);
  const nAud = Number(first(k, "evaluations", "qa_n") || 0);
  miniLine("ops-qa", pickTrend(daily, weekly, ["QA_Score"]), C.green);
  miniLine("ops-csat", pickTrend(daily, o.csat_daily || weekly, ["CSAT_Score", "CSAT", "Value"]), C.csatLine);
  miniDonut("ops-failmix", ["Critical", "Non-critical"], [nCrit, nNon], [C.red, C.navy], int(nCrit + nNon));
  miniCompose("ops-res", ["Resolved", "Not resolved"], [Number(first(res, "n_resolved") || 0), Number(first(res, "n_not_resolved") || 0)], [C.green, C.gold], first(res, "rate") != null ? pct(first(res, "rate"), 1) : int(Number(first(res, "n_resolved") || 0)));
  const wkVol = (key) => xyOf(weekly, [key], ["Week", "Date"]);
  miniBars("ops-contacts", volOf(volumes, "contacts").y.length ? volOf(volumes, "contacts") : wkVol("Contacts"), C.bar);
  miniBars("ops-surveys", volOf(volumes, "surveys").y.length ? volOf(volumes, "surveys") : wkVol("Surveys"), C.bar);
  miniBars("ops-audits", volOf(volumes, "evals").y.length ? volOf(volumes, "evals") : wkVol("Audit_Count"), C.bar);
  miniBars("ops-repeats", volOf(volumes, "recontacts").y.length ? volOf(volumes, "recontacts") : wkVol("Recontacts"), C.rcLine);
  if (nAud > 0) miniDonut("ops-abandon", ["Abandoned", "Not abandoned"], [nAb, Math.max(0, nAud - nAb)], [C.gold, C.navy], int(nAb));
  else emptyPlot("ops-abandon", "No audits in this filter.");
  miniLine("ops-rc", pickTrend(daily, weekly, ["Recontact_Rate"]), C.rcLine, { toZero: true });
  const st = (o.stars || {}).rows || [];
  const hiRows = starSlice(st, true);
  const loRows = starSlice(st, false);
  miniDonut("ops-stars-hi", hiRows.map((r) => r.Rating), hiRows.map((r) => r.Count), [C.bar, C.green], int((o.stars || {}).hi || 0));
  miniDonut("ops-stars-lo", loRows.map((r) => r.Rating), loRows.map((r) => r.Count), [C.gold, "#E07A3D", C.red], int((o.stars || {}).lo || 0));
  const lv1 = o.cr_lv1 || [];
  const lv4 = o.cr_lv4 || [];
  miniHbar("ops-cr1", lv1.map((r) => r.CR_Lv1), lv1.map((r) => r.Contacts), C.bar);
  miniHbar("ops-cr4", lv4.map((r) => r.CR_Lv4), lv4.map((r) => r.Contacts), C.bar);
  const pc = o.phone_chat || {};
  miniDonut("ops-pc", pc.names || [], pc.vals || [], [C.phone, C.chat], int(pc.n || 0));
  miniCompose("ops-unres", ["Process", "Agent"], [Number(first(res, "n_unres_process") || 0), Number(first(res, "n_unres_agent") || 0)], [C.gold, C.navy], int(Number(first(res, "n_unres_process") || 0) + Number(first(res, "n_unres_agent") || 0)));
  const subBars = (o.subcr || {}).bars || [];
  miniHbar("ops-subcr", subBars.map((r) => first(r, "Cat", "SUB_CR", "Reason")), subBars.map((r) => Number(first(r, "Feedback", "n", "Count")) || 0), C.bar);
  const ahtMean = Number(first(o.aht, "aht_min"));
  const ahtMed = Number(first(o.aht, "aht_p50_min"));
  if (Number.isFinite(ahtMean) || Number.isFinite(ahtMed)) {
    miniHbar("ops-aht", ["Mean", "Median"], [ahtMean || 0, ahtMed || 0], C.navy);
  } else emptyPlot("ops-aht", "No handle time in this filter.");
}

function renderOverview(data) {
  const o = data.overview || {};
  const k = data.kpis;
  const g = data.goals;
  const ag = o.agents || {};
  const fail = o.failing || [];
  const rc = o.rc_reasons || o.cr_lv4 || [];
  const lob = o.qa_by_lob || [];
  const corr = o.corr || {};
  document.getElementById("view").innerHTML = `
    ${hero(data)}
    ${opsMinis(data)}
    <div class="row row-2">
      ${card("Americas map — QA / CSAT by market", `<div class="chart map" id="ov-map"></div>`, `Fill is QA where the market was audited, CSAT for CSAT-only markets (DO, PA). N = ${int((o.by_market || []).length)} markets. Recontact has no market field (SSL mix).`)}
      ${card("Market scorecards", marketBoxes(o.by_market), `Same slice as the map. n per box is audits / surveys. Recontact is always SSL.`)}
    </div>
    ${card("QA and CSAT by market", `<div class="chart" id="mkt-chart"></div>`, `n = ${nEvals(data)} evals · CSAT N = ${nSurveys(data)} surveys. Recontact is not split by market.`)}
    <div class="row row-3">
      ${card("Weekly trend by metric", `<div class="chart" id="wk-chart"></div>`, `QA / CSAT on the left axis, recontact on the right. n = ${nEvals(data)} evals · CSAT N = ${nSurveys(data)} surveys · Recontact over ${nContacts(data)} contacts · ${weekSpan(data)}.`)}
      ${card("QA score by channel", `<div class="ch-split"><div class="chart sm" id="qa-ch"></div><div class="legend" id="qa-ch-leg"></div></div>`, `Phone 12 attrs / Live Chat 8. n = ${nEvals(data)} evals. Channels are scored separately and never mixed.`)}
      ${card("CSAT by channel", `<div class="ch-split"><div class="chart sm" id="cs-ch"></div><div class="legend" id="cs-ch-leg"></div></div>`, `CSAT N = ${nSurveys(data)} surveys · (4★+5★) / Feedback CNT.`)}
    </div>
    ${card("Contacts, repeats, and rate by channel", `<div class="chart combo" id="ov-rc-ch"></div>`, `N = ${nContacts(data)} contacts. Rate is Σ repeats / Σ contacts (ratio of sums), not an average of the Rate % column. Self Help dwarfs other channels in volume.`)}
    ${card("QA, CSAT and recontact by channel", `<div class="chart" id="ov-ch-kpi"></div>`, `Phone and Live Chat only. Official QA is the mean of Score_Pct. CSAT is (4★+5★) / Feedback CNT.`)}
    <div class="row row-bars">
      ${card("Pareto · contact reasons (recontact)", paretoBox("rc-bar"), `Bars ranked descending by repeats. Line = cumulative %; gold dash = 80% vital few. Recontact over ${nContacts(data)} contacts · Σ repeats / Σ contacts. Market filter does not cut recontact.`)}
      ${card("QA score by business type", `<div class="chart sm" id="lob-bar"></div>`, `n = ${nEvals(data)} evals. Official QA is the mean of Score_Pct. Dashed line is the ${g.qa} goal.`)}
      ${card("Agent performance summary", `
        <div class="quad">
          <div class="stat"><span>Agents evaluated</span><b data-tween="${ag.n || k.agents || 0}" data-kind="int">0</b></div>
          <div class="stat"><span>Avg QA score</span><b ${ag.avg_qa == null ? "" : `data-tween="${ag.avg_qa}" data-kind="num" data-d="2"`}>${ag.avg_qa == null ? "—" : "0"}</b></div>
          <div class="stat"><span>Bottom 10% avg</span><b ${ag.bottom10_avg == null ? "" : `data-tween="${ag.bottom10_avg}" data-kind="num" data-d="2"`}>${ag.bottom10_avg == null ? "—" : "0"}</b></div>
          <div class="stat"><span>Agents &lt; 5 audits</span><b data-tween="${ag.thin_n || 0}" data-kind="int">0</b></div>
        </div>
        <button type="button" class="linkish" id="go-agents">View agent performance →</button>`, `Reliable agents only (n ≥ 5). ${int(ag.thin_n || 0)} under the floor in this slice.`)}
    </div>
    <div class="row row-2">
      ${card("Pareto · QA failing attributes", paretoBox("fail-bar"), `Bars count attribute-fail events (one audit can contribute more than one). Ranked descending; line = cumulative % of all fails; gold dash = 80% vital few. n = ${nEvals(data)} evals.`)}
      ${card("Fail mix · top attributes", `<div class="chart sm" id="fail-mix"></div>${table(fail.slice(0, 6), [
        { key: "Error_Category", label: "Attribute" },
        { key: "Fail_Count", label: "Fails", fmt: "int" },
      ])}`, `Critical vs non-critical share of the same fail events as the Pareto. n = ${nEvals(data)} evals.`)}
    </div>
    ${downloadBar()}
    <div class="row row-3">
      ${card("Star mix", `<div class="chart sm" id="ov-stars"></div>`, `${int((o.stars || {}).hi || 0)} of 4–5★ · ${int((o.stars || {}).lo || 0)} of 1–3★ · CSAT N = ${nSurveys(data)} surveys.`)}
      ${card("Phone vs Live Chat contacts", `<div class="chart sm" id="ov-pc"></div>`, `Phone and Live Chat contacts only — not the 12-channel mix. Recontact over ${nContacts(data)} contacts.`)}
      ${card("Top SUB_CR", `<p class="hint">${(o.top_sub && o.top_sub.name) || "—"} · ${int((o.top_sub && o.top_sub.n) || 0)} surveys (${(o.top_sub && o.top_sub.pct) != null ? num(o.top_sub.pct, 1) + "%" : "—"})</p>`, `Finest contact reason on CSAT. Official N = ${nSurveys(data)} surveys.`)}
    </div>
    <div class="row row-2">
      ${card("QA / CSAT / recontact by day", `<div class="chart" id="ov-daily"></div>`, `${weekSpan(data)}. QA uses audit date; CSAT and recontact use their own calendar.`)}
      ${card("QA score histogram", `<div class="chart" id="ov-hist"></div>`, `${int((o.crit || {}).n_fatal || 0)} audits scored 0 · N = ${nEvals(data)} evals.`)}
    </div>
    <div class="row row-3">
      ${card("Correlation · QA vs CSAT", `<div class="chart" id="ov-sc-qacs"></div>`, `Each point is a contact reason Lv4 (detail) with both official QA and CSAT. Trend is OLS. n = ${int((corr.cr || []).length)} reasons.`)}
      ${card("Correlation · QA vs AHT", `<div class="chart" id="ov-sc-qaaht"></div>`, `Handle time vs official QA at Lv4. Phone calls are longer by nature — read channel color, not only the pooled cloud.`)}
      ${card("Association R²", `<div class="chart sm" id="ov-r2"></div>`, `R² at contact reason Lv4 (detail). Association only — not a causal claim.`)}
    </div>
    <div class="row row-2">
      ${card("Contact volume · CR Lv1", `<div class="chart" id="ov-lv1"></div>`, `Bars are contacts. Line is Σ repeats / Σ contacts at Lv1 (ratio of sums). Recontact over ${nContacts(data)} contacts.`)}
      ${card("Contact volume · CR Lv4", `<div class="chart" id="ov-lv4"></div>`, `Top reasons by volume. Line is Σ repeats / Σ contacts at Lv4, not an average of row rates.`)}
    </div>
    ${card("Taxonomy coverage", `<div class="chart" id="tax-chart"></div>`, `Share of CSAT surveys that still land in Other / Not mapped at each grain. CSAT N = ${nSurveys(data)} surveys.`)}
    ${card("Pareto · contact reasons (SUB_CR)", paretoBox("subcr-chart"), `Official N = ${int((o.subcr || {}).official_n || k.surveys)} surveys. Bars are the 10 largest SUB_CR reasons; remaining volume stays in N and the cumulative %. Line = cumulative %; gold dash = 80% vital few. If SUB_CR is Other, the bar uses the parent Lv4.`)}
    <div class="row row-2">
      ${card("Supervisor QA impact", table((o.supervisors || []).slice(0, 10), [
        { key: "Supervisor_ID", label: "Supervisor" },
        { key: "QA_Score", label: "QA", fmt: "num", d: 1, goal: g.qa, higher: true },
        { key: "n", label: "Audits", fmt: "int" },
        { key: "QA_Impact", label: "QA impact", fmt: "num", d: 0 },
      ]), `Rows are gap × audits (how far below ${g.qa}, weighted by sample). n = ${nEvals(data)} evals.`)}
      ${card("Supervisor CSAT impact", table([...(o.supervisors || [])].sort((a, b) => (b.CSAT_Impact || 0) - (a.CSAT_Impact || 0)).slice(0, 10), [
        { key: "Supervisor_ID", label: "Supervisor" },
        { key: "CSAT_Score", label: "CSAT", fmt: "pct", goal: g.csat, higher: true },
        { key: "Feedback", label: "Surveys", fmt: "int" },
        { key: "CSAT_Impact", label: "CSAT impact", fmt: "num", d: 0 },
      ]), `Official CSAT is (4★+5★) / Feedback CNT. CSAT N = ${nSurveys(data)} surveys.`)}
    </div>
    <div class="row row-3">
      ${card("QA + AHT · CR Lv1", `<div class="chart" id="ov-aht1"></div>`, `AHT on audited calls. n = ${nEvals(data)} evals. Coach the channel, not the pooled All bar.`)}
      ${card("QA + AHT · CR Lv4", `<div class="chart" id="ov-aht4"></div>`, `AHT vs official QA (mean of Score_Pct) at contact reason Lv4.`)}
      ${card("QA + AHT · SUB_CR", `<div class="chart" id="ov-ahts"></div>`, `Finest contact reason on QA (auditor-corrected SUB_CR).`)}
    </div>
  `;
  const go = document.getElementById("go-agents");
  if (go) go.onclick = () => { state.page = "alerts"; load(); };
  bindDownload();
  paintOps(data);
  americasMap("ov-map", o.by_market || []);
  const mk = o.by_market || [];
  plot("mkt-chart", [
    { name: "QA", x: mk.map((r) => r.Country_Name || r.Country), y: mk.map((r) => r.QA_Score), type: "bar", marker: { color: C.green } },
    { name: "CSAT", x: mk.map((r) => r.Country_Name || r.Country), y: mk.map((r) => r.CSAT_Score), type: "bar", marker: { color: C.orange } },
  ], { noAnim: true, barmode: "group" });
  const wk = o.weekly || [];
  const wkScores = wk.flatMap((r) => [r.QA_Score, r.CSAT_Score]).filter((v) => v != null);
  plot("wk-chart", [
    { name: "QA", x: wk.map((r) => weekLabel(r.Week)), y: wk.map((r) => r.QA_Score), type: "scatter", mode: "lines+markers", line: { color: C.green, width: 3 } },
    { name: "CSAT", x: wk.map((r) => weekLabel(r.Week)), y: wk.map((r) => r.CSAT_Score), type: "scatter", mode: "lines+markers", line: { color: C.orange, width: 3 } },
    { name: "Recontact", x: wk.map((r) => weekLabel(r.Week)), y: wk.map((r) => r.Recontact_Rate), type: "scatter", mode: "lines+markers", yaxis: "y2", line: { color: C.gold, width: 3 } },
  ], { noAnim: true, yaxis: { title: "QA / CSAT %", range: scoreRange([...wkScores, g.qa, g.csat]) }, yaxis2: { title: "Recontact %", overlaying: "y", side: "right", rangemode: "tozero" } });
  const phone = chRow(o.by_channel, "Phone");
  const chat = chRow(o.by_channel, "Live Chat");
  const labels = ["Live Chat", "Phone"];
  const qaN = [Number(chat?.QA_N) || 0, Number(phone?.QA_N) || 0];
  const csN = [Number(chat?.CSAT_N) || Number(chat?.QA_N) || 0, Number(phone?.CSAT_N) || Number(phone?.QA_N) || 0];
  donut("qa-ch", labels, qaN.map((v) => v || 0.01), [C.chat, C.phone], `${num(k.qa)}<br>Overall`);
  donut("cs-ch", labels, csN.map((v) => v || 0.01), [C.chat, C.phone], `${num(k.csat)}%<br>Overall`);
  const qaLeg = document.getElementById("qa-ch-leg");
  const csLeg = document.getElementById("cs-ch-leg");
  if (qaLeg) {
    qaLeg.innerHTML = `<div><b>Live Chat ${num(chat?.QA_Score)}</b> ${chat ? pp((chat.QA_Score || 0) - g.qa) : ""} vs ${g.qa} goal</div>
      <div><b>Phone ${num(phone?.QA_Score)}</b> ${phone ? pp((phone.QA_Score || 0) - g.qa) : ""} vs ${g.qa} goal</div>`;
  }
  if (csLeg) {
    csLeg.innerHTML = `<div><b>Live Chat ${pct(chat?.CSAT_Score)}</b> ${chat && chat.CSAT_Score != null ? pp(chat.CSAT_Score - g.csat) : ""} vs ${g.csat}% goal</div>
      <div><b>Phone ${pct(phone?.CSAT_Score)}</b> ${phone && phone.CSAT_Score != null ? pp(phone.CSAT_Score - g.csat) : ""} vs ${g.csat}% goal</div>`;
  }
  rcChannelCombo("ov-rc-ch", o.channels || [], g.recontact);
  channelKpiCombo("ov-ch-kpi", o.by_channel || [], g);
  pareto("rc-bar", rc, ["CR_Lv4", "CR_Lv1", "Cat"], ["Recontacts", "Contacts", "Count"], { valueTitle: "Repeats", unit: "repeats" });
  pareto("fail-bar", fail, ["Error_Category", "Attr", "Cat"], ["Fail_Count", "Count", "n"], { valueTitle: "Fails", unit: "attribute fails", nAudits: first(data.kpis, "evaluations", "qa_n") });
  miniDonut("fail-mix", ["Critical", "Non-critical"], [
    Number(first(o.crit, "n_crit_fails") || 0),
    Number(first(o.crit, "n_noncrit_fails") || 0),
  ], [C.red, C.navy], int(Number(first(o.crit, "n_crit_fails") || 0) + Number(first(o.crit, "n_noncrit_fails") || 0)));
  plot("lob-bar", [{ type: "bar", orientation: "h", y: lob.map((r) => r.LOB).reverse(), x: lob.map((r) => r.QA_Score).reverse(), marker: { color: C.green } }], {
    noAnim: true,
    margin: { t: 8, r: 16, b: 24, l: 90 },
    shapes: [{ type: "line", x0: g.qa, x1: g.qa, y0: -0.5, y1: Math.max(lob.length - 0.5, 0.5), line: { color: C.ink, dash: "dash", width: 1 } }],
    xaxis: { range: scoreRange([...(lob.map((r) => r.QA_Score)), g.qa]) },
  });
  const tax = o.taxonomy || [];
  plot("tax-chart", [
    { name: "Classified %", x: tax.map((r) => r.Level), y: tax.map((r) => r.Classified_Pct), type: "bar", marker: { color: C.green } },
    { name: "Other %", x: tax.map((r) => r.Level), y: tax.map((r) => r.Other_Pct), type: "bar", marker: { color: C.gold } },
  ], { noAnim: true, barmode: "group" });
  const bars = (o.subcr || {}).bars || [];
  pareto("subcr-chart", bars, ["Cat", "SUB_CR", "Reason"], ["Feedback", "n", "Count"], { valueTitle: "Surveys" });
  const st = (o.stars || {}).rows || [];
  if (st.length) donut("ov-stars", st.map((r) => r.Rating), st.map((r) => r.Count), [C.green, "#7BC47F", C.gold, "#E07A3D", C.red], `${int((o.stars || {}).n || k.surveys)}`);
  const pc = o.phone_chat || {};
  if ((pc.names || []).length) donut("ov-pc", pc.names, pc.vals, [C.phone, C.chat], int(pc.n || 0));
  const daily = o.daily || [];
  plot("ov-daily", [
    { name: "QA", x: daily.map((r) => r.Date), y: daily.map((r) => r.QA_Score), type: "scatter", mode: "lines+markers", line: { color: C.green, width: 2 } },
    { name: "CSAT", x: daily.map((r) => r.Date), y: daily.map((r) => r.CSAT_Score), type: "scatter", mode: "lines+markers", line: { color: C.orange, width: 2 } },
    { name: "Recontact", x: daily.map((r) => r.Date), y: daily.map((r) => r.Recontact_Rate), type: "scatter", mode: "lines+markers", yaxis: "y2", line: { color: C.gold, width: 2 } },
  ], { noAnim: true, yaxis: { range: scoreRange(daily.map((r) => r.QA_Score).concat(daily.map((r) => r.CSAT_Score))) }, yaxis2: { overlaying: "y", side: "right", title: "Recontact %" } });
  const hist = o.hist_qa || {};
  plot("ov-hist", [{ x: hist.x || [], y: hist.y || [], type: "bar", marker: { color: C.green } }], { noAnim: true });
  scatterXY("ov-sc-qacs", corr.cr || [], "QA_Score", "CSAT_Pct", { xTitle: "QA Score %", yTitle: "CSAT %", xGoal: g.qa, yGoal: g.csat });
  scatterXY("ov-sc-qaaht", corr.aht || [], "AHT_min", "QA_Score", { xTitle: "AHT (minutes)", yTitle: "QA Score %", yGoal: g.qa, color: C.green });
  corrBars("ov-r2", corr.corr || []);
  const lv1 = o.cr_lv1 || [];
  combo("ov-lv1", lv1.map((r) => r.CR_Lv1), lv1.map((r) => r.Contacts), lv1.map(rcRate), "Contacts", "Recontact %");
  const lv4 = o.cr_lv4 || [];
  combo("ov-lv4", lv4.map((r) => r.CR_Lv4), lv4.map((r) => r.Contacts), lv4.map(rcRate), "Contacts", "Recontact %");
  ahtCombo("ov-aht1", o.aht_lv1 || [], "CR_Lv1");
  ahtCombo("ov-aht4", o.aht_lv4 || [], "CR_Lv4");
  ahtCombo("ov-ahts", o.aht_sub || [], "SUB_CR");
}
function renderQa(data) {
  const q = data.qa || {};
  const k = data.kpis;
  const g = data.goals;
  const corr = q.corr || {};
  const tQa = toneGoal(k.qa, g.qa, true);
  document.getElementById("view").innerHTML = `
    ${hero(data)}
    <div class="mini">
      ${miniTile({ label: "QA", value: k.qa, kind: "num", d: 2, ...tQa, cap: `Goal ${num(g.qa)}` })}
      ${miniTile({ label: "Audits", value: k.qa_n, tag: "Volume" })}
      ${miniTile({ label: "Fatal %", value: k.fatal, kind: "pct", d: 2, ...(k.fatal ? { tone: "red", tag: "Off goal" } : { tone: "green", tag: "On goal" }) })}
      ${miniTile({ label: "Critical fails", value: q.crit?.n_crit_fails || 0, ...toneFail(q.crit?.n_crit_fails, true) })}
      ${miniTile({ label: "AHT min", value: q.aht?.aht_min, kind: "num", d: 1, tag: "Handle time" })}
      ${miniTile({ label: "Resolution", value: q.resolution?.rate, kind: "pct", d: 1, tag: q.resolution?.rate >= 70 ? "Majority resolved" : "Majority not resolved", tone: q.resolution?.rate >= 70 ? "green" : "amber" })}
    </div>
    <div class="row row-2">
      ${card("QA by week", `<div class="chart" id="qa-week"></div>`, `n = ${nEvals(data)} evals · ${weekSpan(data)}. Official QA is the mean of Score_Pct.`)}
      ${card("QA histogram", `<div class="chart" id="qa-hist"></div>`, `${int(q.crit?.n_fatal || 0)} audits scored 0 · N = ${nEvals(data)} evals.`)}
    </div>
    ${card("QA by day (I-chart)", `<div class="trend-frame"><div class="chart ichart" id="qa-ctrl"></div></div>`, `Daily mean of Score_Pct vs control limits and the ${g.qa} goal. n = ${nEvals(data)} evals.`)}
    <div class="row row-3">
      ${card("Correlation · QA vs CSAT", `<div class="chart" id="qa-sc-csat"></div>`, `Each point is a contact reason Lv4 (detail). Official QA vs official CSAT.`)}
      ${card("Correlation · QA vs AHT", `<div class="chart" id="qa-sc-aht"></div>`, `Handle time vs official QA at Lv4.`)}
      ${card("Association R²", `<div class="chart sm" id="qa-r2"></div>`, `R² at contact reason Lv4. Association only.`)}
    </div>
    ${card("QA, CSAT and recontact by channel", `<div class="chart" id="qa-ch-kpi"></div>`, `Phone 12 attrs / Live Chat 8. n = ${nEvals(data)} evals.`)}
    ${card("Attribute Pareto (critical)", paretoBox("qa-pareto"), `Descending fail count. Line = cumulative % of all attribute fails. Dashed = 80% vital few. Critical attributes in red. Bars count fail events — one audit can contribute more than one. n = ${nEvals(data)} evals.`)}
    <div class="row row-2">
      ${card("Top failing attributes", paretoBox("qa-fail"), `Same fail events as the Pareto. Phone 12 attrs / Live Chat 8. n = ${nEvals(data)} evals.`)}
      ${card("QA by contact reason", table(q.by_cr, [
        { key: "CR_Lv4", label: "Reason" },
        { key: "QA_Score", label: "QA", fmt: "num", d: 1, goal: g.qa, higher: true },
        { key: "N", label: "N", fmt: "int" },
      ]), `Official QA is still the mean of Score_Pct. N is audits on that Lv4. Floor shown is n ≥ 3.`)}
    </div>
    <div class="row row-2">
      ${card("Pareto · fails by CR Lv1", paretoBox("qa-fl1"), `Attribute fails grouped to Lv1 via the CSAT hierarchy. Ranked descending; line = cumulative %; gold dash = 80% vital few.`)}
      ${card("Pareto · fails by CR Lv4", paretoBox("qa-fl4"), `Fails at contact reason Lv4 (detail). n = ${nEvals(data)} evals.`)}
    </div>
    ${card("Pareto · fails by SUB_CR", paretoBox("qa-fls"), `Finest contact reason on QA (auditor-corrected SUB_CR). Other / Non sub cr falls back to the parent Lv4.`)}
    <div class="row row-2">
      ${card("QA + AHT · CR Lv4", `<div class="chart" id="qa-aht4"></div>`, `AHT on audited calls. n = ${nEvals(data)} evals. The pooled All association is not Phone R² plus Chat R².`)}
      ${card("AHT by channel", table(q.aht_channel, [
        { key: "Channel", label: "Channel" },
        { key: "QA_Score", label: "QA", fmt: "num", d: 1, goal: g.qa, higher: true },
        { key: "AHT_min", label: "AHT min", fmt: "num", d: 1 },
        { key: "n", label: "n", fmt: "int" },
      ]), `Phone calls are longer by nature. Coach the channel rows, not All.`)}
    </div>
    <div class="row row-3">
      ${card("Special project", table(q.special, [{ key: "Special_project", label: "Project" }, { key: "QA_Score", label: "QA", fmt: "num", d: 1, goal: g.qa, higher: true }, { key: "n", label: "n", fmt: "int" }]), `n = audits in this slice (${nEvals(data)} evals total).`)}
      ${card("Audit type", table(q.audit_type, [{ key: "Type_of_audit", label: "Type" }, { key: "QA_Score", label: "QA", fmt: "num", d: 1, goal: g.qa, higher: true }, { key: "n", label: "n", fmt: "int" }]), `Official QA is still the mean of Score_Pct.`)}
      ${card("Tenure", table(q.tenure, [{ key: "Tenure_Cohort", label: "Tenure" }, { key: "QA_Score", label: "QA", fmt: "num", d: 1, goal: g.qa, higher: true }, { key: "n", label: "Audits", fmt: "int" }]), `QA Excel Tenure field. n is audits, not agents.`)}
    </div>
    ${card("QA by LOB", `<div class="chart" id="qa-lob"></div>`, `n = ${nEvals(data)} evals. Dashed line is the ${g.qa} goal.`)}
    ${card("QA quartiles", bandsHtml(q.qa_bands), `Q1 is the top 25% of official QA in this filter. Quartile edges move with the filter — they are not the ${g.qa} goal.`)}
    ${card("Agent roster", table(q.roster, [
      { key: "Agent_ID", label: "Agent" },
      { key: "Supervisor_ID", label: "Supervisor" },
      { key: "QA_Score", label: "QA", fmt: "num", d: 1, goal: g.qa, higher: true },
      { key: "Audit_Count", label: "Audits", fmt: "int" },
      { key: "Fail_Count", label: "Fails", fmt: "int" },
      { key: "Crit_Fails", label: "Crit", fmt: "int" },
    ]), `Reliable agents only (n ≥ 5). Official QA is the mean of Score_Pct.`)}
    ${card("Resolution", `<p class="hint">${q.resolution?.rate == null ? "—" : pct(q.resolution.rate)} resolved · abandoned ${int(q.resolution?.n_abandoned || 0)} · process ${int(q.resolution?.n_unres_process || 0)} · agent ${int(q.resolution?.n_unres_agent || 0)}</p>`, `Auditor-judged case close — not FCR, not the QA score. n = ${nEvals(data)} evals.`)}
    ${downloadBar()}
  `;
  bindDownload();
  const wk = q.weekly || q.spark_weekly || [];
  plot("qa-week", [{ x: wk.map((r) => weekLabel(r.Week)), y: wk.map((r) => r.QA_Score), type: "scatter", mode: "lines+markers", line: { color: C.green, width: 3 }, fill: "tozeroy", fillcolor: "rgba(31,157,85,.12)" }], { noAnim: true, yaxis: { range: scoreRange(wk.map((r) => r.QA_Score).concat([g.qa])) } });
  plot("qa-hist", [{ x: (q.hist || {}).x || [], y: (q.hist || {}).y || [], type: "bar", marker: { color: C.green } }], { noAnim: true });
  ichart("qa-ctrl", q.control || [], "QA");
  scatterXY("qa-sc-csat", corr.cr || [], "QA_Score", "CSAT_Pct", { xTitle: "QA Score %", yTitle: "CSAT %", xGoal: g.qa, yGoal: g.csat });
  scatterXY("qa-sc-aht", corr.aht || [], "AHT_min", "QA_Score", { xTitle: "AHT (minutes)", yTitle: "QA Score %", yGoal: g.qa, color: C.green });
  corrBars("qa-r2", corr.corr || []);
  channelKpiCombo("qa-ch-kpi", q.by_channel || [], g);
  const pr = q.pareto || q.failing || [];
  pareto("qa-pareto", pr, ["Error_Category", "Attr", "Cat"], ["Cantidad", "Fail_Count", "Count"], { valueTitle: "Fails", unit: "attribute fails", nAudits: first(data.kpis, "evaluations", "qa_n") });
  const fl = q.failing || [];
  pareto("qa-fail", fl, ["Error_Category", "Attr"], ["Fail_Count", "Cantidad", "Count"], { valueTitle: "Fails" });
  pareto("qa-fl1", q.fails_lv1 || [], ["CR_Lv1", "CR_Lv1"], ["Fail_Count", "Count"], { valueTitle: "Fails" });
  pareto("qa-fl4", q.fails_lv4 || [], ["CR_Lv4", "CR_Lv4"], ["Fail_Count", "Count"], { valueTitle: "Fails" });
  pareto("qa-fls", q.fails_sub || [], ["SUB_CR", "SUB_CR"], ["Fail_Count", "Count"], { valueTitle: "Fails" });
  ahtCombo("qa-aht4", q.aht_lv4 || [], "CR_Lv4");
  const lob = q.qa_by_lob || [];
  plot("qa-lob", [{ type: "bar", orientation: "h", y: lob.map((r) => r.LOB).reverse(), x: lob.map((r) => r.QA_Score).reverse(), marker: { color: C.green } }], {
    noAnim: true,
    shapes: [{ type: "line", x0: g.qa, x1: g.qa, y0: -0.5, y1: Math.max(lob.length - 0.5, 0.5), line: { color: C.ink, dash: "dash", width: 1 } }],
  });
}


function renderCsat(data) {
  const c = data.csat || {};
  const k = data.kpis;
  const g = data.goals;
  const cm = c.comments || {};
  const corr = c.corr || {};
  const tCs = toneGoal(k.csat, g.csat, true);
  document.getElementById("view").innerHTML = `
    ${hero(data)}
    <div class="mini">
      ${miniTile({ label: "CSAT", value: k.csat, kind: "pct", d: 2, ...tCs, cap: `Goal ${pct(g.csat)}` })}
      ${miniTile({ label: "Surveys", value: k.csat_n, tag: "Volume" })}
      ${miniTile({ label: "4–5★", value: c.hi || 0, tone: "green", tag: "Satisfied" })}
      ${miniTile({ label: "1–3★", value: c.lo || 0, tone: (c.lo || 0) ? "amber" : "green", tag: (c.lo || 0) ? "Watch · 1–3★" : "On goal" })}
      ${miniTile({ label: "Readable comments", value: cm.n_real || 0, tag: "Volume" })}
      ${miniTile({ label: "Negative VOC", value: cm.n_negative || 0, tone: (cm.n_negative || 0) ? "amber" : "green", tag: (cm.n_negative || 0) ? "Watch" : "On goal" })}
    </div>
    <div class="row row-3">
      ${card("Star mix", `<div class="chart" id="star-chart"></div>`, `${int(c.hi || 0)} of 4–5★ · ${int(c.lo || 0)} of 1–3★ · CSAT N = ${nSurveys(data)} surveys.`)}
      ${card("Comment polarity", `<div class="chart" id="pol-chart"></div>`, `${int(cm.n_real || 0)} surveys with a readable comment. Positive vs negative uses that full set.`)}
      ${card("Negative VOC themes", `<div class="chart" id="voc-chart"></div>`, `Themes use only the 1–3★ surveys that left a comment. Ranked by mentions.`)}
    </div>
    <div class="row row-2">
      ${card("CSAT by day", `<div class="chart" id="csat-daily"></div>`, `${weekSpan(data)}. CSAT uses its own calendar, not QA audit weekdays.`)}
      ${card("CSAT histogram", `<div class="chart" id="csat-hist"></div>`, `N = ${nSurveys(data)} surveys · official (4★+5★) / Feedback CNT.`)}
    </div>
    ${card("CSAT I-chart", `<div class="trend-frame"><div class="chart ichart" id="csat-ctrl"></div></div>`, `Daily official CSAT vs control limits and the ${data.goals.csat}% goal. CSAT N = ${nSurveys(data)} surveys.`)}
    <div class="row row-3">
      ${card("Correlation · QA vs CSAT", `<div class="chart" id="cs-sc-qa"></div>`, `Each point is a contact reason Lv4 (detail) with both official QA and CSAT.`)}
      ${card("Correlation · CSAT vs recontact", `<div class="chart" id="cs-sc-rc"></div>`, `Official CSAT vs official recontact rate at Lv4.`)}
      ${card("Correlation · CSAT vs AHT", `<div class="chart" id="cs-sc-aht"></div>`, `Handle time vs official CSAT at Lv4.`)}
    </div>
    <div class="row row-2">
      ${card("CSAT · CR Lv1", table(c.by_cr_lv1, [{ key: "CR_Lv1", label: "Group" }, { key: "CSAT_Score", label: "CSAT", fmt: "pct", goal: data.goals.csat, higher: true }, { key: "Feedback", label: "Surveys", fmt: "int" }]), `Official CSAT is (4★+5★) / Feedback CNT at Lv1. CSAT N = ${nSurveys(data)} surveys.`)}
      ${card("CSAT · CR Lv4", table(c.by_cr_lv4, [{ key: "CR_Lv4", label: "Reason" }, { key: "CSAT_Score", label: "CSAT", fmt: "pct", goal: data.goals.csat, higher: true }, { key: "Feedback", label: "Surveys", fmt: "int" }]), `Same formula at contact reason Lv4 (detail).`)}
    </div>
    <div class="row row-2">
      ${card("Survey volume · CR Lv1", `<div class="chart" id="csat-vl1"></div>`, `Bars are survey volume (Feedback CNT). Line is official CSAT. CSAT N = ${nSurveys(data)} surveys.`)}
      ${card("Survey volume · CR Lv4", `<div class="chart" id="csat-vl4"></div>`, `Top reasons by survey volume. Line is (4★+5★) / Feedback CNT, not an average of row rates.`)}
    </div>
    ${card("Unsatisfied volume by CR", paretoBox("csat-unsat"), `Pareto of unsatisfied survey volume (Feedback − satisfied), not a new formula. Ranked descending; line = cumulative %; gold dash = 80% vital few. CSAT N = ${nSurveys(data)} surveys.`)}
    ${card("CSAT by supervisor", table(c.supervisors, [
      { key: "Supervisor_ID", label: "Supervisor" },
      { key: "CSAT_Score", label: "CSAT", fmt: "pct", goal: data.goals.csat, higher: true },
      { key: "Feedback", label: "Surveys", fmt: "int" },
      { key: "Agents", label: "Agents", fmt: "int" },
    ]), `Lowest CSAT first. Official (4★+5★) / Feedback CNT. CSAT N = ${nSurveys(data)} surveys.`)}
    ${card("CSAT by business type", table(c.csat_by_biz, [
      { key: "Business_Type", label: "Type" },
      { key: "CSAT_Score", label: "CSAT", fmt: "pct", goal: data.goals.csat, higher: true },
      { key: "Feedback", label: "Surveys", fmt: "int" },
    ]), `Native on CSAT. Official N = ${nSurveys(data)} surveys.`)}
    ${card("Taxonomy coverage", `<div class="chart" id="csat-tax"></div>`, `Share of CSAT surveys that still land in Other / Not mapped. CSAT N = ${nSurveys(data)} surveys.`)}
    ${card("Pareto · contact reasons (SUB_CR)", paretoBox("csat-subcr"), `Official N = ${int((c.subcr || {}).official_n || k.surveys)} surveys. Bars are the 10 largest SUB_CR reasons; remaining volume stays in N and the cumulative %. Line = cumulative %; gold dash = 80% vital few.`)}
    ${downloadBar()}
  `;
  bindDownload();
  const st = c.stars || [];
  plot("star-chart", [{ labels: st.map((r) => r.Rating), values: st.map((r) => r.Count), type: "pie", hole: 0.55, marker: { colors: [C.green, "#7BC47F", C.gold, "#E07A3D", C.red] } }]);
  const pol = cm.polarity || [];
  plot("pol-chart", [{ labels: pol.map((r) => r.Slice || r.Polarity || r.polarity), values: pol.map((r) => r.Surveys || r.n || r.Count), type: "pie", hole: 0.55, marker: { colors: [C.red, C.green] } }]);
  const voc = c.voc || [];
  hbar("voc-chart", voc.map((r) => r.Theme), voc.map((r) => r.Mentions), C.red);
  const daily = (c.csat_daily || c.daily || []).filter((r) => first(r, "CSAT_Score", "CSAT", "Value") != null);
  plot("csat-daily", [{
    x: daily.map((r) => r.Date || r.date),
    y: daily.map((r) => Number(first(r, "CSAT_Score", "CSAT", "Value"))),
    type: "scatter",
    mode: "lines+markers",
    line: { color: C.orange, width: 3 },
    marker: { size: 6, color: C.orange },
    connectgaps: false,
  }], { noAnim: true, yaxis: { title: "CSAT %", range: scoreRange(daily.map((r) => Number(first(r, "CSAT_Score", "CSAT", "Value"))).concat([data.goals.csat])) } });
  const hx = histXY(c.hist);
  plot("csat-hist", [{
    x: hx.x,
    y: hx.y,
    type: "bar",
    marker: { color: C.orange },
    hovertemplate: "CSAT %{x}<br>Surveys %{y:,}<extra></extra>",
  }], { noAnim: true, yaxis: { title: "Surveys", rangemode: "tozero" }, xaxis: { title: "CSAT %" } });
  ichart("csat-ctrl", c.control || [], "CSAT");
  scatterXY("cs-sc-qa", corr.cr || [], "QA_Score", "CSAT_Pct", { xTitle: "QA Score %", yTitle: "CSAT %", xGoal: data.goals.qa, yGoal: data.goals.csat });
  scatterXY("cs-sc-rc", corr.cr || [], "CSAT_Pct", "Recontact_Rate", { xTitle: "CSAT %", yTitle: "Recontact %", xGoal: data.goals.csat, yGoal: data.goals.recontact, color: C.rcLine });
  scatterXY("cs-sc-aht", corr.aht || [], "AHT_min", "CSAT_Pct", { xTitle: "AHT (minutes)", yTitle: "CSAT %", yGoal: data.goals.csat, color: C.orange });
  combo("csat-vl1", (c.vol_lv1 || []).map((r) => r.CR_Lv1), (c.vol_lv1 || []).map((r) => r.Feedback), (c.vol_lv1 || []).map((r) => r.CSAT_Score), "Surveys", "CSAT");
  combo("csat-vl4", (c.vol_lv4 || []).map((r) => r.CR_Lv4), (c.vol_lv4 || []).map((r) => r.Feedback), (c.vol_lv4 || []).map((r) => r.CSAT_Score), "Surveys", "CSAT");
  pareto("csat-unsat", c.unsat_cr || [], ["CR_Lv4", "SUB_CR", "Cat"], ["Unsatisfied", "Unsat", "Feedback"], { valueTitle: "Unsatisfied", color: C.red });
  const tax = c.taxonomy || [];
  plot("csat-tax", [
    { name: "Classified %", x: tax.map((r) => r.Level), y: tax.map((r) => r.Classified_Pct), type: "bar", marker: { color: C.green } },
    { name: "Other %", x: tax.map((r) => r.Level), y: tax.map((r) => r.Other_Pct), type: "bar", marker: { color: C.gold } },
  ], { barmode: "group" });
  const bars = (c.subcr || {}).bars || [];
  pareto("csat-subcr", bars, ["Cat", "SUB_CR", "Reason"], ["Feedback", "n", "Count"], { valueTitle: "Surveys" });
}

function renderRecontact(data) {
  const r = data.recontact || {};
  const d = r.dilution || {};
  const k = data.kpis;
  const g = data.goals;
  const corr = r.corr || {};
  const tRc = toneGoal(k.recontact, g.recontact, false);
  document.getElementById("view").innerHTML = `
    ${hero(data)}
    <div class="ops-grid">
      ${miniCol("Rate", [
        opsCard({ id: "rc-ops-rate", title: "Recontact Rate", value: k.recontact, kind: "pct", d: 2, ...tRc, cap: `Daily line · Σ repeats / Σ contacts · goal ≤ ${pct(g.recontact)}` }),
        opsCard({ id: "rc-ops-fcr", title: "FCR", value: r.fcr ?? k.fcr, kind: "pct", d: 2, tag: "Companion", cap: "Daily line · 100 minus recontact rate · no CX Quality target" }),
      ])}
      ${miniCol("Volume", [
        opsCard({ id: "rc-ops-contacts", title: "Contacts", value: k.contacts, tag: "Volume", cap: "Bars · customer contacts over time" }),
        opsCard({ id: "rc-ops-repeats", title: "Repeats", value: k.recontacts, tag: "Volume", cap: "Bars · Σ Recontact Volume (numerator)" }),
      ])}
      ${miniCol("Mix", [
        opsCard({ id: "rc-ops-self", title: "Self Help share", value: d.share, kind: "pct", d: 1, tag: "12-channel mix", cap: d.rate == null ? "Donut · Self Help vs other channels" : `Donut · Self Help at ${pct(d.rate)} inside the mix` }),
        opsCard({ id: "rc-ops-ch", title: "Channels", value: d.n_channels || (r.channels || []).length, tag: "Volume", cap: "Bars · contacts by channel (12-channel mix)" }),
      ])}
    </div>
    ${card("Contacts, repeats, and rate by channel", `<div class="chart combo" id="rc-ch-combo"></div>`, `N = ${nContacts(data)} contacts. Grouped bars are Contacts (blue) and Repeats (red). Orange line is Rate %. Dashed is the ${g.recontact}% goal. Rate is Σ repeats / Σ contacts (ratio of sums), not an average of the Rate % column. Self Help dwarfs other channels in volume.`)}
    ${card("Official 12-channel mix", table(r.channels, [
      { key: "Channel", label: "Channel" },
      { key: "Contacts", label: "Contacts", fmt: "int" },
      { key: "Repeats", label: "Repeats", fmt: "int" },
      { key: "Rate %", label: "Rate", fmt: "num", goal: g.recontact, higher: false },
      { key: "Share of contacts %", label: "Share", fmt: "num", d: 1 },
      { key: "Role", label: "Role" },
    ]), `Official recontact is Σ Repeats / Σ Contacts across these rows — do not average the Rate % column. Self Help is ${num(d.share, 1)}% of contacts at ${d.rate == null ? "—" : pct(d.rate)}. Only Phone and Live Chat also appear in QA and CSAT. Recontact over ${nContacts(data)} contacts. Market filter does not cut recontact.`)}
    ${card("Recontact I-chart (daily)", `<div class="trend-frame"><div class="chart ichart" id="rc-ctrl"></div></div>`, `Control chart of the same daily rate as the mini-card above · Σ repeats / Σ contacts vs UCL / LCL / CL and the ${g.recontact}% goal. Recontact over ${nContacts(data)} contacts.`)}
    <div class="row row-2">
      ${card("Correlation · QA vs recontact", `<div class="chart" id="rc-sc-qa"></div>`, `Each point is a contact reason Lv4 (detail) with both official QA and recontact.`)}
      ${card("Correlation · CSAT vs recontact", `<div class="chart" id="rc-sc-cs"></div>`, `Official CSAT vs official recontact rate at Lv4.`)}
    </div>
    <div class="row row-2">
      ${card("Pareto · repeats by CR Lv1", paretoBox("rc-lv1"), `Bars are Σ Recontact Volume. Ranked descending; line = cumulative % of repeats; gold dash = 80% vital few. Recontact over ${nContacts(data)} contacts.`)}
      ${card("Pareto · repeats by CR Lv4", paretoBox("rc-cr"), `Bars are Σ Recontact Volume at Lv4. The official rate is still Σ Repeats / Σ Contacts (ratio of sums), not an average of row rates.`)}
    </div>
    ${card("Pareto · repeats by SUB_CR", paretoBox("rc-sub"), `Recontact has no SUB_CR field. Bars are the official Lv4 repeat volume split by CSAT survey mix inside that Lv4. If SUB_CR is Other, the bar uses the parent Lv4.`)}
    ${card("Phone vs Live Chat contacts", `<div class="chart sm" id="rc-pc"></div>`, `Phone and Live Chat contacts only — not the 12-channel mix.`)}
    ${downloadBar()}
  `;
  bindDownload();
  const daily = r.daily || [];
  const volumes = r.volumes || {};
  const wkVol = (key) => xyOf(r.spark_weekly || [], [key], ["Week", "Date"]);
  miniLine("rc-ops-rate", pickTrend(daily, r.spark_weekly || [], ["Recontact_Rate"]), C.rcLine, { toZero: true });
  const fcrSeries = { x: [], y: [] };
  const rcTrend = pickTrend(daily, r.spark_weekly || [], ["Recontact_Rate"]);
  if (rcTrend.y.length) {
    fcrSeries.x = rcTrend.x;
    fcrSeries.y = rcTrend.y.map((v) => 100 - Number(v));
  }
  miniLine("rc-ops-fcr", fcrSeries, C.green, { toZero: false });
  miniBars("rc-ops-contacts", volOf(volumes, "contacts").y.length ? volOf(volumes, "contacts") : wkVol("Contacts"), C.bar);
  miniBars("rc-ops-repeats", volOf(volumes, "recontacts").y.length ? volOf(volumes, "recontacts") : wkVol("Recontacts"), C.rcLine);
  const chRows = (r.channels || []).filter((row) => row.Channel && !String(row.Channel).startsWith("All 12"));
  const self = chRows.find((row) => /self help/i.test(String(row.Channel))) || {};
  const selfN = Number(self.Contacts) || 0;
  const otherN = chRows.reduce((s, row) => s + (Number(row.Contacts) || 0), 0) - selfN;
  miniDonut("rc-ops-self", ["Self Help", "Other channels"], [selfN, Math.max(0, otherN)], [C.gold, C.navy], d.share != null ? pct(d.share, 1) : int(selfN));
  miniHbar("rc-ops-ch", chRows.map((row) => row.Channel), chRows.map((row) => Number(row.Contacts) || 0), C.bar);
  rcChannelCombo("rc-ch-combo", r.channels || [], g.recontact);
  ichart("rc-ctrl", r.control || [], "Recontact");
  scatterXY("rc-sc-qa", corr.cr || [], "QA_Score", "Recontact_Rate", { xTitle: "QA Score %", yTitle: "Recontact %", xGoal: g.qa, yGoal: g.recontact, color: C.rcLine });
  scatterXY("rc-sc-cs", corr.cr || [], "CSAT_Pct", "Recontact_Rate", { xTitle: "CSAT %", yTitle: "Recontact %", xGoal: g.csat, yGoal: g.recontact, color: C.rcLine });
  const lv1 = r.by_lv1 || [];
  pareto("rc-lv1", lv1, ["CR_Lv1"], ["Recontacts", "Contacts"], { valueTitle: "Repeats" });
  const cr = r.by_cr || [];
  pareto("rc-cr", cr, ["CR_Lv4", "SUB_CR"], ["Recontacts", "Contacts"], { valueTitle: "Repeats" });
  const sub = r.by_sub || [];
  pareto("rc-sub", sub, ["SUB_CR", "CR_Lv4"], ["Recontacts", "Contacts"], { valueTitle: "Repeats" });
  const pc = r.phone_chat || {};
  if ((pc.names || []).length) donut("rc-pc", pc.names, pc.vals, [C.phone, C.chat], int(pc.n || 0));
}

function renderAlerts(data) {
  const a = data.alerts || {};
  const g = data.goals;
  const q4 = ((a.qa_bands || {}).bands || {}).Q4 || {};
  const qCounts = a.q_counts || ["Q1", "Q2", "Q3", "Q4"].map((q) => ({ q, n: ((a.qa_bands || {}).bands || {})[q]?.n || 0 }));
  const tAvg = toneGoal(a.avg_qa, g.qa, true);
  const tBot = toneGoal(a.bottom10_avg, g.qa, true);
  const thin = Number(a.thin_n || 0);
  const n = Number(a.n || 0);
  const ranked = Number((a.qa_bands || {}).ranked || 0);
  const q4n = Number((a.qa_bands || {}).q4 || q4.n || 0);
  document.getElementById("view").innerHTML = `
    ${hero(data)}
    <div class="ops-grid">
      ${miniCol("Coverage", [
        opsCard({ id: "ag-n", title: "Agents evaluated", value: n, tag: "Volume", cap: "Histogram · audit counts per agent" }),
        opsCard({ id: "ag-thin", title: "Agents < 5 audits", value: thin, tone: thin ? "amber" : "green", tag: thin ? "Watch" : "On goal", cap: "Donut · below n ≥ 5 vs reliable" }),
      ])}
      ${miniCol("Quality", [
        opsCard({ id: "ag-avg", title: "Avg QA", value: a.avg_qa, kind: "num", d: 2, ...tAvg, cap: "Histogram · agent official QA (mean of Score_Pct)" }),
        opsCard({ id: "ag-bot", title: "Bottom 10% avg", value: a.bottom10_avg, kind: "num", d: 2, ...tBot, cap: "Bars · all-agent mean vs lowest decile" }),
      ])}
      ${miniCol("Quartiles", [
        opsCard({ id: "ag-q4", title: "Q4 watchlist", value: q4n, tone: q4n ? "red" : "green", tag: q4n ? "Watch" : "On goal", cap: "Donut · Q1–Q4 counts · Q4 is bottom 25% of this filter" }),
        opsCard({ id: "ag-rank", title: "Ranked", value: ranked, tag: "Reliable n ≥ 5", cap: "Bars · agents in Q1–Q4" }),
      ])}
    </div>
    ${card("QA quartiles", bandsHtml(a.qa_bands), `Q4 = bottom 25% of this filter, even if every score is above ${data.goals.qa}. Quartile edges move with the filter — they are not the ${data.goals.qa} goal. n = ${nEvals(data)} evals. Names are a sample of each band.`)}
    ${card("CSAT quartiles", bandsHtml(a.csat_bands), `Official CSAT is 4★+5★ / Feedback (ratio of sums). CSAT N = ${nSurveys(data)} surveys. No recontact-by-agent chart.`)}
    <div class="row row-2">
      ${card("Coaching queue", table(a.low, [
        { key: "Agent_ID", label: "Agent" },
        { key: "Supervisor_ID", label: "Supervisor" },
        { key: "QA_Score", label: "QA", fmt: "num", d: 1, goal: g.qa, higher: true },
        { key: "Audit_Count", label: "Audits", fmt: "int" },
      ]), `Reliable agents only. Floor n ≥ ${a.min_n || 5}. ${int(a.unreliable || 0)} under the floor. Official QA is the mean of Score_Pct.`)}
      ${card("Top QA agents", table(a.high, [
        { key: "Agent_ID", label: "Agent" },
        { key: "Supervisor_ID", label: "Supervisor" },
        { key: "QA_Score", label: "QA", fmt: "num", d: 1, goal: g.qa, higher: true },
        { key: "Audit_Count", label: "Audits", fmt: "int" },
      ]), `Highest official QA in this filter among reliable agents (n ≥ ${a.min_n || 5}).`)}
    </div>
    ${card("Q4 watchlist", table((a.qa_quartiles || []).filter((r) => r.Quartile === "Q4"), [
      { key: "Agent_ID", label: "Agent" },
      { key: "Supervisor_ID", label: "Supervisor" },
      { key: "QA_Score", label: "QA", fmt: "num", d: 1, goal: g.qa, higher: true },
      { key: "QA_n", label: "Audits", fmt: "int" },
      { key: "Quartile", label: "Q" },
    ]), `Q4 is the bottom 25% of reliable agents — not an ${data.goals.qa} cutoff. n = ${nEvals(data)} evals.`)}
    ${card("Supervisor talent mix", table(a.supervisor_mix, [
      { key: "Supervisor_ID", label: "Supervisor" },
      { key: "Ranked_Agents", label: "Agents", fmt: "int" },
      { key: "Q4_Share", label: "Q4 %", fmt: "num", d: 1 },
      { key: "Q1_pct", label: "Q1 %", fmt: "num", d: 1 },
      { key: "Requires_Review", label: "Review" },
    ]), `Talent mix is who sits in each band. Official QA/CSAT on the scorecard are team/operation means.`)}
    ${card("Fail concentrators", table(a.concentrators, [
      { key: "Agent_ID", label: "Agent" },
      { key: "Fail_Count", label: "Fails", fmt: "int" },
      { key: "Crit_Fails", label: "Crit", fmt: "int" },
      { key: "Fail_Share", label: "Share %", fmt: "num", d: 1 },
      { key: "QA_Score", label: "QA", fmt: "num", d: 1, goal: g.qa, higher: true },
    ]), `Share is of all attribute-fail events in this filter. n = ${nEvals(data)} evals.`)}
    ${card("Full QA roster", table(a.roster, [
      { key: "Agent_ID", label: "Agent" },
      { key: "Supervisor_ID", label: "Supervisor" },
      { key: "QA_Score", label: "QA", fmt: "num", d: 1, goal: g.qa, higher: true },
      { key: "Audit_Count", label: "Audits", fmt: "int" },
      { key: "Fail_Count", label: "Fails", fmt: "int" },
      { key: "Team_QA", label: "Team QA", fmt: "num", d: 1, goal: g.qa, higher: true },
    ]), `Reliable agents only (n ≥ ${a.min_n || 5}). Recontact / FCR are not scored by agent.`)}
    ${downloadBar()}
  `;
  bindDownload();
  const histQa = (a.hists || {}).qa || {};
  const histN = (a.hists || {}).n || {};
  miniBars("ag-n", { x: (histN.x || []).map(String), y: histN.y || [] }, C.bar);
  miniDonut("ag-thin", ["< 5 audits", "Reliable"], [thin, Math.max(0, n - thin)], [C.gold, C.navy], int(thin));
  miniBars("ag-avg", { x: (histQa.x || []).map(String), y: histQa.y || [] }, C.green);
  miniHbar("ag-bot", ["All agents", "Bottom 10%"], [Number(a.avg_qa) || 0, Number(a.bottom10_avg) || 0], C.gold);
  miniCompose("ag-q4", qCounts.map((r) => r.q), qCounts.map((r) => r.n), [C.green, C.bar, C.gold, C.red], int(q4n));
  miniHbar("ag-rank", qCounts.map((r) => r.q), qCounts.map((r) => r.n), C.navy);
}

function renderQuality(data) {
  const o = data.overview || {};
  document.getElementById("view").innerHTML = `
    ${hero(data)}
    ${card("How the data is sliced", `
      <p class="hint">The three sources are not a single table. A filter only applies where the column exists.</p>
      <p class="hint"><b>Channel:</b> QA is Phone + Live Chat. Recontact has 12 channels. When Channel = All, QA is the audited mix and recontact is all 12.</p>
      <p class="hint"><b>Market:</b> QA and CSAT yes. Recontact region is always SSL — the market filter does not cut recontact.</p>
      <p class="hint"><b>Supervisor / agent:</b> QA and CSAT. Recontact has neither field.</p>
      <p class="hint"><b>Contact reason:</b> native on CSAT. QA and recontact inherit Lv1 via the Lv4 name.</p>
      <p class="hint"><b>Tenure:</b> QA Excel Tenure field. CSAT joined by agent name. Recontact has none.</p>
      <p class="hint"><b>Business type:</b> native on CSAT. QA is cut to Lv4 names that carry that type. Recontact is not cut.</p>`)}
    ${card("Taxonomy coverage", `<div class="chart" id="tax-chart"></div>`, `Share of CSAT surveys that still land in Other / Not mapped at each grain. CSAT N = ${nSurveys(data)} surveys.`)}
  `;
  const tax = o.taxonomy || [];
  plot("tax-chart", [
    { name: "Classified %", x: tax.map((r) => r.Level), y: tax.map((r) => r.Classified_Pct), type: "bar", marker: { color: C.green } },
    { name: "Other %", x: tax.map((r) => r.Level), y: tax.map((r) => r.Other_Pct), type: "bar", marker: { color: C.gold } },
  ], { barmode: "group" });
}

function renderDefinitions(data) {
  const g = data.goals;
  const c = (state.meta && state.meta.control) || {};
  document.getElementById("view").innerHTML = `
    ${hero(data)}
    ${card("Official formulas", `
      <p><b>QA ≥ ${g.qa}:</b> mean of audit Score_Pct. Critical fail → 0, else −10 from 100. Phone 12 attributes / Chat 8 attributes are never mixed.</p>
      <p><b>CSAT ≥ ${g.csat}%:</b> (4★ + 5★) / Feedback CNT.</p>
      <p><b>Recontact ≤ ${g.recontact}%:</b> Σ Recontact Volume / Σ Contacts across the 12-channel mix. Do not average channel rates. No market field.</p>
      <p class="hint">Control totals (All markets, all weeks): QA ${c.qa} · CSAT ${c.csat}% · Recontact ${c.recontact}% · surveys ${int(c.surveys || 0)} · contacts ${int(c.contacts || 0)} · audits ${int(c.evaluations || 0)}.</p>
      <p class="hint">This slice: n = ${nEvals(data)} evals · CSAT N = ${nSurveys(data)} surveys · Recontact over ${nContacts(data)} contacts · ${weekSpan(data)}.</p>
    `)}
  `;
}

function downloadReport() {
  const data = state.last;
  if (!data) return;
  const k = data.kpis;
  const g = data.goals;
  const rows = [
    ["metric", "value", "goal", "n", "slice"],
    ["QA", k.qa, g.qa, k.qa_n, data.slice_note],
    ["CSAT", k.csat, g.csat, k.csat_n, data.slice_note],
    ["Recontact", k.recontact, g.recontact, k.recontact_n, data.slice_note],
    ["Contacts", k.contacts, "", k.contacts, data.slice_note],
    ["Surveys", k.surveys, "", k.surveys, data.slice_note],
    ["Audits", k.evaluations, "", k.evaluations, data.slice_note],
  ];
  const csv = rows.map((r) => r.map((x) => `"${String(x ?? "").replace(/"/g, '""')}"`).join(",")).join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  a.download = `didi-cx-kpis-${state.page}.csv`;
  a.click();
  const b = document.createElement("a");
  b.href = URL.createObjectURL(new Blob([JSON.stringify({ kpis: k, goals: g, filters: data.filters, slice: data.slice_note }, null, 2)], { type: "application/json" }));
  b.download = `didi-cx-kpis-${state.page}.json`;
  b.click();
}

const RENDER = {
  overview: renderOverview,
  qa: renderQa,
  csat: renderCsat,
  recontact: renderRecontact,
  alerts: renderAlerts,
  quality: renderQuality,
  definitions: renderDefinitions,
};

async function load() {
  titles();
  syncFilters();
  if (state.inflight) state.inflight.abort();
  state.inflight = new AbortController();
  const page = ["quality", "definitions"].includes(state.page) ? "overview" : state.page;
  const params = new URLSearchParams({
    page,
    channel: state.channel,
    country: state.country,
    weeks: state.weeks,
    day: state.day,
    lob: state.lob,
    tenure: state.tenure,
    business_type: state.biz,
  });
  const viewEl = document.getElementById("view");
  setBusy(true);
  if (viewEl && !viewEl.innerHTML.trim()) {
    viewEl.innerHTML = `<article class="card"><h2>Loading this slice…</h2><p class="hint">Fetching KPIs and charts. This can take a few seconds.</p></article>`;
  }
  try {
    const res = await fetch(`/api/dashboard?${params}`, { signal: state.inflight.signal });
    if (!res.ok) throw new Error(`dashboard ${res.status}`);
    const data = await res.json();
    state.last = data;
    document.getElementById("slice-label").textContent = data.slice_note || "";
    const fn = RENDER[state.page];
    if (fn) {
      try {
        fn(data);
        enterView();
      } catch (err) {
        console.error(err);
        setBusy(false);
        const view = document.getElementById("view");
        if (view && !view.innerHTML.trim()) {
          view.innerHTML = card("Could not render this page", `<p class="hint">${err.message}</p>`);
        }
      }
    } else {
      setBusy(false);
    }
  } catch (err) {
    if (err.name === "AbortError") return;
    setBusy(false);
    document.getElementById("view").innerHTML = card("Could not load this slice", `<p class="hint">${err.message}</p>`);
  }
}

async function boot() {
  try {
    renderChrome();
  } catch (err) {
    console.error(err);
  }
  try {
    const res = await fetch("/api/meta");
    if (!res.ok) throw new Error(`meta ${res.status}`);
    state.meta = await res.json();
    renderMeta();
  } catch (err) {
    const asof = document.getElementById("as-of");
    if (asof) asof.textContent = `Could not load filters · ${err.message}`;
  }
  await load();
}
boot();
