const ROLES = ["student", "teacher", "admin"];

const state = {
  tab: "diagnostics",
  diagnostic: "jobs",
  jobs: { status: "", session_id: "", search: "", limit: 25, offset: 0, total: 0 },
  chunks: { course_id: "", source_type: "", search: "", limit: 25, offset: 0, total: 0 },
  indexCourses: [],
  users: { search: "", limit: 25, offset: 0, total: 0 },
  courses: { search: "", limit: 25, offset: 0, total: 0 },
  teachers: [],
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
  ["diagnostics", "users", "courses"].forEach((t) =>
    $("panel-" + t).classList.toggle("hidden", t !== tab)
  );
  refresh();
}

function switchDiagnostic(diagnostic) {
  state.diagnostic = diagnostic;
  document.querySelectorAll(".diagnostic-tab").forEach((button) =>
    button.classList.toggle("active", button.dataset.diagnostic === diagnostic)
  );
  ["jobs", "dlq", "streams", "index", "health"].forEach((item) =>
    $("diagnostic-" + item).classList.toggle("hidden", item !== diagnostic)
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
    <tr class="clickable" data-job-id="${escapeHtml(j.id)}" title="Открыть детали job">
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

function showModal(id) {
  $(id).classList.remove("hidden");
}

function closeModal(id) {
  $(id).classList.add("hidden");
}

function distanceLabel(value) {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  return isNaN(number) ? escapeHtml(value) : number.toFixed(4);
}

function renderJobDetail(job) {
  const sources = Array.isArray(job.sources) ? job.sources : [];
  const sourceRows = sources.length
    ? sources
        .map((source) => {
          const chunkCell =
            source.chunk_id === null || source.chunk_id === undefined
              ? "—"
              : `<button type="button" class="link-btn mono" data-chunk-id="${escapeHtml(source.chunk_id)}">${escapeHtml(source.chunk_id)}</button>`;
          const courseName = source.course_title || source.course_id || "—";
          const courseCell = source.course_url
            ? `<a href="${escapeHtml(source.course_url)}">${escapeHtml(courseName)}</a>`
            : escapeHtml(courseName);
          return `<tr>
            <td>${chunkCell}</td>
            <td>${courseCell}</td>
            <td>${escapeHtml(source.lesson || "—")}</td>
            <td>${escapeHtml(source.source_type || "—")}</td>
            <td>${distanceLabel(source.distance)}</td>
          </tr>`;
        })
        .join("")
    : '<tr><td colspan="5" class="muted">источники не сохранены</td></tr>';
  return `
    <dl class="detail-grid">
      <dt>Job ID</dt><dd class="mono">${escapeHtml(job.id)}</dd>
      <dt>Session</dt><dd>${escapeHtml(job.session_id)}</dd>
      <dt>Статус</dt><dd>${statusBadge(job.status)}</dd>
      <dt>Попытки</dt><dd>${job.attempts ?? 0}</dd>
      <dt>Создан</dt><dd>${fmt(job.created_at)}</dd>
      <dt>Обновлён</dt><dd>${fmt(job.updated_at)}</dd>
    </dl>
    <div class="detail-block"><h3>Вопрос</h3><pre class="detail-text">${escapeHtml(job.question || "—")}</pre></div>
    ${job.rewritten_question ? `<div class="detail-block"><h3>Переписанный вопрос</h3><pre class="detail-text">${escapeHtml(job.rewritten_question)}</pre></div>` : ""}
    <div class="detail-block"><h3>Ответ</h3><pre class="detail-text">${escapeHtml(job.answer || "—")}</pre></div>
    ${job.error ? `<div class="detail-block"><h3>Ошибка</h3><pre class="detail-text error-text">${escapeHtml(job.error)}</pre></div>` : ""}
    <div class="detail-block">
      <h3>Источники</h3>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Chunk</th><th>Курс</th><th>Урок</th><th>Тип</th><th>Distance</th></tr></thead>
          <tbody>${sourceRows}</tbody>
        </table>
      </div>
    </div>`;
}

async function openJob(jobId) {
  $("job-detail").innerHTML = '<p class="muted">загрузка…</p>';
  showModal("job-modal");
  try {
    const job = await getJSON("/api/v1/admin/jobs/" + encodeURIComponent(jobId));
    const detail = $("job-detail");
    detail.innerHTML = renderJobDetail(job);
    detail.querySelectorAll("[data-chunk-id]").forEach((button) => {
      button.addEventListener("click", () => openChunk(button.dataset.chunkId));
    });
  } catch (err) {
    $("job-detail").innerHTML = `<p class="muted">Не удалось загрузить job: ${escapeHtml(err.message)}</p>`;
  }
}

function renderChunkDetail(chunk) {
  return `
    <dl class="detail-grid">
      <dt>ID</dt><dd>${escapeHtml(chunk.id)}</dd>
      <dt>Курс</dt><dd>${escapeHtml(chunk.course_title || "—")} <span class="muted">(${chunk.course_id ?? "—"})</span></dd>
      <dt>Урок</dt><dd>${escapeHtml(chunk.lesson_title || "—")} <span class="muted">(${chunk.lesson_id ?? "—"})</span></dd>
      <dt>Шаг</dt><dd>${chunk.step_id ?? "—"}</dd>
      <dt>Тип</dt><dd>${escapeHtml(chunk.source_type)}</dd>
      <dt>Индекс</dt><dd>${chunk.chunk_index}</dd>
      <dt>Эмбеддинг</dt><dd>${chunk.has_embedding ? escapeHtml(chunk.model_name || "есть") : "нет"}</dd>
      <dt>Размерность</dt><dd>${chunk.embedding_dimension ?? "—"}</dd>
      <dt>Создан</dt><dd>${fmt(chunk.created_at)}</dd>
    </dl>
    <div class="detail-block"><h3>Текст чанка</h3><pre class="detail-text">${escapeHtml(chunk.chunk_text)}</pre></div>`;
}

async function openChunk(chunkId) {
  $("chunk-detail").innerHTML = '<p class="muted">загрузка…</p>';
  showModal("chunk-modal");
  try {
    const chunk = await getJSON("/api/v1/admin/chunks/" + encodeURIComponent(chunkId));
    $("chunk-detail").innerHTML = renderChunkDetail(chunk);
  } catch (err) {
    $("chunk-detail").innerHTML = `<p class="muted">Не удалось загрузить чанк: ${escapeHtml(err.message)}</p>`;
  }
}

function renderIndex(data) {
  $("index-total-chunks").textContent = data.total_chunks || 0;
  $("index-total-embeddings").textContent = data.total_embeddings || 0;
  $("index-without-embedding").textContent = data.chunks_without_embedding || 0;
  $("index-meta").textContent = `Модель: ${data.model_name || "—"} · размерность: ${data.dimension ?? "—"} · последний эмбеддинг: ${fmt(data.last_embedding_at)}`;

  const types = Object.entries(data.by_source_type || {});
  $("index-types-body").innerHTML = types.length
    ? types.map(([name, count]) => `<tr><td class="mono">${escapeHtml(name)}</td><td>${count}</td></tr>`).join("")
    : '<tr><td colspan="2" class="muted">нет данных</td></tr>';

  const courses = data.courses || [];
  state.indexCourses = courses;
  $("index-courses-body").innerHTML = courses.length
    ? courses
        .map(
          (course) => `<tr>
            <td>${escapeHtml(course.title)}</td>
            <td>${course.chunks}</td>
            <td>${course.description_chunks}</td>
            <td>${course.step_chunks}</td>
            <td>${course.embeddings}</td>
            <td>${course.without_embedding}</td>
          </tr>`
        )
        .join("")
    : '<tr><td colspan="6" class="muted">нет данных</td></tr>';

  const select = $("ch-course");
  select.innerHTML =
    '<option value="">все</option>' +
    courses
      .map((course) => `<option value="${course.id}">${escapeHtml(course.title)}</option>`)
      .join("");
  if (state.chunks.course_id && courses.some((course) => String(course.id) === state.chunks.course_id)) {
    select.value = state.chunks.course_id;
  } else {
    state.chunks.course_id = "";
    select.value = "";
  }
}

async function loadIndex() {
  try {
    const data = await getJSON("/api/v1/admin/index");
    renderIndex(data);
  } catch (err) {
    showError("Не удалось загрузить индекс: " + err.message);
    return;
  }
  await loadChunks();
}

function renderChunks(items) {
  const body = $("chunks-body");
  if (!items.length) {
    body.innerHTML = '<tr><td colspan="7" class="muted">пусто</td></tr>';
    return;
  }
  body.innerHTML = items
    .map(
      (chunk) => `
    <tr class="clickable" data-chunk-id="${escapeHtml(chunk.id)}" title="Открыть текст чанка">
      <td class="mono">${escapeHtml(chunk.id)}</td>
      <td>${escapeHtml(chunk.course_title || "—")}</td>
      <td>${escapeHtml(chunk.lesson_title || "—")}</td>
      <td class="mono">${escapeHtml(chunk.source_type)}</td>
      <td class="truncate" title="${escapeHtml(chunk.preview)}">${escapeHtml(chunk.preview)}</td>
      <td>${chunk.has_embedding ? `<span class="badge done">${escapeHtml(chunk.model_name || "есть")}</span>` : '<span class="badge failed">нет</span>'}</td>
      <td class="muted">${fmt(chunk.created_at)}</td>
    </tr>`
    )
    .join("");
}

async function loadChunks() {
  const p = new URLSearchParams();
  if (state.chunks.course_id) p.set("course_id", state.chunks.course_id);
  if (state.chunks.source_type) p.set("source_type", state.chunks.source_type);
  if (state.chunks.search) p.set("search", state.chunks.search);
  p.set("limit", state.chunks.limit);
  p.set("offset", state.chunks.offset);
  try {
    const data = await getJSON("/api/v1/admin/chunks?" + p.toString());
    state.chunks.total = data.total;
    renderChunks(data.items);
    const from = data.total === 0 ? 0 : data.offset + 1;
    const to = Math.min(data.offset + data.limit, data.total);
    $("chunks-page").textContent = `${from}–${to} из ${data.total}`;
    $("chunks-prev").disabled = data.offset <= 0;
    $("chunks-next").disabled = data.offset + data.limit >= data.total;
  } catch (err) {
    showError("Не удалось загрузить чанки: " + err.message);
  }
}

function renderHealth(data) {
  ["postgres", "redis", "ollama"].forEach((name) => {
    const card = $("dep-" + name);
    const value = (data.dependencies || {})[name] || "неизвестно";
    const ok = value === "ok";
    card.classList.toggle("ok", ok);
    card.classList.toggle("bad", !ok);
    card.querySelector(".health-state").textContent = value;
  });
  $("health-ollama-model").textContent = data.ollama_model
    ? `Модель ${data.ollama_model}: ${data.ollama_model_available ? "загружена" : "не найдена"}`
    : "Модель эмбеддингов не настроена";

  const jobs = data.jobs || {};
  const rows = [
    ["Последний done", jobs.last_done_at],
    ["Последний failed", jobs.last_failed_at],
    ["Самый старый queued", jobs.oldest_queued_at],
  ];
  $("health-jobs-body").innerHTML = rows
    .map(([label, value]) => `<tr><td>${label}</td><td class="muted">${fmt(value)}</td></tr>`)
    .join("");

  const settings = data.settings || {};
  $("health-settings").innerHTML = `
    <dt>Модель</dt><dd class="mono">${escapeHtml(settings.embedding_model || "—")}</dd>
    <dt>Размерность</dt><dd>${settings.embedding_dimension ?? "—"}</dd>
    <dt>Top-K</dt><dd>${settings.retrieval_top_k ?? "—"}</dd>`;
}

async function loadHealth() {
  try {
    const data = await getJSON("/api/v1/admin/health");
    renderHealth(data);
  } catch (err) {
    showError("Не удалось загрузить состояние: " + err.message);
  }
}

function renderDlq(items) {
  const body = $("dlq-body");
  if (!items.length) {
    body.innerHTML = '<tr><td colspan="7" class="muted">пусто</td></tr>';
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
    body.innerHTML = '<tr><td colspan="6" class="muted">пусто</td></tr>';
    return;
  }
  body.innerHTML = items
    .map(
      (u) => `
    <tr data-user-id="${u.id}">
      <td>${u.id}</td>
      <td><input class="user-email mono" type="email" value="${escapeHtml(u.email)}" aria-label="Email"></td>
      <td><input class="user-name" value="${escapeHtml(u.name)}" aria-label="Имя"></td>
      <td>
        <select class="role-select">
          ${ROLES.map(
            (r) => `<option value="${r}" ${r === u.role ? "selected" : ""}>${r}</option>`
          ).join("")}
        </select>
      </td>
      <td><input class="user-password" type="password" minlength="6" placeholder="Не менять" aria-label="Новый пароль"></td>
      <td><button class="btn save-user" type="button">Сохранить</button></td>
      <td><button class="btn danger delete-user" type="button">Удалить</button></td>
    </tr>`
    )
    .join("");
  body.querySelectorAll(".save-user").forEach((btn) => {
    btn.addEventListener("click", () => {
      const row = btn.closest("tr");
      const payload = {
        email: row.querySelector(".user-email").value.trim(),
        name: row.querySelector(".user-name").value.trim(),
        role: row.querySelector(".role-select").value,
      };
      const password = row.querySelector(".user-password").value;
      if (!payload.email || !payload.name) { showError("Email и имя обязательны"); return; }
      if (password && password.length < 6) { showError("Новый пароль должен содержать минимум 6 символов"); return; }
      if (password) payload.password = password;
      saveUser(Number(row.dataset.userId), payload);
    });
  });
  body.querySelectorAll(".delete-user").forEach((btn) => {
    btn.addEventListener("click", () => {
      const row = btn.closest("tr");
      deleteUser(Number(row.dataset.userId), row.querySelector(".user-email").value);
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

async function saveUser(userId, payload) {
  try {
    const resp = await fetch("/api/v1/admin/users/" + userId, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}));
      showError(data.detail || "Не удалось сохранить пользователя");
      return;
    }
    state.teachers = [];
    await loadUsers();
  } catch (err) {
    showError("Не удалось сохранить пользователя: " + err.message);
  }
}

async function createUser(form) {
  const payload = {
    email: $("new-user-email").value.trim(),
    name: $("new-user-name").value.trim(),
    role: $("new-user-role").value,
    password: $("new-user-password").value,
  };
  try {
    const resp = await fetch("/api/v1/admin/users", {
      method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" },
      credentials: "same-origin", body: JSON.stringify(payload),
    });
    if (!resp.ok) { const data = await resp.json().catch(() => ({})); showError(data.detail || "Не удалось создать пользователя"); return; }
    form.reset();
    state.teachers = [];
    state.users.offset = 0;
    await loadUsers();
  } catch (err) { showError("Не удалось создать пользователя: " + err.message); }
}

async function deleteUser(userId, email) {
  if (!window.confirm(`Удалить пользователя ${email}? Будут удалены его прогресс, зачисления, чаты и сессии.`)) return;
  try {
    const resp = await fetch("/api/v1/admin/users/" + userId, { method: "DELETE", credentials: "same-origin" });
    if (!resp.ok) { const data = await resp.json().catch(() => ({})); showError(data.detail || "Не удалось удалить пользователя"); return; }
    state.teachers = [];
    if (state.users.offset > 0 && state.users.offset >= state.users.total - 1) state.users.offset -= state.users.limit;
    await loadUsers();
  } catch (err) { showError("Не удалось удалить пользователя: " + err.message); }
}

async function loadTeachers() {
  try {
    const data = await getJSON("/api/v1/admin/users?limit=200&offset=0");
    state.teachers = (data.items || []).filter((user) => user.role === "teacher");
  } catch (err) {
    showError("Не удалось загрузить преподавателей: " + err.message);
  }
}

function renderCourses(items) {
  const body = $("courses-body");
  if (!items.length) {
    body.innerHTML = '<tr><td colspan="8" class="muted">пусто</td></tr>';
    return;
  }
  body.innerHTML = items.map((course) => {
    const owners = [`<option value="" ${course.owner_id === null ? "selected" : ""}>Платформа / не назначен</option>`]
      .concat(state.teachers.map((teacher) => `<option value="${teacher.id}" ${teacher.id === course.owner_id ? "selected" : ""}>${escapeHtml(teacher.name)} · ${escapeHtml(teacher.email)}</option>`));
    return `<tr data-course-id="${course.id}">
      <td>${course.id}</td><td>${escapeHtml(course.title)}</td>
      <td><select class="course-owner">${owners.join("")}</select></td>
      <td>${course.lessons_count} уроков · ${course.steps_count} шагов</td><td>${course.students_count}</td>
      <td><label class="toggle-label"><input class="course-published" type="checkbox" ${course.is_published ? "checked" : ""}> опубликован</label></td>
      <td><button class="btn save-course" type="button">Сохранить</button></td>
      <td><button class="btn danger delete-course" type="button">Удалить</button></td>
    </tr>`;
  }).join("");
  body.querySelectorAll(".save-course").forEach((button) => button.addEventListener("click", () => {
    const row = button.closest("tr");
    saveCourse(Number(row.dataset.courseId), row.querySelector(".course-owner").value, row.querySelector(".course-published").checked);
  }));
  body.querySelectorAll(".delete-course").forEach((button) => button.addEventListener("click", () => {
    const row = button.closest("tr");
    const title = row.children[1].textContent;
    deleteCourse(Number(row.dataset.courseId), title);
  }));
}

async function loadCourses() {
  const p = new URLSearchParams();
  if (state.courses.search) p.set("search", state.courses.search);
  p.set("limit", state.courses.limit); p.set("offset", state.courses.offset);
  try {
    if (!state.teachers.length) await loadTeachers();
    const data = await getJSON("/api/v1/admin/courses?" + p.toString());
    state.courses.total = data.total;
    renderCourses(data.items);
    const from = data.total === 0 ? 0 : data.offset + 1;
    const to = Math.min(data.offset + data.limit, data.total);
    $("courses-page").textContent = `${from}–${to} из ${data.total}`;
    $("courses-prev").disabled = data.offset <= 0;
    $("courses-next").disabled = data.offset + data.limit >= data.total;
  } catch (err) { showError("Не удалось загрузить курсы: " + err.message); }
}

async function saveCourse(courseId, ownerId, isPublished) {
  try {
    const resp = await fetch("/api/v1/admin/courses/" + courseId, {
      method: "PATCH", headers: { "Content-Type": "application/json", Accept: "application/json" }, credentials: "same-origin",
      body: JSON.stringify({ owner_id: ownerId ? Number(ownerId) : null, is_published: isPublished }),
    });
    if (!resp.ok) { const data = await resp.json().catch(() => ({})); showError(data.detail || "Не удалось сохранить курс"); return; }
    await loadCourses();
  } catch (err) { showError("Не удалось сохранить курс: " + err.message); }
}

async function deleteCourse(courseId, title) {
  if (!window.confirm(`Удалить курс «${title}» вместе с его содержимым, прогрессом студентов и чатами?`)) return;
  try {
    const resp = await fetch("/api/v1/admin/courses/" + courseId, { method: "DELETE", credentials: "same-origin" });
    if (!resp.ok) { const data = await resp.json().catch(() => ({})); showError(data.detail || "Не удалось удалить курс"); return; }
    await loadCourses();
  } catch (err) { showError("Не удалось удалить курс: " + err.message); }
}

async function refresh() {
  if (state.tab === "diagnostics") {
    await loadOverview();
    if (state.diagnostic === "jobs") await loadJobs();
    else if (state.diagnostic === "dlq") await loadDlq();
    else if (state.diagnostic === "index") await loadIndex();
    else if (state.diagnostic === "health") await loadHealth();
  }
  else if (state.tab === "users") await loadUsers();
  else if (state.tab === "courses") await loadCourses();
}

function init() {
  document.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => switchTab(t.dataset.tab))
  );
  document.querySelectorAll(".diagnostic-tab").forEach((t) =>
    t.addEventListener("click", () => switchDiagnostic(t.dataset.diagnostic))
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
  $("user-create-form").addEventListener("submit", (event) => {
    event.preventDefault();
    createUser(event.currentTarget);
  });
  $("c-apply").addEventListener("click", () => { state.courses.search = $("c-search").value; state.courses.offset = 0; loadCourses(); });
  $("c-reset").addEventListener("click", () => { $("c-search").value = ""; state.courses.search = ""; state.courses.offset = 0; loadCourses(); });
  $("courses-prev").addEventListener("click", () => { state.courses.offset = Math.max(0, state.courses.offset - state.courses.limit); loadCourses(); });
  $("courses-next").addEventListener("click", () => { state.courses.offset += state.courses.limit; loadCourses(); });
  $("ch-apply").addEventListener("click", () => {
    state.chunks.course_id = $("ch-course").value;
    state.chunks.source_type = $("ch-source").value;
    state.chunks.search = $("ch-search").value;
    state.chunks.offset = 0;
    loadChunks();
  });
  $("ch-reset").addEventListener("click", () => {
    $("ch-course").value = "";
    $("ch-source").value = "";
    $("ch-search").value = "";
    state.chunks.course_id = "";
    state.chunks.source_type = "";
    state.chunks.search = "";
    state.chunks.offset = 0;
    loadChunks();
  });
  $("chunks-prev").addEventListener("click", () => {
    state.chunks.offset = Math.max(0, state.chunks.offset - state.chunks.limit);
    loadChunks();
  });
  $("chunks-next").addEventListener("click", () => {
    state.chunks.offset += state.chunks.limit;
    loadChunks();
  });
  $("jobs-body").addEventListener("click", (event) => {
    const row = event.target.closest("tr[data-job-id]");
    if (row) openJob(row.dataset.jobId);
  });
  $("chunks-body").addEventListener("click", (event) => {
    const row = event.target.closest("tr[data-chunk-id]");
    if (row) openChunk(row.dataset.chunkId);
  });
  document.querySelectorAll("[data-close]").forEach((button) =>
    button.addEventListener("click", () => closeModal(button.dataset.close))
  );
  document.querySelectorAll(".modal-backdrop").forEach((backdrop) =>
    backdrop.addEventListener("click", (event) => {
      if (event.target === backdrop) closeModal(backdrop.id);
    })
  );
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    ["chunk-modal", "job-modal"].forEach((id) => {
      if (!$(id).classList.contains("hidden")) closeModal(id);
    });
  });
  document.querySelectorAll("#status-cards .card").forEach((c) =>
    c.addEventListener("click", () => {
      switchTab("diagnostics");
      switchDiagnostic("jobs");
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
