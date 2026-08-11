/**
 * DeepGuard Results Dashboard Renderer
 */

document.addEventListener("DOMContentLoaded", async () => {
  const params = new URLSearchParams(window.location.search);
  const analysisId = params.get("id");

  if (!analysisId) {
    showToast("No analysis ID provided.", "error");
    setTimeout(() => { window.location.href = "analyze.html"; }, 1500);
    return;
  }

  try {
    const response = await fetch(`/api/analysis/${analysisId}`);
    if (!response.ok) {
      throw new Error("Analysis report not found.");
    }
    const data = await response.json();
    renderResults(data);
  } catch (err) {
    showToast(err.message || "Failed to load analysis report.", "error");
  }
});

function renderResults(data) {
  // 1. Overall Result Banner & Confidence Gauge
  const banner = document.getElementById("result-banner");
  const resultTitle = document.getElementById("result-title");
  const confidenceVal = document.getElementById("confidence-val");
  const mediaPreview = document.getElementById("results-media-preview");
  const fileMetaInfo = document.getElementById("file-meta-info");

  const resultClass = data.result.includes("AUTHENTIC") ? "authentic" :
                      data.result.includes("SUSPICIOUS") ? "suspicious" : "deepfake";

  if (banner) {
    banner.className = `result-banner ${resultClass}`;
    resultTitle.textContent = data.result;
    confidenceVal.textContent = `${Math.round(data.confidence_score)}%`;
  }

  // Media preview element
  if (mediaPreview && data.media_url) {
    if (data.file_type === "image") {
      mediaPreview.innerHTML = `<img src="${data.media_url}" class="preview-media" alt="Analyzed Media">`;
    } else {
      mediaPreview.innerHTML = `<video src="${data.media_url}" class="preview-media" controls></video>`;
    }
  }

  if (fileMetaInfo) {
    fileMetaInfo.innerHTML = `
      <strong>Filename:</strong> ${data.filename}<br>
      <strong>Media Type:</strong> ${data.file_type.toUpperCase()} | <strong>Size:</strong> ${formatBytes(data.file_size)}<br>
      <strong>Scanned Date:</strong> ${new Date(data.created_at).toLocaleString()}
    `;
  }

  // 2. Summary Breakdown Cards
  const aiStatusElem = document.getElementById("summary-ai-status");
  const metaStatusElem = document.getElementById("summary-meta-status");
  const forensicStatusElem = document.getElementById("summary-forensic-status");
  const faceStatusElem = document.getElementById("summary-face-status");

  if (aiStatusElem) {
    if (data.ai_model_status === "Available" && data.ai_score !== null) {
      aiStatusElem.innerHTML = `<span class="badge badge-deepfake">${data.ai_score}% Risk</span>`;
    } else {
      aiStatusElem.innerHTML = `<span class="badge badge-suspicious">Not Configured</span>`;
    }
  }

  if (metaStatusElem) {
    metaStatusElem.innerHTML = `<span class="badge badge-authentic">${data.metadata_score}% Risk</span>`;
  }

  if (forensicStatusElem) {
    const fClass = data.forensic_score > 50 ? "badge-deepfake" : data.forensic_score > 25 ? "badge-suspicious" : "badge-authentic";
    forensicStatusElem.innerHTML = `<span class="badge ${fClass}">${data.forensic_score}% Risk</span>`;
  }

  if (faceStatusElem) {
    faceStatusElem.innerHTML = `<span class="badge badge-authentic">${data.faces_detected} Detected</span>`;
  }

  // 3. Explainability Reasons List
  const reasonsList = document.getElementById("reasons-list");
  if (reasonsList && data.explanations) {
    reasonsList.innerHTML = "";
    data.explanations.forEach(reason => {
      const li = document.createElement("li");
      let iconClass = "fa-check-circle text-authentic";
      if (reason.toLowerCase().includes("risk") || reason.toLowerCase().includes("detected") || reason.toLowerCase().includes("inconsistency")) {
        iconClass = "fa-exclamation-triangle text-suspicious";
      }
      li.innerHTML = `<i class="fas ${iconClass}"></i> <span>${reason}</span>`;
      reasonsList.appendChild(li);
    });
  }

  // 4. Metadata Details Table
  const metadataTableBody = document.getElementById("metadata-table-body");
  if (metadataTableBody && data.metadata_info) {
    metadataTableBody.innerHTML = "";
    Object.entries(data.metadata_info).forEach(([key, val]) => {
      if (val !== null && val !== undefined) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td style="font-weight: 600; text-transform: capitalize;">${key.replace(/_/g, " ")}</td>
          <td style="font-family: var(--font-mono);">${val}</td>
        `;
        metadataTableBody.appendChild(tr);
      }
    });
  }

  // 5. Forensic Metrics & ELA Image Modal
  const elaContainer = document.getElementById("ela-container");
  if (elaContainer && data.ela_image_url) {
    elaContainer.innerHTML = `
      <div style="margin-top: 1rem;">
        <h4 style="margin-bottom: 0.5rem;"><i class="fas fa-eye"></i> Error Level Analysis (ELA) Heatmap</h4>
        <img src="${data.ela_image_url}" class="preview-media" style="border: 1px solid var(--border-accent);" alt="ELA Heatmap">
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.5rem;">Brighter highlighted regions indicate elevated JPEG compression error difference (potential local modifications).</p>
      </div>
    `;
  }

  // 6. Chart.js Visualization
  renderChart(data);
}

function renderChart(data) {
  const ctx = document.getElementById("resultsChart");
  if (!ctx || typeof Chart === "undefined") return;

  const aiVal = data.ai_score !== null ? data.ai_score : 0;
  const metaVal = data.metadata_score || 0;
  const forensicVal = data.forensic_score || 0;
  const elaVal = data.forensics_info.ela_score || 0;
  const noiseVal = data.forensics_info.noise_variance || 0;

  new Chart(ctx, {
    type: "radar",
    data: {
      labels: ["AI Neural Model", "EXIF Metadata", "Digital Forensics", "ELA Compression", "Noise Variance"],
      datasets: [{
        label: "Risk Index (%)",
        data: [aiVal, metaVal, forensicVal, elaVal, noiseVal],
        backgroundColor: "rgba(6, 182, 212, 0.2)",
        borderColor: "#06b6d4",
        pointBackgroundColor: "#38bdf8",
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      scales: {
        r: {
          angleLines: { color: "rgba(255, 255, 255, 0.1)" },
          grid: { color: "rgba(255, 255, 255, 0.1)" },
          pointLabels: { color: "#94a3b8", font: { family: "Inter", size: 12 } },
          ticks: { color: "#64748b", backdropColor: "transparent" },
          suggestedMin: 0,
          suggestedMax: 100
        }
      },
      plugins: {
        legend: { labels: { color: "#f8fafc", font: { family: "Inter" } } }
      }
    }
  });
}
