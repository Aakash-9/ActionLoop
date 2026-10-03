const api = (path, options = {}) =>
  fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  }).then(async (res) => {
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
    return res.json();
  });

function escapeHtml(str) {
  return (str ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function setStatus(el, message, kind) {
  el.textContent = message;
  el.className = "status" + (kind ? " " + kind : "");
}

// ---------- navigation ----------
function initNav() {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("view-" + btn.dataset.view).classList.add("active");
      refreshView(btn.dataset.view);
    });
  });
}

function refreshView(view) {
  if (view === "review") loadReviewQueue();
  if (view === "meetings") loadMeetings();
  if (view === "initiatives") loadInitiatives();
}

// ---------- review queue ----------
let cachedInitiatives = [];

async function loadReviewQueue() {
  const list = document.getElementById("review-list");
  list.innerHTML = "<div class='empty'>Loading…</div>";
  try {
    const [items, initiatives] = await Promise.all([
      api("/action-items?status=pending_review"),
      api("/initiatives"),
    ]);
    cachedInitiatives = initiatives;
    if (!items.length) {
      list.innerHTML = "<div class='empty'>Nothing waiting on review.</div>";
      return;
    }
    list.innerHTML = items.map((item) => reviewCard(item)).join("");
    list.querySelectorAll("[data-action]").forEach((btn) => btn.addEventListener("click", onReviewAction));
  } catch (err) {
    list.innerHTML = `<div class='empty'>Failed to load: ${escapeHtml(err.message)}</div>`;
  }
}

function reviewCard(item) {
  const initiativeOptions = cachedInitiatives
    .map((i) => `<option value="${i.id}" ${item.initiative_id === i.id ? "selected" : ""}>${escapeHtml(i.name)}</option>`)
    .join("");
  return `
    <div class="card" data-id="${item.id}">
      <div class="card-row">
        <div>
          <p class="card-title">${escapeHtml(item.description)}</p>
          <div class="card-meta">
            <span class="badge badge-${item.priority}">${item.priority}</span>
            <span>owner: ${escapeHtml(item.owner) || "unassigned"}</span>
            <span>due: ${item.deadline || "—"}</span>
          </div>
        </div>
      </div>
      <div class="card-actions">
        <button class="btn-approve" data-action="approve">Approve</button>
        <button class="btn-reject" data-action="reject">Reject</button>
        <select data-action="assign">
          <option value="">Assign to initiative…</option>
          ${initiativeOptions}
        </select>
      </div>
    </div>`;
}

async function onReviewAction(e) {
  const card = e.target.closest(".card");
  const id = card.dataset.id;
  const action = e.target.dataset.action;

  try {
    if (action === "approve") await api(`/action-items/${id}`, { method: "PATCH", body: JSON.stringify({ status: "approved" }) });
    if (action === "reject") await api(`/action-items/${id}`, { method: "PATCH", body: JSON.stringify({ status: "rejected" }) });
    if (action === "assign") {
      const initiativeId = e.target.value;
      if (!initiativeId) return;
      await api(`/action-items/${id}`, { method: "PATCH", body: JSON.stringify({ initiative_id: Number(initiativeId) }) });
    }
    loadReviewQueue();
  } catch (err) {
    alert("Failed: " + err.message);
  }
}

// ---------- meetings ----------
async function loadMeetings() {
  const list = document.getElementById("meetings-list");
  list.innerHTML = "<div class='empty'>Loading…</div>";
  try {
    const meetings = await api("/meetings");
    if (!meetings.length) {
      list.innerHTML = "<div class='empty'>No meetings yet.</div>";
      return;
    }
    list.innerHTML = meetings
      .map(
        (m) => `
        <div class="card">
          <p class="card-title">${escapeHtml(m.title)}</p>
          <div class="card-meta"><span>${m.action_items.length} action item(s) extracted</span></div>
        </div>`
      )
      .join("");
  } catch (err) {
    list.innerHTML = `<div class='empty'>Failed to load: ${escapeHtml(err.message)}</div>`;
  }
}

document.getElementById("transcript-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const statusEl = document.getElementById("transcript-status");
  const title = document.getElementById("meeting-title").value;
  const transcript = document.getElementById("meeting-transcript").value;
  setStatus(statusEl, "Extracting…");
  try {
    const meeting = await api("/meetings", { method: "POST", body: JSON.stringify({ title, transcript }) });
    setStatus(statusEl, `Done — ${meeting.action_items.length} action item(s) sent to review.`, "ok");
    e.target.reset();
    loadMeetings();
  } catch (err) {
    setStatus(statusEl, err.message, "error");
  }
});

document.getElementById("audio-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const statusEl = document.getElementById("audio-status");
  const title = document.getElementById("audio-title").value;
  const file = document.getElementById("audio-file").files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  setStatus(statusEl, "Transcribing (this can take a while locally)…");
  try {
    const res = await fetch(`/meetings/upload-audio?title=${encodeURIComponent(title)}`, { method: "POST", body: formData });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
    const meeting = await res.json();
    setStatus(statusEl, `Done — ${meeting.action_items.length} action item(s) sent to review.`, "ok");
    e.target.reset();
    loadMeetings();
  } catch (err) {
    setStatus(statusEl, err.message, "error");
  }
});

// ---------- initiatives ----------
async function loadInitiatives() {
  const list = document.getElementById("initiatives-list");
  list.innerHTML = "<div class='empty'>Loading…</div>";
  try {
    const initiatives = await api("/initiatives");
    cachedInitiatives = initiatives;
    if (!initiatives.length) {
      list.innerHTML = "<div class='empty'>No initiatives yet.</div>";
      return;
    }
    list.innerHTML = initiatives
      .map(
        (i) => `
        <div class="card">
          <div class="card-row">
            <div>
              <p class="card-title">${escapeHtml(i.name)}</p>
              <div class="card-meta">${escapeHtml(i.description) || ""}</div>
            </div>
            <span class="badge badge-${i.status}">${i.status.replace("_", " ")}</span>
          </div>
          <div class="card-meta" style="margin-top:10px">
            <span>${i.total_items} total</span>
            <span class="badge badge-done">${i.done_items} done</span>
            ${i.overdue_items ? `<span class="badge badge-overdue">${i.overdue_items} overdue</span>` : ""}
          </div>
        </div>`
      )
      .join("");
  } catch (err) {
    list.innerHTML = `<div class='empty'>Failed to load: ${escapeHtml(err.message)}</div>`;
  }
}

document.getElementById("initiative-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const statusEl = document.getElementById("initiative-status");
  const name = document.getElementById("initiative-name").value;
  const description = document.getElementById("initiative-desc").value;
  try {
    await api("/initiatives", { method: "POST", body: JSON.stringify({ name, description }) });
    setStatus(statusEl, "Created.", "ok");
    e.target.reset();
    loadInitiatives();
  } catch (err) {
    setStatus(statusEl, err.message, "error");
  }
});

// ---------- reports ----------
document.getElementById("generate-report").addEventListener("click", async () => {
  const statusEl = document.getElementById("report-status");
  try {
    const result = await api("/reports/weekly/generate", { method: "POST" });
    setStatus(statusEl, `Saved to ${result.path}`, "ok");
  } catch (err) {
    setStatus(statusEl, err.message, "error");
  }
});

document.getElementById("preview-report").addEventListener("click", async () => {
  const statusEl = document.getElementById("report-status");
  const output = document.getElementById("report-output");
  try {
    const result = await api("/reports/weekly/preview");
    output.textContent = result.report;
    setStatus(statusEl, "");
  } catch (err) {
    setStatus(statusEl, err.message, "error");
  }
});

// ---------- init ----------
initNav();
loadReviewQueue();
