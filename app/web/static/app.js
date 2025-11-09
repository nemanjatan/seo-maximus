const form = document.getElementById("optimize-form");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");
const resultsSection = document.getElementById("results");
const resultBody = document.getElementById("result-body");

const API_BASE = "/v1/images";

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const targetUrl = formData.get("target_url");
  const sourceUrl = formData.get("source_url");
  const prefetch = formData.get("prefetch") === "on";
  const formats = Array.from(formData.getAll("formats")).filter(Boolean);

  const payload = {
    target_page_url: targetUrl,
    formats: formats.length ? formats : ["webp"],
    prefetch,
  };

  if (sourceUrl) {
    payload.source_url = sourceUrl;
  }

  setStatus("Submitting job …", false);
  toggleForm(false);

  try {
    const response = await fetch(`${API_BASE}/convert`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer dev-token",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "Request failed");
    }

    const { job_id, status } = await response.json();
    setStatus(`Job ${job_id} queued`, false);
    await pollJob(job_id);
  } catch (error) {
    console.error(error);
    setStatus(error.message || "Something went wrong", true);
    toggleForm(true);
  }
});

async function pollJob(jobId, attempt = 0) {
  const maxAttempts = 40;
  const intervalMs = 1500;

  try {
    const response = await fetch(`${API_BASE}/${jobId}`, {
      headers: { Authorization: "Bearer dev-token" },
    });
    if (!response.ok) {
      throw new Error("Unable to fetch job status");
    }
    const data = await response.json();

    if (data.status === "completed" && data.result) {
      renderResult(data);
      setStatus("Optimization completed.", false);
      toggleForm(true);
      return;
    }

    if (data.status === "failed") {
      throw new Error(data.error || "Job failed");
    }

    if (attempt >= maxAttempts) {
      throw new Error("Timed out waiting for job");
    }

    setStatus(`Job ${jobId} processing …`, false);
    setTimeout(() => pollJob(jobId, attempt + 1), intervalMs);
  } catch (error) {
    console.error(error);
    setStatus(error.message || "Something went wrong", true);
    toggleForm(true);
  }
}

function renderResult(job) {
  const { result } = job;
  if (!result) return;

  resultsSection.classList.remove("hidden");
  const detected = result.detected_image;
  const heroMeta = detected
    ? `
      <div class="meta-grid">
        <div><span>Detected Source:</span> ${escapeHtml(detected.source_url)}</div>
        <div><span>Selector:</span> <code>${escapeHtml(detected.selector)}</code></div>
        <div><span>Score:</span> ${detected.score.toFixed(1)}</div>
        <div><span>Visible Area:</span> ${Math.round(detected.position.visible_area).toLocaleString()} px²</div>
      </div>
    `
    : "<p>No hero image detected (manual source used).</p>";

  const assetsList = result.optimized_assets
    .map((asset, index) => {
      const title = `${asset.format.toUpperCase()} (${formatBytes(asset.bytes)} • saved ${asset.savings_percent}% )`;
      const copyId = `asset-url-${index}`;
      return `
        <article class="result-section">
          <h3>${title}</h3>
          <div class="optimized-images">
            <img src="${asset.url}" alt="Optimized ${asset.format}" />
            <button type="button" class="copy-btn" data-target="${copyId}">Copy Image Data URL</button>
            <textarea id="${copyId}" class="code-block" readonly>${asset.url}</textarea>
          </div>
        </article>
      `;
    })
    .join("");

  const snippetBlock = result.img_snippet
    ? `
      <article class="result-section">
        <h3>Inline Snippet</h3>
        <textarea class="code-block" readonly>${result.img_snippet}</textarea>
      </article>
    `
    : "";

  const prefetchBlock = result.prefetch_tag
    ? `
      <article class="result-section">
        <h3>Prefetch Tag</h3>
        <textarea class="code-block" readonly>${result.prefetch_tag}</textarea>
      </article>
    `
    : "";

  resultBody.innerHTML = `
    <div class="result-grid">
      <article class="result-section">
        <h3>Detected Hero (Mobile viewport)</h3>
        ${heroMeta}
      </article>
      ${assetsList}
      ${snippetBlock}
      ${prefetchBlock}
    </div>
  `;

  attachCopyHandlers();
}

function attachCopyHandlers() {
  document.querySelectorAll(".copy-btn").forEach((button) => {
    button.addEventListener("click", async () => {
      const targetId = button.dataset.target;
      const textarea = document.getElementById(targetId);
      if (!textarea) return;
      try {
        await navigator.clipboard.writeText(textarea.value);
        button.textContent = "Copied!";
        setTimeout(() => (button.textContent = "Copy Image Data URL"), 1600);
      } catch (err) {
        console.error(err);
        button.textContent = "Copy failed";
        setTimeout(() => (button.textContent = "Copy Image Data URL"), 1600);
      }
    });
  });
}

function setStatus(message, isError) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", Boolean(isError));
}

function toggleForm(enable) {
  submitBtn.disabled = !enable;
  form.querySelectorAll("input, select, button").forEach((el) => {
    if (el !== submitBtn) el.disabled = !enable;
  });
}

function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

