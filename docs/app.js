const sourceGrid = document.getElementById("source-grid");
const filterButtons = document.querySelectorAll(".filter-btn");
const ingestionBody = document.getElementById("ingestion-body");
const ingestionMeta = document.getElementById("ingestion-meta");
const simForm = document.getElementById("sim-form");
const jsonOutput = document.getElementById("json-output");
const benefitScoreEl = document.getElementById("benefit-score");
const riskScoreEl = document.getElementById("risk-score");
const uncertaintyScoreEl = document.getElementById("uncertainty-score");
const trajectoryLabelEl = document.getElementById("trajectory-label");
const historyBody = document.getElementById("history-body");
const historyFilterInput = document.getElementById("history-filter");
const clearHistoryButton = document.getElementById("clear-history");
const comparisonBars = document.getElementById("comparison-bars");

const HISTORY_KEY = "meditwin_experiments_v1";

let sources = [];
let activeFilter = "all";
let knowledgeBase = { sources: {} };
let experimentHistory = [];

function clamp(value, low, high) {
  return Math.max(low, Math.min(high, value));
}

function uid() {
  return `exp_${new Date().toISOString().replace(/[-:.]/g, "").slice(0, 15)}_${Math.random()
    .toString(36)
    .slice(2, 7)}`;
}

async function loadSources() {
  try {
    const response = await fetch("data/sources.json");
    sources = await response.json();
    renderSources();
  } catch (error) {
    sourceGrid.innerHTML = "<p>Impossibile caricare le fonti dati.</p>";
    console.error(error);
  }
}

function renderSources() {
  const filtered =
    activeFilter === "all"
      ? sources
      : sources.filter((source) => source.category === activeFilter);

  sourceGrid.innerHTML = filtered
    .map(
      (source) => `
      <article class="source-card">
        <div class="tag-row">
          <span class="tag ${source.category}">${labelCategory(source.category)}</span>
          <span class="tag">Priorita ${source.priority}</span>
          <span class="tag">${source.license}</span>
        </div>
        <h3>${source.name}</h3>
        <p>${source.summary}</p>
        <a href="${source.url}" target="_blank" rel="noopener noreferrer">Apri fonte</a>
      </article>
    `
    )
    .join("");
}

function labelCategory(value) {
  if (value === "medical") return "Medicale";
  if (value === "chemical") return "Chimico";
  if (value === "food") return "Alimentare";
  return value;
}

async function loadIngestionData() {
  try {
    const [manifestResponse, kbResponse] = await Promise.all([
      fetch("data/live/manifest.json"),
      fetch("data/live/knowledge_base.json"),
    ]);
    const manifest = await manifestResponse.json();
    knowledgeBase = await kbResponse.json();

    ingestionMeta.innerHTML = `
      <div class="meta-pill">Run ID: ${manifest.run_id}</div>
      <div class="meta-pill">Generated: ${new Date(manifest.generated_at).toLocaleString("it-IT")}</div>
    `;

    ingestionBody.innerHTML = manifest.sources
      .map((item) => {
        const statusClass = item.status === "ok" ? "status ok" : "status error";
        return `
          <tr>
            <td>${item.name}</td>
            <td>${labelCategory(item.category)}</td>
            <td><span class="${statusClass}">${item.status}</span></td>
            <td>${item.record_count}</td>
            <td><span class="path-chip">${item.snapshot_normalized}</span></td>
          </tr>
        `;
      })
      .join("");
  } catch (error) {
    ingestionBody.innerHTML = '<tr><td colspan="5">Manifest ingestione non disponibile.</td></tr>';
    console.error(error);
  }
}

function computeRiskScore(input) {
  let score = 20;
  const drivers = [];

  if (input.age >= 75) {
    score += 16;
    drivers.push("eta avanzata");
  } else if (input.age >= 65) {
    score += 10;
    drivers.push("eta > 65");
  }

  if (["moderate", "severe", "reduced"].includes(input.renal_status)) {
    score += 18;
    drivers.push("funzione renale ridotta");
  }

  if (["moderate", "severe", "reduced"].includes(input.liver_status)) {
    score += 16;
    drivers.push("funzione epatica ridotta");
  }

  if (input.selected_therapies.length >= 3) {
    score += 14;
    drivers.push("politerapia");
  } else if (input.selected_therapies.length === 2) {
    score += 8;
    drivers.push("terapia combinata");
  }

  if (input.risk_factors.includes("smoking")) {
    score += 7;
    drivers.push("fumo");
  }
  if (input.risk_factors.includes("alcohol_high")) {
    score += 6;
    drivers.push("alcol elevato");
  }
  if (input.risk_factors.includes("obesity")) {
    score += 8;
    drivers.push("obesita");
  }

  return { score: clamp(score, 0, 100), drivers };
}

function computeBenefitScore(input) {
  let score = 35;
  const reasons = [];
  const p = input.pathology.toLowerCase();

  if (p.includes("epiless")) {
    score += 20;
    reasons.push("potenziale riduzione crisi");
  }
  if (p.includes("onc") || p.includes("tum")) {
    score += 15;
    reasons.push("potenziale controllo progressione");
  }
  if (p.includes("cardio")) {
    score += 12;
    reasons.push("potenziale riduzione rischio cardiovascolare");
  }
  if (p.includes("infiam")) {
    score += 10;
    reasons.push("potenziale riduzione infiammazione");
  }

  if (input.selected_therapies.length > 1) {
    score += 6;
    reasons.push("sinergia teorica combinazione");
  }

  if (input.adherence >= 0.8) {
    score += 8;
    reasons.push("aderenza alta");
  } else if (input.adherence < 0.5) {
    score -= 8;
    reasons.push("aderenza bassa");
  }

  return { score: clamp(score, 0, 100), reasons };
}

function detectInteractions(selectedTherapies) {
  const lower = selectedTherapies.map((x) => x.toLowerCase());
  const interactions = [];

  if (lower.includes("valproato") && lower.includes("lamotrigina")) {
    interactions.push({
      severity: "medium-high",
      description: "Valproato puo aumentare esposizione a lamotrigina (rischio cutaneo/sedazione).",
    });
  }

  if (lower.includes("carbamazepina") && lower.includes("clopidogrel")) {
    interactions.push({
      severity: "medium",
      description: "Possibile variazione di efficacia dovuta a induzione enzimatica.",
    });
  }

  if (lower.length >= 3) {
    interactions.push({
      severity: "medium",
      description: "Numero elevato di farmaci: aumentata complessita farmacocinetica.",
    });
  }

  return interactions;
}

function computeUncertainty(input) {
  let uncertainty = 35;

  if (!input.pathology) uncertainty += 10;
  if (input.selected_therapies.length === 0) uncertainty += 25;
  if (input.liver_status === "unknown" || input.renal_status === "unknown") uncertainty += 14;

  const sourceRecords = Object.values(knowledgeBase.sources || {}).reduce(
    (acc, source) => acc + Number(source.record_count || 0),
    0
  );

  if (sourceRecords >= 10) uncertainty -= 8;
  if (sourceRecords === 0) uncertainty += 12;

  return clamp(uncertainty, 0, 100);
}

function buildSimulationReport(input) {
  const { score: riskScore, drivers } = computeRiskScore(input);
  const { score: benefitScore, reasons } = computeBenefitScore(input);
  const interactions = detectInteractions(input.selected_therapies);
  const uncertainty = computeUncertainty(input);

  const trajectoryIndex = clamp(benefitScore * 0.58 - riskScore * 0.42, -100, 100);
  let trajectoryLabel = "stabilita incerta con bisogno di monitoraggio";
  if (trajectoryIndex >= 20) trajectoryLabel = "miglioramento probabile nel breve periodo";
  if (trajectoryIndex < -10) trajectoryLabel = "rischio di peggioramento teorico";

  const report = {
    report_meta: {
      report_id: uid(),
      created_at: new Date().toISOString(),
      engine: "MediTwin Browser Rule Engine v0.1",
      disclaimer: "Research-only simulation. Not medical advice.",
    },
    patient_profile: {
      patient_id: input.patient_id,
      age: input.age,
      sex: input.sex,
      weight_kg: input.weight_kg,
      pathology: input.pathology,
      liver_status: input.liver_status,
      renal_status: input.renal_status,
      selected_therapies: input.selected_therapies,
      risk_factors: input.risk_factors,
    },
    assessment: {
      potential_benefits: {
        score: Number(benefitScore.toFixed(1)),
        reasons,
      },
      risks_and_contraindications: {
        score: Number(riskScore.toFixed(1)),
        risk_drivers: drivers,
        interactions,
      },
      evolution_scenario: {
        trajectory_index: Number(trajectoryIndex.toFixed(1)),
        label: trajectoryLabel,
        short_horizon: "2-4 settimane virtuali",
      },
      monitoring_parameters: [
        "funzionalita epatica (ALT, AST)",
        "funzionalita renale (eGFR, creatinina)",
        "eventi avversi teorici",
        "aderenza e qualita di vita",
      ],
      uncertainty: {
        score: Number(uncertainty.toFixed(1)),
        confidence: Number((100 - uncertainty).toFixed(1)),
        notes: [
          "l'incertezza aumenta con dati mancanti",
          "la simulazione non sostituisce validazione clinica",
        ],
      },
    },
  };

  return report;
}

function parseCommaList(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function saveHistory() {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(experimentHistory));
}

function loadHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    experimentHistory = raw ? JSON.parse(raw) : [];
  } catch (error) {
    experimentHistory = [];
    console.error(error);
  }
}

function renderComparisonBars(rows) {
  if (rows.length === 0) {
    comparisonBars.innerHTML = "<p class=\"muted\">Nessun esperimento disponibile.</p>";
    return;
  }

  const latest = rows.slice(0, 6);
  comparisonBars.innerHTML = latest
    .map((item) => {
      const b = Number(item.assessment.potential_benefits.score);
      const r = Number(item.assessment.risks_and_contraindications.score);
      const u = Number(item.assessment.uncertainty.score);
      return `
        <article class="bar-card">
          <h4>${item.report_meta.report_id}</h4>
          <div class="bar-row"><span>Beneficio</span><div class="bar"><i style="width:${b}%"></i></div><strong>${b}</strong></div>
          <div class="bar-row"><span>Rischio</span><div class="bar risk"><i style="width:${r}%"></i></div><strong>${r}</strong></div>
          <div class="bar-row"><span>Incertezza</span><div class="bar unc"><i style="width:${u}%"></i></div><strong>${u}</strong></div>
        </article>
      `;
    })
    .join("");
}

function renderHistory() {
  const filterValue = historyFilterInput.value.trim().toLowerCase();
  const sortedRows = [...experimentHistory].sort(
    (a, b) => new Date(b.report_meta.created_at).getTime() - new Date(a.report_meta.created_at).getTime()
  );
  const rows = filterValue
    ? sortedRows.filter((item) => item.patient_profile.patient_id.toLowerCase().includes(filterValue))
    : sortedRows;

  renderComparisonBars(rows);

  historyBody.innerHTML = rows
    .map(
      (item) => `
      <tr>
        <td>${item.report_meta.report_id}</td>
        <td>${item.patient_profile.patient_id}</td>
        <td>${item.patient_profile.pathology}</td>
        <td>${item.assessment.potential_benefits.score}</td>
        <td>${item.assessment.risks_and_contraindications.score}</td>
        <td>${item.assessment.uncertainty.score}</td>
        <td>${new Date(item.report_meta.created_at).toLocaleString("it-IT")}</td>
      </tr>
    `
    )
    .join("");
}

function updateCurrentResult(report) {
  benefitScoreEl.textContent = report.assessment.potential_benefits.score;
  riskScoreEl.textContent = report.assessment.risks_and_contraindications.score;
  uncertaintyScoreEl.textContent = report.assessment.uncertainty.score;
  trajectoryLabelEl.textContent = report.assessment.evolution_scenario.label;
  jsonOutput.textContent = JSON.stringify(report, null, 2);
}

function bootstrapSeed() {
  if (experimentHistory.length > 0) return;
  fetch("data/seed_experiments.json")
    .then((res) => res.json())
    .then((seed) => {
      experimentHistory = seed.experiments || [];
      saveHistory();
      renderHistory();
    })
    .catch((error) => {
      console.error(error);
    });
}

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    filterButtons.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    activeFilter = button.dataset.filter;
    renderSources();
  });
});

simForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(simForm);
  const input = {
    patient_id: String(data.get("patient_id") || "vp-001"),
    age: Number(data.get("age") || 50),
    sex: String(data.get("sex") || "unknown"),
    weight_kg: Number(data.get("weight_kg") || 70),
    pathology: String(data.get("pathology") || "unknown"),
    liver_status: String(data.get("liver_status") || "unknown"),
    renal_status: String(data.get("renal_status") || "unknown"),
    selected_therapies: parseCommaList(String(data.get("selected_therapies") || "")),
    risk_factors: parseCommaList(String(data.get("risk_factors") || "")),
    adherence: Number(data.get("adherence") || 0.8),
  };

  const report = buildSimulationReport(input);
  experimentHistory.push(report);
  saveHistory();
  updateCurrentResult(report);
  renderHistory();
});

historyFilterInput.addEventListener("input", renderHistory);

clearHistoryButton.addEventListener("click", () => {
  experimentHistory = [];
  saveHistory();
  bootstrapSeed();
  renderHistory();
});

loadHistory();
bootstrapSeed();
renderHistory();
loadSources();
loadIngestionData();
