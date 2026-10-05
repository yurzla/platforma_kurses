const ROLES = ["student", "teacher", "admin"];

const state = {
  tab: "jobs",
  jobs: { status: "", session_id: "", search: "", limit: 25, offset: 0, total: 0 },
  users: { search: "", limit: 25, offset: 0, total: 0 },
};

const $ = (id) => document.getElementById(id);

function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function fmt(value) {
  if (!value) return "—";
  const d = new Date(value);
  return isNaN(d) ? escapeHtml(value) : d.toLocaleString();
}

let errorTimer = null;
function showError(message) {
  const el = $("error-banner");
  el.textContent = message;
  el.classList.remove("hidden");
  clearTimeout(errorTimer);
  errorTimer = setTimeout(() => el.classList.add("hidden"), 6000);
}

async function getJSON(url) {
  const resp = await fetch(url, { headers: { Accept: "application/json" } });
  if (resp.status === 401) {
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = "/login?role=admin&next=" + next;
    throw new Error("401: требуется вход");
  }
  if (!resp.ok) throw new Error("HTTP " + resp.status);
  return resp.json();
}

function statusBadge(status) {
  return `<span class="badge ${escapeHtml(status)}">${escapeHtml(status)}</span>`;
}

function switchTab(tab) {
  state.tab = tab;
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
  ["jobs", "dlq", "streams", "users"].forEach((t) =>
    $("panel-" + t).classList.toggle("hidden", t !== tab)
  );
  refresh();
}

function renderStreams(streams) {
  const body = $("streams-body");
  if (!streams.length) {
    body.innerHTML = '<tr><td colspan="6" class="muted">нет данных</td></tr>';
    return;
  }
  body.innerHTML = streams
    .map(
      (s) => `
    <tr>
      <td class="mono">${escapeHtml(s.stream)}</td>
      <td class="mono">${escapeHtml(s.group)}</td>
      <td>${s.length ?? 0}</td>
      <td>${s.pending ?? "—"}</td>
      <td>${s.lag ?? "—"}</td>
      <td>${s.consumers ?? "—"}</td>
    </tr>`
    )
    .join("");
}

async function loadOverview() {
  try {
    const data = await getJSON("/api/v1/admin/overview");
    const counts = data.status_counts || {};
    ["queued", "running", "done", "failed"].forEach((s) => {
      $("cnt-" + s).textContent = counts[s] || 0;
    });
    renderStreams(data.streams || []);
    $("updated").textContent = new Date().toLocaleTimeString();
  } catch (err) {
    showError("Не удалось загрузить overview: " + err.message);
  }
}

function renderJobs(items) {
  const body = $("jobs-body");
  if (!items.length) {
    body.innerHTML = '<tr><td colspan="8" class="muted">пусто</td></tr>';
    return;
  }
  body.innerHTML = items
    .map(
      (j) => `
    <tr>
      <td class="mono">${escapeHtml(j.id).slice(0, 8)}…</td>
      <td>${j.session_id}</td>
      <td>${statusBadge(j.status)}</td>
      <td>${j.attempts}</td>
      <td class="truncate" title="${escapeHtml(j.question)}">${escapeHtml(j.question)}</td>
      <td class="truncate muted" title="${escapeHtml(j.error || "")}">${escapeHtml(j.error || "")}</td>
      <td class="muted">${fmt(j.created_at)}</td>
      <td class="muted">${fmt(j.updated_at)}</td>
    </tr>`
    )
    .join("");
}

async function loadJobs() {
  const p = new URLSearchParams();
  if (state.jobs.status) p.set("status", state.jobs.status);
  if (state.jobs.session_id) p.set("session_id", state.jobs.session_id);
  if (state.jobs.search) p.set("search", state.jobs.search);
  p.set("limit", state.jobs.limit);
  p.set("offset", state.jobs.offset);
  try {
    const data = await getJSON("/api/v1/admin/jobs?" + p.toString());
    state.jobs.total = data.total;
    renderJobs(data.items);
    const from = data.total === 0 ? 0 : data.offset + 1;
    const to = Math.min(data.offset + data.limit, data.total);
    $("jobs-page").textContent = `${from}–${to} из ${data.total}`;
    $("jobs-prev").disabled = data.offset <= 0;
    $("jobs-next").disabled = data.offset + data.limit >= data.total;
  } catch (err) {
    showError("Не удалось загрузить jobs: " + err.message);
  }
}

function renderDlq(items) {
  const body = $("dlq-body");
  if (!items.length) {
    body.innerHTML = '<tr><td colspan="6" class="muted">пусто</td></tr>';
    return;
  }
  body.innerHTML = items
    .map(
      (e) => `
    <tr>
      <td class="mono">${escapeHtml(e.message_id)}</td>
      <td>${escapeHtml(e.task || "—")}</td>
      <td class="mono">${escapeHtml(e.job_id || "—")}</td>
      <td>${e.session_id ?? "—"}</td>
      <td class="truncate" title="${escapeHtml(e.error || "")}">${escapeHtml(e.error || "—")}</td>
      <td class="mono">${escapeHtml(e.source_stream || "—")}</td>
    </tr>`
    )
    .join("");
}

async function loadDlq() {
  try {
    const items = await getJSON("/api/v1/admin/dlq?limit=100");
    renderDlq(items);
  } catch (err) {
    showError("Не удалось загрузить DLQ: " + err.message);
  }
}

function renderUsers(items) {
  const body = $("users-body");
  if (!items.length) {
    body.innerHTML = '<tr><td colspan="5" class="muted">пусто</td></tr>';
    return;
  }
  body.innerHTML = items
    .map(
      (u) => `
    <tr data-user-id="${u.id}">
      <td>${u.id}</td>
      <td class="mono">${escapeHtml(u.email)}</td>
      <td>${escapeHtml(u.name)}</td>
      <td>
        <select class="role-select">
          ${ROLES.map(
            (r) => `<option value="${r}" ${r === u.role ? "selected" : ""}>${r}</option>`
          ).join("")}
        </select>
      </td>
      <td><button class="btn save-role" type="button">Сохранить</button></td>
    </tr>`
    )
    .join("");
  body.querySelectorAll(".save-role").forEach((btn) => {
    btn.addEventListener("click", () => {
      const row = btn.closest("tr");
      saveRole(Number(row.dataset.userId), row.querySelector(".role-select").value);
    });
  });
}

async function loadUsers() {
  const p = new URLSearchParams();
  if (state.users.search) p.set("search", state.users.search);
  p.set("limit", state.users.limit);
  p.set("offset", state.users.offset);
  try {
    const data = await getJSON("/api/v1/admin/users?" + p.toString());
    state.users.total = data.total;
    renderUsers(data.items);
    const from = data.total === 0 ? 0 : data.offset + 1;
    const to = Math.min(data.offset + data.limit, data.total);
    $("users-page").textContent = `${from}–${to} из ${data.total}`;
    $("users-prev").disabled = data.offset <= 0;
    $("users-next").disabled = data.offset + data.limit >= data.total;
  } catch (err) {
    showError("Не удалось загрузить пользователей: " + err.message);
  }
}

async function saveRole(userId, role) {
  try {
    const resp = await fetch("/api/v1/admin/users/" + userId, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ role: role }),
    });
    if (resp.status === 403) {
      showError("Нельзя менять собственную роль");
      return;
    }
    if (!resp.ok) {
      showError("Не удалось изменить роль: HTTP " + resp.status);
      return;
    }
    await loadUsers();
  } catch (err) {
    showError("Не удалось изменить роль: " + err.message);
  }
}

async function refresh() {
  await loadOverview();
  if (state.tab === "jobs") await loadJobs();
  else if (state.tab === "dlq") await loadDlq();
  else if (state.tab === "users") await loadUsers();
}

function init() {
  document.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => switchTab(t.dataset.tab))
  );
  $("f-apply").addEventListener("click", () => {
    state.jobs.status = $("f-status").value;
    state.jobs.session_id = $("f-session").value;
    state.jobs.search = $("f-search").value;
    state.jobs.offset = 0;
    loadJobs();
  });
  $("f-reset").addEventListener("click", () => {
    $("f-status").value = "";
    $("f-session").value = "";
    $("f-search").value = "";
    state.jobs.status = "";
    state.jobs.session_id = "";
    state.jobs.search = "";
    state.jobs.offset = 0;
    loadJobs();
  });
  $("jobs-prev").addEventListener("click", () => {
    state.jobs.offset = Math.max(0, state.jobs.offset - state.jobs.limit);
    loadJobs();
  });
  $("jobs-next").addEventListener("click", () => {
    state.jobs.offset += state.jobs.limit;
    loadJobs();
  });
  $("u-apply").addEventListener("click", () => {
    state.users.search = $("u-search").value;
    state.users.offset = 0;
    loadUsers();
  });
  $("u-reset").addEventListener("click", () => {
    $("u-search").value = "";
    state.users.search = "";
    state.users.offset = 0;
    loadUsers();
  });
  $("users-prev").addEventListener("click", () => {
    state.users.offset = Math.max(0, state.users.offset - state.users.limit);
    loadUsers();
  });
  $("users-next").addEventListener("click", () => {
    state.users.offset += state.users.limit;
    loadUsers();
  });
  document.querySelectorAll(".card").forEach((c) =>
    c.addEventListener("click", () => {
      switchTab("jobs");
      $("f-status").value = c.dataset.status;
      state.jobs.status = c.dataset.status;
      state.jobs.offset = 0;
      loadJobs();
    })
  );
}

document.addEventListener("DOMContentLoaded", () => {
  init();
  refresh();
  setInterval(refresh, 5000);
});
