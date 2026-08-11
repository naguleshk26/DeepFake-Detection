/**
 * DeepGuard Analysis History Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  const historyTableBody = document.getElementById("history-table-body");
  const searchInput = document.getElementById("search-input");
  const typeFilter = document.getElementById("type-filter");

  if (!historyTableBody) return;

  loadHistory();

  if (searchInput) {
    searchInput.addEventListener("input", debounce(() => loadHistory(), 300));
  }

  if (typeFilter) {
    typeFilter.addEventListener("change", () => loadHistory());
  }

  async function loadHistory() {
    try {
      const search = searchInput ? searchInput.value.trim() : "";
      const fileType = typeFilter ? typeFilter.value : "";

      let url = "/api/analysis?limit=50";
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (fileType) url += `&file_type=${encodeURIComponent(fileType)}`;

      const response = await fetch(url);
      if (!response.ok) throw new Error("Failed to fetch analysis history.");

      const data = await response.json();
      renderHistoryTable(data);
    } catch (err) {
      showToast(err.message || "Could not load history.", "error");
    }
  }

  function renderHistoryTable(items) {
    historyTableBody.innerHTML = "";

    if (items.length === 0) {
      historyTableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2.5rem;">
            <i class="fas fa-inbox" style="font-size: 2rem; margin-bottom: 0.5rem; display: block;"></i>
            No previous analysis records found.
          </td>
        </tr>
      `;
      return;
    }

    items.forEach(item => {
      const tr = document.createElement("tr");

      const badgeClass = item.result.includes("AUTHENTIC") ? "badge-authentic" :
                         item.result.includes("SUSPICIOUS") ? "badge-suspicious" : "badge-deepfake";

      const formattedDate = new Date(item.created_at).toLocaleString();

      tr.innerHTML = `
        <td style="font-family: var(--font-mono); font-size: 0.85rem;">${item.id.substring(0, 8)}...</td>
        <td style="font-weight: 600;">${item.filename}</td>
        <td><span class="badge" style="background: rgba(255,255,255,0.05); color: var(--text-secondary);">${item.file_type.toUpperCase()}</span></td>
        <td>${formatBytes(item.file_size)}</td>
        <td><span class="badge ${badgeClass}">${item.result}</span></td>
        <td style="font-family: var(--font-mono); font-weight: 700;">${Math.round(item.confidence_score)}%</td>
        <td style="font-size: 0.85rem; color: var(--text-muted);">${formattedDate}</td>
        <td>
          <div style="display: flex; gap: 0.5rem;">
            <a href="results.html?id=${item.id}" class="btn btn-secondary" style="padding: 0.35rem 0.75rem; font-size: 0.85rem;">
              <i class="fas fa-eye"></i> View
            </a>
            <button class="btn btn-danger btn-delete" data-id="${item.id}" style="padding: 0.35rem 0.75rem; font-size: 0.85rem;">
              <i class="fas fa-trash-alt"></i>
            </button>
          </div>
        </td>
      `;

      historyTableBody.appendChild(tr);
    });

    // Attach delete listeners
    document.querySelectorAll(".btn-delete").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        const id = e.currentTarget.getAttribute("data-id");
        if (confirm(`Are you sure you want to delete analysis record ${id}?`)) {
          await deleteRecord(id);
        }
      });
    });
  }

  async function deleteRecord(id) {
    try {
      const response = await fetch(`/api/analysis/${id}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Delete failed.");

      showToast("Analysis record deleted.", "success");
      loadHistory();
    } catch (err) {
      showToast(err.message || "Failed to delete record.", "error");
    }
  }

  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
});
