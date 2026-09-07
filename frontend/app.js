const API = (() => {
  const host = window.location.hostname;
  // GitHub Codespaces: <codespace>-8000.app.github.dev
  if (host.endsWith(".app.github.dev")) {
    return `${window.location.protocol}//${host.replace(/-\d+\.app\.github\.dev$/, "-8000.app.github.dev")}`;
  }
  return `${window.location.protocol}//${host}:8000`;
})();

async function apiFetch(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const response = await fetch(`${API}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {"Accept": "application/json", ...(options.headers || {})}
    });
    if (!response.ok) throw new Error(`HTTP ${response.status} for ${path}`);
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}
let map, markers = [];

function levelClass(level){
  return level === "CRITICAL" ? "critical" :
         level === "HIGH" ? "bad" :
         level === "MODERATE" ? "warn" : "good";
}
function levelColor(level){
  return level === "CRITICAL" ? "#f87171" :
         level === "HIGH" ? "#fb923c" :
         level === "MODERATE" ? "#facc15" : "#4ade80";
}

async function loadSummary(){
  try {
    const s = await apiFetch("/api/risk-summary");
  const levels = s.levels;
  document.getElementById("summaryCards").innerHTML = `
    <div class="card"><div class="metric">${s.total_zones}</div><div class="label">Monitored zones</div></div>
    <div class="card"><div class="metric">${levels.CRITICAL}</div><div class="label">Critical</div></div>
    <div class="card"><div class="metric">${levels.HIGH}</div><div class="label">High risk</div></div>
    <div class="card"><div class="metric">${levels.MODERATE}</div><div class="label">Moderate</div></div>
  `;
    renderRiskList(s.critical);
  } catch (err) {
    document.getElementById("riskList").innerHTML =
      `<div class="risk-item"><b>Backend connection failed</b><div class="risk-meta">${err.message}<br>Backend: ${API}</div></div>`;
  }
}

function renderRiskList(items){
  document.getElementById("riskList").innerHTML = items.map(z=>`
    <div class="risk-item">
      <div class="risk-row">
        <div class="risk-name">${z.location}, ${z.state}</div>
        <span class="tag" style="background:${levelColor(z.risk_level)}22;color:${levelColor(z.risk_level)}">${z.risk_level}</span>
      </div>
      <div class="risk-meta">Risk ${z.risk_score}/100 · Road risk ${z.road_risk}/100 · Confidence ${z.confidence}%</div>
    </div>`).join("");
}

async function loadMap(minScore=0){
  try {
    const zones = await apiFetch(`/api/zones?min_score=${minScore}`);
  markers.forEach(m=>map.removeLayer(m)); markers=[];
    zones.forEach(z=>{
    const marker = L.circleMarker([z.lat,z.lon],{
      radius: 10,
      color: levelColor(z.risk_level),
      fillColor: levelColor(z.risk_level),
      fillOpacity: 0.70
    }).addTo(map);
    marker.bindPopup(`<b>${z.location}, ${z.state}</b><br>Risk: ${z.risk_score}/100<br>Level: ${z.risk_level}<br>Road risk: ${z.road_risk}/100`);
    markers.push(marker);
  });
}
  } catch (err) {
    console.error("Map load failed:", err);
  }
}

async function calculate(){
  const body={
    rainfall_24h_mm:+document.getElementById("r24").value,
    rainfall_7d_mm:+document.getElementById("r7").value,
    slope_deg:+document.getElementById("slope").value,
    elevation_m:+document.getElementById("elev").value,
    geology_risk:+document.getElementById("geo").value,
    landcover_change:+document.getElementById("land").value,
    historical_risk:+document.getElementById("hist").value,
  };
  const r = await fetch(`${API}/api/risk-score`,{
    method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)
  }).then(r=>r.json());
  document.getElementById("result").classList.remove("hidden");
  document.getElementById("result").innerHTML = `
    <div class="big">${r.risk_score}/100 — ${r.risk_level}</div>
    <div style="color:var(--muted);margin:6px 0 14px">Confidence: ${r.confidence}% · Prototype risk engine</div>
    ${r.top_contributors.map(f=>`<div class="factor"><span>${f.factor}</span><b>${f.contribution}%</b></div>`).join("")}
  `;
}

window.addEventListener("DOMContentLoaded", async ()=>{
  map = L.map("map").setView([25.9, 91.9], 6);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:"© OpenStreetMap contributors"}).addTo(map);
  document.getElementById("filter").addEventListener("change", e=>loadMap(+e.target.value));
  document.getElementById("calc").addEventListener("click", calculate);
  await loadSummary();
  await loadMap();
});

async function mlCalculate(){
  const body={
    rainfall_24h_mm:+document.getElementById("r24").value,
    rainfall_7d_mm:+document.getElementById("r7").value,
    slope_deg:+document.getElementById("slope").value,
    elevation_m:+document.getElementById("elev").value,
    geology_risk:+document.getElementById("geo").value,
    landcover_change:+document.getElementById("land").value,
    historical_risk:+document.getElementById("hist").value,
  };
  const res = await fetch(`${API}/api/ml-predict`,{
    method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)
  });
  const r = await res.json();
  document.getElementById("result").classList.remove("hidden");
  if(!res.ok){
    document.getElementById("result").innerHTML = `<b>ML model unavailable</b><div style="color:var(--muted);margin-top:6px">${r.detail || "Train the prototype model first."}</div>`;
    return;
  }
  document.getElementById("result").innerHTML = `
    <div class="big">${r.risk_score}/100 — ${r.risk_level}</div>
    <div style="color:var(--muted);margin:6px 0 0">Confidence: ${r.confidence}%</div>
    <div style="color:var(--muted);margin-top:8px">${r.warning}</div>
  `;
}
