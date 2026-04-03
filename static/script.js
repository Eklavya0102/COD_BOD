/**
 * Water Quality Analysis – BOD & COD Calculator
 * Frontend Logic: data collection, API calls, chart rendering, PDF download
 */

// ── Constants ──────────────────────────────────────────────────────────────
const MONTHS = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December"
];

/**
 * Realistic sample dissolved oxygen values (mg/L) for 2025.
 * Summer months typically show lower DO due to higher temperatures.
 * Values represent a moderately impacted freshwater body.
 */
const SAMPLE_DO_INITIAL = [8.4, 8.1, 7.8, 7.2, 6.8, 6.4, 6.1, 6.3, 6.9, 7.5, 8.0, 8.3];
const SAMPLE_DO_FINAL   = [5.1, 4.8, 4.4, 3.9, 3.5, 3.1, 2.8, 3.0, 3.6, 4.2, 4.7, 5.0];

// ── Chart reference ────────────────────────────────────────────────────────
let trendChart = null;

// ── Collected results (used for PDF download) ─────────────────────────────
let lastResults = [];
let lastStudent = {};
let lastLocation = {};
let lastYear = 2025;
let lastChartImage = null;

// ── DOM Ready ──────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("sample-btn").addEventListener("click", generateSampleData);
  document.getElementById("calculate-btn").addEventListener("click", calculate);
  document.getElementById("pdf-btn").addEventListener("click", downloadPDF);

  // Theme toggle init
  initTheme();
  document.getElementById("theme-toggle-btn").addEventListener("click", toggleTheme);

  // Year badge sync
//   const yearInput = document.getElementById("analysis-year");
//   yearInput.addEventListener("input", () => {
//     const yr = yearInput.value || "2025";
//     document.getElementById("header-badge").textContent = yr;
//     document.getElementById("chart-year-label").textContent = yr;
//   });


yearInput.addEventListener("change", updateYear);
yearInput.addEventListener("keyup", updateYear);
yearInput.addEventListener("input", updateYear);

function updateYear() {
  const yr = yearInput.value || "2025";
  document.getElementById("header-badge").textContent = yr;
  document.getElementById("chart-year-label").textContent = yr;
}
});

/**
 * Fill inputs with realistic sample dissolved oxygen values.
 * Useful for demonstration without manual entry.
 */
function generateSampleData() {
  const initInputs = document.querySelectorAll(".do-initial");
  const finalInputs = document.querySelectorAll(".do-final");

  initInputs.forEach((inp, i) => {
    inp.value = SAMPLE_DO_INITIAL[i];
    inp.classList.add("filled");
  });
  finalInputs.forEach((inp, i) => {
    inp.value = SAMPLE_DO_FINAL[i];
    inp.classList.add("filled");
  });

  // Pulse animation feedback
  const btn = document.getElementById("sample-btn");
  btn.textContent = "✓ Sample Data Loaded";
  btn.style.color = "var(--cyan)";
  setTimeout(() => {
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Generate Sample Data`;
    btn.style.color = "";
  }, 1800);
}

/**
 * Collect DO values, send to Flask backend for BOD/COD computation,
 * then render the results table and chart.
 */
async function calculate() {
  const doInitial = [...document.querySelectorAll(".do-initial")].map(i => parseFloat(i.value) || 0);
  const doFinal   = [...document.querySelectorAll(".do-final")].map(i => parseFloat(i.value) || 0);

  // Validate: at least one month must have non-zero data
  if (doInitial.every(v => v === 0) && doFinal.every(v => v === 0)) {
    showToast("Please enter dissolved oxygen values or generate sample data first.", "warn");
    return;
  }

  // Collect student & location info
  lastStudent = {
    name:        document.getElementById("student-name").value.trim() || "—",
    register_no: document.getElementById("register-no").value.trim()  || "—",
    branch:      document.getElementById("branch").value.trim()       || "—",
    section:     document.getElementById("section").value.trim()      || "—",
  };
  lastLocation = {
    hometown: document.getElementById("hometown").value.trim() || "—",
    district: document.getElementById("district").value.trim() || "—",
    state:    document.getElementById("state").value.trim()    || "—",
  };
  lastYear = parseInt(document.getElementById("analysis-year").value) || 2025;
  document.getElementById("chart-year-label").textContent = lastYear;
  document.getElementById("header-badge").textContent = lastYear;

  const calcBtn = document.getElementById("calculate-btn");
  calcBtn.textContent = "Calculating…";
  calcBtn.disabled = true;

  try {
    const res = await fetch("/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ do_initial: doInitial, do_final: doFinal })
    });
    const data = await res.json();
    lastResults = data.results;
    renderResults(lastResults);
  } catch (err) {
    showToast("Calculation failed. Please try again.", "error");
    console.error(err);
  } finally {
    calcBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="12" y2="14"/></svg> Calculate BOD &amp; COD`;
    calcBtn.disabled = false;
  }
}

/**
 * Render results table, summary chips, and Chart.js line graph.
 * @param {Array} results - Array of {month, do_initial, do_final, bod, cod}
 */
function renderResults(results) {
  // Show section
  const section = document.getElementById("results-section");
  section.classList.remove("hidden");
  section.scrollIntoView({ behavior: "smooth", block: "start" });

  // ── Summary chips ──────────────────────────────────────────────────────
  const avgBOD = results.reduce((s, r) => s + r.bod, 0) / results.length;
  const avgCOD = results.reduce((s, r) => s + r.cod, 0) / results.length;
  const maxBOD = Math.max(...results.map(r => r.bod));
  const maxMonth = results.find(r => r.bod === maxBOD)?.month || "—";

  document.getElementById("summary-chips").innerHTML = `
    <div class="chip cyan">Avg BOD: <strong>${avgBOD.toFixed(3)} mg/L</strong></div>
    <div class="chip red">Avg COD: <strong>${avgCOD.toFixed(3)} mg/L</strong></div>
    <div class="chip">Peak BOD Month: <strong>${maxMonth}</strong></div>
    <div class="chip">Months Analysed: <strong>12</strong></div>
  `;

  // ── Table ──────────────────────────────────────────────────────────────
  const tbody = document.getElementById("results-body");
  tbody.innerHTML = results.map(r => `
    <tr>
      <td>${r.month}</td>
      <td>${r.do_initial.toFixed(2)}</td>
      <td>${r.do_final.toFixed(2)}</td>
      <td class="bod-val">${r.bod.toFixed(3)}</td>
      <td class="cod-val">${r.cod.toFixed(3)}</td>
    </tr>
  `).join("");

  // ── Chart ──────────────────────────────────────────────────────────────
  const labels = results.map(r => r.month.substring(0, 3));
  const bodData = results.map(r => r.bod);
  const codData = results.map(r => r.cod);

  if (trendChart) trendChart.destroy();

  const ctx = document.getElementById("trend-chart").getContext("2d");
  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "BOD (mg/L)",
          data: bodData,
          borderColor: "#4ec9ff",
          backgroundColor: "rgba(78,201,255,0.08)",
          borderWidth: 2.5,
          pointBackgroundColor: "#4ec9ff",
          pointBorderColor: "#060e24",
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
          tension: 0.4,
          fill: true,
        },
        {
          label: "COD (mg/L)",
          data: codData,
          borderColor: "#ff6b6b",
          backgroundColor: "rgba(255,107,107,0.06)",
          borderWidth: 2.5,
          pointBackgroundColor: "#ff6b6b",
          pointBorderColor: "#060e24",
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
          tension: 0.4,
          fill: true,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 900,
        easing: "easeInOutQuart",
        onComplete: () => {
          // Feature 3: capture chart as image after animation completes
          lastChartImage = trendChart.toBase64Image("image/png", 1.0);
        }
      },
      plugins: {
        legend: {
          display: false  // custom legend shown in HTML
        },
        tooltip: {
          backgroundColor: "rgba(11,26,58,0.95)",
          borderColor: "rgba(25,212,232,0.3)",
          borderWidth: 1,
          titleColor: "#19d4e8",
          bodyColor: "#f0f8ff",
          padding: 10,
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(3)} mg/L`
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(240,248,255,0.05)" },
          ticks: { color: "rgba(240,248,255,0.5)", font: { size: 11 } }
        },
        y: {
          grid: { color: "rgba(240,248,255,0.05)" },
          ticks: {
            color: "rgba(240,248,255,0.5)",
            font: { size: 11 },
            callback: v => v.toFixed(2)
          },
          title: {
            display: true,
            text: "Concentration (mg/L)",
            color: "rgba(240,248,255,0.4)",
            font: { size: 11 }
          }
        }
      }
    }
  });
}

/**
 * Request PDF generation from the Flask backend and trigger download.
 */
async function downloadPDF() {
  if (!lastResults.length) {
    showToast("Please calculate results first before downloading the PDF.", "warn");
    return;
  }

  const pdfBtn = document.getElementById("pdf-btn");
  pdfBtn.textContent = "Generating…";
  pdfBtn.disabled = true;

  try {
    const res = await fetch("/download_pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student:     lastStudent,
        location:    lastLocation,
        results:     lastResults,
        year:        lastYear,
        chart_image: lastChartImage || null
      })
    });

    if (!res.ok) throw new Error("PDF generation failed");

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `BOD_and_COD_Report${lastYear}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("PDF downloaded successfully!", "success");

  } catch (err) {
    showToast("PDF download failed. Please try again.", "error");
    console.error(err);
  } finally {
    pdfBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg> Download PDF`;
    pdfBtn.disabled = false;
  }
}

/**
 * Display a transient toast notification.
 * @param {string} message - Text to display
 * @param {"success"|"warn"|"error"} type - Visual style
 */
function showToast(message, type = "success") {
  const existing = document.querySelector(".toast");
  if (existing) existing.remove();

  const colors = { success: "#0abfa3", warn: "#f0a500", error: "#ff6b6b" };
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  Object.assign(toast.style, {
    position: "fixed",
    bottom: "28px",
    right: "28px",
    background: "rgba(11,26,58,0.97)",
    border: `1px solid ${colors[type] || colors.success}`,
    color: "#f0f8ff",
    padding: "12px 20px",
    borderRadius: "10px",
    fontSize: "0.88rem",
    fontFamily: "'DM Sans', sans-serif",
    zIndex: 9999,
    boxShadow: `0 4px 24px rgba(0,0,0,0.5)`,
    animation: "slideUp 0.3s ease",
    maxWidth: "320px",
    lineHeight: "1.4"
  });
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

